#!/usr/bin/env python
"""Test tile matrix shapes."""

from tilematrix import TilePyramid


def test_geodetic_matrix_shapes():
    """Test shapes of geodetic tile matrices."""
    # 1 metatiling
    matrix_shapes = {
        0: (2, 1),
        1: (4, 2),
        2: (8, 4),
        3: (16, 8),
        4: (32, 16),
        5: (64, 32),
        6: (128, 64)
    }
    tp = TilePyramid("geodetic")
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 2 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (2, 1),
        2: (4, 2),
        3: (8, 4),
        4: (16, 8),
        5: (32, 16),
        6: (64, 32),
    }
    tp = TilePyramid("geodetic", metatiling=2)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 4 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (2, 1),
        3: (4, 2),
        4: (8, 4),
        5: (16, 8),
        6: (32, 16),
    }
    tp = TilePyramid("geodetic", metatiling=4)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 8 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (2, 1),
        4: (4, 2),
        5: (8, 4),
        6: (16, 8),
    }
    tp = TilePyramid("geodetic", metatiling=8)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 16 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (1, 1),
        4: (2, 1),
        5: (4, 2),
        6: (8, 4),
    }
    tp = TilePyramid("geodetic", metatiling=16)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape


def test_mercator_matrix_shapes():
    """Test shapes of mercator tile matrices."""
    # 1 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (2, 2),
        2: (4, 4),
        3: (8, 8),
        4: (16, 16),
        5: (32, 32),
        6: (64, 64)
    }
    tp = TilePyramid("mercator")
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 2 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (2, 2),
        3: (4, 4),
        4: (8, 8),
        5: (16, 16),
        6: (32, 32),
    }
    tp = TilePyramid("mercator", metatiling=2)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 4 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (2, 2),
        4: (4, 4),
        5: (8, 8),
        6: (16, 16),
    }
    tp = TilePyramid("mercator", metatiling=4)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 8 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (1, 1),
        4: (2, 2),
        5: (4, 4),
        6: (8, 8),
    }
    tp = TilePyramid("mercator", metatiling=8)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape

    # 16 metatiling
    matrix_shapes = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (1, 1),
        4: (1, 1),
        5: (2, 2),
        6: (4, 4),
    }
    tp = TilePyramid("mercator", metatiling=16)
    for zoom, shape in matrix_shapes.items():
        assert (tp.matrix_width(zoom), tp.matrix_height(zoom)) == shape
