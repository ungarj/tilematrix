"""Helper functions."""

from shapely.geometry import Polygon, GeometryCollection, box
from shapely.affinity import translate
from itertools import product

from tilematrix import TilePyramid, MetaTilePyramid, Tile


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
    if tile.crs != tilepyramid.crs:
        raise ValueError("Tile and TilePyramid CRSes must be the same.")
    tile_metatiling = tile.tile_pyramid.metatiling
    pyramid_metatiling = tilepyramid.metatiling
    zoom, row, col = tile.id
    multiplier = float(tile_metatiling)/float(pyramid_metatiling)
    if tile_metatiling == pyramid_metatiling:
        return [tilepyramid.tile(*tile.id)]
    elif tile_metatiling > pyramid_metatiling:
        out_tiles = []
        for row_offset, col_offset in product(
            range(int(multiplier)), range(int(multiplier))
        ):
            try:
                out_tiles.append(
                    tilepyramid.tile(
                        zoom, int(multiplier*row+row_offset),
                        int(multiplier*col+col_offset))
                )
            except Exception:
                pass
        return out_tiles
    elif tile_metatiling < pyramid_metatiling:
        try:
            return [
                tilepyramid.tile(
                    zoom, int(multiplier*row), int(multiplier*col)
                )
            ]
        except Exception:
            return []


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
