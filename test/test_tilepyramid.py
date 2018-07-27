#!/usr/bin/env python
"""TilePyramid creation."""

import pytest
from shapely.geometry import Point
from shapely.ops import unary_union
from tilematrix import TilePyramid, snap_bounds


def test_init():
    """Initialize TilePyramids."""
    for tptype in ["geodetic", "mercator"]:
        assert TilePyramid(tptype)
    try:
        TilePyramid("invalid")
        raise Exception()
    except ValueError:
        pass


def test_metatiling():
    """Metatiling setting."""
    for metatiling in [1, 2, 4, 8, 16]:
        assert TilePyramid("geodetic", metatiling=metatiling)
    try:
        TilePyramid("geodetic", metatiling=5)
        raise Exception()
    except ValueError:
        pass


def test_tile_size():
    """Tile sizes."""
    for tile_size in [128, 256, 512, 1024]:
        tp = TilePyramid("geodetic", tile_size=tile_size)
        assert tp.tile_size == tile_size


def test_intersect():
    """Get intersecting Tiles."""
    # same metatiling
    tp = TilePyramid("geodetic")
    intersect_tile = TilePyramid("geodetic").tile(5, 1, 1)
    control = {(5, 1, 1)}
    test_tiles = {tile.id for tile in tp.intersecting(intersect_tile)}
    assert control == test_tiles

    # smaller metatiling
    tp = TilePyramid("geodetic")
    intersect_tile = TilePyramid("geodetic", metatiling=2).tile(5, 1, 1)
    control = {(5, 2, 2), (5, 2, 3), (5, 3, 3), (5, 3, 2)}
    test_tiles = {tile.id for tile in tp.intersecting(intersect_tile)}
    assert control == test_tiles

    # bigger metatiling
    tp = TilePyramid("geodetic", metatiling=2)
    intersect_tile = TilePyramid("geodetic").tile(5, 1, 1)
    control = {(5, 0, 0)}
    test_tiles = {tile.id for tile in tp.intersecting(intersect_tile)}
    assert control == test_tiles

    # different CRSes
    tp = TilePyramid("geodetic")
    intersect_tile = TilePyramid("mercator").tile(5, 1, 1)
    try:
        test_tiles = {tile.id for tile in tp.intersecting(intersect_tile)}
        raise Exception()
    except ValueError:
        pass


def test_tilepyramid_compare(grid_definition_proj, grid_definition_epsg):
    """Comparison operators."""
    gproj, gepsg = grid_definition_proj, grid_definition_epsg
    # predefined
    assert TilePyramid("geodetic") == TilePyramid("geodetic")
    assert TilePyramid("geodetic") != TilePyramid("geodetic", metatiling=2)
    assert TilePyramid("geodetic") != TilePyramid("geodetic", tile_size=512)
    assert TilePyramid("mercator") == TilePyramid("mercator")
    assert TilePyramid("mercator") != TilePyramid("mercator", metatiling=2)
    assert TilePyramid("mercator") != TilePyramid("mercator", tile_size=512)
    # epsg based
    assert TilePyramid(gepsg) == TilePyramid(gepsg)
    assert TilePyramid(gepsg) != TilePyramid(gepsg, metatiling=2)
    assert TilePyramid(gepsg) != TilePyramid(gepsg, tile_size=512)
    # proj based
    assert TilePyramid(gproj) == TilePyramid(gproj)
    assert TilePyramid(gproj) != TilePyramid(gproj, metatiling=2)
    assert TilePyramid(gproj) != TilePyramid(gproj, tile_size=512)
    # altered bounds
    abounds = dict(**gproj)
    abounds.update(bounds=(-5000000., -5000000., 5000000., 5000000.))
    assert TilePyramid(abounds) == TilePyramid(abounds)
    assert TilePyramid(gproj) != TilePyramid(abounds)
    # other type
    assert TilePyramid("geodetic") != "string"


def test_grid_compare(grid_definition_proj, grid_definition_epsg):
    """Comparison operators."""
    gproj, gepsg = grid_definition_proj, grid_definition_epsg
    # predefined
    assert TilePyramid("geodetic").grid == TilePyramid("geodetic").grid
    assert TilePyramid("geodetic").grid == TilePyramid(
        "geodetic", metatiling=2).grid
    assert TilePyramid("geodetic").grid == TilePyramid(
        "geodetic", tile_size=512).grid
    assert TilePyramid("mercator").grid == TilePyramid("mercator").grid
    assert TilePyramid("mercator").grid == TilePyramid(
        "mercator", metatiling=2).grid
    assert TilePyramid("mercator").grid == TilePyramid(
        "mercator", tile_size=512).grid
    # epsg based
    assert TilePyramid(gepsg).grid == TilePyramid(gepsg).grid
    assert TilePyramid(gepsg).grid == TilePyramid(gepsg, metatiling=2).grid
    assert TilePyramid(gepsg).grid == TilePyramid(gepsg, tile_size=512).grid
    # proj based
    assert TilePyramid(gproj).grid == TilePyramid(gproj).grid
    assert TilePyramid(gproj).grid == TilePyramid(gproj, metatiling=2).grid
    assert TilePyramid(gproj).grid == TilePyramid(gproj, tile_size=512).grid
    # altered bounds
    abounds = dict(**gproj)
    abounds.update(bounds=(-5000000., -5000000., 5000000., 5000000.))
    assert TilePyramid(abounds).grid == TilePyramid(abounds).grid
    assert TilePyramid(gproj).grid != TilePyramid(abounds).grid


def test_tile_from_xy():
    tp = TilePyramid("geodetic")
    zoom = 5

    # point inside tile
    p_in = (0.5, 0.5, zoom)
    control_in = [
        ((5, 15, 32), "rb"),
        ((5, 15, 32), "lb"),
        ((5, 15, 32), "rt"),
        ((5, 15, 32), "lt"),
    ]
    for tile_id, on_edge_use in control_in:
        tile = tp.tile_from_xy(*p_in, on_edge_use=on_edge_use)
        assert tile.id == tile_id
        assert Point(p_in[0], p_in[1]).within(tile.bbox())

    # point is on tile edge
    p_edge = (0, 0, zoom)
    control_edge = [
        ((5, 16, 32), "rb"),
        ((5, 16, 31), "lb"),
        ((5, 15, 32), "rt"),
        ((5, 15, 31), "lt"),
    ]
    for tile_id, on_edge_use in control_edge:
        tile = tp.tile_from_xy(*p_edge, on_edge_use=on_edge_use)
        assert tile.id == tile_id
        assert Point(p_edge[0], p_edge[1]).touches(tile.bbox())

    with pytest.raises(ValueError):
        tp.tile_from_xy(180, -90, zoom, on_edge_use="rb")
    with pytest.raises(ValueError):
        tp.tile_from_xy(180, -90, zoom, on_edge_use="lb")

    tile = tp.tile_from_xy(180, -90, zoom, on_edge_use="rt")
    assert tile.id == (5, 31, 0)
    tile = tp.tile_from_xy(180, -90, zoom, on_edge_use="lt")
    assert tile.id == (5, 31, 63)

    with pytest.raises(ValueError):
        tp.tile_from_xy(-180, 90, zoom, on_edge_use="lt")
    with pytest.raises(ValueError):
        tp.tile_from_xy(-180, 90, zoom, on_edge_use="rt")

    tile = tp.tile_from_xy(-180, 90, zoom, on_edge_use="rb")
    assert tile.id == (5, 0, 0)
    tile = tp.tile_from_xy(-180, 90, zoom, on_edge_use="lb")
    assert tile.id == (5, 0, 63)


def test_tiles_from_bounds():
    tp = TilePyramid("geodetic")
    parent = tp.tile(8, 5, 5)
    from_bounds = set([t.id for t in tp.tiles_from_bounds(parent.bounds(), 9)])
    children = set([t.id for t in parent.get_children()])
    assert from_bounds == children


def test_snap_bounds():
    bounds = (0, 1, 2, 3)
    tp = TilePyramid("geodetic")
    zoom = 8

    snapped = snap_bounds(bounds=bounds, tile_pyramid=tp, zoom=zoom)
    control = unary_union([
        tile.bbox() for tile in tp.tiles_from_bounds(bounds, zoom)
    ]).bounds
    assert snapped == control

    pixelbuffer = 10
    snapped = snap_bounds(
        bounds=bounds, tile_pyramid=tp, zoom=zoom, pixelbuffer=pixelbuffer
    )
    control = unary_union([
        tile.bbox(pixelbuffer) for tile in tp.tiles_from_bounds(bounds, zoom)
    ]).bounds
    assert snapped == control
