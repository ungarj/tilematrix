#!/usr/bin/env python
"""TilePyramid creation."""

from tilematrix import TilePyramid


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
