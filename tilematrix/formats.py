#!/usr/bin/env python

import os
from rasterio import profiles
import numpy as np

class OutputFormat(object):
    """
    Class which handles different output formats and their properties. The
    intension is to have two main choices:
    (1) store tile pyramid on filesystem using files and directories (e.g.
        name/zoom/row/col.tif), or
    (2) store tile pyramid in an extended geopackage.
    """
    def __init__(self, output_format):

        supported_rasterformats = ["GTiff", "PNG", "PNG_hillshade"]
        supported_vectorformats = ["GeoJSON"]
        supported_formats = supported_rasterformats + supported_vectorformats

        format_extensions = {
            "GTiff": ".tif",
            "PNG": ".png",
            "PNG_hillshade": ".png",
            "GeoJSON": ".geojson"
        }

        try:
            assert output_format in supported_formats
        except:
            return ValueError(
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
            self._gpkg = False

        if self.format == "PNG":
            self.profile = {
                'dtype': 'uint8',
                'nodata': None,
                'driver': 'PNG',
                'count': 3
            }
            self._gpkg = False

        if self.format == "PNG_hillshade":
            self.profile = {
                'dtype': 'uint8',
                'nodata': 0,
                'driver': 'PNG',
                'count': 4
            }
            self._gpkg = False

        self.extension = format_extensions[self.name]

    def prepare(self, output_name, tile):
        """
        If format is file based, this function shall create the desired
        directories.
        If it is a GeoPackage, it shall initialize the SQLite file.
        """
        if self._gpkg:
            pass
            # TODO initialize SQLite file
        else:
            zoomdir = os.path.join(output_name, str(tile.zoom))
            if os.path.exists(zoomdir):
                pass
            else:
                try:
                    os.makedirs(zoomdir)
                except:
                    pass
            rowdir = os.path.join(zoomdir, str(tile.row))
            if os.path.exists(rowdir):
                pass
            else:
                try:
                    os.makedirs(rowdir)
                except:
                    pass


    def get_tile_name(self, output_name, tile):
        """
        Returns full name of tile.
        """
        if self._gpkg:
            return None
        else:
            zoomdir = os.path.join(output_name, str(tile.zoom))
            rowdir = os.path.join(zoomdir, str(tile.row))
            tile_name = os.path.join(rowdir, str(tile.col)+self.extension)
            return tile_name


    def set_dtype(self, dtype):
        self.profile["dtype"] = dtype
