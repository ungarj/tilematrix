#!/usr/bin/env python

import sys
from shapely.geometry import *
from shapely.validation import *
from shapely.prepared import prep
from itertools import product
import math

from .formats import OutputFormat

ROUND = 20


class TilePyramid(object):

    def __init__(self, projection, tile_size=256):
        """
        Initialize TilePyramid.
        """
        projections = ("geodetic", "mercator")
        try:
            assert projection in projections
        except:
            print "WMTS tileset '%s' not found. Use one of %s" %(projection,
                projections)
            sys.exit(0)
        self.type = projection
        self.tile_size = tile_size
        if projection == "geodetic":
            # spatial extent
            self.left = float(-180)
            self.top = float(90)
            self.right = float(180)
            self.bottom = float(-90)
            # size in degrees
            self.x_size = float(round(self.right - self.left, ROUND))
            self.y_size = float(round(self.top - self.bottom, ROUND))
            # SRS
            self.crs = {'init': u'epsg:4326'}
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
        if self.type == "geodetic":
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
        if self.type == "geodetic":
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

    def get_neighbors(self, tile, count):
        """
        Returns tile neighbors.
        """
        neighbors = get_neighbors(self, tile, count)
        return neighbors

    def tile_is_valid(self, tile):
        """
        Returns True if tile is available in tile pyramid.
        """
        return tile_is_valid(self, tile)


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
        self.tile_size = tilepyramid.tile_size * metatiles
        # spatial extent:
        self.left = self.tilepyramid.left
        self.top = self.tilepyramid.top
        self.right = self.tilepyramid.right
        self.bottom = self.tilepyramid.bottom
        # size in degrees:
        self.x_size = tilepyramid.x_size
        self.y_size = tilepyramid.y_size
        # SRS
        self.type = tilepyramid.type
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
        if self.type == "geodetic":
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
        if self.type == "geodetic":
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

    def get_neighbors(self, tile, count):
        """
        Returns tile neighbors.
        """
        neighbors = get_neighbors(self, tile, count)
        return neighbors

    def tile_is_valid(self, tile):
        """
        Returns True if tile is available in tile pyramid.
        """
        return tile_is_valid(self, tile)

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
    for tile in list(product([zoom], rows, cols)):
        yield tile


def tiles_from_geom(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with input geometry.
    """

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

    if geometry.almost_equals(geometry.envelope, ROUND):
        for tile in tilepyramid.tiles_from_bbox(geometry, zoom):
            yield tile

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
        yield (zoom, row, col)

    elif geometry.geom_type in ("LineString", "MultiLineString", "Polygon",
        "MultiPolygon", "MultiPoint"):
        prepared_geometry = prep(geometry)
        for tile in tilepyramid.tiles_from_bbox(geometry, zoom):
            if prepared_geometry.intersects(tilepyramid.tile_bbox(*tile)):
                yield tile
    else:
        print "ERROR: no valid geometry"



def get_neighbors(self, tile, count):
    """
    Returns tile neighbors.
    -------------
    | 8 | 1 | 5 |
    -------------
    | 4 | x | 2 |
    -------------
    | 7 | 3 | 6 |
    -------------
    """
    if count > 8:
        count = 8
    if count == 0:
        return []
    zoom, row, col = tile
    neighbors = []
    # fill up set with up to 8 direct neighbors
    for newtile in [
        (zoom, row-1, col),
        (zoom, row, col+1),
        (zoom, row+1, col),
        (zoom, row, col-1),
        (zoom, row-1, col+1),
        (zoom, row+1, col+1),
        (zoom, row+1, col-1),
        (zoom, row-1, col-1)
        ]:
        # top
        if self.tile_is_valid(newtile):
            neighbors.append(newtile)
        if len(neighbors) >= count:
            return neighbors


def tile_is_valid(self, tile):
    """
    Returns True if tile is available in tile pyramid.
    """
    zoom, row, col = tile
    try:
        assert isinstance(zoom, int)
        assert zoom >= 0
        assert isinstance(col, int)
        assert col >= 0
        assert isinstance(col, int)
        assert col >= 0
        assert col <= self.matrix_width(zoom)
        assert row <= self.matrix_height(zoom)
    except:
        return False
    else:
        return True
