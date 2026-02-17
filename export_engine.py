"""
PG2GPKG - Export engine
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import os
import re
import xml.etree.ElementTree as ET

from qgis.core import (
    QgsDataSourceUri,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject,
    QgsMessageLog,
    Qgis,
)
from qgis.PyQt.QtCore import QThread, QVariant, pyqtSignal

from .db_utils import normalize_sslmode, pg_connect, get_qgis_projects_in_db

LOG_TAG = "PG2GPKG"


def export_table_to_gpkg(conn_params, schema, table_info, gpkg_path,
                          layer_name_override=None, transform_context=None):
    """
    Export a single PostgreSQL table/view to a GeoPackage layer.

    :param conn_params: dict with host, port, database, username, password, sslmode
    :param schema: schema name
    :param table_info: dict with table, geom_column, geom_type, srid, table_type
    :param gpkg_path: output GeoPackage file path
    :param layer_name_override: optional layer name in the GPKG
    :param transform_context: QgsCoordinateTransformContext (pass from main thread)
    :returns: tuple (success: bool, message: str)
    """
    ssl_map = {
        "disable": 0, "allow": 1, "prefer": 2,
        "require": 3, "verify-ca": 4, "verify-full": 5,
    }
    uri = QgsDataSourceUri()
    uri.setConnection(
        conn_params["host"], str(conn_params["port"]), conn_params["database"],
        conn_params["username"], conn_params["password"],
        QgsDataSourceUri.SslMode(
            ssl_map.get(normalize_sslmode(conn_params.get("sslmode")), 2)),
    )

    table_name = table_info["table"]
    geom_column = table_info["geom_column"]

    if geom_column:
        uri.setDataSource(schema, table_name, geom_column)
    else:
        uri.setDataSource(schema, table_name, None)

    # Detect primary key
    try:
        c = pg_connect(conn_params)
        try:
            cur = c.cursor()
            cur.execute("""
                SELECT a.attname FROM pg_index i
                JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=ANY(i.indkey)
                WHERE i.indrelid=%s::regclass AND i.indisprimary
            """, (f'"{schema}"."{table_name}"',))
            pk = cur.fetchone()
            if pk:
                uri.setKeyColumn(pk[0])
            cur.close()
        finally:
            c.close()
    except Exception:
        pass

    layer = QgsVectorLayer(uri.uri(False), table_name, "postgres")
    if not layer.isValid():
        return False, f"Invalid layer: {schema}.{table_name}"

    layer_name = layer_name_override or table_name

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    options.fileEncoding = "UTF-8"

    # Handle fid field type conflict (GPKG requires integer fid)
    fidx = layer.fields().lookupField("fid")
    if fidx >= 0:
        ft = layer.fields().at(fidx).type()
        if ft not in (QVariant.Int, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong):
            options.layerOptions = ["FID=gpkg_fid"]

    if os.path.exists(gpkg_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    else:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

    ctx = transform_context or QgsProject.instance().transformContext()
    err, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(layer, gpkg_path, ctx, options)

    if err != QgsVectorFileWriter.NoError:
        return False, f"Export error {schema}.{table_name}: {msg}"
    return True, f"OK: {schema}.{table_name} → {layer_name}"


def rewrite_qgis_project_datasources(xml_content, schema_gpkg_map=None,
                                      table_gpkg_map=None, layer_prefix_map=None):
    """
    Rewrite PostgreSQL datasources in a QGIS project XML to point to GeoPackage files.

    :param xml_content: project XML as string
    :param schema_gpkg_map: {schema: gpkg_path} for per-schema / single modes
    :param table_gpkg_map: {(schema, table): gpkg_path} for per-table mode
    :param layer_prefix_map: {schema: "prefix__"} for single-gpkg multi-schema
    :returns: modified XML string
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        QgsMessageLog.logMessage(f"XML parse error: {e}", LOG_TAG, Qgis.Warning)
        return xml_content

    schema_gpkg_map = schema_gpkg_map or {}
    table_gpkg_map = table_gpkg_map or {}

    rewritten = 0
    skipped = 0

    for layer_elem in root.iter("maplayer"):
        prov = layer_elem.find("provider")
        ds = layer_elem.find("datasource")
        if prov is None or ds is None or ds.text is None:
            continue

        is_pg = (prov.text == "postgres" or "dbname=" in ds.text or "service=" in ds.text)
        if not is_pg:
            continue

        ds_text = ds.text

        # Extract schema
        schema_name = None
        for pat in [r"schema='([^']*)'", r'schema="([^"]*)"', r"schema=(\S+)"]:
            m = re.search(pat, ds_text)
            if m:
                schema_name = m.group(1)
                break

        # Extract table
        table_name = None
        for pat in [
            r'table="([^"]*)"[.\s]*"([^"]*)"',
            r"table='([^']*)'\.'([^']*)'",
            r'table="([^"]*)"',
            r"table='([^']*)'"
        ]:
            m = re.search(pat, ds_text)
            if m:
                if m.lastindex == 2:
                    table_name = m.group(2)
                    if not schema_name:
                        schema_name = m.group(1)
                else:
                    table_name = m.group(1)
                break

        if not schema_name or not table_name:
            QgsMessageLog.logMessage(
                f"Rewrite skip: can't parse: {ds_text[:120]}", LOG_TAG, Qgis.Warning)
            skipped += 1
            continue

        # Resolve GPKG path
        gpkg_path = None
        gpkg_layer_name = table_name

        if (schema_name, table_name) in table_gpkg_map:
            gpkg_path = table_gpkg_map[(schema_name, table_name)]
        elif schema_name in schema_gpkg_map:
            gpkg_path = schema_gpkg_map[schema_name]
            if layer_prefix_map and schema_name in layer_prefix_map:
                gpkg_layer_name = f"{layer_prefix_map[schema_name]}{table_name}"

        if not gpkg_path:
            QgsMessageLog.logMessage(
                f"Rewrite skip: no GPKG for {schema_name}.{table_name}", LOG_TAG, Qgis.Warning)
            skipped += 1
            continue

        new_ds = f"{gpkg_path}|layername={gpkg_layer_name}"
        QgsMessageLog.logMessage(
            f"Rewrite: {schema_name}.{table_name} → {new_ds}", LOG_TAG, Qgis.Info)

        ds.text = new_ds
        prov.text = "ogr"
        rewritten += 1

    QgsMessageLog.logMessage(
        f"Rewrite: {rewritten} rewritten, {skipped} skipped", LOG_TAG, Qgis.Info)

    # Clean up project metadata
    to_rm = []
    for parent in root.iter():
        for child in list(parent):
            if child.tag == "projectstorage":
                to_rm.append((parent, child))
    for p, c in to_rm:
        p.remove(c)

    if root.tag == "qgis":
        root.attrib.setdefault("projectname", "")

    for hp in root.iter("homePath"):
        pv = hp.get("path", "")
        if "postgresql" in pv.lower() or "dbname=" in pv.lower():
            hp.set("path", "")

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ============================================================================
# Export worker (QThread)
# ============================================================================

class ExportWorker(QThread):
    """Background thread for exporting PostgreSQL tables to GeoPackage."""

    progress_updated = pyqtSignal(int, int, str)   # step, total, label
    export_finished = pyqtSignal(dict)              # results

    def __init__(self, conn_params, selected, mode, output_dir,
                 single_path, do_projects, transform_context, parent=None):
        super().__init__(parent)
        self.conn_params = conn_params
        self.selected = selected
        self.mode = mode
        self.output_dir = output_dir
        self.single_path = single_path
        self.do_projects = do_projects
        self.transform_context = transform_context
        self._cancelled = False

    def request_cancel(self):
        self._cancelled = True

    def run(self):
        errors = []
        ok_count = 0
        gpkg_count = 0
        schema_gpkg_map = {}
        table_gpkg_map = {}
        layer_prefix_map = None
        exported_projects = []

        schemas = list(self.selected.keys())
        total = sum(len(v) for v in self.selected.values())
        step = 0

        # ── MODE 0: one GPKG per schema ──
        if self.mode == 0:
            for schema, tables in self.selected.items():
                if self._cancelled:
                    break
                gp = os.path.join(self.output_dir, f"{schema}.gpkg")
                schema_gpkg_map[schema] = gp
                if os.path.exists(gp):
                    os.remove(gp)

                for t in tables:
                    if self._cancelled:
                        break
                    step += 1
                    self.progress_updated.emit(
                        step, total, f"{schema}.{t['table']}")

                    ok, msg = export_table_to_gpkg(
                        self.conn_params, schema, t, gp,
                        transform_context=self.transform_context)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(msg)
                    QgsMessageLog.logMessage(
                        msg, LOG_TAG, Qgis.Info if ok else Qgis.Warning)

            gpkg_count = sum(
                1 for gp in schema_gpkg_map.values() if os.path.exists(gp))

        # ── MODE 1: single GPKG ──
        elif self.mode == 1:
            if self.single_path and os.path.exists(self.single_path):
                os.remove(self.single_path)

            multi = len(schemas) > 1
            if multi:
                layer_prefix_map = {s: f"{s}__" for s in schemas}

            for schema, tables in self.selected.items():
                if self._cancelled:
                    break
                schema_gpkg_map[schema] = self.single_path
                for t in tables:
                    if self._cancelled:
                        break
                    step += 1
                    self.progress_updated.emit(
                        step, total, f"{schema}.{t['table']}")

                    override = f"{schema}__{t['table']}" if multi else t["table"]
                    ok, msg = export_table_to_gpkg(
                        self.conn_params, schema, t, self.single_path,
                        layer_name_override=override,
                        transform_context=self.transform_context)
                    if ok:
                        ok_count += 1
                    else:
                        errors.append(msg)
                    QgsMessageLog.logMessage(
                        msg, LOG_TAG, Qgis.Info if ok else Qgis.Warning)

            gpkg_count = 1 if (
                self.single_path and os.path.exists(self.single_path)) else 0

        # ── MODE 2: one GPKG per table ──
        elif self.mode == 2:
            for schema, tables in self.selected.items():
                if self._cancelled:
                    break
                schema_dir = os.path.join(self.output_dir, schema)
                os.makedirs(schema_dir, exist_ok=True)

                for t in tables:
                    if self._cancelled:
                        break
                    step += 1
                    self.progress_updated.emit(
                        step, total, f"{schema}.{t['table']}")

                    gp = os.path.join(schema_dir, f"{t['table']}.gpkg")
                    if os.path.exists(gp):
                        os.remove(gp)

                    ok, msg = export_table_to_gpkg(
                        self.conn_params, schema, t, gp,
                        transform_context=self.transform_context)
                    if ok:
                        ok_count += 1
                        gpkg_count += 1
                        table_gpkg_map[(schema, t["table"])] = gp
                    else:
                        errors.append(msg)
                    QgsMessageLog.logMessage(
                        msg, LOG_TAG, Qgis.Info if ok else Qgis.Warning)

        # ── QGIS projects ──
        if self.do_projects and not self._cancelled:
            self.progress_updated.emit(step, total, "QGIS projects...")
            conn = None
            try:
                conn = pg_connect(self.conn_params)
                projects = get_qgis_projects_in_db(conn)
                for proj in projects:
                    if self._cancelled:
                        break
                    pn = proj["name"]
                    if pn.lower().endswith(".qgz"):
                        pn = pn[:-4] + ".qgs"
                    elif not pn.lower().endswith(".qgs"):
                        pn += ".qgs"

                    self.progress_updated.emit(step, total, f"Project: {pn}")

                    try:
                        xml = rewrite_qgis_project_datasources(
                            proj["xml_content"],
                            schema_gpkg_map=schema_gpkg_map if self.mode != 2 else None,
                            table_gpkg_map=table_gpkg_map if self.mode == 2 else None,
                            layer_prefix_map=layer_prefix_map,
                        )
                        pp = os.path.join(self.output_dir, pn)
                        with open(pp, "w", encoding="utf-8") as f:
                            f.write(xml)
                        exported_projects.append(pn)
                        QgsMessageLog.logMessage(
                            f"Project exported: {pn}", LOG_TAG, Qgis.Info)
                    except Exception as e:
                        errors.append(f"Project {pn}: {e}")
                        QgsMessageLog.logMessage(
                            f"Project {pn}: {e}", LOG_TAG, Qgis.Warning)
            except Exception as e:
                errors.append(f"Projects: {e}")
                QgsMessageLog.logMessage(
                    f"Error connecting for projects: {e}", LOG_TAG, Qgis.Warning)
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        self.export_finished.emit({
            "ok_count": ok_count,
            "errors": errors,
            "gpkg_count": gpkg_count,
            "exported_projects": exported_projects,
            "mode": self.mode,
            "total": total,
            "cancelled": self._cancelled,
        })
