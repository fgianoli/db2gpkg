"""
PG2GPKG - Database utility functions
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import os
import re
import zlib
import zipfile
import io
import xml.etree.ElementTree as ET

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import QSettings

try:
    import psycopg2
    from psycopg2 import sql as psql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

SYSTEM_TABLES = {
    "geography_columns", "geometry_columns", "spatial_ref_sys",
    "raster_columns", "raster_overviews", "qgis_projects",
}

LOG_TAG = "PG2GPKG"


# ============================================================================
# Connection helpers
# ============================================================================

def get_pg_connections():
    """Return dict of registered PostgreSQL connections from QGIS settings."""
    s = QSettings()
    s.beginGroup("PostgreSQL/connections")
    connections = {}
    for name in s.childGroups():
        s.beginGroup(name)
        connections[name] = {
            "host": s.value("host", "localhost"),
            "port": s.value("port", "5432"),
            "database": s.value("database", ""),
            "username": s.value("username", ""),
            "password": s.value("password", ""),
            "sslmode": s.value("sslmode", "prefer"),
            "authcfg": s.value("authcfg", ""),
        }
        s.endGroup()
    s.endGroup()
    return connections


def resolve_auth_params(params):
    """Resolve QGIS authcfg to actual username/password. Must be called from main thread."""
    authcfg = params.get("authcfg", "")
    if not authcfg or (params.get("username") and params.get("password")):
        return params
    try:
        from qgis.core import QgsApplication, QgsAuthMethodConfig
        conf = QgsAuthMethodConfig()
        if QgsApplication.authManager().loadAuthenticationConfig(authcfg, conf, True):
            params = dict(params)
            params["username"] = conf.config("username") or params.get("username", "")
            params["password"] = conf.config("password") or params.get("password", "")
    except Exception as e:
        QgsMessageLog.logMessage(
            f"Auth config resolution failed for {authcfg}: {e}", LOG_TAG, Qgis.Warning)
    return params


def normalize_sslmode(value):
    """Convert QGIS/Qt sslmode enum values to psycopg2-compatible strings."""
    if value is None:
        return "prefer"
    mapping = {
        "SslPrefer": "prefer", "SslDisable": "disable", "SslAllow": "allow",
        "SslRequire": "require", "SslVerifyCa": "verify-ca", "SslVerifyFull": "verify-full",
        "0": "prefer", "1": "disable", "2": "allow",
        "3": "require", "4": "verify-ca", "5": "verify-full",
    }
    s = str(value).strip()
    valid = ("prefer", "disable", "allow", "require", "verify-ca", "verify-full")
    return mapping.get(s, s.lower() if s.lower() in valid else "prefer")


def pg_connect(params):
    """Open a psycopg2 connection. Call resolve_auth_params first if using authcfg."""
    return psycopg2.connect(
        host=params["host"], port=params["port"], dbname=params["database"],
        user=params["username"], password=params["password"],
        sslmode=normalize_sslmode(params.get("sslmode")),
    )


# ============================================================================
# Schema / table discovery
# ============================================================================

def get_schemas(conn):
    """Return list of non-system schemas."""
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast','topology')
            ORDER BY schema_name
        """)
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close()


def get_tables_and_views(conn, schema):
    """
    Return list of dicts with table info.
    Each dict: {table, geom_column, geom_type, srid, table_type}
    """
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT f_table_name, f_geometry_column, type, srid
            FROM geometry_columns WHERE f_table_schema = %s ORDER BY f_table_name
        """, (schema,))
        spatial = {}
        for tname, gcol, gtype, srid in cur.fetchall():
            spatial.setdefault(tname, []).append(
                {"geom_column": gcol, "geom_type": gtype, "srid": srid})

        cur.execute("""
            SELECT table_name, table_type FROM information_schema.tables
            WHERE table_schema = %s ORDER BY table_name
        """, (schema,))
        results = []
        for tname, ttype in cur.fetchall():
            if tname in SYSTEM_TABLES:
                continue
            if tname in spatial:
                for gi in spatial[tname]:
                    results.append({
                        "table": tname, "geom_column": gi["geom_column"],
                        "geom_type": gi["geom_type"], "srid": gi["srid"],
                        "table_type": ttype,
                    })
            else:
                results.append({
                    "table": tname, "geom_column": None,
                    "geom_type": None, "srid": 0, "table_type": ttype,
                })
        return results
    finally:
        cur.close()


# ============================================================================
# QGIS projects in database
# ============================================================================

def get_qgis_projects_in_db(conn):
    """
    Find QGIS projects stored in the database.
    Returns list of dicts: {schema, name, xml_content}
    """
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT table_schema, table_name FROM information_schema.tables
            WHERE table_name = 'qgis_projects'
        """)
        project_tables = cur.fetchall()
    finally:
        cur.close()

    projects = []
    for pschema, ptable in project_tables:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position
            """, (pschema, ptable))
            columns = [r[0] for r in cur.fetchall()]
            QgsMessageLog.logMessage(
                f"{pschema}.{ptable} columns: {columns}", LOG_TAG, Qgis.Info)

            xml_col = "content" if "content" in columns else (
                "metadata" if "metadata" in columns else None)
            if not xml_col:
                continue

            cur.execute(
                psql.SQL("SELECT name, {} FROM {}.{}").format(
                    psql.Identifier(xml_col),
                    psql.Identifier(pschema),
                    psql.Identifier(ptable),
                )
            )
            for name, raw in cur.fetchall():
                if raw is None:
                    continue
                if isinstance(raw, memoryview):
                    raw = bytes(raw)
                xml = _extract_qgs_xml(name, raw)
                if xml:
                    projects.append({"schema": pschema, "name": name, "xml_content": xml})
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error reading projects from {pschema}.{ptable}: {e}",
                LOG_TAG, Qgis.Warning)
            conn.rollback()
        finally:
            cur.close()

    return projects


def _extract_qgs_xml(name, raw):
    """Extract QGIS project XML from various storage formats."""
    if isinstance(raw, str):
        s = raw.strip()
        return raw if (s.startswith("<?xml") or s.startswith("<qgis")) else None
    if isinstance(raw, dict) or not isinstance(raw, bytes):
        return None

    QgsMessageLog.logMessage(
        f"Project {name}: {len(raw)} bytes, header: {raw[:4].hex()}", LOG_TAG, Qgis.Info)

    def _is_qgs(text):
        s = text.strip()
        return s.startswith("<?xml") or s.startswith("<qgis")

    # ZIP (.qgz)
    if raw[:4] == b'PK\x03\x04':
        try:
            with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
                qgs = [f for f in zf.namelist() if f.lower().endswith(".qgs")]
                target = qgs[0] if qgs else (zf.namelist()[0] if zf.namelist() else None)
                if target:
                    text = zf.read(target).decode("utf-8")
                    if _is_qgs(text):
                        return text
        except Exception as e:
            QgsMessageLog.logMessage(f"Project {name}: ZIP error: {e}", LOG_TAG, Qgis.Warning)

    # zlib
    if raw[:1] == b'\x78':
        try:
            text = zlib.decompress(raw).decode("utf-8")
            if _is_qgs(text):
                return text
        except Exception:
            pass

    # plain UTF-8
    try:
        text = raw.decode("utf-8")
        if _is_qgs(text):
            return text
    except Exception:
        pass

    # last resort zlib
    try:
        text = zlib.decompress(raw).decode("utf-8")
        if _is_qgs(text):
            return text
    except Exception:
        pass

    QgsMessageLog.logMessage(
        f"Project {name}: cannot extract XML. header: {raw[:16].hex()}", LOG_TAG, Qgis.Warning)
    return None
