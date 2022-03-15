"""Handling tile pyramids."""

from shapely.prepared import prep
import math
import warnings

from ._conf import ROUND
from ._grid import GridDefinition
from ._tile import Tile
from ._funcs import (
    validate_zoom,
    clip_geometry_to_srs_bounds,
    _tile_intersecting_tilepyramid,
    _global_tiles_from_bounds,
    _tiles_from_cleaned_bounds,
    _tile_from_xy,
)
from ._types import Bounds


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

    def __init__(self, grid=None, tile_size=256, metatiling=1):
        """Initialize TilePyramid."""
        if grid is None:
            raise ValueError("grid definition required")
        _metatiling_opts = [2 ** x for x in range(10)]
        if metatiling not in _metatiling_opts:
            raise ValueError(f"metatling must be one of {_metatiling_opts}")
        # get source grid parameters
        self.grid = GridDefinition(grid)
        self.bounds = self.grid.bounds
        self.left, self.bottom, self.right, self.top = self.bounds
        self.crs = self.grid.crs
        self.is_global = self.grid.is_global
        self.metatiling = metatiling
        # size in pixels
        self.tile_size = tile_size
        self.metatile_size = tile_size * metatiling
        # size in map units
        self.x_size = float(round(self.right - self.left, ROUND))
        self.y_size = float(round(self.top - self.bottom, ROUND))

    @property
    def type(self):
        warnings.warn(DeprecationWarning("'type' attribute is deprecated"))
        return self.grid.type

    @property
    def srid(self):
        warnings.warn(DeprecationWarning("'srid' attribute is deprecated"))
        return self.grid.srid

    def tile(self, zoom=None, row=None, col=None):
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
        width = int(math.ceil(self.grid.shape.width * 2 ** (zoom) / self.metatiling))
        return 1 if width < 1 else width

    def matrix_height(self, zoom):
        """
        Tile matrix height (number of rows) at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        height = int(math.ceil(self.grid.shape.height * 2 ** (zoom) / self.metatiling))
        return 1 if height < 1 else height

    def tile_x_size(self, zoom):
        """
        Width of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        warnings.warn(DeprecationWarning("tile_x_size is deprecated"))
        validate_zoom(zoom)
        return round(self.x_size / self.matrix_width(zoom), ROUND)

    def tile_y_size(self, zoom):
        """
        Height of a tile in SRID units at zoom level.

        - zoom: zoom level
        """
        warnings.warn(DeprecationWarning("tile_y_size is deprecated"))
        validate_zoom(zoom)
        return round(self.y_size / self.matrix_height(zoom), ROUND)

    def tile_width(self, zoom):
        """
        Tile width in pixel.

        - zoom: zoom level
        """
        warnings.warn(DeprecationWarning("tile_width is deprecated"))
        validate_zoom(zoom)
        matrix_pixel = 2 ** (zoom) * self.tile_size * self.grid.shape.width
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def tile_height(self, zoom):
        """
        Tile height in pixel.

        - zoom: zoom level
        """
        warnings.warn(DeprecationWarning("tile_height is deprecated"))
        validate_zoom(zoom)
        matrix_pixel = 2 ** (zoom) * self.tile_size * self.grid.shape.height
        tile_pixel = self.tile_size * self.metatiling
        return matrix_pixel if tile_pixel > matrix_pixel else tile_pixel

    def pixel_x_size(self, zoom):
        """
        Width of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return round(
            (self.grid.right - self.grid.left)
            / (self.grid.shape.width * 2 ** zoom * self.tile_size),
            ROUND,
        )

    def pixel_y_size(self, zoom):
        """
        Height of a pixel in SRID units at zoom level.

        - zoom: zoom level
        """
        validate_zoom(zoom)
        return round(
            (self.grid.top - self.grid.bottom)
            / (self.grid.shape.height * 2 ** zoom * self.tile_size),
            ROUND,
        )

    def intersecting(self, tile):
        """
        Return all tiles intersecting with tile.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tile: a Tile object
        """
        return _tile_intersecting_tilepyramid(tile, self)

    def tiles_from_bounds(self, bounds=None, zoom=None, batch_by=None):
        """
        Return all tiles intersecting with bounds.

        Bounds values will be cleaned if they cross the antimeridian or are
        outside of the Northern or Southern tile pyramid bounds.

        - bounds: tuple of (left, bottom, right, top) bounding values in tile
            pyramid CRS
        - zoom: zoom level
        - batch_by: yield tiles in row or column batches if activated
        """
        validate_zoom(zoom)
        if not isinstance(bounds, tuple) or len(bounds) != 4:
            raise ValueError(
                "bounds must be a tuple of left, bottom, right, top values"
            )
        if not isinstance(bounds, Bounds):
            bounds = Bounds(*bounds)
        if self.is_global:
            yield from _global_tiles_from_bounds(self, bounds, zoom, batch_by=batch_by)
        else:
            yield from _tiles_from_cleaned_bounds(self, bounds, zoom, batch_by=batch_by)

    def tiles_from_bbox(self, geometry=None, zoom=None, batch_by=None):
        """
        All metatiles intersecting with given bounding box.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        validate_zoom(zoom)
        yield from self.tiles_from_bounds(geometry.bounds, zoom, batch_by=batch_by)

    def tiles_from_geom(self, geometry=None, zoom=None, batch_by=None, exact=False):
        """
        Return all tiles intersecting with input geometry.

        - geometry: shapely geometry
        - zoom: zoom level
        """
        validate_zoom(zoom)
        if geometry.is_empty:
            return
        if not geometry.is_valid:
            raise ValueError("no valid geometry: %s" % geometry.type)
        if geometry.geom_type == "Point":
            if batch_by:
                yield (
                    self.tile_from_xy(geometry.x, geometry.y, zoom) for _ in range(1)
                )
            else:
                yield self.tile_from_xy(geometry.x, geometry.y, zoom)
        elif geometry.geom_type in (
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
            "GeometryCollection",
        ):
            if exact:
                geometry = clip_geometry_to_srs_bounds(geometry, self)
                if batch_by:
                    for batch in self.tiles_from_bbox(
                        geometry, zoom, batch_by=batch_by
                    ):
                        yield (
                            tile
                            for tile in batch
                            if geometry.intersection(tile.bbox()).area
                        )
                else:
                    for tile in self.tiles_from_bbox(geometry, zoom, batch_by=batch_by):
                        if geometry.intersection(tile.bbox()).area:
                            yield tile
            else:
                prepared_geometry = prep(clip_geometry_to_srs_bounds(geometry, self))
                if batch_by:
                    for batch in self.tiles_from_bbox(
                        geometry, zoom, batch_by=batch_by
                    ):
                        yield (
                            tile
                            for tile in batch
                            if prepared_geometry.intersects(tile.bbox())
                        )
                else:
                    for tile in self.tiles_from_bbox(geometry, zoom, batch_by=batch_by):
                        if prepared_geometry.intersects(tile.bbox()):
                            yield tile

    def tile_from_xy(self, x=None, y=None, zoom=None, on_edge_use="rb"):
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
        return _tile_from_xy(self, x, y, zoom, on_edge_use=on_edge_use)

    def to_dict(self):
        """
        Return dictionary representation of pyramid parameters.
        """
        return dict(
            grid=self.grid.to_dict(),
            metatiling=self.metatiling,
            tile_size=self.tile_size,
        )

    def from_dict(config_dict):
        """
        Initialize TilePyramid from configuration dictionary.
        """
        return TilePyramid(**config_dict)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.grid == other.grid
            and self.tile_size == other.tile_size
            and self.metatiling == other.metatiling
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "TilePyramid(%s, tile_size=%s, metatiling=%s)" % (
            self.grid,
            self.tile_size,
            self.metatiling,
        )

    def __hash__(self):
        return hash(repr(self) + repr(self.grid))
