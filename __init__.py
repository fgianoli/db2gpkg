"""
PG2GPKG - Export PostgreSQL/PostGIS to GeoPackage
Copyright (C) 2025 Federico Gianoli

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PG2GPKG plugin class.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .pg2gpkg_plugin import PG2GPKGPlugin
    return PG2GPKGPlugin(iface)
