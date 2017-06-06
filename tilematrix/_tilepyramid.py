"""Handling tile pyramids."""

from shapely.prepared import prep
import math
from rasterio.crs import CRS

from . import _conf, _funcs
from _tile import Tile


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
        if projection not in _conf.PYRAMID_PARAMS:
            raise ValueError(
                "WMTS tileset '%s' not found. Use one of %s" % (
                    projection, _conf.PYRAMID_PARAMS.keys()
                )
            )
        try:
            assert metatiling in (1, 2, 4, 8, 16)
        except AssertionError:
            raise ValueError("metatling must be one of 1, 2, 4, 8, 16")
        self.metatiling = metatiling
        self.tile_size = tile_size
        self.metatile_size = tile_size * metatiling
        self.type = projection
        self._shape = _conf.PYRAMID_PARAMS[projection]["shape"]
        self.left, self.top, self.right, self.bottom = _conf.PYRAMID_PARAMS[
            projection]["bounds"]
        self.is_global = _conf.PYRAMID_PARAMS[projection]["is_global"]
        self.srid = _conf.PYRAMID_PARAMS[projection]["epsg"]
        self.crs = CRS().from_epsg(self.srid)
        # size in map units
        self.x_size = float(round(self.right - self.left, _conf.ROUND))
        self.y_size = float(round(self.top - self.bottom, _conf.ROUND))

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
        width = int(math.ceil(self._shape[0] * 2**(zoom) / self.metatiling))
        return 1 if width < 1 else width

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.

        - zoom: zoom level
        """
        height = int(math.ceil(self._shape[1] * 2**(zoom) / self.metatiling))
        return 1 if height < 1 else height

    def tile_x_size(self, zoom):
        """
        Width of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        return round(self.x_size / self.matrix_width(zoom), _conf.ROUND)

    def tile_y_size(self, zoom):
        """
        Height of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        return round(self.y_size / self.matrix_height(zoom), _conf.ROUND)

    def tile_width(self, zoom):
        """
        Tile width in pixel.

        - zoom: zoom level
        """
        matrix_pixel = 2**(zoom) * self.tile_size * self._shape[0]
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def tile_height(self, zoom):
        """
        Tile height in pixel.

        - zoom: zoom level
        """
        matrix_pixel = 2**(zoom) * self.tile_size * self._shape[1]
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def pixel_x_size(self, zoom):
        """
        Width of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        return float(
            round(self.tile_x_size(zoom)/self.tile_width(zoom), _conf.ROUND))

    def pixel_y_size(self, zoom):
        """
        Height of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        return float(
            round(self.tile_y_size(zoom)/self.tile_height(zoom), _conf.ROUND))

    def intersecting(self, tile):
        """
        Return all tiles intersecting with tile.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tile: a Tile object
        """
        return _funcs._tile_intersecting_tilepyramid(tile, self)

    def tiles_from_bounds(self, bounds, zoom):
        """
        Return all tiles intersecting with bounds.

        Bounds values will be cleaned if they cross the antimeridian or are
        outside of the Northern or Southern tile pyramid bounds.

        - bounds: tuple of (left, bottom, right, top) bounding values in tile
            pyramid CRS
        - zoom: zoom level
        """
        if not isinstance(bounds, tuple) or len(bounds) != 4:
            raise ValueError(
                "bounds must be a tuple of left, bottom, right, top values"
            )
        if self.is_global:
            for tile in _funcs._global_tiles_from_bounds(self, bounds, zoom):
                yield tile
        else:
            for tile in _funcs._tiles_from_cleaned_bounds(self, bounds, zoom):
                yield tile

    def tiles_from_bbox(self, geometry, zoom):
        """
        All metatiles intersecting with given bounding box.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        return self.tiles_from_bounds(geometry.bounds, zoom)

    def tiles_from_geom(self, geometry, zoom):
        """
        Return all tiles intersecting with input geometry.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        if geometry.is_empty:
            raise StopIteration()
        if geometry.geom_type == "Point":
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
                _funcs.clip_geometry_to_srs_bounds(geometry, self)
            )
            for tile in self.tiles_from_bbox(geometry, zoom):
                if prepared_geometry.intersects(tile.bbox()):
                    yield tile
        else:
            raise ValueError("no valid geometry: %s" % geometry.type)
