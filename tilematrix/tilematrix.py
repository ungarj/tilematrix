#!/usr/bin/env python

from shapely.geometry import Polygon, GeometryCollection, box
from shapely.validation import explain_validity
from shapely.prepared import prep
from shapely.affinity import translate
from itertools import product, chain
import math
from affine import Affine
from rasterio.crs import CRS

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
            # SRS
            self.is_global = True
            self.srid = 4326
            self.crs = CRS().from_epsg(self.srid)
        if projection == "mercator":
            # spatial extent
            self.left = float(-20037508.3427892)
            self.top = float(20037508.3427892)
            self.right = float(20037508.3427892)
            self.bottom = float(-20037508.3427892)
            # SRS
            self.is_global = True
            self.srid = 3857
            self.crs = CRS().from_epsg(self.srid)
        # size in map units
        self.x_size = float(round(self.right - self.left, ROUND))
        self.y_size = float(round(self.top - self.bottom, ROUND))

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

    def tiles_from_bounds(self, bounds, zoom):
        """
        All metatiles intersecting with given bounds.
        """
        return tiles_from_bounds(self, bounds, zoom)

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
        self.width = self._get_tile_width()
        self.height = self._get_tile_height()
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
        if top > self.tile_pyramid.top:
            top = self.tile_pyramid.top
        if bottom < self.tile_pyramid.bottom:
            bottom = self.tile_pyramid.bottom
        return (left, bottom, right, top)

    def bbox(self, pixelbuffer=0):
        """
        Tile bounding box with optional pixelbuffer.
        """
        return box(*self.bounds(pixelbuffer=pixelbuffer))

    def affine(self, pixelbuffer=0):
        """
        Returns an Affine object of tile.
        """
        left = self.bounds(pixelbuffer=pixelbuffer)[0]
        top = self.bounds(pixelbuffer=pixelbuffer)[3]
        return Affine.translation(
            left,
            top
            ) * Affine.scale(
            self.pixel_x_size,
            -self.pixel_y_size
            )

    def shape(self, pixelbuffer=0):
        """
        Returns a tuple of tile height and width.
        """
        height = self.height + 2 * pixelbuffer
        width = self.width + 2 * pixelbuffer
        if pixelbuffer:
            matrix_height = self.tile_pyramid.matrix_height(self.zoom)
            if self.row in [0, matrix_height-1]:
                height = self.height+pixelbuffer
            if matrix_height == 1:
                height = self.height
        return (height, width)

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
            assert self.col < self.tile_pyramid.matrix_width(self.zoom)
            assert self.row < self.tile_pyramid.matrix_height(self.zoom)
        except AssertionError:
            return False
        else:
            return True

    def get_neighbors(self, connectedness=8, count=None):
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
        try:
            assert connectedness in [4, 8]
        except AssertionError:
            raise ValueError("only connectedness values 8 or 4 are allowed")
        if count:
            raise DeprecationWarning(
                "'count' parameter was replaced by 'connectedness'"
            )
        zoom, row, col = self.zoom, self.row, self.col
        neighbors = []
        # 4-connected neighbors
        for candidate in [
            self.tile_pyramid.tile(zoom, row-1, col),
            self.tile_pyramid.tile(zoom, row, col+1),
            self.tile_pyramid.tile(zoom, row+1, col),
            self.tile_pyramid.tile(zoom, row, col-1),
            ]:
            neighbor = self._clean_tile(candidate)
            if neighbor:
                neighbors.append(neighbor)
        # 8-connected neighbors
        if connectedness == 8:
            for candidate in [
                self.tile_pyramid.tile(zoom, row-1, col+1),
                self.tile_pyramid.tile(zoom, row+1, col+1),
                self.tile_pyramid.tile(zoom, row+1, col-1),
                self.tile_pyramid.tile(zoom, row-1, col-1)
            ]:
                neighbor = self._clean_tile(candidate)
                if neighbor:
                    neighbors.append(neighbor)

        return neighbors

    def _get_tile_width(self):
        """
        Calculates Tile width in pixels.
        """
        if isinstance(self.tile_pyramid, MetaTilePyramid):
            init_tile_size = self.tile_pyramid.tile_pyramid.tile_size
            matrix_width = self.tile_pyramid.tile_pyramid.matrix_width(
                self.zoom
                )
            matrix_pixel_width = (
                matrix_width*init_tile_size
                )
            tile_size = init_tile_size*self.tile_pyramid.metatiles
            if tile_size > matrix_pixel_width:
                tile_size = matrix_pixel_width
            return tile_size
        else:
            return self.tile_pyramid.tile_size

    def _get_tile_height(self):
        """
        Calculates Tile height in pixels.
        """
        if isinstance(self.tile_pyramid, MetaTilePyramid):
            init_tile_size = self.tile_pyramid.tile_pyramid.tile_size
            matrix_height = self.tile_pyramid.tile_pyramid.matrix_height(
                self.zoom
                )
            matrix_pixel_height = (
                matrix_height*init_tile_size
                )
            tile_size = init_tile_size*self.tile_pyramid.metatiles
            if tile_size > matrix_pixel_height:
                tile_size = matrix_pixel_height
            return tile_size
        else:
            return self.tile_pyramid.tile_size

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

    def _clean_tile(self, tile):
        """
        Returns valid neighbor by wrapping around the antimeridian if necessary
        or None if tile could not be cleaned.
        """
        zoom, row, col = tile.id
        # return None if tile is above or below tile matrix
        if row >= 0 and row < self.tile_pyramid.matrix_height(zoom):
            # fix if on eastern side of antimeridian
            if col < 0:
                col += self.tile_pyramid.matrix_width(zoom)
            # fix if on western side of antimeridian
            if col >= self.tile_pyramid.matrix_width(zoom):
                col -= self.tile_pyramid.matrix_width(zoom)
            out_tile = self.tile_pyramid.tile(zoom, row, col)
            # final validity check
            if out_tile.is_valid():
                return out_tile
            else:
                return None
        else:
            return None


class MetaTilePyramid(TilePyramid):

    def __init__(self, tilepyramid, metatiles=1):
        """
        Initialize MetaTilePyramid using a TilePyramid.
        """
        assert isinstance(tilepyramid, TilePyramid)
        assert isinstance(metatiles, int)
        assert metatiles in (1, 2, 4, 8, 16)
        self.tilepyramid = tilepyramid
        self.tile_pyramid = tilepyramid
        self.metatiles = metatiles
        self.tile_size = tilepyramid.tile_size*metatiles
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
        self.is_global = tilepyramid.is_global

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

    def tiles_from_bounds(self, bounds, zoom):
        """
        All metatiles intersecting with given bounds.
        """
        return tiles_from_bounds(self, bounds, zoom)

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

def tiles_from_bounds(tilepyramid, bounds, zoom):
    """
    All tiles intersecting with given bounds. Bounds values will be cleaned if
    they cross the antimeridian or are outside of the Northern or Southern
    tile pyramid bounds.
    """
    try:
        assert isinstance(bounds, tuple)
        left, bottom, right, top = bounds
    except:
        raise ValueError(
            "bounds must be a tuple of left, bottom, right, top values"
        )
    try:
        assert isinstance(zoom, int)
    except:
        raise ValueError("Zoom (%s) must be an integer." %(zoom))

    if tilepyramid.is_global:
        seen = set()
        if top > tilepyramid.top:
            top = tilepyramid.top
        if bottom < tilepyramid.bottom:
            bottom = tilepyramid.bottom
        if left < tilepyramid.left:
            for tile in chain(
                # tiles west of antimeridian
                _tiles_from_cleaned_bounds(
                    tilepyramid,
                    (left+(2*tilepyramid.left), bottom, tilepyramid.right, top),
                    zoom
                ),
                # tiles east of antimeridian
                _tiles_from_cleaned_bounds(
                    tilepyramid,
                    (tilepyramid.left, bottom, right, top),
                    zoom
                )
            ):
                # make output tiles unique
                if tile.id not in seen:
                    seen.add(tile.id)
                    yield tile
        elif right > tilepyramid.right:
            for tile in chain(
                # tiles west of antimeridian
                _tiles_from_cleaned_bounds(
                    tilepyramid,
                    (left, bottom, tilepyramid.right, top),
                    zoom
                ),
                # tiles east of antimeridian
                _tiles_from_cleaned_bounds(
                    tilepyramid,
                    (
                        tilepyramid.left,
                        bottom,
                        right-(2*tilepyramid.right),
                        top
                    ),
                    zoom
                )
            ):
                # make output tiles unique
                if tile.id not in seen:
                    seen.add(tile.id)
                    yield tile
        else:
            for tile in _tiles_from_cleaned_bounds(tilepyramid, bounds, zoom):
                yield tile
    else:
        for tile in _tiles_from_cleaned_bounds(tilepyramid, bounds, zoom):
            yield tile


def _tiles_from_cleaned_bounds(tilepyramid, bounds, zoom):
    """
    All tiles intersecting with given bounds where bounds must not be outside
    of SRS bounds.
    """
    left, bottom, right, top = bounds
    tile_x_size = tilepyramid.tile_x_size(zoom)
    tile_y_size = tilepyramid.tile_y_size(zoom)
    tilelon = tilepyramid.left
    tilelat = tilepyramid.top
    cols = []
    rows = []
    col = -1
    row = -1
    while tilelon <= left:
        tilelon += tile_x_size
        col += 1
    cols.append(col)
    while tilelon < right:
        tilelon += tile_x_size
        col += 1
        cols.append(col)
    while tilelat >= top:
        tilelat -= tile_y_size
        row += 1
    rows.append(row)
    while tilelat > bottom:
        tilelat -= tile_y_size
        row += 1
        rows.append(row)
    for tile_id in product([zoom], rows, cols):
        tile = tilepyramid.tile(*tile_id)
        if tile.is_valid():
            yield tile

def tiles_from_bbox(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with bounding box of input geometry.
    """
    try:
        assert isinstance(zoom, int)
    except:
        raise ValueError("Zoom (%s) must be an integer." %(zoom))
    return tiles_from_bounds(tilepyramid, geometry.bounds, zoom)

def tiles_from_geom(tilepyramid, geometry, zoom):
    """
    All tiles intersecting with input geometry.
    """
    try:
        assert geometry.is_valid
    except AssertionError:
        try:
            clean = geometry.buffer(0.0)
            assert clean.is_valid
            assert clean.area > 0
            geometry = clean
        except AssertionError:
            raise IOError(
                str(
                    "invalid geometry could not be fixed: '%s'" %
                    explain_validity(geometry)
                    )
                )
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
        "MultiPolygon", "MultiPoint", "GeometryCollection"):
        prepared_geometry = prep(
            clip_geometry_to_srs_bounds(geometry, tilepyramid)
            )
        for tile in tilepyramid.tiles_from_bbox(geometry, zoom):
            if prepared_geometry.intersects(tile.bbox()):
                yield tile
    elif geometry.is_empty:
        pass
    else:
        raise ValueError("ERROR: no valid geometry: %s" % geometry.type)

def clip_geometry_to_srs_bounds(geometry, tilepyramid, multipart=False):
    """
    Clips input geometry to SRS bounds of given TilePyramid. If geometry passes
    the antimeridian, it will be split up in a multipart geometry and shifted
    to within the SRS boundaries.
    Note: geometry SRS must be the TilePyramid SRS!
    multipart: return list of geometries instead of a GeometryCollection
    """
    try:
        assert geometry.is_valid
    except AssertionError:
        raise ValueError("invalid geometry given")
    try:
        assert isinstance(tilepyramid, TilePyramid or MetaTilePyramid)
    except AssertionError:
        raise ValueError("not a TilePyramid object")
    tilepyramid_bbox = box(
        tilepyramid.left,
        tilepyramid.bottom,
        tilepyramid.right,
        tilepyramid.top
    )
    if tilepyramid.is_global and not geometry.within(tilepyramid_bbox):
        inside_geom = geometry.intersection(tilepyramid_bbox)
        outside_geom = geometry.difference(tilepyramid_bbox)
        # shift outside geometry so it lies within SRS bounds
        if isinstance(outside_geom, Polygon):
            outside_geom = [outside_geom]
        all_geoms = [inside_geom]
        for geom in outside_geom:
            geom_left = geom.bounds[0]
            geom_right = geom.bounds[2]
            if geom_left < tilepyramid.left:
                geom = translate(geom, xoff=2*tilepyramid.right)
            elif geom_right > tilepyramid.right:
                geom = translate(geom, xoff=-2*tilepyramid.right)
            all_geoms.append(geom)
        if multipart:
            return all_geoms
        else:
            return GeometryCollection(all_geoms)
    else:
        if multipart:
            return [geometry]
        else:
            return geometry
