"""Helper functions."""

from itertools import product

from rasterio.crs import CRS
from shapely.affinity import translate
from shapely.geometry import Polygon, GeometryCollection, box
from shapely.ops import unary_union
from shapely.prepared import prep

from ._conf import DELTA, ROUND
from ._types import Bounds, Shape


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
                geom = translate(geom, xoff=2 * pyramid.right)
            elif geom_bounds.right > pyramid.right:
                geom = translate(geom, xoff=-2 * pyramid.right)
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


def _verify_shape_bounds(shape, bounds):
    """Verify that shape corresponds to bounds apect ratio."""
    if not isinstance(shape, (tuple, list)) or len(shape) != 2:
        raise TypeError(
            "shape must be a tuple or list with two elements: %s" % str(shape)
        )
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 4:
        raise TypeError(
            "bounds must be a tuple or list with four elements: %s" % str(bounds)
        )
    shape = Shape(*shape)
    bounds = Bounds(*bounds)
    shape_ratio = shape.width / shape.height
    bounds_ratio = (bounds.right - bounds.left) / (bounds.top - bounds.bottom)
    if abs(shape_ratio - bounds_ratio) > DELTA:
        min_length = min(
            [
                (bounds.right - bounds.left) / shape.width,
                (bounds.top - bounds.bottom) / shape.height,
            ]
        )
        proposed_bounds = Bounds(
            bounds.left,
            bounds.bottom,
            bounds.left + shape.width * min_length,
            bounds.bottom + shape.height * min_length,
        )
        raise ValueError(
            "shape ratio (%s) must equal bounds ratio (%s); try %s"
            % (shape_ratio, bounds_ratio, proposed_bounds)
        )


def _get_crs(srs):
    if not isinstance(srs, dict):
        raise TypeError("'srs' must be a dictionary")
    if "wkt" in srs:
        return CRS().from_wkt(srs["wkt"])
    elif "epsg" in srs:
        return CRS().from_epsg(srs["epsg"])
    elif "proj" in srs:
        return CRS().from_string(srs["proj"])
    else:
        raise TypeError("provide either 'wkt', 'epsg' or 'proj' definition")


def _tile_intersecting_tilepyramid(tile, tp):
    """Return all tiles from tilepyramid intersecting with tile."""
    if tile.tp.grid != tp.grid:
        raise ValueError("Tile and TilePyramid source grids must be the same.")
    tile_metatiling = tile.tile_pyramid.metatiling
    pyramid_metatiling = tp.metatiling
    multiplier = tile_metatiling / pyramid_metatiling
    if tile_metatiling > pyramid_metatiling:
        return [
            tp.tile(
                tile.zoom,
                int(multiplier) * tile.row + row_offset,
                int(multiplier) * tile.col + col_offset,
            )
            for row_offset, col_offset in product(
                range(int(multiplier)), range(int(multiplier))
            )
        ]
    elif tile_metatiling < pyramid_metatiling:
        return [
            tp.tile(tile.zoom, int(multiplier * tile.row), int(multiplier * tile.col))
        ]
    else:
        return [tp.tile(*tile.id)]


def _global_tiles_from_bounds(tp, bounds, zoom, batch_by=None):
    """Return also Tiles if bounds cross the antimeridian."""

    # clip to tilepyramid top and bottom bounds
    left, right = bounds.left, bounds.right
    top = min([tp.top, bounds.top])
    bottom = max([tp.bottom, bounds.bottom])

    # special case if bounds cross the antimeridian
    if left < tp.left or right > tp.right:
        # shift overlap to valid side of antimeridian
        # create MultiPolygon
        # yield tiles by
        bounds_geoms = []

        # tiles west of antimeridian
        if left < tp.left:
            # move outside part of bounding box to the valid side of antimeridian
            bounds_geoms.append(box(left + (tp.right - tp.left), bottom, tp.right, top))
            bounds_geoms.append(
                # remaining part of bounding box
                box(tp.left, bottom, min([right, tp.right]), top)
            )

        # tiles east of antimeridian
        if right > tp.right:
            # move outside part of bounding box to the valid side of antimeridian
            bounds_geoms.append(box(tp.left, bottom, right - (tp.right - tp.left), top))
            bounds_geoms.append(box(max([left, tp.left]), bottom, tp.right, top))

        bounds_geom = unary_union(bounds_geoms).buffer(0)
        bounds_geom_prep = prep(bounds_geom)

        # if union of bounding boxes is a multipart geometry, do some costly checks to be able
        # to yield in batches
        if bounds_geom.geom_type.lower().startswith("multi"):
            if batch_by:
                for batch in _tiles_from_cleaned_bounds(
                    tp, bounds_geom.bounds, zoom, batch_by
                ):
                    yield (
                        tile
                        for tile in batch
                        if bounds_geom_prep.intersects(tile.bbox())
                    )
            else:
                for tile in _tiles_from_cleaned_bounds(tp, bounds_geom.bounds, zoom):
                    if bounds_geom_prep.intersects(tile.bbox()):
                        yield tile
            return

        # else, continue with cleaned bounds
        bounds = bounds_geom.bounds

    # yield using cleaned bounds
    yield from _tiles_from_cleaned_bounds(tp, bounds, zoom, batch_by=batch_by)


def _tiles_from_cleaned_bounds(tp, bounds, zoom, batch_by=None):
    """Return all tiles intersecting with bounds."""
    bounds = Bounds(*bounds)
    lb = _tile_from_xy(tp, bounds.left, bounds.bottom, zoom, on_edge_use="rt")
    rt = _tile_from_xy(tp, bounds.right, bounds.top, zoom, on_edge_use="lb")
    row_range = range(rt.row, lb.row + 1)
    col_range = range(lb.col, rt.col + 1)
    if batch_by is None:
        for row, col in product(row_range, col_range):
            yield tp.tile(zoom, row, col)
    elif batch_by == "row":
        for row in row_range:
            yield (tp.tile(zoom, row, col) for col in col_range)
    elif batch_by == "column":
        for col in col_range:
            yield (tp.tile(zoom, row, col) for row in row_range)
    else:  # pragma: no cover
        raise ValueError("'batch_by' must either be None, 'row' or 'column'.")


def _tile_from_xy(tp, x, y, zoom, on_edge_use="rb"):
    # determine row
    tile_y_size = round(tp.pixel_y_size(zoom) * tp.tile_size * tp.metatiling, ROUND)
    row = int((tp.top - y) / tile_y_size)
    if on_edge_use in ["rt", "lt"] and (tp.top - y) % tile_y_size == 0.0:
        row -= 1

    # determine column
    tile_x_size = round(tp.pixel_x_size(zoom) * tp.tile_size * tp.metatiling, ROUND)
    col = int((x - tp.left) / tile_x_size)
    if on_edge_use in ["lb", "lt"] and (x - tp.left) % tile_x_size == 0.0:
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
            "on_edge_use '%s' results in an invalid tile: %s" % (on_edge_use, e)
        )
