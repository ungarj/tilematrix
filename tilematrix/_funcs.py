"""Helper functions."""

from shapely.geometry import Polygon, GeometryCollection, box
from shapely.affinity import translate
from itertools import product, chain
from collections import namedtuple


Bounds = namedtuple("Bounds", "left bottom right top")
Shape = namedtuple("Shape", "width height")


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


def _tile_intersecting_tilepyramid(tile, tp):
    """Return all tiles from tilepyramid intersecting with tile."""
    if tile.crs != tp.crs:
        raise ValueError("Tile and TilePyramid CRSes must be the same.")
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


def _tiles_from_cleaned_bounds(tilepyramid, bounds, zoom):
    """Return all tiles intersecting with bounds."""
    tile_x_size = tilepyramid.tile_x_size(zoom)
    tile_y_size = tilepyramid.tile_y_size(zoom)
    tile_left = tilepyramid.left
    tile_top = tilepyramid.top
    cols = []
    rows = []
    col = -1
    row = -1
    while tile_left <= bounds.left:
        tile_left += tile_x_size
        col += 1
    cols.append(col)
    while tile_left < bounds.right:
        tile_left += tile_x_size
        col += 1
        cols.append(col)
    while tile_top >= bounds.top:
        tile_top -= tile_y_size
        row += 1
    rows.append(row)
    while tile_top > bounds.bottom:
        tile_top -= tile_y_size
        row += 1
        rows.append(row)
    for tile_id in product([zoom], rows, cols):
        try:
            yield tilepyramid.tile(*tile_id)
        except ValueError:
            pass
