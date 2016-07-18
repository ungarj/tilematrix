#!/usr/bin/env python

import os
from rasterio import profiles


class OutputFormat(object):
    """
    Class which handles different output formats and their properties. The
    intension is to have two main choices:
    (1) store tile pyramid on filesystem using files and directories (e.g.
        name/zoom/row/col.tif), or
    (2) store tile pyramid in an extended geopackage.
    """
    def __init__(
        self,
        output_format,
        db_params=None
        ):

        supported_rasterformats = ["GTiff", "PNG", "PNG_hillshade"]
        supported_vectorformats = ["GeoJSON", "postgis"]
        supported_formats = supported_rasterformats + supported_vectorformats

        format_extensions = {
            "GTiff": ".tif",
            "PNG": ".png",
            "PNG_hillshade": ".png",
            "GeoJSON": ".geojson",
            "postgis": None
        }

        try:
            assert output_format in supported_formats
        except:
            raise ValueError(
                "ERROR: Output format %s not found. Please use one of %s" %(
                output_format, supported_formats)
            )

        self.name = output_format

        if output_format in supported_rasterformats:
            self.format = output_format
            self.datatype = "raster"
        elif output_format in supported_vectorformats:
            self.format = output_format
            self.datatype = "vector"

        if self.format == "GTiff":
            self.profile = profiles.DefaultGTiffProfile().defaults
            self.profile.update(
                driver="GTiff",
                nodata=None
                )
            self.is_db = False

        if self.format == "PNG":
            self.profile = {
                'dtype': 'uint8',
                'nodata': None,
                'driver': 'PNG',
                'count': 3
            }
            self.is_db = False

        if self.format == "PNG_hillshade":
            self.profile = {
                'dtype': 'uint8',
                'nodata': 0,
                'driver': 'PNG',
                'count': 4
            }
            self.is_db = False

        if self.format == "GeoJSON":
            self.schema = {}
            self.driver = "GeoJSON"
            self.is_db = False

        if self.format == "postgis":
            self.is_db = True
            self.driver = "postgis"
            if not db_params:
                raise ValueError("please provide database credentials")
            for param in ["db", "host", "port", "user", "password", "table"]:
                try:
                    assert param in db_params
                    assert db_params[param]
                except:
                    raise ValueError("database parameter %s is missing" %param)
            self.db_params = db_params

        self.extension = format_extensions[self.name]

    def prepare(self, output_name, tile):
        """
        If format is file based, this function shall create the desired
        directories.
        If it is a GeoPackage, it shall initialize the SQLite file.
        """
        if self.is_db:
            pass
        else:
            zoomdir = os.path.join(output_name, str(tile.zoom))
            try:
                os.makedirs(zoomdir)
            except OSError, err:
                if err.errno == 17:
                    pass
                else:
                    raise
            rowdir = os.path.join(zoomdir, str(tile.row))
            try:
                os.makedirs(rowdir)
            except OSError, err:
                if err.errno == 17:
                    pass
                else:
                    raise


    def get_tile_name(self, output_name, tile):
        """
        Returns full name of tile.
        """
        if self.is_db:
            return None
        else:
            zoomdir = os.path.join(output_name, str(tile.zoom))
            rowdir = os.path.join(zoomdir, str(tile.row))
            tile_name = os.path.join(rowdir, str(tile.col)+self.extension)
            return tile_name


    def set_dtype(self, dtype):
        """
        Sets profile data type.
        """
        self.profile["dtype"] = dtype
