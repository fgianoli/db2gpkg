"""
PG2GPKG - QGIS Plugin main class
Copyright (C) 2025 Federico Gianoli — GPLv3
"""

import os
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings, QLocale
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .pg2gpkg_dialog import ExportPGtoGPKGDialog


class PG2GPKGPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "PG2GPKG"
        self.toolbar = self.iface.addToolBar("PG2GPKG")
        self.toolbar.setObjectName("PG2GPKGToolbar")

        # i18n
        locale = QSettings().value("locale/userLocale", QLocale.system().name())
        locale_code = locale[:2] if locale else "en"
        locale_path = os.path.join(self.plugin_dir, "i18n", f"pg2gpkg_{locale_code}.qm")
        self.translator = QTranslator()
        if os.path.exists(locale_path):
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def tr(self, message):
        return QCoreApplication.translate("PG2GPKG", message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icons", "pg2gpkg.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        action = QAction(icon, self.tr("Export PostgreSQL to GeoPackage"), self.iface.mainWindow())
        action.triggered.connect(self.run)
        action.setStatusTip(self.tr("Export PostgreSQL/PostGIS database to GeoPackage"))

        self.iface.addPluginToDatabaseMenu(self.menu, action)
        self.toolbar.addAction(action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(self.menu, action)
            self.toolbar.removeAction(action)
        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.deleteLater()
        self.toolbar = None

    def run(self):
        dialog = ExportPGtoGPKGDialog(self.iface, parent=self.iface.mainWindow())
        dialog.exec_()
