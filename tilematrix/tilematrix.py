"""Handling tile pyramids."""

from shapely.geometry import Polygon, GeometryCollection, box
from shapely.validation import explain_validity
from shapely.prepared import prep
from shapely.affinity import translate
from itertools import product, chain
import math
from affine import Affine
from rasterio.crs import CRS
import warnings

ROUND = 20
PYRAMID_PARAMS = {
    "geodetic": {
        "shape": (2, 1),  # tile columns and rows at zoom level 0
        "bounds": (-180., 90., 180., -90.),  # pyramid bounds
        "is_global": True,  # if false, no antimeridian handling
        "epsg": 4326  # EPSG code
        },
    "mercator": {
        "shape": (1, 1),
        "bounds": (
            -20037508.3427892, 20037508.3427892, 20037508.3427892,
            -20037508.3427892),
        "is_global": True,
        "epsg": 3857
        }
    }


class TilePyramid(object):
    """
    A Tile pyramid is a collection of tile matrices for different zoom levels.

    TilePyramids can be defined either for the Web Mercator or the geodetic
    projection. A TilePyramid holds tiles for different discrete zoom levels.
    Each zoom level is a 2D tile matrix, thus every Tile can be defined by
    providing the zoom level as well as the row and column of the tile matrix.

    - projection: one of "geodetic" or "mercator"
    - tile_size: target pixel size of each tile
    - metatiling: tile size mulipilcation factor, must be one of 1, 2, 4, 8 or
        16.
    """

    def __init__(self, projection, tile_size=256, metatiling=1):
        """Initialize TilePyramid."""
        projections = ("geodetic", "mercator")
        try:
            assert projection in projections
        except AssertionError:
            raise ValueError("WMTS tileset '%s' not found. Use one of %s" % (
                projection, projections))
        try:
            assert metatiling in (1, 2, 4, 8, 16)
        except AssertionError:
            raise ValueError("metatling must be one of 1, 2, 4, 8, 16")
        self.metatiling = metatiling
        self.tile_size = tile_size
        self.metatile_size = tile_size*metatiling
        self.type = projection
        self._shape = PYRAMID_PARAMS[projection]["shape"]
        self.left, self.top, self.right, self.bottom = PYRAMID_PARAMS[
            projection]["bounds"]
        self.is_global = PYRAMID_PARAMS[projection]["is_global"]
        self.srid = PYRAMID_PARAMS[projection]["epsg"]
        self.crs = CRS().from_epsg(self.srid)
        # size in map units
        self.x_size = float(round(self.right - self.left, ROUND))
        self.y_size = float(round(self.top - self.bottom, ROUND))

    def tile(self, zoom, row, col):
        """
        Return Tile object of this TilePyramid.

        - zoom: zoom level
        - row: tile matrix row
        - col: tile matrix column
        """
        return Tile(self, zoom, row, col)

    def matrix_width(self, zoom):
        """
        Tile matrix width (number of columns) at zoom level.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        width = int(math.ceil(self._shape[0]*2**(zoom)/self.metatiling))
        return 1 if width < 1 else width

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        height = int(math.ceil(self._shape[1]*2**(zoom)/self.metatiling))
        return 1 if height < 1 else height

    def tile_x_size(self, zoom):
        """
        Width of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        return round(self.x_size/self.matrix_width(zoom), ROUND)

    def tile_y_size(self, zoom):
        """
        Height of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        return round(self.y_size/self.matrix_height(zoom), ROUND)

    def tile_width(self, zoom):
        """
        Tile width in pixel.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        matrix_pixel = 2**(zoom)*self.tile_size*self._shape[0]
        tile_pixel = self.tile_size*self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def tile_height(self, zoom):
        """
        Tile height in pixel.

        - zoom: zoom level
        """
        self._check_zoom(zoom)
        matrix_pixel = 2**(zoom)*self.tile_size*self._shape[1]
        tile_pixel = self.tile_size*self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def pixel_x_size(self, zoom):
        """
        Width of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        return float(
            round(self.tile_x_size(zoom)/self.tile_width(zoom), ROUND))

    def pixel_y_size(self, zoom):
        """
        Height of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        return float(
            round(self.tile_y_size(zoom)/self.tile_height(zoom), ROUND))

    def intersecting(self, tile):
        """
        Return all tiles intersecting with tile.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tile: a Tile object
        """
        return _tile_intersecting_tilepyramid(tile, self)

    def tiles_from_bounds(self, bounds, zoom):
        """
        Return all tiles intersecting with bounds.

        Bounds values will be cleaned if they cross the antimeridian or are
        outside of the Northern or Southern tile pyramid bounds.

        - bounds: tuple of (left, bottom, right, top) bounding values in tile
            pyramid CRS
        - zoom: zoom level
        """
        try:
            assert isinstance(bounds, tuple)
            left, bottom, right, top = bounds
        except:
            raise ValueError(
                "bounds must be a tuple of left, bottom, right, top values"
            )
        self._check_zoom(zoom)

        if self.is_global:
            seen = set()
            if top > self.top:
                top = self.top
            if bottom < self.bottom:
                bottom = self.bottom
            if left < self.left:
                for tile in chain(
                    # tiles west of antimeridian
                    _tiles_from_cleaned_bounds(
                        self, (left+(2*self.left), bottom, self.right, top),
                        zoom
                    ),
                    # tiles east of antimeridian
                    _tiles_from_cleaned_bounds(
                        self, (self.left, bottom, right, top), zoom)
                ):
                    # make output tiles unique
                    if tile.id not in seen:
                        seen.add(tile.id)
                        yield tile
            elif right > self.right:
                for tile in chain(
                    # tiles west of antimeridian
                    _tiles_from_cleaned_bounds(
                        self, (left, bottom, self.right, top), zoom),
                    # tiles east of antimeridian
                    _tiles_from_cleaned_bounds(
                        self, (self.left, bottom, right-(2*self.right), top),
                        zoom)
                ):
                    # make output tiles unique
                    if tile.id not in seen:
                        seen.add(tile.id)
                        yield tile
            else:
                for tile in _tiles_from_cleaned_bounds(self, bounds, zoom):
                    yield tile
        else:
            for tile in _tiles_from_cleaned_bounds(self, bounds, zoom):
                yield tile

    def tiles_from_bbox(self, geometry, zoom):
        """
        All metatiles intersecting with given bounding box.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        self._check_zoom(zoom)
        return self.tiles_from_bounds(geometry.bounds, zoom)

    def tiles_from_geom(self, geometry, zoom):
        """
        Return all tiles intersecting with input geometry.

        - geometry: shapely geometry
        - zoom: zoom level
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
            for tile in self.tiles_from_bbox(geometry, zoom):
                yield tile
        elif geometry.geom_type == "Point":
            lon, lat = list(geometry.coords)[0]
            tilelon = self.left
            tilelat = self.top
            tile_x_size = self.tile_x_size(zoom)
            tile_y_size = self.tile_y_size(zoom)
            col = -1
            row = -1
            while tilelon < lon:
                tilelon += tile_x_size
                col += 1
            while tilelat > lat:
                tilelat -= tile_y_size
                row += 1
            yield self.tile(zoom, row, col)
        elif geometry.geom_type in (
            "LineString", "MultiLineString", "Polygon", "MultiPolygon",
            "MultiPoint", "GeometryCollection"
        ):
            prepared_geometry = prep(
                clip_geometry_to_srs_bounds(geometry, self)
                )
            for tile in self.tiles_from_bbox(geometry, zoom):
                if prepared_geometry.intersects(tile.bbox()):
                    yield tile
        elif geometry.is_empty:
            pass
        else:
            raise ValueError("ERROR: no valid geometry: %s" % geometry.type)

    def _check_zoom(self, zoom):
        try:
            assert isinstance(zoom, int)
        except:
            raise ValueError("Zoom (%s) must be an integer." % (zoom))


class Tile(object):
    """
    A Tile is a square somewhere on Earth.

    Each Tile can be identified with the zoom, row, column index in a
    TilePyramid.

    Some tile functions can accept a tile buffer in pixels (pixelbuffer). A
    pixelbuffer value of e.g. 1 will extend the tile boundaries by 1 pixel.
    """

    def __init__(self, tile_pyramid, zoom, row, col):
        """Initialize Tile."""
        try:
            for p in (zoom, row, col):
                assert isinstance(p, int)
        except:
            raise ValueError("Tile index (%s %s %s) must be integers." % (
                zoom, row, col))
        self.tile_pyramid = tile_pyramid
        self.crs = tile_pyramid.crs
        self.zoom = zoom
        self.row = row
        self.col = col
        try:
            assert self.is_valid()
        except AssertionError:
            raise ValueError("invalid tile index given: %s %s %s" % (
                zoom, row, col))
        self.index = (zoom, row, col)
        self.id = (zoom, row, col)
        self.pixel_x_size = self.tile_pyramid.pixel_x_size(self.zoom)
        self.pixel_y_size = self.tile_pyramid.pixel_y_size(self.zoom)
        self.left = float(round(
            self.tile_pyramid.left+((self.col)*self.x_size),
            ROUND))
        self.top = float(round(
            self.tile_pyramid.top-((self.row)*self.y_size),
            ROUND))
        self.right = self.left + self.x_size
        self.bottom = self.top - self.y_size
        self.srid = tile_pyramid.srid

    @property
    def width(self):
        """Calculate Tile width in pixels."""
        return self.tile_pyramid.tile_width(self.zoom)

    @property
    def height(self):
        """Calculate Tile height in pixels."""
        return self.tile_pyramid.tile_height(self.zoom)

    @property
    def x_size(self):
        """Width of tile in SRID units at zoom level."""
        return self.tile_pyramid.tile_x_size(self.zoom)

    @property
    def y_size(self):
        """Height of tile in SRID units at zoom level."""
        return self.tile_pyramid.tile_y_size(self.zoom)

    def bounds(self, pixelbuffer=0):
        """
        Return Tile boundaries.

        - pixelbuffer: tile buffer in pixels
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
        Return Tile bounding box.

        - pixelbuffer: tile buffer in pixels
        """
        return box(*self.bounds(pixelbuffer=pixelbuffer))

    def affine(self, pixelbuffer=0):
        """
        Return an Affine object of tile.

        - pixelbuffer: tile buffer in pixels
        """
        left = self.bounds(pixelbuffer=pixelbuffer)[0]
        top = self.bounds(pixelbuffer=pixelbuffer)[3]
        return Affine.translation(left, top) * Affine.scale(
            self.pixel_x_size, -self.pixel_y_size)

    def shape(self, pixelbuffer=0):
        """
        Return a tuple of tile height and width.

        - pixelbuffer: tile buffer in pixels
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
        """Return True if tile is available in tile pyramid."""
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

    def get_parent(self):
        """Return tile from previous zoom level."""
        if self.zoom == 0:
            return None
        else:
            return self.tile_pyramid.tile(
                self.zoom-1, int(self.row/2), int(self.col/2))

    def get_children(self):
        """Return tiles from next zoom level."""
        return [
            self.tile_pyramid.tile(self.zoom+1, self.row*2, self.col*2),
            self.tile_pyramid.tile(self.zoom+1, self.row*2+1, self.col*2),
            self.tile_pyramid.tile(self.zoom+1, self.row*2, self.col*2+1),
            self.tile_pyramid.tile(self.zoom+1, self.row*2+1, self.col*2+1)
        ]

    def get_neighbors(self, connectedness=8, count=None):
        """
        Return tile neighbors.

        -------------
        | 8 | 1 | 5 |
        -------------
        | 4 | x | 2 |
        -------------
        | 7 | 3 | 6 |
        -------------

        - connectedness: [4 or 8] return four direct neighbors or all eight.
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

    def intersecting(self, tilepyramid):
        """
        Return all tiles intersecting with tilepyramid.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tilepyramid: a TilePyramid object
        """
        return _tile_intersecting_tilepyramid(self, tilepyramid)

    def _clean_tile(self, tile):
        """
        Return valid neighbor over tile matrix bounds.

        By wrapping around the antimeridian if necessary or None if tile could
        not be cleaned.
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
    """
    Do not use, it's deprecated.

    Use a TilePyramid with metatiling setting instead.
    """

    def __init__(self, tilepyramid, metatiles=1):
        """Initialize MetaTilePyramid using a TilePyramid."""
        warnings.warn(
            "use TilePyraid(metatiling=...) instead of MetaTilePyramid")
        assert isinstance(tilepyramid, TilePyramid)
        assert isinstance(metatiles, int)
        assert metatiles in (1, 2, 4, 8, 16)
        TilePyramid.__init__(self, tilepyramid.type, metatiling=metatiles)
        self.tilepyramid = tilepyramid
        self.tile_pyramid = tilepyramid
        self.metatiles = metatiles
        self.metatiling = metatiles
        self.metatile_x_size = self.tile_x_size
        self.metatile_y_size = self.tile_y_size


"""Helper functions."""


def clip_geometry_to_srs_bounds(geometry, pyramid, multipart=False):
    """
    Clip input geometry to SRS bounds of given TilePyramid.

    If geometry passes the antimeridian, it will be split up in a multipart
    geometry and shifted to within the SRS boundaries.
    Note: geometry SRS must be the TilePyramid SRS!

    - geometry: any shapely geometry
    - pyramid: a TilePyramid object
    - multipart: return list of geometries instead of a GeometryCollection
    """
    try:
        assert geometry.is_valid
    except AssertionError:
        raise ValueError("invalid geometry given")
    try:
        assert isinstance(pyramid, TilePyramid or MetaTilePyramid)
    except AssertionError:
        raise ValueError("not a TilePyramid object")
    pyramid_bbox = box(
        pyramid.left, pyramid.bottom, pyramid.right, pyramid.top)

    # Special case for global tile pyramids if geometry extends over tile
    # pyramid boundaries (such as the antimeridian).
    if pyramid.is_global and not geometry.within(pyramid_bbox):
        inside_geom = geometry.intersection(pyramid_bbox)
        outside_geom = geometry.difference(pyramid_bbox)
        # shift outside geometry so it lies within SRS bounds
        if isinstance(outside_geom, Polygon):
            outside_geom = [outside_geom]
        all_geoms = [inside_geom]
        for geom in outside_geom:
            geom_left = geom.bounds[0]
            geom_right = geom.bounds[2]
            if geom_left < pyramid.left:
                geom = translate(geom, xoff=2*pyramid.right)
            elif geom_right > pyramid.right:
                geom = translate(geom, xoff=-2*pyramid.right)
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


def _tile_intersecting_tilepyramid(tile, tilepyramid):
    """Return all tiles from tilepyramid intersecting with tile."""
    assert isinstance(tile, Tile)
    assert isinstance(tilepyramid, TilePyramid)
    assert tile.crs == tilepyramid.crs
    tile_metatiling = tile.tile_pyramid.metatiling
    pyramid_metatiling = tilepyramid.metatiling
    zoom, row, col = tile.id
    multiplier = float(tile_metatiling)/float(pyramid_metatiling)
    if tile_metatiling == pyramid_metatiling:
        return [tilepyramid.tile(*tile.id)]
    elif tile_metatiling > pyramid_metatiling:
        return [
            tilepyramid.tile(
                zoom,
                int(multiplier*row+row_offset),
                int(multiplier*col+col_offset)
            )
            for row_offset, col_offset in product(
                range(int(multiplier)), range(int(multiplier)))
        ]
    elif tile_metatiling < pyramid_metatiling:
        return [tilepyramid.tile(
            zoom,
            int(multiplier*row),
            int(multiplier*col)
        )]

def _tiles_from_cleaned_bounds(tilepyramid, bounds, zoom):
    """Return all tiles intersecting with bounds."""
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
        try:
            yield tilepyramid.tile(*tile_id)
        except ValueError:
            pass
