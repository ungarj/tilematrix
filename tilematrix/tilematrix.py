#!/usr/bin/env python

from shapely.geometry import Polygon
from shapely.validation import explain_validity
from shapely.prepared import prep
from itertools import product
import math
from affine import Affine

ROUND = 20


class Tile(object):

    def __init__(self, tile_pyramid, zoom, row, col):
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        self.tile_pyramid = tile_pyramid
        self.crs = tile_pyramid.crs
        self.zoom = zoom
        self.row = row
        self.col = col
        self.index = (zoom, row, col)
        self.x_size = self._get_x_size()
        self.y_size = self._get_y_size()
        self.id = (zoom, row, col)
        self.pixel_x_size = self.tile_pyramid.pixel_x_size(self.zoom)
        self.pixel_y_size = self.tile_pyramid.pixel_y_size(self.zoom)
        self.left = float(round(
            self.tile_pyramid.left+((self.col)*self.x_size),
            ROUND
        ))
        self.top = float(round(
            self.tile_pyramid.top-((self.row)*self.y_size),
            ROUND
        ))
        self.right = self.left + self.x_size
        self.bottom = self.top - self.y_size
        self.width = tile_pyramid.tile_size
        self.height = tile_pyramid.tile_size
        self.srid = tile_pyramid.srid


    def get_parent(self):
        """
        Returns tile from previous zoomlevel.
        """
        if self.zoom == 0:
            return None
        else:
            return self.tile_pyramid.tile(
                self.zoom-1,
                int(self.row/2),
                int(self.col/2),
                )

    def get_children(self):
        """
        Returns tiles from next zoomlevel.
        """
        return [
            self.tile_pyramid.tile(
                self.zoom+1,
                self.row*2,
                self.col*2
                ),
            self.tile_pyramid.tile(
                self.zoom+1,
                self.row*2+1,
                self.col*2
                ),
            self.tile_pyramid.tile(
                self.zoom+1,
                self.row*2,
                self.col*2+1
                ),
            self.tile_pyramid.tile(
                self.zoom+1,
                self.row*2+1,
                self.col*2+1
                )
            ]


    def _get_x_size(self):
        """
        Width of tile in SRID units at zoom level.
        """
        if isinstance(self.tile_pyramid, MetaTilePyramid):
            tile_x_size = self.tile_pyramid.tilepyramid.tile_x_size(self.zoom)
            metatile_x_size = tile_x_size * float(self.tile_pyramid.metatiles)
            if metatile_x_size > self.tile_pyramid.x_size:
                metatile_x_size = self.tile_pyramid.x_size
            return metatile_x_size
        else:
            return self.tile_pyramid.tile_x_size(self.zoom)


    def _get_y_size(self):
        """
        Height of tile in SRID units at zoom level.
        """
        if isinstance(self.tile_pyramid, MetaTilePyramid):
            tile_y_size = self.tile_pyramid.tilepyramid.tile_y_size(self.zoom)
            metatile_y_size = tile_y_size * float(self.tile_pyramid.metatiles)
            if metatile_y_size > self.tile_pyramid.y_size:
                metatile_y_size = self.tile_pyramid.y_size
            return metatile_y_size
        else:
            return self.tile_pyramid.tile_y_size(self.zoom)


    def bounds(self, pixelbuffer=0):
        """
        Tile boundaries with optional pixelbuffer.
        """
        left = self.left
        bottom = self.top - self.y_size
        right = self.left + self.x_size
        top = self.top
        if pixelbuffer > 0:
            assert isinstance(pixelbuffer, int)
            offset = self.pixel_x_size * float(pixelbuffer)
            left -= offset
            bottom -= offset
            right += offset
            top += offset
        if right > self.tile_pyramid.right:
            right = self.tile_pyramid.right
        if bottom < self.tile_pyramid.bottom:
            bottom = self.tile_pyramid.bottom
        return (left, bottom, right, top)

    def bbox(self, pixelbuffer=0):
        """
        Tile bounding box with optional pixelbuffer.
        """
        left, bottom, right, top = self.bounds(pixelbuffer=pixelbuffer)
        ul = left, top
        ur = right, top
        lr = right, bottom
        ll = left, bottom
        return Polygon([ul, ur, lr, ll])

    def affine(self, pixelbuffer=0):
        """
        Returns an Affine object of tile.
        """
        left = self.bounds(pixelbuffer=pixelbuffer)[0]
        top = self.bounds(pixelbuffer=pixelbuffer)[3]
        px_size = self.pixel_x_size
        tile_affine = Affine.from_gdal(left, px_size, 0.0, top, 0.0, -px_size)
        return tile_affine

    def shape(self, pixelbuffer=0):
        """
        Returns a tuple of tile width and height
        """
        return (self.width + 2 * pixelbuffer, self.height + 2 * pixelbuffer)

    def is_valid(self):
        """
        Returns True if tile is available in tile pyramid.
        """
        try:
            assert isinstance(self.zoom, int)
            assert self.zoom >= 0
            assert isinstance(self.row, int)
            assert self.row >= 0
            assert isinstance(self.col, int)
            assert self.col >= 0
            assert self.col <= self.tile_pyramid.matrix_width(self.zoom)
            assert self.row <= self.tile_pyramid.matrix_height(self.zoom)
        except AssertionError:
            return False
        else:
            return True

    def get_neighbors(self, count=8):
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
        zoom, row, col = self.zoom, self.row, self.col
        neighbors = []
        # fill up set with up to 8 direct neighbors
        for newtile in [
            self.tile_pyramid.tile(zoom, row-1, col),
            self.tile_pyramid.tile(zoom, row, col+1),
            self.tile_pyramid.tile(zoom, row+1, col),
            self.tile_pyramid.tile(zoom, row, col-1),
            self.tile_pyramid.tile(zoom, row-1, col+1),
            self.tile_pyramid.tile(zoom, row+1, col+1),
            self.tile_pyramid.tile(zoom, row+1, col-1),
            self.tile_pyramid.tile(zoom, row-1, col-1)
            ]:
            # top
            if newtile.is_valid:
                neighbors.append(newtile)
            if len(neighbors) >= count:
                return neighbors



class TilePyramid(object):

    def __init__(self, projection, tile_size=256):
        """
        Initialize TilePyramid.
        """
        projections = ("geodetic", "mercator")
        try:
            assert projection in projections
        except:
            raise ValueError("WMTS tileset '%s' not found. Use one of %s" %(
                projection,
                projections)
                )
        self.type = projection
        self.tile_size = tile_size
        if projection == "geodetic":
            # spatial extent
            self.left = float(-180)
            self.top = float(90)
            self.right = float(180)
            self.bottom = float(-90)
            # size in map units
            self.x_size = float(round(self.right - self.left, ROUND))
            self.y_size = float(round(self.top - self.bottom, ROUND))
            # SRS
            self.crs = {'init': u'epsg:4326'}
            self.srid = 4326
        if projection == "mercator":
            # spatial extent
            self.left = float(-20037508.3427892)
            self.top = float(20037508.3427892)
            self.right = float(20037508.3427892)
            self.bottom = float(-20037508.3427892)
            # size in map units
            self.x_size = float(round(self.right - self.left, ROUND))
            self.y_size = float(round(self.top - self.bottom, ROUND))
            # SRS
            self.crs = {'init': u'epsg:3857'}
            self.srid = 3857

    def tile(self, zoom, row, col):
        """
        Returns Tile object.
        """
        return Tile(self, zoom, row, col)

    def matrix_width(self, zoom):
        """
        Tile matrix width (number of columns) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        if self.type == "geodetic":
            return 2**(zoom+1)
        if self.type == "mercator":
            return 2**(zoom)

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        if self.type == "geodetic":
            return 2**(zoom+1)/2
        if self.type == "mercator":
            return 2**(zoom)

    def tile_x_size(self, zoom):
        """
        Width of a tile in SRID units at zoom level.
        """
        matrix_width = self.matrix_width(zoom)
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        tile_x_size = float(round(self.x_size/matrix_width, ROUND))
        return tile_x_size

    def tile_y_size(self, zoom):
        """
        Height of a tile in SRID units at zoom level.
        """
        matrix_height = self.matrix_height(zoom)
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        tile_y_size = float(round(self.y_size/matrix_height, ROUND))
        return tile_y_size

    def pixel_x_size(self, zoom):
        """
        Size of a pixel in SRID units at zoom level.
        """
        pixel_x_size = float(round(
            self.tile_x_size(zoom) / self.tile_size,
            ROUND))
        return pixel_x_size

    def pixel_y_size(self, zoom):
        """
        Size of a pixel in SRID units at zoom level.
        """
        pixel_y_size = float(round(
            self.tile_y_size(zoom) / self.tile_size,
            ROUND))
        return pixel_y_size

    def tiles_from_bbox(self, geometry, zoom):
        """
        All metatiles intersecting with given bounding box.
        """
        return tiles_from_bbox(self, geometry, zoom)

    def tiles_from_geom(self, geometry, zoom):
        """
        All metatiles intersecting with input geometry.
        """
        return tiles_from_geom(self, geometry, zoom)


class MetaTilePyramid(TilePyramid):

    def __init__(self, tilepyramid, metatiles=1):
        """
        Initialize MetaTilePyramid using a TilePyramid.
        """
        assert isinstance(tilepyramid, TilePyramid)
        assert isinstance(metatiles, int)
        assert metatiles in (1, 2, 4, 8, 16)
        self.tilepyramid = tilepyramid
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
        self.srid = tilepyramid.srid

    def tile(self, zoom, row, col):
        """
        Returns Tile object of underlying tile_pyramid.
        """
        return Tile(self, zoom, row, col)

    def matrix_width(self, zoom):
        """
        Metatile matrix width (number of columns) at zoom level.
        """
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
            raise ValueError("Zoom (%s) must be an integer." %(zoom))
        tile_y_size = self.tilepyramid.tile_y_size(zoom)
        metatile_y_size = tile_y_size * float(self.metatiles)
        if metatile_y_size > self.y_size:
            metatile_y_size = self.y_size
        return metatile_y_size

    def pixel_x_size(self, zoom):
        """
        Size of a pixel in SRID units at zoom level.
        """
        pixel_x_size = float(round(
            self.metatile_x_size(zoom) / self.metatile_width(zoom),
            ROUND))
        return pixel_x_size

    def pixel_y_size(self, zoom):
        """
        Size of a pixel in SRID units at zoom level.
        """
        pixel_y_size = float(round(
            self.metatile_y_size(zoom) / self.metatile_height(zoom),
            ROUND))
        return pixel_y_size

    def tiles_from_bbox(self, geometry, zoom):
        """
        All metatiles intersecting with given bounding box.
        """
        return tiles_from_bbox(self, geometry, zoom)

    def tiles_from_geom(self, geometry, zoom):
        """
        All metatiles intersecting with input geometry.
        """
        return tiles_from_geom(self, geometry, zoom)

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


def tiles_from_bbox(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with given bounding box.
    """
    try:
        assert isinstance(zoom, int)
    except:
        raise ValueError("Zoom (%s) must be an integer." %(zoom))
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
    for tile_id in product([zoom], rows, cols):
        tile = tilepyramid.tile(*tile_id)
        if tile.is_valid():
            yield tile


def tiles_from_geom(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with input geometry.
    """

    try:
        assert geometry.is_valid
    except AssertionError:
        print "WARNING: geometry seems not to be valid"
        try:
            clean = geometry.buffer(0.0)
            assert clean.is_valid
            assert clean.area > 0
            geometry = clean
            print "... cleaning successful"
        except:
            print explain_validity(geometry)
            raise IOError("... geometry could not be fixed")

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
        yield tilepyramid.tile(zoom, row, col)

    elif geometry.geom_type in ("LineString", "MultiLineString", "Polygon",
        "MultiPolygon", "MultiPoint"):
        prepared_geometry = prep(geometry)
        for tile in tilepyramid.tiles_from_bbox(geometry, zoom):
            if prepared_geometry.intersects(tile.bbox()):
                yield tile
    elif geometry.is_empty:
        pass
    else:
        raise ValueError("ERROR: no valid geometry")
