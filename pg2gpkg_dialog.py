"""
PG2GPKG - Export dialog
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import os

from qgis.core import QgsApplication, QgsMessageLog, QgsProject, Qgis
from qgis.PyQt.QtCore import Qt, QCoreApplication, QSettings
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QFileDialog, QComboBox,
    QLabel, QProgressDialog, QMessageBox, QCheckBox,
    QGroupBox, QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QRadioButton, QButtonGroup, QDialogButtonBox,
)

from .db_utils import (
    HAS_PSYCOPG2, get_pg_connections, pg_connect,
    get_schemas, get_tables_and_views, resolve_auth_params,
)
from .export_engine import ExportWorker

LOG_TAG = "PG2GPKG"


class ExportPGtoGPKGDialog(QDialog):

    def __init__(self, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.conn = None
        self.conn_params = None
        self._all_tables = {}
        self._worker = None
        self._progress = None

        self.setWindowTitle(self.tr("Export PostgreSQL → GeoPackage"))
        self.setMinimumWidth(720)
        self.setMinimumHeight(680)
        self._setup_ui()

    def tr(self, message):
        return QCoreApplication.translate("PG2GPKG", message)

    # ================================================================
    # UI setup
    # ================================================================

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ── Connection ────────────────────────────────────────────
        cg = QGroupBox(self.tr("PostgreSQL Connection"))
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
        self.pass_edit.setEchoMode(QLineEdit.Password)

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

        btn_connect = QPushButton(self.tr("Connect and load schemas/tables"))
        btn_connect.clicked.connect(self._load_all)
        cl.addRow(btn_connect)
        layout.addWidget(cg)

        # ── Table tree ────────────────────────────────────────────
        tg = QGroupBox(self.tr("Schemas and tables"))
        tl = QVBoxLayout()
        tg.setLayout(tl)

        self.table_tree = QTreeWidget()
        self.table_tree.setHeaderLabels([
            self.tr("Name"), self.tr("Type"),
            self.tr("Geometry"), self.tr("SRID"),
        ])
        self.table_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3):
            self.table_tree.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table_tree.setSelectionMode(QAbstractItemView.NoSelection)
        tl.addWidget(self.table_tree)

        br = QHBoxLayout()
        for label, fn in [
            (self.tr("Select all"), lambda: self._set_all_check(True)),
            (self.tr("Deselect all"), lambda: self._set_all_check(False)),
            (self.tr("Spatial only"), self._check_spatial_only),
        ]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            br.addWidget(b)
        tl.addLayout(br)
        layout.addWidget(tg)

        # ── Export mode ───────────────────────────────────────────
        mg = QGroupBox(self.tr("GeoPackage mode"))
        ml = QVBoxLayout()
        mg.setLayout(ml)

        self.mode_per_schema = QRadioButton(
            self.tr("One GeoPackage per schema  (output/schema.gpkg)"))
        self.mode_single = QRadioButton(
            self.tr("Everything in a single GeoPackage"))
        self.mode_per_table = QRadioButton(
            self.tr("One GeoPackage per table  (output/schema/table.gpkg)"))
        self.mode_per_schema.setChecked(True)

        self.gpkg_mode = QButtonGroup(self)
        self.gpkg_mode.addButton(self.mode_per_schema, 0)
        self.gpkg_mode.addButton(self.mode_single, 1)
        self.gpkg_mode.addButton(self.mode_per_table, 2)

        ml.addWidget(self.mode_per_schema)

        sr = QHBoxLayout()
        sr.addWidget(self.mode_single)
        self.single_name = QLineEdit()
        self.single_name.setPlaceholderText(self.tr("filename.gpkg"))
        self.single_name.setEnabled(False)
        sr.addWidget(self.single_name)
        ml.addLayout(sr)

        ml.addWidget(self.mode_per_table)
        self.mode_single.toggled.connect(self.single_name.setEnabled)
        layout.addWidget(mg)

        # ── Options ───────────────────────────────────────────────
        og = QGroupBox(self.tr("Options"))
        ol = QVBoxLayout()
        og.setLayout(ol)

        self.cb_projects = QCheckBox(
            self.tr("Export QGIS projects from DB (with updated paths to GeoPackages)"))
        self.cb_projects.setChecked(True)
        ol.addWidget(self.cb_projects)
        layout.addWidget(og)

        # ── Output ────────────────────────────────────────────────
        orow = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self.tr("Select output folder..."))
        last_dir = QSettings().value("PG2GPKG/lastOutputDir", "")
        if last_dir and os.path.isdir(last_dir):
            self.output_edit.setText(last_dir)
        btn_browse = QPushButton(self.tr("Browse..."))
        btn_browse.clicked.connect(self._browse)
        orow.addWidget(QLabel(self.tr("Output:")))
        orow.addWidget(self.output_edit)
        orow.addWidget(btn_browse)
        layout.addLayout(orow)

        # ── Buttons ───────────────────────────────────────────────
        bb = QDialogButtonBox()
        self.btn_export = QPushButton(self.tr("Export"))
        self.btn_export.clicked.connect(self._run_export)
        self.btn_export.setEnabled(False)
        btn_close = QPushButton(self.tr("Close"))
        btn_close.clicked.connect(self.reject)
        bb.addButton(self.btn_export, QDialogButtonBox.AcceptRole)
        bb.addButton(btn_close, QDialogButtonBox.RejectRole)
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

    def _conn_params(self):
        if self.use_manual.isChecked():
            return {
                "host": self.host_edit.text(), "port": self.port_edit.text(),
                "database": self.db_edit.text(), "username": self.user_edit.text(),
                "password": self.pass_edit.text(), "sslmode": "prefer",
            }
        name = self.conn_combo.currentData()
        return self.connections.get(name) if name else None

    def _browse(self):
        f = QFileDialog.getExistingDirectory(self, self.tr("Select output folder"))
        if f:
            self.output_edit.setText(f)

    def closeEvent(self, event):
        """Ensure background worker and DB connection are cleaned up."""
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()
            self._worker.wait()
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
        super().closeEvent(event)

    # ================================================================
    # Load schemas/tables
    # ================================================================

    def _load_all(self):
        if not HAS_PSYCOPG2:
            QMessageBox.critical(self, self.tr("Missing dependency"),
                self.tr("The 'psycopg2' module is not installed.\n\n"
                         "Install it with: pip install psycopg2-binary"))
            return

        self.table_tree.clear()
        self._all_tables = {}
        params = self._conn_params()
        if not params:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("No connection selected."))
            return

        params = resolve_auth_params(params)

        try:
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
            self.conn = pg_connect(params)
            self.conn_params = params
        except Exception as e:
            QMessageBox.critical(self, self.tr("Connection error"), str(e))
            return

        schemas = get_schemas(self.conn)
        n = 0
        for schema in schemas:
            tables = get_tables_and_views(self.conn, schema)
            if not tables:
                continue
            self._all_tables[schema] = tables

            si = QTreeWidgetItem([schema, "", "", ""])
            si.setFlags(si.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            si.setCheckState(0, Qt.Checked)

            for t in tables:
                geom = t["geom_type"] or "—"
                srid = str(t["srid"]) if t["geom_column"] else "—"
                ttype = self.tr("View") if "VIEW" in (t["table_type"] or "") \
                    else self.tr("Table")
                if t["geom_column"]:
                    ttype += f"  [{t['geom_column']}]"

                ci = QTreeWidgetItem([t["table"], ttype, geom, srid])
                ci.setFlags(ci.flags() | Qt.ItemIsUserCheckable)
                ci.setCheckState(0, Qt.Checked)
                ci.setData(0, Qt.UserRole, t)
                ci.setData(0, Qt.UserRole + 1, schema)
                si.addChild(ci)
                n += 1

            self.table_tree.addTopLevelItem(si)

        self.table_tree.expandAll()
        self.btn_export.setEnabled(True)
        self.status_label.setText(
            self.tr("{count} tables/views in {schemas} schemas — {db}").format(
                count=n, schemas=len(self._all_tables),
                db=params["database"]))

    def _set_all_check(self, on):
        st = Qt.Checked if on else Qt.Unchecked
        for i in range(self.table_tree.topLevelItemCount()):
            self.table_tree.topLevelItem(i).setCheckState(0, st)

    def _check_spatial_only(self):
        for i in range(self.table_tree.topLevelItemCount()):
            si = self.table_tree.topLevelItem(i)
            for j in range(si.childCount()):
                ci = si.child(j)
                info = ci.data(0, Qt.UserRole)
                ci.setCheckState(
                    0, Qt.Checked if info and info.get("geom_column") else Qt.Unchecked)

    def _selected_tables(self):
        """Return {schema: [table_info, ...]} for checked items."""
        result = {}
        for i in range(self.table_tree.topLevelItemCount()):
            si = self.table_tree.topLevelItem(i)
            for j in range(si.childCount()):
                ci = si.child(j)
                if ci.checkState(0) == Qt.Checked:
                    info = ci.data(0, Qt.UserRole)
                    schema = ci.data(0, Qt.UserRole + 1)
                    if schema and info:
                        result.setdefault(schema, []).append(info)
        return result

    # ================================================================
    # Export
    # ================================================================

    def _run_export(self):
        output_dir = self.output_edit.text()
        if not output_dir or not os.path.isdir(output_dir):
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Select a valid output folder."))
            return

        selected = self._selected_tables()
        if not selected:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Select at least one table."))
            return

        if not self.conn_params:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Connect to database first."))
            return

        mode = self.gpkg_mode.checkedId()  # 0=per-schema 1=single 2=per-table

        single_path = None
        if mode == 1:
            gn = self.single_name.text().strip()
            if not gn:
                gn = f"{self.conn_params['database']}.gpkg"
            if not gn.lower().endswith(".gpkg"):
                gn += ".gpkg"
            single_path = os.path.join(output_dir, gn)

        do_projects = self.cb_projects.isChecked()
        total = sum(len(v) for v in selected.values())

        # Get transform context from main thread (thread-safe copy)
        transform_context = QgsProject.instance().transformContext()

        # Save last output directory
        QSettings().setValue("PG2GPKG/lastOutputDir", output_dir)

        # Progress dialog
        self._progress = QProgressDialog(
            self.tr("Exporting..."), self.tr("Cancel"), 0, total + 1, self)
        self._progress.setWindowTitle(self.tr("Export PostgreSQL → GeoPackage"))
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        # Create worker thread
        self._worker = ExportWorker(
            conn_params=self.conn_params,
            selected=selected,
            mode=mode,
            output_dir=output_dir,
            single_path=single_path,
            do_projects=do_projects,
            transform_context=transform_context,
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.export_finished.connect(self._on_export_finished)
        self._progress.canceled.connect(self._worker.request_cancel)

        # Disable UI during export
        self.btn_export.setEnabled(False)

        self._worker.start()

    def _on_progress(self, step, total, label):
        if self._progress:
            self._progress.setValue(step)
            self._progress.setLabelText(f"{label}  ({step}/{total})")

    def _on_export_finished(self, results):
        if self._progress:
            self._progress.close()
            self._progress = None

        self.btn_export.setEnabled(True)
        self._worker = None

        mode = results["mode"]
        ok_count = results["ok_count"]
        total = results["total"]
        gpkg_count = results["gpkg_count"]
        errors = results["errors"]
        exported_proj = results["exported_projects"]

        mode_labels = {
            0: self.tr("one GeoPackage per schema"),
            1: self.tr("single GeoPackage"),
            2: self.tr("one GeoPackage per table"),
        }

        if results.get("cancelled"):
            s = self.tr("Export cancelled.\n\n")
        else:
            s = ""

        s += self.tr("Export completed! ({mode})\n\n"
                     "Layers exported: {ok}/{total}\n"
                     "GeoPackages created: {gpkg}\n").format(
            mode=mode_labels[mode], ok=ok_count, total=total, gpkg=gpkg_count)

        if exported_proj:
            s += self.tr("\nQGIS projects: {count}\n").format(count=len(exported_proj))
            for p in exported_proj:
                s += f"  • {p}\n"
        if errors:
            s += self.tr("\nErrors ({count}):\n").format(count=len(errors))
            for e in errors[:25]:
                s += f"  • {e}\n"
            if len(errors) > 25:
                s += self.tr("  … and {n} more (see log)\n").format(n=len(errors) - 25)

        QMessageBox.information(self, self.tr("Result"), s)
        self.status_label.setText(
            self.tr("Completed: {ok} layers, {err} errors").format(
                ok=ok_count, err=len(errors)))
