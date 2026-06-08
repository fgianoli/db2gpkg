"""
PG2GPKG - Import engine (GeoPackage → PostgreSQL/PostGIS)
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import os

try:
    from osgeo import gdal, ogr
    HAS_GDAL = True
except ImportError:
    HAS_GDAL = False

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeedback,
    QgsMessageLog,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    Qgis,
)
from qgis.PyQt.QtCore import QThread, pyqtSignal

from .db_utils import (
    drop_table_cascade,
    get_table_columns,
    normalize_sslmode,
    pg_connect,
    rename_table_columns,
    table_exists,
)

LOG_TAG = "PG2GPKG"

# Transient PostgreSQL errors that warrant an automatic retry.
# Match is case-insensitive on the full message returned by psycopg2/GDAL.
_TRANSIENT_PATTERNS = (
    "the database system is in recovery mode",
    "the database system is starting up",
    "the database system is shutting down",
    "terminating connection due to administrator command",
    "server closed the connection unexpectedly",
    "connection reset by peer",
    "could not connect to server",
    "no connection to the server",
    "connection refused",
    "too many connections",
    "remaining connection slots are reserved",
    "ssl syscall error",
)

# Backoff schedule in seconds between retry attempts (one entry per retry).
_RETRY_BACKOFF = (2, 5, 10)


def is_transient_error(message):
    """True if the error message looks like a recoverable transient PG error."""
    if not message:
        return False
    s = message.lower()
    return any(p in s for p in _TRANSIENT_PATTERNS)


# ============================================================================
# GeoPackage inspection
# ============================================================================

def list_gpkg_layers(gpkg_path):
    """
    Return list of dicts describing layers in a GeoPackage.
    Each dict: {name, geom_type, srid, crs_str, count, fields}
    fields: list of {name, type, type_pg}
    """
    if not HAS_GDAL:
        return []

    ds = ogr.Open(gpkg_path)
    if ds is None:
        return []

    layers = []
    try:
        for i in range(ds.GetLayerCount()):
            lyr = ds.GetLayerByIndex(i)
            name = lyr.GetName()

            wkb = lyr.GetGeomType()
            geom_type = ogr.GeometryTypeToName(wkb) if wkb != ogr.wkbNone else None

            srs = lyr.GetSpatialRef()
            srid = None
            crs_str = "—"
            if srs:
                try:
                    srs.AutoIdentifyEPSG()
                except Exception:
                    pass
                code = srs.GetAuthorityCode(None)
                if code:
                    srid = int(code)
                    crs_str = f"EPSG:{srid}"
                else:
                    crs_str = srs.GetName() or "Unknown"

            count = lyr.GetFeatureCount()

            defn = lyr.GetLayerDefn()
            fields = []
            for fi in range(defn.GetFieldCount()):
                fd = defn.GetFieldDefn(fi)
                fields.append({
                    "name": fd.GetName(),
                    "type": fd.GetTypeName(),
                    "type_pg": _ogr_to_pg_type(fd.GetTypeName()),
                })

            layers.append({
                "name": name,
                "geom_type": geom_type,
                "srid": srid,
                "crs_str": crs_str,
                "count": count,
                "fields": fields,
            })
    finally:
        ds = None

    return layers


def read_gpkg_preview(gpkg_path, layer_name, limit=50):
    """
    Read the first `limit` features of a GPKG layer.
    Returns (column_names, rows) where rows is a list of tuples (str values).
    """
    if not HAS_GDAL:
        return [], []

    ds = ogr.Open(gpkg_path)
    if ds is None:
        return [], []

    try:
        lyr = ds.GetLayerByName(layer_name)
        if lyr is None:
            return [], []
        defn = lyr.GetLayerDefn()
        cols = [defn.GetFieldDefn(i).GetName() for i in range(defn.GetFieldCount())]
        wkb = lyr.GetGeomType()
        if wkb != ogr.wkbNone:
            cols.append("geometry")

        rows = []
        for n, feat in enumerate(lyr):
            if n >= limit:
                break
            vals = [feat.GetField(i) for i in range(defn.GetFieldCount())]
            if wkb != ogr.wkbNone:
                geom = feat.GetGeometryRef()
                gname = geom.GetGeometryName() if geom else "NULL"
                vals.append(gname)
            rows.append(tuple("" if v is None else str(v) for v in vals))
        return cols, rows
    finally:
        ds = None


def _ogr_to_pg_type(ogr_type):
    """Map OGR field type names to PostgreSQL type hints (display only)."""
    mapping = {
        "Integer": "integer",
        "Integer64": "bigint",
        "Real": "double precision",
        "String": "text",
        "Date": "date",
        "Time": "time",
        "DateTime": "timestamp",
        "Binary": "bytea",
    }
    return mapping.get(ogr_type, ogr_type.lower())


# ============================================================================
# Append-mode column validation
# ============================================================================

def validate_append_columns(conn_params, schema, table, dest_columns):
    """
    Compare the destination columns we will write against the existing
    table columns. Returns (missing_in_table, missing_in_source, common).
    `missing_in_table` = we ship them but they don't exist in PG (will fail / be dropped)
    `missing_in_source` = exist in PG but we won't ship them (filled with NULL / default)
    """
    conn = pg_connect(conn_params)
    try:
        existing = set(get_table_columns(conn, schema, table))
    finally:
        conn.close()

    shipped = set(dest_columns)
    # PG-managed columns we generate automatically — ignore them as "missing"
    ignored = {"fid", "geom", "geometry"}

    missing_in_table = sorted(c for c in shipped - existing if c not in ignored)
    missing_in_source = sorted(c for c in existing - shipped if c not in ignored)
    common = sorted(shipped & existing)
    return missing_in_table, missing_in_source, common


# ============================================================================
# Single-layer import
# ============================================================================

def import_layer_to_pg(conn_params, gpkg_path, layer_name, target_schema,
                       target_table, mode="append", field_map=None,
                       target_srid=None, source_srid_override=None,
                       transform_context=None, feedback=None,
                       use_copy=True, create_spatial_index=True,
                       force_2d=False):
    """
    Import one GPKG layer into a PostgreSQL/PostGIS table.

    Strategy:
      * column exclusion is done via options.attributes (writer-level, no copy)
      * column rename is applied AFTER import via ALTER TABLE RENAME COLUMN
        (avoids loading the layer into a memory copy)
      * 'replace' issues DROP TABLE ... CASCADE explicitly via psycopg2
      * the password is exposed via PGPASSWORD env var rather than the DSN
      * QgsFeedback (if provided) reports feature-level progress

    :param conn_params: dict with host, port, database, username, password, sslmode
    :param gpkg_path: source .gpkg path
    :param layer_name: source layer name inside the GPKG
    :param target_schema: destination PostgreSQL schema
    :param target_table: destination PostgreSQL table
    :param mode: "append" | "replace" | "create"
    :param field_map: optional {src_col: dest_col}, columns absent are excluded
    :param target_srid: optional EPSG code to reproject to (e.g. 4326)
    :param source_srid_override: assign this EPSG as the source CRS if the layer has none
    :param transform_context: QgsCoordinateTransformContext from main thread
    :param feedback: optional QgsFeedback for live progress
    :returns: (success: bool, message: str, n_features: int)
    """
    # Prefix prepended to every error message so the caller can always tell
    # which layer and which destination triggered the failure.
    where = f"{layer_name} → {target_schema}.{target_table}"

    if not HAS_GDAL:
        return False, f"{where}: GDAL/OGR not available", 0

    src_uri = f"{gpkg_path}|layername={layer_name}"
    layer = QgsVectorLayer(src_uri, layer_name, "ogr")
    if not layer.isValid():
        return False, f"{where}: invalid source layer", 0

    # Assign source CRS if missing
    if source_srid_override and not layer.crs().isValid():
        crs = QgsCoordinateReferenceSystem.fromEpsgId(int(source_srid_override))
        if crs.isValid():
            layer.setCrs(crs)

    # ── Build the writer attribute whitelist (column exclusion) ──────
    attribute_indices = None
    renames = []         # [(field_index, original_name, final_name)]
    final_columns = []   # names that will land in PG after rename
    if field_map:
        attribute_indices = []
        for i, f in enumerate(layer.fields()):
            new_name = field_map.get(f.name())
            if not new_name:
                continue
            attribute_indices.append(i)
            if new_name != f.name():
                renames.append((i, f.name(), new_name))
            final_columns.append(new_name)
    else:
        final_columns = [f.name() for f in layer.fields()]

    # ── Mode handling: existence check + replace via DROP CASCADE ────
    conn = None
    try:
        conn = pg_connect(conn_params)
        exists = table_exists(conn, target_schema, target_table)

        if mode == "create" and exists:
            return False, (f"{where}: table already exists "
                           f"(use append or replace)"), 0

        if mode == "replace" and exists:
            try:
                drop_table_cascade(conn, target_schema, target_table)
                exists = False
                QgsMessageLog.logMessage(
                    f"Dropped {target_schema}.{target_table} CASCADE",
                    LOG_TAG, Qgis.Info)
            except Exception as e:
                return False, f"{where}: cannot drop table: {e}", 0
    except Exception as e:
        return False, f"{where}: cannot inspect destination: {e}", 0
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # ── Column-rename strategy ───────────────────────────────────────
    # create / replace : the writer creates the columns under their ORIGINAL
    #   names and we rename them afterwards via ALTER TABLE (fast, no copy).
    # append into an existing table : the destination columns already carry
    #   their FINAL names, so writing original names would not match. We apply
    #   the renames on an UNCOMMITTED edit buffer (the source GeoPackage is
    #   never modified) so the writer emits the final names directly, and we
    #   skip the post-import ALTER TABLE.
    renames_after = []   # [(written_name, final_name)] for create/replace
    appending = (mode == "append" and exists)
    if renames:
        if appending:
            if not layer.startEditing():
                return False, (f"{where}: cannot rename columns for append "
                               f"(could not open an edit buffer)"), 0
            for idx, _orig, new_name in renames:
                layer.renameAttribute(idx, new_name)
            # NB: intentionally NOT committed — keeps the .gpkg untouched.
        else:
            renames_after = [(orig, new) for _idx, orig, new in renames]

    # ── PG connection string for GDAL PostgreSQL driver ──────────────
    ssl = normalize_sslmode(conn_params.get("sslmode"))
    # NOTE: password is passed via PGPASSWORD env var, not in DSN
    pg_dsn = (
        f"PG:host={conn_params['host']} "
        f"port={conn_params['port']} "
        f"dbname={conn_params['database']} "
        f"user={conn_params['username']} "
        f"sslmode={ssl}"
    )

    layer_options = [
        f"SCHEMA={target_schema}",
        "GEOMETRY_NAME=geom",
        "FID=fid",
        f"SPATIAL_INDEX={'GIST' if create_spatial_index else 'NONE'}",
        "PRECISION=YES",
    ]
    if force_2d:
        # OGR's PG driver: DIM=2 forces XY output regardless of source dimension
        layer_options.append("DIM=2")

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "PostgreSQL"
    options.layerName = target_table
    options.fileEncoding = "UTF-8"
    options.layerOptions = layer_options
    if attribute_indices is not None:
        options.attributes = attribute_indices
    if feedback is not None:
        options.feedback = feedback

    if mode == "append" and exists:
        options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
    else:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

    # ── Reprojection ─────────────────────────────────────────────────
    ctx = transform_context or QgsProject.instance().transformContext()
    if target_srid:
        dest_crs = QgsCoordinateReferenceSystem.fromEpsgId(int(target_srid))
        if dest_crs.isValid() and layer.crs() != dest_crs:
            options.ct = QgsCoordinateTransform(layer.crs(), dest_crs, ctx)

    # ── Toggle COPY mode + isolate password via env var ──────────────
    prev_use_copy = gdal.GetConfigOption("PG_USE_COPY")
    gdal.SetConfigOption("PG_USE_COPY", "YES" if use_copy else "NO")
    prev_pgpassword = os.environ.get("PGPASSWORD")
    os.environ["PGPASSWORD"] = conn_params.get("password") or ""

    QgsMessageLog.logMessage(
        f"Writing {where} (copy={use_copy}, spatial_index={create_spatial_index}"
        f", 2d={force_2d}, n≈{layer.featureCount()})",
        LOG_TAG, Qgis.Info)

    try:
        err, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, pg_dsn, ctx, options
        )
    finally:
        gdal.SetConfigOption("PG_USE_COPY", prev_use_copy)
        if prev_pgpassword is None:
            os.environ.pop("PGPASSWORD", None)
        else:
            os.environ["PGPASSWORD"] = prev_pgpassword

    if err != QgsVectorFileWriter.NoError:
        return False, f"{where}: writer error: {msg}", 0

    n_feat = layer.featureCount()

    # ── Apply column renames via ALTER TABLE ─────────────────────────
    if renames_after:
        try:
            conn = pg_connect(conn_params)
            try:
                rename_table_columns(
                    conn, target_schema, target_table, renames_after)
            finally:
                conn.close()
            QgsMessageLog.logMessage(
                f"Renamed {len(renames_after)} column(s) on "
                f"{target_schema}.{target_table}", LOG_TAG, Qgis.Info)
        except Exception as e:
            return True, f"{where}: OK but rename failed: {e}", n_feat

    return True, f"OK: {where}", n_feat


# ============================================================================
# Import worker (QThread)
# ============================================================================

class ImportWorker(QThread):
    """
    Background thread for importing one or more GPKG layers into PostgreSQL.

    `jobs` is a list of dicts, one per layer to import:
        {
            "gpkg_path": str,
            "layer_name": str,
            "target_schema": str,
            "target_table": str,
            "mode": "append" | "replace" | "create",
            "field_map": {src_col: dest_col} or None,
            "target_srid": int or None,
            "source_srid_override": int or None,
            "feat_count": int,        # used for percentage scaling
        }
    """

    # step_done, total_steps, label, sub_percent (0-100), feat_count
    progress_updated = pyqtSignal(int, int, str, int)
    import_finished = pyqtSignal(dict)

    def __init__(self, conn_params, jobs, transform_context,
                 pause_between_layers_ms=0, parent=None):
        super().__init__(parent)
        self.conn_params = conn_params
        self.jobs = jobs
        self.transform_context = transform_context
        self.pause_between_layers_ms = max(0, int(pause_between_layers_ms))
        self._cancelled = False
        self._feedback = None

    def request_cancel(self):
        self._cancelled = True
        if self._feedback is not None:
            self._feedback.cancel()

    def run(self):
        errors = []
        failed_jobs = []
        ok_count = 0
        feat_total = 0
        total = len(self.jobs)

        for step, job in enumerate(self.jobs, start=1):
            if self._cancelled:
                # Anything not yet attempted is reported as a failed job
                # so the user can retry it.
                failed_jobs.append({
                    **job, "error": "cancelled before start"})
                continue

            label = f"{job['layer_name']} → {job['target_schema']}.{job['target_table']}"
            self.progress_updated.emit(step, total, label, 0)

            ok, msg, n = False, "", 0
            attempt = 0
            max_attempts = len(_RETRY_BACKOFF) + 1   # initial + retries

            while True:
                if self._cancelled:
                    break

                self._feedback = QgsFeedback()
                self._feedback.progressChanged.connect(
                    lambda pct, _step=step, _label=label:
                        self.progress_updated.emit(_step, total, _label, int(pct)))

                try:
                    ok, msg, n = import_layer_to_pg(
                        self.conn_params,
                        job["gpkg_path"],
                        job["layer_name"],
                        job["target_schema"],
                        job["target_table"],
                        mode=job.get("mode", "append"),
                        field_map=job.get("field_map"),
                        target_srid=job.get("target_srid"),
                        source_srid_override=job.get("source_srid_override"),
                        transform_context=self.transform_context,
                        feedback=self._feedback,
                        use_copy=job.get("use_copy", True),
                        create_spatial_index=job.get(
                            "create_spatial_index", True),
                        force_2d=job.get("force_2d", False),
                    )
                except Exception as e:
                    ok, msg, n = False, f"{label}: exception: {e}", 0

                self._feedback = None

                # Success, hard failure, or out of attempts → stop the loop.
                if ok or attempt >= max_attempts - 1 \
                        or not is_transient_error(msg):
                    break

                wait_sec = _RETRY_BACKOFF[attempt]
                attempt += 1
                QgsMessageLog.logMessage(
                    f"Transient error on {label}, retry "
                    f"{attempt}/{max_attempts - 1} in {wait_sec}s: {msg}",
                    LOG_TAG, Qgis.Warning)
                self.progress_updated.emit(
                    step, total,
                    f"{label} — retrying in {wait_sec}s "
                    f"(attempt {attempt + 1}/{max_attempts})", 0)
                # Cancel-aware sleep
                slept = 0.0
                while slept < wait_sec:
                    if self._cancelled:
                        break
                    self.msleep(200)
                    slept += 0.2

            if self._cancelled and not ok:
                msg = msg or f"{label}: cancelled during retry"

            if ok:
                ok_count += 1
                feat_total += n
            else:
                errors.append(msg)
                failed_jobs.append({**job, "error": msg})
            QgsMessageLog.logMessage(msg, LOG_TAG, Qgis.Info if ok else Qgis.Warning)

            # Optional pause between layers (give the server breathing room)
            if self.pause_between_layers_ms and step < total:
                slept = 0
                while slept < self.pause_between_layers_ms and not self._cancelled:
                    self.msleep(100)
                    slept += 100

        self.import_finished.emit({
            "ok_count": ok_count,
            "total": total,
            "feat_total": feat_total,
            "errors": errors,
            "failed_jobs": failed_jobs,
            "cancelled": self._cancelled,
        })
