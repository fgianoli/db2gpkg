"""
PG2GPKG - Import dialog (GeoPackage → PostgreSQL/PostGIS)
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import json
import os
import re

from qgis.core import QgsMessageLog, QgsProject, Qgis
from qgis.PyQt.QtCore import Qt, QCoreApplication, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QFileDialog, QComboBox,
    QLabel, QProgressDialog, QMessageBox, QCheckBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialogButtonBox, QSpinBox, QInputDialog,
)

# Collapsible group box (accordion). Falls back to a plain group box if the
# QGIS gui module is unavailable.
try:
    from qgis.gui import QgsCollapsibleGroupBox as _CollapsibleGroupBox
except ImportError:
    _CollapsibleGroupBox = QGroupBox

from .db_utils import (
    HAS_PSYCOPG2, create_schema, get_pg_connections,
    get_postgis_version, get_server_version, pg_connect,
    pg_is_in_recovery, get_writable_schemas, resolve_auth_params,
)
from .import_engine import (
    HAS_GDAL, ImportWorker, list_gpkg_layers,
    read_gpkg_preview, validate_append_columns,
)

LOG_TAG = "PG2GPKG"

# ── Qt6 scoped-enum compatibility ─────────────────────────────────────
try:
    _EchoPassword = QLineEdit.EchoMode.Password
except AttributeError:
    _EchoPassword = QLineEdit.Password

try:
    _HdrStretch = QHeaderView.ResizeMode.Stretch
except AttributeError:
    _HdrStretch = QHeaderView.Stretch

try:
    _HdrResizeToContents = QHeaderView.ResizeMode.ResizeToContents
except AttributeError:
    _HdrResizeToContents = QHeaderView.ResizeToContents

try:
    _NoEdit = QAbstractItemView.EditTrigger.NoEditTriggers
except AttributeError:
    _NoEdit = QAbstractItemView.NoEditTriggers

try:
    _ItemIsUserCheckable = Qt.ItemFlag.ItemIsUserCheckable
except AttributeError:
    _ItemIsUserCheckable = Qt.ItemIsUserCheckable

try:
    _ItemIsEnabled = Qt.ItemFlag.ItemIsEnabled
except AttributeError:
    _ItemIsEnabled = Qt.ItemIsEnabled

try:
    _ItemIsSelectable = Qt.ItemFlag.ItemIsSelectable
except AttributeError:
    _ItemIsSelectable = Qt.ItemIsSelectable

try:
    _Checked = Qt.CheckState.Checked
except AttributeError:
    _Checked = Qt.Checked

try:
    _Unchecked = Qt.CheckState.Unchecked
except AttributeError:
    _Unchecked = Qt.Unchecked

try:
    _UserRole = Qt.ItemDataRole.UserRole
except AttributeError:
    _UserRole = Qt.UserRole

try:
    _WindowModal = Qt.WindowModality.WindowModal
except AttributeError:
    _WindowModal = Qt.WindowModal

try:
    _AcceptRole = QDialogButtonBox.ButtonRole.AcceptRole
    _RejectRole = QDialogButtonBox.ButtonRole.RejectRole
    _ActionRole = QDialogButtonBox.ButtonRole.ActionRole
except AttributeError:
    _AcceptRole = QDialogButtonBox.AcceptRole
    _RejectRole = QDialogButtonBox.RejectRole
    _ActionRole = QDialogButtonBox.ActionRole

try:
    _MBYes = QMessageBox.StandardButton.Yes
    _MBNo = QMessageBox.StandardButton.No
except AttributeError:
    _MBYes = QMessageBox.Yes
    _MBNo = QMessageBox.No

# Strict PG identifier: lowercase letters, digits, underscore; must start with letter or _
_PG_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _sanitize_pg_name(name):
    """Lowercase + replace non-alphanumeric chars with underscore."""
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()
    if not s:
        s = "layer"
    if s[0].isdigit():
        s = "_" + s
    return s


def _pg_name_warnings(name):
    """Return a short warning string if a PG identifier will need quoting
    forever (uppercase, special chars). Empty string = looks clean."""
    if not name:
        return "empty"
    if not _PG_IDENT_RE.match(name):
        return "needs quoting"
    return ""


# ============================================================================
# Preview sub-dialog
# ============================================================================

class PreviewDialog(QDialog):
    """Read-only preview of the first N rows of a GPKG layer."""

    LIMIT = 50

    def __init__(self, gpkg_path, layer_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Preview — {layer}").format(layer=layer_name))
        self.setMinimumWidth(720)
        self.setMinimumHeight(420)

        layout = QVBoxLayout()
        self.setLayout(layout)

        cols, rows = read_gpkg_preview(gpkg_path, layer_name, self.LIMIT)

        layout.addWidget(QLabel(
            self.tr("Showing first {n} rows of '{layer}' "
                    "({total} columns)").format(
                n=len(rows), layer=layer_name, total=len(cols))))

        table = QTableWidget(len(rows), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.setEditTriggers(_NoEdit)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(_ItemIsEnabled | _ItemIsSelectable)
                table.setItem(r, c, item)
        table.resizeColumnsToContents()
        layout.addWidget(table)

        bb = QDialogButtonBox()
        close = QPushButton(self.tr("Close"))
        close.clicked.connect(self.accept)
        bb.addButton(close, _RejectRole)
        layout.addWidget(bb)

    def tr(self, message):
        return QCoreApplication.translate("PG2GPKG", message)


# ============================================================================
# Field mapping sub-dialog
# ============================================================================

class FieldMappingDialog(QDialog):
    """Per-layer column mapping (include/rename) dialog."""

    COL_INCLUDE = 0
    COL_SRC = 1
    COL_TYPE = 2
    COL_DEST = 3

    def __init__(self, layer_name, fields, current_map=None, parent=None):
        super().__init__(parent)
        self.fields_info = fields
        self.result_map = None

        self.setWindowTitle(self.tr("Field mapping — {layer}").format(layer=layer_name))
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(
            self.tr("Uncheck columns to exclude them. Edit destination names "
                    "to rename. Lowercase + snake_case is recommended.")))

        self.table = QTableWidget(len(fields), 4)
        self.table.setHorizontalHeaderLabels([
            self.tr("Include"), self.tr("GPKG column"),
            self.tr("Type"), self.tr("Destination column"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_DEST, _HdrStretch)
        for col in (self.COL_INCLUDE, self.COL_SRC, self.COL_TYPE):
            self.table.horizontalHeader().setSectionResizeMode(
                col, _HdrResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        for row, f in enumerate(fields):
            src = f["name"]
            if current_map is not None:
                dest = current_map.get(src, "")
                included = bool(dest)
            else:
                dest = _sanitize_pg_name(src)
                included = True

            chk = QTableWidgetItem()
            chk.setFlags(_ItemIsUserCheckable | _ItemIsEnabled)
            chk.setCheckState(_Checked if included else _Unchecked)
            self.table.setItem(row, self.COL_INCLUDE, chk)

            src_item = QTableWidgetItem(src)
            src_item.setFlags(_ItemIsEnabled)
            self.table.setItem(row, self.COL_SRC, src_item)

            type_item = QTableWidgetItem(f"{f['type']} → {f['type_pg']}")
            type_item.setFlags(_ItemIsEnabled)
            self.table.setItem(row, self.COL_TYPE, type_item)

            dest_item = QTableWidgetItem(dest if dest else _sanitize_pg_name(src))
            self.table.setItem(row, self.COL_DEST, dest_item)

        ar = QHBoxLayout()
        b_all = QPushButton(self.tr("Include all"))
        b_all.clicked.connect(lambda: self._set_all(True))
        b_none = QPushButton(self.tr("Exclude all"))
        b_none.clicked.connect(lambda: self._set_all(False))
        b_lower = QPushButton(self.tr("All to snake_case"))
        b_lower.clicked.connect(self._snake_all)
        b_reset = QPushButton(self.tr("Reset to original"))
        b_reset.clicked.connect(self._reset_names)
        for b in (b_all, b_none, b_lower, b_reset):
            ar.addWidget(b)
        layout.addLayout(ar)

        bb = QDialogButtonBox()
        ok = QPushButton(self.tr("OK"))
        ok.clicked.connect(self._accept)
        cancel = QPushButton(self.tr("Cancel"))
        cancel.clicked.connect(self.reject)
        bb.addButton(ok, _AcceptRole)
        bb.addButton(cancel, _RejectRole)
        layout.addWidget(bb)

    def tr(self, message):
        return QCoreApplication.translate("PG2GPKG", message)

    def _set_all(self, on):
        st = _Checked if on else _Unchecked
        for r in range(self.table.rowCount()):
            self.table.item(r, self.COL_INCLUDE).setCheckState(st)

    def _snake_all(self):
        for r in range(self.table.rowCount()):
            src = self.table.item(r, self.COL_SRC).text()
            self.table.item(r, self.COL_DEST).setText(_sanitize_pg_name(src))

    def _reset_names(self):
        for r in range(self.table.rowCount()):
            src = self.table.item(r, self.COL_SRC).text()
            self.table.item(r, self.COL_DEST).setText(src)

    def _accept(self):
        result = {}
        seen = set()
        for r in range(self.table.rowCount()):
            if self.table.item(r, self.COL_INCLUDE).checkState() != _Checked:
                continue
            src = self.table.item(r, self.COL_SRC).text()
            dest = self.table.item(r, self.COL_DEST).text().strip()
            if not dest:
                QMessageBox.warning(self, self.tr("Invalid mapping"),
                    self.tr("Destination column for '{col}' cannot be empty.")
                    .format(col=src))
                return
            if dest in seen:
                QMessageBox.warning(self, self.tr("Invalid mapping"),
                    self.tr("Duplicate destination column: '{col}'")
                    .format(col=dest))
                return
            seen.add(dest)
            result[src] = dest

        if not result:
            QMessageBox.warning(self, self.tr("Invalid mapping"),
                                self.tr("At least one column must be included."))
            return

        self.result_map = result
        self.accept()


# ============================================================================
# Main import dialog
# ============================================================================

class ImportGPKGtoPGDialog(QDialog):

    # Layer table columns
    COL_CHECK = 0
    COL_LAYER = 1
    COL_ROWS = 2
    COL_GEOM = 3
    COL_SRID = 4
    COL_SCHEMA = 5
    COL_TABLE = 6
    COL_MODE = 7
    COL_MAP = 8
    COL_PREVIEW = 9
    COLUMNS = 10

    def __init__(self, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.conn_params = None
        self.gpkg_path = None
        self.gpkg_layers = []         # list of layer info dicts
        self.field_maps = {}          # {layer_name: {src: dest}}
        self.source_srid_overrides = {}  # {layer_name: int} for layers w/o CRS
        self.writable_schemas = []
        self._worker = None
        self._progress = None
        self._failed_jobs = []        # list of job dicts (+ 'error') for retry

        self.setWindowTitle(self.tr("Import GeoPackage → PostgreSQL"))
        icon = QIcon(os.path.join(
            os.path.dirname(__file__), "icons", "gpkg2pg.png"))
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.setMinimumWidth(960)
        self.setMinimumHeight(760)
        self._setup_ui()

    def tr(self, message):
        return QCoreApplication.translate("PG2GPKG", message)

    # ================================================================
    # UI setup
    # ================================================================

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ── GPKG file ─────────────────────────────────────────────
        fg = QGroupBox(self.tr("GeoPackage file"))
        fl = QHBoxLayout()
        fg.setLayout(fl)
        self.gpkg_edit = QLineEdit()
        self.gpkg_edit.setPlaceholderText(self.tr("Select a .gpkg file..."))
        last_path = QSettings().value("PG2GPKG/lastImportGpkg", "")
        if last_path and os.path.isfile(last_path):
            self.gpkg_edit.setText(last_path)
        btn_browse = QPushButton(self.tr("Browse..."))
        btn_browse.clicked.connect(self._browse_gpkg)
        btn_analyze = QPushButton(self.tr("Analyze GPKG"))
        btn_analyze.clicked.connect(self._analyze_gpkg)
        fl.addWidget(self.gpkg_edit)
        fl.addWidget(btn_browse)
        fl.addWidget(btn_analyze)
        layout.addWidget(fg)

        # ── Connection (collapsible / accordion) ──────────────────
        cg = _CollapsibleGroupBox(self.tr("PostgreSQL Connection"))
        self.conn_group = cg
        cl = QFormLayout()
        cg.setLayout(cl)

        self.conn_combo = QComboBox()
        self.connections = get_pg_connections()
        for name in sorted(self.connections.keys()):
            db = self.connections[name].get("database", "")
            self.conn_combo.addItem(f"{name} ({db})", name)
        cl.addRow(self.tr("Connection:"), self.conn_combo)

        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("5432")
        self.db_edit = QLineEdit()
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(_EchoPassword)

        self.use_manual = QCheckBox(self.tr("Use manual parameters"))
        self.use_manual.toggled.connect(self._toggle_manual)
        cl.addRow(self.use_manual)
        cl.addRow(self.tr("Host:"), self.host_edit)
        cl.addRow(self.tr("Port:"), self.port_edit)
        cl.addRow(self.tr("Database:"), self.db_edit)
        cl.addRow(self.tr("User:"), self.user_edit)
        cl.addRow(self.tr("Password:"), self.pass_edit)
        for w in (self.host_edit, self.port_edit, self.db_edit,
                  self.user_edit, self.pass_edit):
            w.setEnabled(False)

        btn_connect = QPushButton(self.tr("Connect and load schemas"))
        btn_connect.clicked.connect(self._connect_db)
        cl.addRow(btn_connect)
        layout.addWidget(cg)
        # Start collapsed to keep the dialog compact; the user expands it only
        # to connect, and it re-collapses automatically afterwards.
        if hasattr(cg, "setCollapsed"):
            cg.setCollapsed(True)

        # ── Batch helpers ─────────────────────────────────────────
        bg = QGroupBox(self.tr("Apply to all selected layers"))
        bgl = QGridLayout()
        bg.setLayout(bgl)

        self.batch_schema_combo = QComboBox()
        self.batch_schema_combo.addItem("public")
        self.btn_apply_schema = QPushButton(self.tr("Set schema"))
        self.btn_apply_schema.setToolTip(self.tr(
            "Set the destination schema for all selected layers."))
        self.btn_apply_schema.clicked.connect(self._apply_schema_to_all)

        self.btn_new_schema = QPushButton(self.tr("New schema..."))
        self.btn_new_schema.setToolTip(self.tr(
            "Create a new schema in the database. Requires CREATE privilege "
            "on the database."))
        self.btn_new_schema.clicked.connect(self._create_new_schema)
        self.btn_new_schema.setEnabled(False)

        self.batch_mode_combo = QComboBox()
        self.batch_mode_combo.addItem(self.tr("create"), "create")
        self.batch_mode_combo.addItem(self.tr("append"), "append")
        self.batch_mode_combo.addItem(self.tr("replace"), "replace")
        self.btn_apply_mode = QPushButton(self.tr("Set mode"))
        self.btn_apply_mode.setToolTip(self.tr(
            "Set the create/append/replace mode for all selected layers."))
        self.btn_apply_mode.clicked.connect(self._apply_mode_to_all)

        srid_tooltip = self.tr(
            "EPSG code to assign to layers that DO NOT declare a CRS in the "
            "GeoPackage. This is NOT a reprojection — layers that already "
            "have a CRS are left untouched. For reprojection use the Options "
            "panel below.")
        self.batch_srid_spin = QSpinBox()
        self.batch_srid_spin.setRange(0, 999999)
        self.batch_srid_spin.setValue(0)
        self.batch_srid_spin.setSpecialValueText("—")
        self.batch_srid_spin.setToolTip(srid_tooltip)
        self.btn_apply_srid = QPushButton(
            self.tr("Assign source SRID (only layers without CRS)"))
        self.btn_apply_srid.setToolTip(srid_tooltip)
        self.btn_apply_srid.clicked.connect(self._apply_srid_to_all)

        self.lbl_srid = QLabel(self.tr("EPSG for layers without CRS:"))
        self.lbl_srid.setToolTip(srid_tooltip)

        bgl.addWidget(QLabel(self.tr("Schema:")), 0, 0)
        bgl.addWidget(self.batch_schema_combo, 0, 1)
        bgl.addWidget(self.btn_apply_schema, 0, 2)
        bgl.addWidget(self.btn_new_schema, 0, 3)
        bgl.addWidget(QLabel(self.tr("Mode:")), 1, 0)
        bgl.addWidget(self.batch_mode_combo, 1, 1)
        bgl.addWidget(self.btn_apply_mode, 1, 2)
        bgl.addWidget(self.lbl_srid, 2, 0)
        bgl.addWidget(self.batch_srid_spin, 2, 1)
        bgl.addWidget(self.btn_apply_srid, 2, 2)
        bgl.setColumnStretch(4, 1)
        layout.addWidget(bg)

        # ── Layers table ──────────────────────────────────────────
        lg = QGroupBox(self.tr("Layers in the GeoPackage"))
        ll = QVBoxLayout()
        lg.setLayout(ll)

        self.layer_table = QTableWidget(0, self.COLUMNS)
        self.layer_table.setHorizontalHeaderLabels([
            "", self.tr("Layer"), self.tr("Rows"), self.tr("Geometry"),
            self.tr("SRID"), self.tr("Dest. schema"), self.tr("Dest. table"),
            self.tr("Mode"), self.tr("Mapping"), self.tr("Preview"),
        ])
        hdr = self.layer_table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_TABLE, _HdrStretch)
        for col in (self.COL_CHECK, self.COL_LAYER, self.COL_ROWS,
                    self.COL_GEOM, self.COL_SRID, self.COL_SCHEMA,
                    self.COL_MODE, self.COL_MAP, self.COL_PREVIEW):
            hdr.setSectionResizeMode(col, _HdrResizeToContents)
        self.layer_table.verticalHeader().setVisible(False)
        ll.addWidget(self.layer_table)

        br = QHBoxLayout()
        b_sel_all = QPushButton(self.tr("Select all"))
        b_sel_all.clicked.connect(lambda: self._set_all_check(True))
        b_sel_none = QPushButton(self.tr("Deselect all"))
        b_sel_none.clicked.connect(lambda: self._set_all_check(False))
        br.addWidget(b_sel_all)
        br.addWidget(b_sel_none)
        br.addStretch()
        ll.addLayout(br)

        layout.addWidget(lg)

        # ── Options ───────────────────────────────────────────────
        og = QGroupBox(self.tr("Options"))
        ol = QFormLayout()
        og.setLayout(ol)

        self.cb_reproject = QCheckBox(
            self.tr("Reproject all layers to a target SRID"))
        ol.addRow(self.cb_reproject)

        self.srid_spin = QSpinBox()
        self.srid_spin.setRange(1, 999999)
        self.srid_spin.setValue(4326)
        self.srid_spin.setEnabled(False)
        self.cb_reproject.toggled.connect(self.srid_spin.setEnabled)
        ol.addRow(self.tr("Target EPSG:"), self.srid_spin)

        layout.addWidget(og)

        # ── Advanced options (collapsible / accordion) ────────────
        ag = _CollapsibleGroupBox(
            self.tr("Advanced options (for fragile PostgreSQL servers)"))
        al = QFormLayout()
        ag.setLayout(al)

        self.cb_use_copy = QCheckBox(
            self.tr("Use COPY (fast bulk-load)"))
        self.cb_use_copy.setChecked(True)
        self.cb_use_copy.setToolTip(self.tr(
            "Uncheck if the server crashes during large imports. Falls back "
            "to INSERT statements: much slower (5-10×), but lighter on the "
            "server's memory and more compatible with old PostgreSQL versions."))
        al.addRow(self.cb_use_copy)

        self.cb_spatial_index = QCheckBox(
            self.tr("Create spatial index after load"))
        self.cb_spatial_index.setChecked(True)
        self.cb_spatial_index.setToolTip(self.tr(
            "Uncheck if the server crashes right at the end of an import. "
            "Building a GiST index on millions of features can double the "
            "memory the server needs."))
        al.addRow(self.cb_spatial_index)

        self.cb_force_2d = QCheckBox(
            self.tr("Force 2D geometry (drop Z/M components)"))
        self.cb_force_2d.setChecked(False)
        self.cb_force_2d.setToolTip(self.tr(
            "Strips Z and M values from 3D/Measured geometries. Useful when "
            "the server has bugs with COPY on 3D/Measured types, or when "
            "you don't need the third dimension."))
        al.addRow(self.cb_force_2d)

        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 60000)
        self.pause_spin.setSingleStep(500)
        self.pause_spin.setValue(0)
        self.pause_spin.setSuffix(" ms")
        self.pause_spin.setToolTip(self.tr(
            "Wait this many milliseconds between layers. Gives the server "
            "time to flush WAL, autovacuum, and free memory between burst loads."))
        al.addRow(self.tr("Pause between layers:"), self.pause_spin)

        layout.addWidget(ag)
        self.advanced_group = ag
        # Collapsed by default — only opened on servers that need the mitigations.
        if hasattr(ag, "setCollapsed"):
            ag.setCollapsed(True)

        # ── Buttons ───────────────────────────────────────────────
        bb = QDialogButtonBox()
        self.btn_import = QPushButton(self.tr("Import"))
        self.btn_import.clicked.connect(self._run_import)
        self.btn_import.setEnabled(False)
        self.btn_retry = QPushButton(self.tr("Retry failed (0)"))
        self.btn_retry.setToolTip(self.tr(
            "Re-run the import for the layers that failed in the last run "
            "(e.g. when the database was momentarily in recovery mode)."))
        self.btn_retry.setEnabled(False)
        self.btn_retry.clicked.connect(self._retry_failed)
        btn_close = QPushButton(self.tr("Close"))
        btn_close.clicked.connect(self.reject)
        bb.addButton(self.btn_import, _AcceptRole)
        bb.addButton(self.btn_retry, _ActionRole)
        bb.addButton(btn_close, _RejectRole)
        layout.addWidget(bb)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    # ================================================================
    # UI helpers
    # ================================================================

    def _toggle_manual(self, on):
        for w in (self.host_edit, self.port_edit, self.db_edit,
                  self.user_edit, self.pass_edit):
            w.setEnabled(on)
        self.conn_combo.setEnabled(not on)

    def _conn_params_from_form(self):
        if self.use_manual.isChecked():
            return {
                "host": self.host_edit.text(), "port": self.port_edit.text(),
                "database": self.db_edit.text(), "username": self.user_edit.text(),
                "password": self.pass_edit.text(), "sslmode": "prefer",
            }
        name = self.conn_combo.currentData()
        return self.connections.get(name) if name else None

    def _browse_gpkg(self):
        last = QSettings().value("PG2GPKG/lastImportGpkg", "")
        start_dir = os.path.dirname(last) if last else ""
        f, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select GeoPackage"),
            start_dir, self.tr("GeoPackage files (*.gpkg)"))
        if f:
            self.gpkg_edit.setText(f)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()
            self._worker.wait()
        super().closeEvent(event)

    # ================================================================
    # Analyze GPKG
    # ================================================================

    def _analyze_gpkg(self):
        if not HAS_GDAL:
            QMessageBox.critical(self, self.tr("Missing dependency"),
                self.tr("GDAL/OGR Python bindings are not available."))
            return

        path = self.gpkg_edit.text().strip().strip('"').strip("'")
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Select a valid .gpkg file."))
            return

        QSettings().setValue("PG2GPKG/lastImportGpkg", path)

        layers = list_gpkg_layers(path)
        if not layers:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("No layers found in the GeoPackage."))
            return

        self.gpkg_path = path
        self.gpkg_layers = layers
        # Restore persisted field maps (per gpkg + layer)
        self.field_maps = self._load_all_field_map_presets()
        self.source_srid_overrides = {}
        # Reset any pending retry — those jobs referred to a different GPKG
        self._failed_jobs = []
        self._update_retry_button()
        self._populate_layer_table()
        self._update_import_button()
        self.status_label.setText(
            self.tr("Loaded {n} layer(s) from {file}").format(
                n=len(layers), file=os.path.basename(path)))

    def _populate_layer_table(self):
        # Disconnect during repopulation to avoid spurious updates
        try:
            self.layer_table.itemChanged.disconnect(self._on_table_item_changed)
        except (TypeError, RuntimeError):
            pass

        self.layer_table.setRowCount(len(self.gpkg_layers))

        for row, lyr in enumerate(self.gpkg_layers):
            # Checkbox
            chk = QTableWidgetItem()
            chk.setFlags(_ItemIsUserCheckable | _ItemIsEnabled)
            chk.setCheckState(_Checked)
            self.layer_table.setItem(row, self.COL_CHECK, chk)

            # Layer name (read-only)
            name_item = QTableWidgetItem(lyr["name"])
            name_item.setFlags(_ItemIsEnabled)
            name_item.setData(_UserRole, lyr)
            self.layer_table.setItem(row, self.COL_LAYER, name_item)

            # Rows
            rows_item = QTableWidgetItem(str(lyr["count"]))
            rows_item.setFlags(_ItemIsEnabled)
            self.layer_table.setItem(row, self.COL_ROWS, rows_item)

            # Geometry
            geom_item = QTableWidgetItem(lyr["geom_type"] or "—")
            geom_item.setFlags(_ItemIsEnabled)
            self.layer_table.setItem(row, self.COL_GEOM, geom_item)

            # SRID — editable spinbox for layers without CRS
            if lyr["srid"]:
                srid_item = QTableWidgetItem(str(lyr["srid"]))
                srid_item.setFlags(_ItemIsEnabled)
                self.layer_table.setItem(row, self.COL_SRID, srid_item)
            else:
                spin = QSpinBox()
                spin.setRange(0, 999999)
                spin.setValue(0)
                spin.setSpecialValueText("—")
                spin.setToolTip(self.tr(
                    "Layer has no CRS. Set an EPSG code to assign one "
                    "before import."))
                spin.valueChanged.connect(
                    lambda v, name=lyr["name"]: self._set_srid_override(name, v))
                self.layer_table.setCellWidget(row, self.COL_SRID, spin)

            # Dest schema (combobox)
            schema_combo = QComboBox()
            schemas = self.writable_schemas or ["public"]
            schema_combo.addItems(schemas)
            if "public" in schemas:
                schema_combo.setCurrentText("public")
            self.layer_table.setCellWidget(row, self.COL_SCHEMA, schema_combo)

            # Dest table (editable)
            tbl_item = QTableWidgetItem(_sanitize_pg_name(lyr["name"]))
            self.layer_table.setItem(row, self.COL_TABLE, tbl_item)

            # Mode (combobox)
            mode_combo = QComboBox()
            mode_combo.addItem(self.tr("create"), "create")
            mode_combo.addItem(self.tr("append"), "append")
            mode_combo.addItem(self.tr("replace"), "replace")
            self.layer_table.setCellWidget(row, self.COL_MODE, mode_combo)

            # Mapping button
            preset = self.field_maps.get(lyr["name"])
            map_label = self.tr("Edit... ({n})").format(n=len(preset)) \
                if preset else self.tr("Edit...")
            btn = QPushButton(map_label)
            btn.clicked.connect(lambda _checked=False, r=row: self._edit_mapping(r))
            self.layer_table.setCellWidget(row, self.COL_MAP, btn)

            # Preview button
            prev_btn = QPushButton(self.tr("View..."))
            prev_btn.clicked.connect(
                lambda _checked=False, r=row: self._show_preview(r))
            self.layer_table.setCellWidget(row, self.COL_PREVIEW, prev_btn)

        # Reconnect after population
        self.layer_table.itemChanged.connect(self._on_table_item_changed)
        self._update_batch_buttons_state()

    def _on_table_item_changed(self, item):
        if item.column() == self.COL_CHECK:
            self._update_batch_buttons_state()

    def _update_batch_buttons_state(self):
        sel = self._selected_rows()
        any_sel = bool(sel)
        self.btn_apply_schema.setEnabled(any_sel)
        self.btn_apply_mode.setEnabled(any_sel)

        any_no_crs = any(
            isinstance(self.layer_table.cellWidget(r, self.COL_SRID), QSpinBox)
            for r in sel)
        self.btn_apply_srid.setEnabled(any_no_crs)
        # Visually de-emphasize the row when no layer needs it
        self.batch_srid_spin.setEnabled(any_no_crs)
        self.lbl_srid.setEnabled(any_no_crs)

    def _set_all_check(self, on):
        st = _Checked if on else _Unchecked
        for r in range(self.layer_table.rowCount()):
            self.layer_table.item(r, self.COL_CHECK).setCheckState(st)
        self._update_batch_buttons_state()

    def _set_srid_override(self, layer_name, value):
        if value > 0:
            self.source_srid_overrides[layer_name] = value
        else:
            self.source_srid_overrides.pop(layer_name, None)

    def _edit_mapping(self, row):
        lyr = self.layer_table.item(row, self.COL_LAYER).data(_UserRole)
        current = self.field_maps.get(lyr["name"])
        dlg = FieldMappingDialog(lyr["name"], lyr["fields"], current, self)
        if dlg.exec() and dlg.result_map is not None:
            self.field_maps[lyr["name"]] = dlg.result_map
            self._save_field_map_preset(lyr["name"], dlg.result_map)
            self.layer_table.cellWidget(row, self.COL_MAP).setText(
                self.tr("Edit... ({n})").format(n=len(dlg.result_map)))

    def _show_preview(self, row):
        lyr = self.layer_table.item(row, self.COL_LAYER).data(_UserRole)
        dlg = PreviewDialog(self.gpkg_path, lyr["name"], self)
        dlg.exec()

    # ================================================================
    # Batch helpers
    # ================================================================

    def _selected_rows(self):
        return [r for r in range(self.layer_table.rowCount())
                if self.layer_table.item(r, self.COL_CHECK).checkState() == _Checked]

    def _apply_schema_to_all(self):
        target = self.batch_schema_combo.currentText()
        for r in self._selected_rows():
            combo = self.layer_table.cellWidget(r, self.COL_SCHEMA)
            if combo and target:
                idx = combo.findText(target)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

    def _apply_mode_to_all(self):
        target = self.batch_mode_combo.currentData()
        for r in self._selected_rows():
            combo = self.layer_table.cellWidget(r, self.COL_MODE)
            if combo:
                idx = combo.findData(target)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

    def _apply_srid_to_all(self):
        srid = self.batch_srid_spin.value()
        if srid <= 0:
            return
        for r in self._selected_rows():
            widget = self.layer_table.cellWidget(r, self.COL_SRID)
            # Only rows that have a spinbox (no CRS in the layer)
            if isinstance(widget, QSpinBox):
                widget.setValue(srid)

    # ================================================================
    # Preset persistence (field maps)
    # ================================================================

    def _preset_key(self, layer_name):
        if not self.gpkg_path:
            return None
        return f"PG2GPKG/fieldMaps/{os.path.basename(self.gpkg_path)}/{layer_name}"

    def _save_field_map_preset(self, layer_name, mapping):
        key = self._preset_key(layer_name)
        if key is None:
            return
        try:
            QSettings().setValue(key, json.dumps(mapping))
        except Exception:
            pass

    def _load_all_field_map_presets(self):
        if not self.gpkg_path:
            return {}
        loaded = {}
        s = QSettings()
        for lyr in self.gpkg_layers:
            key = self._preset_key(lyr["name"])
            if key is None:
                continue
            raw = s.value(key, "")
            if raw:
                try:
                    loaded[lyr["name"]] = json.loads(raw)
                except Exception:
                    pass
        return loaded

    # ================================================================
    # Connect / load schemas
    # ================================================================

    def _connect_db(self):
        if not HAS_PSYCOPG2:
            QMessageBox.critical(self, self.tr("Missing dependency"),
                self.tr("The 'psycopg2' module is not installed.\n\n"
                         "Install it with: pip install psycopg2-binary"))
            return

        params = self._conn_params_from_form()
        if not params:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("No connection selected."))
            return

        params = resolve_auth_params(params)

        try:
            conn = pg_connect(params)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Connection error"), str(e))
            return

        try:
            self.writable_schemas = get_writable_schemas(conn) or ["public"]
        finally:
            try:
                conn.close()
            except Exception:
                pass

        self.conn_params = params
        self._refresh_schema_combos(preserve_selection=False)
        self.btn_new_schema.setEnabled(True)

        # Show the connected database in the group title and collapse it again
        # to reclaim vertical space now that the connection is established.
        self.conn_group.setTitle(
            self.tr("PostgreSQL Connection — {db}").format(db=params["database"]))
        if hasattr(self.conn_group, "setCollapsed"):
            self.conn_group.setCollapsed(True)

        self._update_import_button()
        self.status_label.setText(
            self.tr("Connected to {db} — {n} writable schemas").format(
                db=params["database"], n=len(self.writable_schemas)))

    def _refresh_schema_combos(self, preserve_selection=True, prefer=None):
        """Repopulate batch + per-row schema combos from self.writable_schemas.

        :param preserve_selection: keep current per-row choice when possible
        :param prefer: schema name to select where possible (e.g. just-created)
        """
        schemas = self.writable_schemas or ["public"]

        # Batch combo
        batch_current = self.batch_schema_combo.currentText() \
            if preserve_selection else None
        self.batch_schema_combo.clear()
        self.batch_schema_combo.addItems(schemas)
        target = prefer or batch_current or (
            "public" if "public" in schemas else schemas[0])
        if target in schemas:
            self.batch_schema_combo.setCurrentText(target)

        # Per-row combos
        for row in range(self.layer_table.rowCount()):
            combo = self.layer_table.cellWidget(row, self.COL_SCHEMA)
            if combo is None:
                continue
            current = combo.currentText() if preserve_selection else None
            combo.clear()
            combo.addItems(schemas)
            row_target = current if current in schemas else (
                "public" if "public" in schemas else schemas[0])
            combo.setCurrentText(row_target)

    def _create_new_schema(self):
        if not self.conn_params:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Connect to database first."))
            return

        name, ok = QInputDialog.getText(
            self, self.tr("New schema"),
            self.tr("New schema name (lowercase, snake_case recommended):"))
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        warn = _pg_name_warnings(name)
        if warn == "empty":
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Schema name cannot be empty."))
            return
        if warn:
            r = QMessageBox.question(self, self.tr("Quoting required"),
                self.tr("'{name}' contains characters that will require "
                        "quoting in every future SQL statement. Create it "
                        "anyway?").format(name=name),
                _MBYes | _MBNo, _MBNo)
            if r != _MBYes:
                return

        if name in self.writable_schemas:
            QMessageBox.information(self, self.tr("Schema exists"),
                self.tr("Schema '{name}' already exists.").format(name=name))
            self._refresh_schema_combos(preserve_selection=True, prefer=name)
            return

        try:
            conn = pg_connect(self.conn_params)
            try:
                create_schema(conn, name)
                self.writable_schemas = get_writable_schemas(conn) \
                    or self.writable_schemas + [name]
            finally:
                conn.close()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Cannot create schema"), str(e))
            return

        QgsMessageLog.logMessage(
            f"Created schema '{name}'", LOG_TAG, Qgis.Info)
        self._refresh_schema_combos(preserve_selection=True, prefer=name)
        self.status_label.setText(
            self.tr("Schema '{name}' created.").format(name=name))

    def _update_import_button(self):
        ready = bool(self.conn_params) and bool(self.gpkg_layers)
        self.btn_import.setEnabled(ready)

    # ================================================================
    # Pre-import validation
    # ================================================================

    def _validate_jobs(self, jobs):
        """Validate destination names + warn on append-mode column mismatches.
        Returns True if user wants to proceed."""
        warnings = []

        # Identifier-style validation (non-blocking; warn on quoting needs)
        quoting_warnings = []
        for j in jobs:
            for kind, value in (("schema", j["target_schema"]),
                                ("table", j["target_table"])):
                w = _pg_name_warnings(value)
                if w == "empty":
                    QMessageBox.warning(self, self.tr("Error"),
                        self.tr("Destination {kind} for layer '{layer}' is empty.")
                        .format(kind=kind, layer=j["layer_name"]))
                    return False
                if w:
                    quoting_warnings.append(
                        f"  • {j['layer_name']}: {kind}='{value}' ({w})")

        if quoting_warnings:
            warnings.append(self.tr(
                "These names contain characters that will require quoting "
                "in every future SQL statement:") + "\n" + "\n".join(quoting_warnings))

        # Duplicate destinations within this batch
        dest_seen = {}
        for j in jobs:
            k = (j["target_schema"], j["target_table"])
            if k in dest_seen:
                QMessageBox.warning(self, self.tr("Error"),
                    self.tr("Layers '{a}' and '{b}' both target {s}.{t}").format(
                        a=dest_seen[k], b=j["layer_name"],
                        s=k[0], t=k[1]))
                return False
            dest_seen[k] = j["layer_name"]

        # Append-mode column validation
        for j in jobs:
            if j["mode"] != "append":
                continue
            try:
                dest_cols = list((j.get("field_map") or {}).values()) \
                    or [f["name"] for f in self._fields_for_layer(j["layer_name"])]
                missing_in_table, missing_in_src, _ = validate_append_columns(
                    self.conn_params, j["target_schema"], j["target_table"], dest_cols)
            except Exception as e:
                warnings.append(self.tr(
                    "Could not validate append schema for {layer}: {err}").format(
                    layer=j["layer_name"], err=e))
                continue

            parts = []
            if missing_in_table:
                parts.append(self.tr("missing in destination: {cols}").format(
                    cols=", ".join(missing_in_table)))
            if missing_in_src:
                parts.append(self.tr("missing in source: {cols}").format(
                    cols=", ".join(missing_in_src)))
            if parts:
                warnings.append(self.tr(
                    "Append mismatch on {s}.{t} ← {layer}: {parts}").format(
                    s=j["target_schema"], t=j["target_table"],
                    layer=j["layer_name"], parts="; ".join(parts)))

        # Replace confirmation
        replace_count = sum(1 for j in jobs if j["mode"] == "replace")
        if replace_count:
            warnings.insert(0, self.tr(
                "{n} layer(s) will DROP and recreate existing tables (CASCADE).")
                .format(n=replace_count))

        if warnings:
            msg = self.tr("Pre-import checks:") + "\n\n" + "\n\n".join(warnings) \
                + "\n\n" + self.tr("Proceed with import?")
            r = QMessageBox.question(self, self.tr("Pre-import checks"), msg,
                                     _MBYes | _MBNo, _MBNo)
            if r != _MBYes:
                return False
        return True

    def _fields_for_layer(self, layer_name):
        for lyr in self.gpkg_layers:
            if lyr["name"] == layer_name:
                return lyr["fields"]
        return []

    # ================================================================
    # Import
    # ================================================================

    def _run_import(self):
        if not self.conn_params:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Connect to database first."))
            return
        if not self.gpkg_path or not self.gpkg_layers:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Analyze a GeoPackage first."))
            return

        target_srid = self.srid_spin.value() if self.cb_reproject.isChecked() else None
        use_copy = self.cb_use_copy.isChecked()
        create_spatial_index = self.cb_spatial_index.isChecked()
        force_2d = self.cb_force_2d.isChecked()

        jobs = []
        any_3d_layer = False
        for row in self._selected_rows():
            lyr = self.layer_table.item(row, self.COL_LAYER).data(_UserRole)
            schema = self.layer_table.cellWidget(row, self.COL_SCHEMA).currentText()
            table = self.layer_table.item(row, self.COL_TABLE).text().strip()
            mode = self.layer_table.cellWidget(row, self.COL_MODE).currentData()

            src_srid_override = self.source_srid_overrides.get(lyr["name"])

            gt = (lyr.get("geom_type") or "").lower()
            if "3d" in gt or "z" in gt or "measured" in gt:
                any_3d_layer = True

            jobs.append({
                "gpkg_path": self.gpkg_path,
                "layer_name": lyr["name"],
                "target_schema": schema,
                "target_table": table,
                "mode": mode,
                "field_map": self.field_maps.get(lyr["name"]),
                "target_srid": target_srid,
                "source_srid_override": src_srid_override,
                "feat_count": lyr["count"],
                "use_copy": use_copy,
                "create_spatial_index": create_spatial_index,
                "force_2d": force_2d,
            })

        if not jobs:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Select at least one layer."))
            return

        if not self._validate_jobs(jobs):
            return

        if not self._health_check(any_3d_layer, use_copy):
            return

        self._launch_jobs(jobs)

    def _health_check(self, any_3d_layer, use_copy):
        """Quick pre-import sanity check: is the server up, primary, and not
        in recovery? Also flag the known 3D-Measured + COPY combo."""
        try:
            conn = pg_connect(self.conn_params)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Connection error"),
                self.tr("Cannot reach the database: {err}").format(err=e))
            return False

        try:
            try:
                in_recovery = pg_is_in_recovery(conn)
            except Exception:
                in_recovery = False
            srv = get_server_version(conn) or "?"
            pg_v = get_postgis_version(conn) or "?"
        finally:
            try:
                conn.close()
            except Exception:
                pass

        warnings = []
        if in_recovery:
            warnings.append(self.tr(
                "Server reports pg_is_in_recovery()=true. The database is "
                "still completing recovery from a previous crash or is a "
                "read-only replica. Writes will fail."))

        if any_3d_layer and use_copy:
            warnings.append(self.tr(
                "Some selected layers have 3D / Measured geometry types. "
                "If the server crashes during import, retry with 'Use COPY' "
                "disabled or with 'Force 2D' enabled in Advanced options."))

        QgsMessageLog.logMessage(
            f"Server check: server_version_num={srv}, postgis={pg_v}, "
            f"in_recovery={in_recovery}", LOG_TAG, Qgis.Info)

        if warnings:
            msg = self.tr("Health check:") + "\n\n" + "\n\n".join(warnings) \
                + "\n\n" + self.tr("Proceed anyway?")
            r = QMessageBox.question(self, self.tr("Health check"), msg,
                                     _MBYes | _MBNo, _MBNo)
            if r != _MBYes:
                return False
        return True

    def _launch_jobs(self, jobs):
        """Spin up the worker for the given job list. Shared by Import and
        Retry-failed paths."""
        transform_context = QgsProject.instance().transformContext()

        # Progress dialog uses sub-percent granularity (0..total*100)
        self._progress = QProgressDialog(
            self.tr("Importing..."), self.tr("Cancel"), 0, len(jobs) * 100, self)
        self._progress.setWindowTitle(self.tr("Import GeoPackage → PostgreSQL"))
        self._progress.setWindowModality(_WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        self._worker = ImportWorker(
            conn_params=self.conn_params,
            jobs=jobs,
            transform_context=transform_context,
            pause_between_layers_ms=self.pause_spin.value(),
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.import_finished.connect(self._on_import_finished)
        self._progress.canceled.connect(self._worker.request_cancel)

        self.btn_import.setEnabled(False)
        self.btn_retry.setEnabled(False)
        self._worker.start()

    def _retry_failed(self):
        if not self._failed_jobs:
            return
        # Strip the 'error' key — the worker doesn't need it
        jobs = [{k: v for k, v in fj.items() if k != "error"}
                for fj in self._failed_jobs]
        # User explicitly chose to retry, no need to re-confirm replaces
        self._launch_jobs(jobs)

    def _update_retry_button(self):
        n = len(self._failed_jobs)
        self.btn_retry.setText(self.tr("Retry failed ({n})").format(n=n))
        self.btn_retry.setEnabled(n > 0 and not self._worker)

    def _on_progress(self, step, total, label, sub_percent):
        if self._progress:
            value = (step - 1) * 100 + max(0, min(100, sub_percent))
            self._progress.setValue(value)
            self._progress.setLabelText(
                f"{label}  ({step}/{total} — {sub_percent}%)")

    def _on_import_finished(self, results):
        if self._progress:
            self._progress.close()
            self._progress = None

        self.btn_import.setEnabled(True)
        self._worker = None

        ok = results["ok_count"]
        total = results["total"]
        feat = results["feat_total"]
        failed_jobs = results.get("failed_jobs", [])

        # Track failed jobs for the Retry button (overwrites any previous set)
        self._failed_jobs = list(failed_jobs)
        self._update_retry_button()

        if results.get("cancelled"):
            s = self.tr("Import cancelled.\n\n")
        else:
            s = ""

        s += self.tr("Import completed!\n\n"
                     "Layers imported: {ok}/{total}\n"
                     "Features inserted: {feat}\n").format(
            ok=ok, total=total, feat=feat)

        if failed_jobs:
            s += self.tr("\nFailed layers ({n}):\n").format(n=len(failed_jobs))
            for fj in failed_jobs[:25]:
                s += (f"  • {fj['layer_name']} → "
                      f"{fj['target_schema']}.{fj['target_table']}\n"
                      f"      {fj.get('error', '?')}\n")
            if len(failed_jobs) > 25:
                s += self.tr("  … and {n} more (see log)\n").format(
                    n=len(failed_jobs) - 25)
            s += self.tr(
                "\nClick 'Retry failed ({n})' below to re-run just these layers."
            ).format(n=len(failed_jobs))

        QMessageBox.information(self, self.tr("Result"), s)
        self.status_label.setText(
            self.tr("Completed: {ok} layers, {feat} features, {err} errors")
            .format(ok=ok, feat=feat, err=len(failed_jobs)))
