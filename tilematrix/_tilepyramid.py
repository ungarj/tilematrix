"""Handling tile pyramids."""

from shapely.prepared import prep
import math

from . import _funcs
from ._conf import ROUND
from ._tile import Tile
from ._funcs import validate_zoom


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

    def __init__(self, grid_definition, tile_size=256, metatiling=1):
        """Initialize TilePyramid."""
        # get source grid parameters
        self.grid = _funcs.GridDefinition(
            grid_definition, tile_size=tile_size, metatiling=metatiling
        )
        self.type = self.grid.type
        self.bounds = self.grid.bounds
        self.left, self.bottom, self.right, self.top = self.bounds
        self.crs = self.grid.crs
        self.srid = self.grid.srid
        self.is_global = self.grid.is_global
        self.metatiling = metatiling
        # size in pixels
        self.tile_size = tile_size
        self.metatile_size = tile_size * metatiling
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
        validate_zoom(zoom)
        width = int(math.ceil(
            self.grid.shape.width * 2**(zoom) / self.metatiling))
        return 1 if width < 1 else width

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        height = int(
            math.ceil(self.grid.shape.height * 2**(zoom) / self.metatiling))
        return 1 if height < 1 else height

    def tile_x_size(self, zoom):
        """
        Width of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return round(self.x_size / self.matrix_width(zoom), ROUND)

    def tile_y_size(self, zoom):
        """
        Height of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return round(self.y_size / self.matrix_height(zoom), ROUND)

    def tile_width(self, zoom):
        """
        Tile width in pixel.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        matrix_pixel = 2**(zoom) * self.tile_size * self.grid.shape.width
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def tile_height(self, zoom):
        """
        Tile height in pixel.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        matrix_pixel = 2**(zoom) * self.tile_size * self.grid.shape.height
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def pixel_x_size(self, zoom):
        """
        Width of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return float(
            round(self.tile_x_size(zoom)/self.tile_width(zoom), ROUND))

    def pixel_y_size(self, zoom):
        """
        Height of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return float(
            round(self.tile_y_size(zoom)/self.tile_height(zoom), ROUND))

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
        validate_zoom(zoom)
        if not isinstance(bounds, tuple) or len(bounds) != 4:
            raise ValueError(
                "bounds must be a tuple of left, bottom, right, top values")
        if not isinstance(bounds, _funcs.Bounds):
            bounds = _funcs.Bounds(*bounds)
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
        validate_zoom(zoom)
        return self.tiles_from_bounds(geometry.bounds, zoom)

    def tiles_from_geom(self, geometry, zoom):
        """
        Return all tiles intersecting with input geometry.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        validate_zoom(zoom)
        if geometry.is_empty:
            raise StopIteration()
        if geometry.geom_type == "Point":
            yield self.tile_from_xy(geometry.x, geometry.y, zoom)
        elif geometry.geom_type == "MultiPoint":
            for point in geometry:
                yield self.tile_from_xy(point.x, point.y, zoom)
        elif geometry.geom_type in (
            "LineString", "MultiLineString", "Polygon", "MultiPolygon",
            "GeometryCollection"
        ):
            prepared_geometry = prep(
                _funcs.clip_geometry_to_srs_bounds(geometry, self))
            for tile in self.tiles_from_bbox(geometry, zoom):
                if prepared_geometry.intersects(tile.bbox()):
                    yield tile
        else:
            raise ValueError("no valid geometry: %s" % geometry.type)

    def tile_from_xy(self, x, y, zoom, on_edge_use="rb"):
        """
        Return tile covering a point defined by x and y values.

        - x: x coordinate
        - y: y coordinate
        - zoom: zoom level
        - on_edge_use: determine which Tile to pick if Point hits a grid edge
            - rb: right bottom (default)
            - rt: right top
            - lt: left top
            - lb: left bottom
        """
        validate_zoom(zoom)
        if x < self.left or x > self.right or y < self.bottom or y > self.top:
            raise ValueError("x or y are outside of grid bounds")
        if on_edge_use not in ["lb", "rb", "rt", "lt"]:
            raise ValueError("on_edge_use must be one of lb, rb, rt or lt")
        return _funcs._tile_from_xy(self, x, y, zoom, on_edge_use=on_edge_use)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.grid == other.grid and
            self.tile_size == other.tile_size and
            self.metatiling == other.metatiling
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'TilePyramid(%s, tile_size=%s, metatiling=%s)' % (
            self.type, self.tile_size, self.metatiling
        )

    def __hash__(self):
        return hash(repr(self) + repr(self.grid))
