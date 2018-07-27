#!/usr/bin/env python
"""Tile properties."""

from affine import Affine

from tilematrix import TilePyramid


def test_affine():
    """Affine output."""
    tp = TilePyramid("geodetic")
    test_tiles = [(0, 0, 0), (1, 1, 1), (2, 2, 2)]
    for tile_id in test_tiles:
        tile = tp.tile(*tile_id)
        test_affine = Affine(
            tile.pixel_x_size, 0, tile.left, 0, -tile.pixel_y_size, tile.top
        )
        assert tile.affine() == test_affine
    # include pixelbuffer
    pixelbuffer = 10
    test_tiles = [(1, 1, 1), (2, 2, 2), (3, 3, 3)]
    for tile_id in test_tiles:
        tile = tp.tile(*tile_id)
        test_affine = Affine(
            tile.pixel_x_size,
            0,
            tile.bounds(pixelbuffer).left,
            0,
            -tile.pixel_y_size,
            tile.bounds(pixelbuffer).top
        )
        assert tile.affine(10) == test_affine


def test_get_parent():
    """Get parent Tile."""
    tp = TilePyramid("geodetic")
    # default
    tile = tp.tile(8, 100, 100)
    assert tile.get_parent().id == (7, 50, 50)
    # from top of pyramid
    tile = tp.tile(0, 0, 0)
    assert tile.get_parent() is None


def test_get_children():
    """Get Tile children."""
    # no metatiling
    tp = TilePyramid("geodetic")
    tile = tp.tile(8, 100, 100)
    test_children = {
        (9, 200, 200), (9, 201, 200), (9, 200, 201), (9, 201, 201)
    }
    children = {t.id for t in tile.get_children()}
    assert test_children == children

    # 2 metatiling
    tp = TilePyramid("geodetic", metatiling=2)
    tile = tp.tile(0, 0, 0)
    test_children = {(1, 0, 0), (1, 0, 1)}
    children = {t.id for t in tile.get_children()}
    assert test_children == children

    # 4 metatiling
    tp = TilePyramid("geodetic", metatiling=4)
    tile = tp.tile(0, 0, 0)
    test_children = {(1, 0, 0)}
    children = {t.id for t in tile.get_children()}
    assert test_children == children


def test_get_neighbors():
    """Get Tile neighbors."""
    tp = TilePyramid("geodetic")

    # default
    tile = tp.tile(8, 100, 100)
    # 8 neighbors
    test_neighbors = {
        (8, 101, 100), (8, 100, 101), (8, 99, 100), (8, 100, 99),
        (8, 99, 101), (8, 101, 101), (8, 101, 99), (8, 99, 99)
    }
    neighbors = {t.id for t in tile.get_neighbors()}
    assert test_neighbors == neighbors
    # 4 neighbors
    test_neighbors = {
        (8, 101, 100), (8, 100, 101), (8, 99, 100), (8, 100, 99)
    }
    neighbors = {t.id for t in tile.get_neighbors(connectedness=4)}
    assert test_neighbors == neighbors

    # over antimeridian
    tile = tp.tile(3, 1, 0)
    # 8 neighbors
    test_neighbors = {
        (3, 0, 0), (3, 1, 1), (3, 2, 0), (3, 1, 15),
        (3, 0, 1), (3, 2, 1), (3, 2, 15), (3, 0, 15)
    }
    neighbors = {t.id for t in tile.get_neighbors()}
    assert test_neighbors == neighbors
    # 4 neighbors
    test_neighbors = {
        (3, 0, 0), (3, 1, 1), (3, 2, 0), (3, 1, 15)
    }
    neighbors = {t.id for t in tile.get_neighbors(connectedness=4)}
    assert test_neighbors == neighbors

    # tile has exactly two identical neighbors
    tile = tp.tile(0, 0, 0)
    test_tile = [(0, 0, 1)]
    neighbors = [t.id for t in tile.get_neighbors()]
    assert test_tile == neighbors

    # tile is alone at current zoom level
    tp = TilePyramid("geodetic", metatiling=2)
    tile = tp.tile(0, 0, 0)
    neighbors = [t.id for t in tile.get_neighbors()]
    assert neighbors == []

    # wrong connectedness parameter
    try:
        tile.get_neighbors(connectedness="wrong_param")
        raise Exception()
    except ValueError:
        pass


def test_intersecting():
    """Get intersecting Tiles from other TilePyramid."""
    tp_source = TilePyramid("geodetic", metatiling=2)
    tp_target = TilePyramid("geodetic")
    tile = tp_source.tile(5, 2, 2)
    test_tiles = {(5, 4, 4), (5, 5, 4), (5, 4, 5), (5, 5, 5)}
    intersecting_tiles = {t.id for t in tile.intersecting(tp_target)}
    assert test_tiles == intersecting_tiles


def test_tile_compare():
    tp = TilePyramid("geodetic")
    a = tp.tile(5, 5, 5)
    b = tp.tile(5, 5, 5)
    c = tp.tile(5, 5, 6)
    assert a == b
    assert a != c
    assert b != c
    assert a != "invalid type"
    assert len(set([a, b, c])) == 2
