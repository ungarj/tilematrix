"""Helper functions."""

from collections import namedtuple
from itertools import product, chain
from rasterio.crs import CRS
from shapely.geometry import Polygon, GeometryCollection, box
from shapely.affinity import translate
import six

from ._conf import DELTA, PYRAMID_PARAMS


Bounds = namedtuple("Bounds", "left bottom right top")
Shape = namedtuple("Shape", "width height")
TileIndex = namedtuple("TileIndex", "zoom row col")


def validate_zoom(zoom):
    if not isinstance(zoom, int):
        raise TypeError("zoom must be an integer")
    if zoom < 0:
        raise ValueError("zoom must be greater or equal 0")


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
    if not geometry.is_valid:
        raise ValueError("invalid geometry given")
    pyramid_bbox = box(*pyramid.bounds)

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
            geom_bounds = Bounds(*geom.bounds)
            if geom_bounds.left < pyramid.left:
                geom = translate(geom, xoff=2*pyramid.right)
            elif geom_bounds.right > pyramid.right:
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


def snap_bounds(bounds=None, tile_pyramid=None, zoom=None, pixelbuffer=0):
    """
    Extend bounds to be aligned with union of tile bboxes.

    - bounds: (left, bottom, right, top)
    - tile_pyramid: a TilePyramid object
    - zoom: target zoom level
    - pixelbuffer: apply pixelbuffer
    """
    bounds = Bounds(*bounds)
    validate_zoom(zoom)
    lb = _tile_from_xy(tile_pyramid, bounds.left, bounds.bottom, zoom, on_edge_use="rt")
    rt = _tile_from_xy(tile_pyramid, bounds.right, bounds.top, zoom, on_edge_use="lb")
    left, bottom, _, _ = lb.bounds(pixelbuffer)
    _, _, right, top = rt.bounds(pixelbuffer)
    return Bounds(left, bottom, right, top)


class GridDefinition(object):
    """Object representing the tile pyramid source grid."""

    def __init__(self, grid_definition, tile_size=256, metatiling=1):
        if metatiling not in (1, 2, 4, 8, 16):
            raise ValueError("metatling must be one of 1, 2, 4, 8, 16")
        if isinstance(grid_definition, dict):
            self.init_definition = dict(**grid_definition)
            self.type = "custom"
            if "shape" not in self.init_definition:
                raise AttributeError("grid shape not provided")
            self.shape = Shape(*self.init_definition["shape"])
            self.bounds = Bounds(*self.init_definition["bounds"])
            # verify that shape aspect ratio fits bounds apsect ratio
            _verify_shape_bounds(shape=self.shape, bounds=self.bounds)
            self.left, self.bottom, self.right, self.top = self.bounds
            self.is_global = self.init_definition.get("is_global", False)
            if all([i in self.init_definition for i in ["proj", "epsg"]]):
                raise ValueError("either 'epsg' or 'proj' are allowed.")
            if "epsg" in self.init_definition:
                self.crs = CRS().from_epsg(self.init_definition["epsg"])
                self.srid = self.init_definition["epsg"]
            elif "proj" in self.init_definition:
                self.crs = CRS().from_string(self.init_definition["proj"])
                self.srid = None
            else:
                raise AttributeError("either 'epsg' or 'proj' is required")
        elif isinstance(grid_definition, six.string_types):
            self.init_definition = grid_definition
            if self.init_definition not in PYRAMID_PARAMS:
                raise ValueError(
                    "WMTS tileset '%s' not found. Use one of %s" % (
                        self.init_definition, PYRAMID_PARAMS.keys()
                    )
                )
            self.type = self.init_definition
            self.shape = Shape(*PYRAMID_PARAMS[self.init_definition]["shape"])
            self.bounds = Bounds(*PYRAMID_PARAMS[self.init_definition]["bounds"])
            self.left, self.bottom, self.right, self.top = self.bounds
            self.is_global = PYRAMID_PARAMS[self.init_definition]["is_global"]
            self.srid = PYRAMID_PARAMS[self.init_definition]["epsg"]
            self.crs = CRS().from_epsg(self.srid)
        elif isinstance(grid_definition, GridDefinition):
            self.__init__(
                grid_definition.init_definition, tile_size=tile_size,
                metatiling=metatiling
            )
        else:
            raise TypeError(
                "invalid grid definition type: %s" % type(grid_definition))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.init_definition == other.init_definition
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'GridDefinition(init_definition=%s)' % self.init_definition

    def __hash__(self):
        return hash(repr(self))


def _verify_shape_bounds(shape, bounds):
    """Verify that shape corresponds to bounds apect ratio."""
    shape = Shape(*map(float, shape))
    bounds = Bounds(*map(float, bounds))
    shape_ratio = shape.width / shape.height
    bounds_ratio = (bounds.right - bounds.left) / (bounds.top - bounds.bottom)
    if abs(shape_ratio - bounds_ratio) > DELTA:
        min_length = min([
            (bounds.right - bounds.left) / shape.width,
            (bounds.top - bounds.bottom) / shape.height
        ])
        proposed_bounds = Bounds(
            bounds.left,
            bounds.bottom,
            bounds.left + shape.width * min_length,
            bounds.bottom + shape.height * min_length)
        raise ValueError(
            "shape ratio (%s) must equal bounds ratio (%s); try %s" % (
                shape_ratio, bounds_ratio, proposed_bounds))


def _tile_intersecting_tilepyramid(tile, tp):
    """Return all tiles from tilepyramid intersecting with tile."""
    if tile.tp.grid != tp.grid:
        raise ValueError("Tile and TilePyramid source grids must be the same.")
    tile_metatiling = tile.tile_pyramid.metatiling
    pyramid_metatiling = tp.metatiling
    multiplier = float(tile_metatiling)/float(pyramid_metatiling)
    if tile_metatiling > pyramid_metatiling:
        return [
            tp.tile(
                tile.zoom,
                int(multiplier) * tile.row + row_offset,
                int(multiplier) * tile.col + col_offset
            )
            for row_offset, col_offset in product(
                range(int(multiplier)), range(int(multiplier))
            )
        ]
    elif tile_metatiling < pyramid_metatiling:
        return [tp.tile(
            tile.zoom, int(multiplier*tile.row), int(multiplier*tile.col)
        )]
    else:
        return [tp.tile(*tile.id)]


def _global_tiles_from_bounds(tp, bounds, zoom):
    """Return also Tiles if bounds cross the antimeridian."""
    seen = set()

    # clip to tilepyramid top and bottom bounds
    left, right = bounds.left, bounds.right
    top = tp.top if bounds.top > tp.top else bounds.top
    bottom = tp.bottom if bounds.bottom < tp.bottom else bounds.bottom

    if left >= tp.left and right <= tp.right:
        for tile in _tiles_from_cleaned_bounds(tp, bounds, zoom):
            yield tile

    # bounds overlap on the Western side with antimeridian
    if left < tp.left:
        for tile in chain(
            # tiles west of antimeridian
            _tiles_from_cleaned_bounds(
                tp,
                Bounds(left + (tp.right - tp.left), bottom, tp.right, top),
                zoom
            ),
            # tiles east of antimeridian
            _tiles_from_cleaned_bounds(
                tp, Bounds(tp.left, bottom, right, top), zoom
            )
        ):
            # make output tiles unique
            if tile.id not in seen:
                seen.add(tile.id)
                yield tile

    # bounds overlap on the Eastern side with antimeridian
    if right > tp.right:
        for tile in chain(
            # tiles west of antimeridian
            _tiles_from_cleaned_bounds(
                tp, Bounds(left, bottom, tp.right, top), zoom
            ),
            # tiles east of antimeridian
            _tiles_from_cleaned_bounds(
                tp,
                Bounds(tp.left, bottom, right - (tp.right - tp.left), top),
                zoom
            )
        ):
            # make output tiles unique
            if tile.id not in seen:
                seen.add(tile.id)
                yield tile


def _tiles_from_cleaned_bounds(tp, bounds, zoom):
    """Return all tiles intersecting with bounds."""
    lb = _tile_from_xy(tp, bounds.left, bounds.bottom, zoom, on_edge_use="rt")
    rt = _tile_from_xy(tp, bounds.right, bounds.top, zoom, on_edge_use="lb")
    for tile_id in product([zoom], range(rt.row, lb.row + 1), range(lb.col, rt.col + 1)):
        try:
            yield tp.tile(*tile_id)
        except ValueError:
            pass


def _tile_from_xy(tp, x, y, zoom, on_edge_use="rb"):
    # determine row
    row = int((tp.top - y) / tp.tile_y_size(zoom))
    if on_edge_use in ["rt", "lt"] and (tp.top - y) % tp.tile_y_size(zoom) == 0.:
        row -= 1

    # determine column
    col = int((x - tp.left) / tp.tile_x_size(zoom))
    if on_edge_use in ["lb", "lt"] and (x - tp.left) % tp.tile_x_size(zoom) == 0.:
        col -= 1
    # handle Antimeridian wrapping
    if tp.is_global:
        # left side
        if col == -1:
            col = tp.matrix_width(zoom) - 1
        # right side
        elif col >= tp.matrix_width(zoom):
            col = col % tp.matrix_width(zoom)

    try:
        return tp.tile(zoom, row, col)
    except ValueError as e:
        raise ValueError(
                "on_edge_use '%s' results in an invalid tile here: %s" % (on_edge_use, e)
            )
