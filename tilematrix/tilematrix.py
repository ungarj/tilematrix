#!/usr/bin/env python

import sys
from shapely.geometry import *
from shapely.validation import *
from shapely.prepared import prep
from itertools import product
from rasterio import profiles
import math

ROUND = 20


class TilePyramid(object):

    def __init__(self, projection, tile_size=256):
        """
        Initialize TilePyramid.
        """
        projections = ("4326", "3857")
        try:
            assert projection in projections
        except:
            print "WMTS tileset '%s' not found. Use one of %s" %(projection,
                projections)
            sys.exit(0)
        self.projection = projection
        self.tile_size = tile_size
        if projection == "4326":
            # spatial extent
            self.left = float(-180)
            self.top = float(90)
            self.right = float(180)
            self.bottom = float(-90)
            # size in degrees
            self.x_size = float(round(self.right - self.left, ROUND))
            self.y_size = float(round(self.top - self.bottom, ROUND))
            # SRS
            self.crs = {'init': u'EPSG:4326'}
            # optional output format
            self.format = None

    def set_format(self, output_format, dtype=None):
        self.format = OutputFormat(output_format)
        if dtype:
            self.format.set_dtype(dtype)

    def matrix_width(self, zoom):
        """
        Tile matrix width (number of columns) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.projection == "4326":
            width = 2**(zoom+1)
        return width

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.projection == "4326":
            height = 2**(zoom+1)/2
        return height

    def tile_x_size(self, zoom):
        """
        Width of tile in SRID units at zoom level.
        """
        matrix_width = self.matrix_width(zoom)
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        tile_x_size = float(round(self.x_size/matrix_width, ROUND))
        return tile_x_size

    def tile_y_size(self, zoom):
        """
        Height of tile in SRID units at zoom level.
        """
        matrix_height = self.matrix_height(zoom)
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        tile_y_size = float(round(self.y_size/matrix_height, ROUND))
        return tile_y_size

    def pixel_x_size(self, zoom):
        """
        Size of pixels in SRID units at zoom level.
        """
        pixel_x_size = float(round(
            self.tile_x_size(zoom) / self.tile_size,
            ROUND))
        return pixel_x_size

    def pixel_y_size(self, zoom):
        """
        Size of pixels in SRID units at zoom level.
        """
        pixel_y_size = float(round(
            self.tile_y_size(zoom) / self.tile_size,
            ROUND))
        return pixel_y_size

    def top_left_tile_coords(self, zoom, row, col):
        """
        Top left coordinate of tile.
        """
        left, upper = top_left_tile_coords(self, zoom, row, col)
        return left, upper

    def tile_bounds(self, zoom, row, col, pixelbuffer=None):
        """
        Tile boundaries with optional pixelbuffer.
        """
        bounds = tile_bounds(self, zoom, row, col, pixelbuffer=pixelbuffer)
        return bounds

    def tile_bbox(self, zoom, row, col, pixelbuffer=None):
        """
        Tile bounding box with optional pixelbuffer as WKT.
        """
        bbox = tile_bbox(self, zoom, row, col, pixelbuffer=pixelbuffer)
        return bbox

    def tiles_from_bbox(self, geometry, zoom):
        """
        All tiles intersecting with given bounding box.
        """
        tilelist = tiles_from_bbox(self, geometry, zoom)
        return tilelist

    def tiles_from_geom(self, geometry, zoom):
        """
        All tiles intersecting with input geometry.
        """
        tilelist = tiles_from_geom(self, geometry, zoom)
        return tilelist


class MetaTilePyramid(TilePyramid):

    def __init__(self, tilepyramid, metatiles=1):
        """
        Initialize MetaTilePyramid using a TilePyramid.
        """
        assert isinstance(tilepyramid, TilePyramid)
        assert isinstance(metatiles, int)
        assert metatiles in (1, 2, 4, 8, 16)
        self.tilepyramid = tilepyramid
        if tilepyramid.format:
            self.format = tilepyramid.format
        else:
            self.format = None
        self.metatiles = metatiles
        # spatial extent:
        self.left = self.tilepyramid.left
        self.top = self.tilepyramid.top
        self.right = self.tilepyramid.right
        self.bottom = self.tilepyramid.bottom
        # size in degrees:
        self.x_size = tilepyramid.x_size
        self.y_size = tilepyramid.y_size
        # SRS
        self.projection = tilepyramid.projection
        self.crs = tilepyramid.crs



    def matrix_width(self, zoom):
        """
        Metatile matrix width (number of columns) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.projection == "4326":
            width = self.tilepyramid.matrix_width(zoom)
            width = math.ceil(width / float(self.metatiles))
            if width < 1:
                width = 1
        return int(width)

    def matrix_height(self, zoom):
        """
        Metatile matrix height (number of columns) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.projection == "4326":
            height = self.tilepyramid.matrix_height(zoom)
            height = math.ceil(height / float(self.metatiles))
            if height < 1:
                height = 1
        return int(height)

    def metatile_width(self, zoom):
        """
        Metatile width in pixel. It is the equivalent of tile_size in a
        TilePyramid and can change per zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.tilepyramid.matrix_width(zoom) >= self.metatiles:
            metatile_width = self.tilepyramid.tile_size*self.metatiles
        else:
            metatile_width = (
                self.tilepyramid.matrix_width(zoom)*self.tilepyramid.tile_size
            )
        return metatile_width

    def metatile_height(self, zoom):
        """
        Metatile height in pixel. It is the equivalent of tile_size in a
        TilePyramid and can change per zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        if self.tilepyramid.matrix_height(zoom) >= self.metatiles:
            metatile_height = self.tilepyramid.tile_size*self.metatiles
        else:
            metatile_height = (
                self.tilepyramid.matrix_height(zoom)*self.tilepyramid.tile_size
            )
        return metatile_height

    def metatile_x_size(self, zoom):
        """
        Width of metatile in SRID units at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        tile_x_size = self.tilepyramid.tile_x_size(zoom)
        metatile_x_size = tile_x_size * float(self.metatiles)
        if metatile_x_size > self.x_size:
            metatile_x_size = self.x_size
        return metatile_x_size

    def metatile_y_size(self, zoom):
        """
        Height of metatile in SRID units at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            print "Zoom (%s) must be an integer." %(zoom)
            sys.exit(0)
        tile_y_size = self.tilepyramid.tile_y_size(zoom)
        metatile_y_size = tile_y_size * float(self.metatiles)
        if metatile_y_size > self.y_size:
            metatile_y_size = self.y_size
        return metatile_y_size

    def pixel_x_size(self, zoom):
        """
        Size of pixels in SRID units at zoom level.
        """
        pixel_x_size = float(round(
            self.metatile_x_size(zoom) / self.metatile_width(zoom),
            ROUND))
        return pixel_x_size

    def pixel_y_size(self, zoom):
        """
        Size of pixels in SRID units at zoom level.
        """
        pixel_y_size = float(round(
            self.metatile_y_size(zoom) / self.metatile_height(zoom),
            ROUND))
        return pixel_y_size

    def top_left_tile_coords(self, zoom, row, col):
        """
        Top left coordinate of metatile.
        """
        try:
            left, upper = top_left_tile_coords(self, zoom, row, col)
            return left, upper
        except:
            print "ERROR determining tile coordinates."
            raise

    def tile_bounds(self, zoom, row, col, pixelbuffer=None):
        """
        Metatile boundaries with optional pixelbuffer.
        """
        bounds = tile_bounds(self, zoom, row, col, pixelbuffer=pixelbuffer)
        return bounds

    def tile_bbox(self, zoom, row, col, pixelbuffer=None):
        """
        Metatile bounding box with optional pixelbuffer as WKT.
        """
        bbox = tile_bbox(self, zoom, row, col, pixelbuffer=pixelbuffer)
        return bbox

    def tiles_from_bbox(self, geometry, zoom):
        """
        All metatiles intersecting with given bounding box.
        """
        tilelist = tiles_from_bbox(self, geometry, zoom)
        return tilelist

    def tiles_from_geom(self, geometry, zoom):
        """
        All metatiles intersecting with input geometry.
        """
        tilelist = tiles_from_geom(self, geometry, zoom)
        return tilelist

    def tiles_from_tilepyramid(self, zoom, row, col, geometry=None):
        """
        All tiles from original tilepyramid intersecting with input geometry.
        """
        tilepyramid = self.tilepyramid
        metatile_bbox = self.tile_bbox(zoom, row, col)
        if geometry:
            geom_clipped = geometry.intersection(metatile_bbox)
            tilelist = tilepyramid.tiles_from_geom(geom_clipped, zoom)
        else:
            tilelist = tilepyramid.tiles_from_bbox(metatile_bbox, zoom)
        return tilelist

"""
Shared methods for TilePyramid and MetaTilePyramid.
"""
def tile_bounds(tilepyramid, zoom, row, col, pixelbuffer=None):
    """
    Tile boundaries with optional pixelbuffer.
    """
    try:
        assert isinstance(zoom, int)
    except:
        print "Zoom (%s) must be an integer." %(zoom)
        sys.exit(0)
    tile_x_size = tilepyramid.tile_x_size(zoom)
    tile_y_size = tilepyramid.tile_y_size(zoom)
    ul = tilepyramid.top_left_tile_coords(zoom, row, col)
    left = ul[0]
    bottom = ul[1] - tile_y_size
    right = ul[0] + tile_x_size
    top = ul[1]
    if pixelbuffer:
        assert isinstance(pixelbuffer, int)
        offset = tilepyramid.pixel_x_size(zoom) * float(pixelbuffer)
        left -= offset
        bottom -= offset
        right += offset
        top += offset
    if right > tilepyramid.right:
        right = tilepyramid.right
    if bottom < tilepyramid.bottom:
        bottom = tilepyramid.bottom
    return (left, bottom, right, top)


def tile_bbox(tilepyramid, zoom, row, col, pixelbuffer=None):
    """
    Tile bounding box with optional pixelbuffer as WKT.
    """
    try:
        assert isinstance(zoom, int)
    except:
        print "Zoom (%s) must be an integer." %(zoom)
        sys.exit(0)
    left, bottom, right, top = tilepyramid.tile_bounds(zoom, row, col,
        pixelbuffer=pixelbuffer)
    ul = left, top
    ur = right, top
    lr = right, bottom
    ll = left, bottom
    return Polygon([ul, ur, lr, ll])


def top_left_tile_coords(tilepyramid, zoom, row, col):
    """
    Top left coordinate of tile.
    """
    try:
        assert isinstance(zoom, int)
    except:
        print "Zoom (%s) must be an integer." %(zoom)
        sys.exit(0)
    tile_x_size = tilepyramid.tile_x_size(zoom)
    tile_y_size = tilepyramid.tile_y_size(zoom)
    matrix_width = tilepyramid.matrix_width(zoom)
    matrix_height = tilepyramid.matrix_height(zoom)

    if (col > matrix_width) or (row > matrix_height):
        print "no tile indices available on this zoom"
        print zoom, row, col
        print tilepyramid.tiles_per_zoom(zoom)
    else:
        left = float(round(tilepyramid.left+((col)*tile_x_size), ROUND))
        upper = float(round(tilepyramid.top-((row)*tile_y_size), ROUND))
        return left, upper


def tiles_from_bbox(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with given bounding box.
    """
    try:
        assert isinstance(zoom, int)
    except:
        print "Zoom (%s) must be an integer." %(zoom)
        sys.exit(0)
    tile_x_size = tilepyramid.tile_x_size(zoom)
    tile_y_size = tilepyramid.tile_y_size(zoom)
    tilelist = []
    l, b, r, t = geometry.bounds
    tilelon = tilepyramid.left
    tilelat = tilepyramid.top
    cols = []
    rows = []
    col = -1
    row = -1
    while tilelon <= l:
        tilelon += tile_x_size
        col += 1
    cols.append(col)
    while tilelon < r:
        tilelon += tile_x_size
        col += 1
        cols.append(col)
    while tilelat >= t:
        tilelat -= tile_y_size
        row += 1
    rows.append(row)
    while tilelat > b:
        tilelat -= tile_y_size
        row += 1
        rows.append(row)
    tilelist = list(product([zoom], rows, cols))
    return tilelist


def tiles_from_geom(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with input geometry.
    """

    tilelist = []

    try:
        assert geometry.is_valid
    except:
        print "WARNING: geometry seems not to be valid"
        #print explain_validity(geometry)
        try:
            clean = geometry.buffer(0.0)
            assert clean.is_valid
            assert clean.area > 0
            geometry = clean
            print "... cleaning successful"
        except:
            print "... geometry could not be fixed"
            sys.exit(0)

    if geometry.almost_equals(geometry.envelope, ROUND):
        tilelist = tilepyramid.tiles_from_bbox(geometry, zoom)

    elif geometry.geom_type == "Point":
        lon, lat = list(geometry.coords)[0]
        tilelon = tilepyramid.left
        tilelat = tilepyramid.top
        tile_x_size = tilepyramid.tile_x_size(zoom)
        tile_y_size = tilepyramid.tile_y_size(zoom)
        col = -1
        row = -1
        while tilelon < lon:
            tilelon += tile_x_size
            col += 1
        while tilelat > lat:
            tilelat -= tile_y_size
            row += 1
        tilelist.append((zoom, row, col))

    elif geometry.geom_type in ("LineString", "MultiLineString", "Polygon",
        "MultiPolygon", "MultiPoint"):
        prepared_geometry = prep(geometry)
        bbox_tilelist = tilepyramid.tiles_from_bbox(geometry, zoom)
        for tile in bbox_tilelist:
            zoom, row, col = tile
            geometry = tilepyramid.tile_bbox(zoom, row, col)
            if prepared_geometry.intersects(geometry):
                tilelist.append((zoom, row, col))

    else:
        print "ERROR: no valid geometry"
        sys.exit(0)

    return tilelist


class OutputFormat(object):

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
            print "ERROR: Output format %s not found. Please use one of %s" %(
                output_format, supported_formats)
            sys.exit(0)

        self.name = output_format

        if output_format in supported_rasterformats:
            self.format = output_format
            self.type = "raster"
        elif output_format in supported_vectorformats:
            self.format = output_format
            self.type = "vector"

        # Default driver equals format name .

        if self.format == "GTiff":
            self.profile = profiles.DefaultGTiffProfile().defaults
            self.profile.update(driver="GTiff")

        if self.format == "PNG":
            self.profile = {
                'dtype': 'uint8',
                'nodata': 0,
                'driver': 'PNG'
            }

        if self.format == "PNG_hillshade":
            self.profile = {
                'dtype': 'uint8',
                'nodata': 0,
                'driver': 'PNG',
                'count': 4
            }


        self.extension = format_extensions[self.name]

    def set_dtype(self, dtype):
        self.profile["dtype"] = dtype
