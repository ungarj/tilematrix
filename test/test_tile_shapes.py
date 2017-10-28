#!/usr/bin/env python
"""Test Tile shapes."""

from tilematrix import TilePyramid


def test_simple_shapes():
    """Without metatiling & buffer."""
    # default
    tile = TilePyramid("geodetic").tile(0, 0, 0)
    assert tile.width == tile.height == 256
    assert tile.shape() == (256, 256)
    # 512x512
    tile = TilePyramid("geodetic", tile_size=512).tile(0, 0, 0)
    assert tile.width == tile.height == 512
    assert tile.shape() == (512, 512)


def test_geodetic_metatiling_shapes():
    """Metatile shapes."""
    # metatiling 2
    tp = TilePyramid("geodetic", metatiling=2)
    assert tp.metatile_size == 512
    tile_shapes = {
        (0, 0, 0): (256, 512),
        (1, 0, 0): (512, 512),
        (2, 0, 0): (512, 512),
        (3, 0, 0): (512, 512),
        (4, 0, 0): (512, 512),
        (5, 0, 0): (512, 512)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.height == control_shape[0]
        assert tile.width == control_shape[1]
        assert tile.shape() == control_shape

    # metatiling 4
    tp = TilePyramid("geodetic", metatiling=4)
    assert tp.metatile_size == 1024
    tile_shapes = {
        (0, 0, 0): (256, 512),
        (1, 0, 0): (512, 1024),
        (2, 0, 0): (1024, 1024),
        (3, 0, 0): (1024, 1024),
        (4, 0, 0): (1024, 1024),
        (5, 0, 0): (1024, 1024)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.height == control_shape[0]
        assert tile.width == control_shape[1]
        assert tile.shape() == control_shape

    # metatiling 8
    tp = TilePyramid("geodetic", metatiling=8)
    assert tp.metatile_size == 2048
    tile_shapes = {
        (0, 0, 0): (256, 512),
        (1, 0, 0): (512, 1024),
        (2, 0, 0): (1024, 2048),
        (3, 0, 0): (2048, 2048),
        (4, 0, 0): (2048, 2048),
        (5, 0, 0): (2048, 2048)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.height == control_shape[0]
        assert tile.width == control_shape[1]
        assert tile.shape() == control_shape

    # metatiling 16
    tp = TilePyramid("geodetic", metatiling=16)
    assert tp.metatile_size == 4096
    tile_shapes = {
        (0, 0, 0): (256, 512),
        (1, 0, 0): (512, 1024),
        (2, 0, 0): (1024, 2048),
        (3, 0, 0): (2048, 4096),
        (4, 0, 0): (4096, 4096),
        (5, 0, 0): (4096, 4096)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.height == control_shape[0]
        assert tile.width == control_shape[1]
        assert tile.shape() == control_shape


def test_geodetic_pixelbuffer_shapes():
    """Tile shapes using pixelbuffer."""
    tp = TilePyramid("geodetic")
    pixelbuffer = 10
    tile_shapes = {
        (0, 0, 0): (256, 276),  # single tile at zoom 0
        (1, 0, 0): (266, 276),  # top left
        (2, 0, 0): (266, 276),  # top left
        (2, 0, 2): (266, 276),  # top middle
        (2, 0, 3): (266, 276),  # top right
        (2, 3, 0): (266, 276),  # bottom left
        (2, 3, 2): (266, 276),  # bottom middle
        (2, 3, 7): (266, 276),  # bottom right
        (3, 1, 0): (276, 276),  # middle left
        (3, 1, 1): (276, 276),  # middle middle
        (3, 1, 15): (276, 276),  # middle right
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.shape(pixelbuffer) == control_shape


def test_geodetic_metatile_shapes():
    """Metatile shapes."""
    # metatiling 2
    tp = TilePyramid("geodetic", metatiling=2)
    pixelbuffer = 10
    assert tp.metatile_size == 512
    tile_shapes = {
        (0, 0, 0): (256, 532),
        (1, 0, 0): (512, 532),
        (2, 0, 0): (522, 532),
        (3, 0, 0): (522, 532),
        (4, 0, 0): (522, 532),
        (5, 0, 0): (522, 532),
        (5, 1, 1): (532, 532)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.shape(pixelbuffer) == control_shape

    # metatiling 4
    tp = TilePyramid("geodetic", metatiling=4)
    assert tp.metatile_size == 1024
    tile_shapes = {
        (0, 0, 0): (256, 532),
        (1, 0, 0): (512, 1044),
        (2, 0, 0): (1024, 1044),
        (3, 0, 0): (1034, 1044),
        (4, 0, 0): (1034, 1044),
        (5, 0, 0): (1034, 1044),
        (5, 1, 1): (1044, 1044)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.shape(pixelbuffer) == control_shape

    # metatiling 8
    tp = TilePyramid("geodetic", metatiling=8)
    assert tp.metatile_size == 2048
    tile_shapes = {
        (0, 0, 0): (256, 532),
        (1, 0, 0): (512, 1044),
        (2, 0, 0): (1024, 2068),
        (3, 0, 0): (2048, 2068),
        (4, 0, 0): (2058, 2068),
        (5, 0, 0): (2058, 2068),
        (5, 1, 1): (2068, 2068)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.shape(pixelbuffer) == control_shape

    # metatiling 16
    tp = TilePyramid("geodetic", metatiling=16)
    assert tp.metatile_size == 4096
    tile_shapes = {
        (0, 0, 0): (256, 532),
        (1, 0, 0): (512, 1044),
        (2, 0, 0): (1024, 2068),
        (3, 0, 0): (2048, 4116),
        (4, 0, 0): (4096, 4116),
        (5, 0, 0): (4106, 4116),
        (6, 1, 1): (4116, 4116)
    }
    for tile_id, control_shape in tile_shapes.items():
        tile = tp.tile(*tile_id)
        assert tile.shape(pixelbuffer) == control_shape
