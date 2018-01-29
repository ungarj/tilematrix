"""TilePyramid creation."""

import pytest
from tilematrix import TilePyramid


def test_proj_str(grid_definition_proj):
    """Initialize with proj string."""
    tp = TilePyramid(grid_definition_proj)
    assert tp.tile(0, 0, 0).bounds() == grid_definition_proj["bounds"]


def test_epsg_code(grid_definition_epsg):
    """Initialize with EPSG code."""
    tp = TilePyramid(grid_definition_epsg)
    assert tp.tile(0, 0, 0).bounds() == grid_definition_epsg["bounds"]


def test_shape_error(grid_definition_epsg):
    """Raise error when shape aspect ratio is not bounds apsect ratio."""
    grid_definition_epsg.update(
        bounds=(2426378.0132, 1528101.2618, 6293974.6215, 5446513.5222))
    with pytest.raises(ValueError):
        TilePyramid(grid_definition_epsg)


def test_neighbors(grid_definition_epsg):
    """Initialize with EPSG code."""
    tp = TilePyramid(grid_definition_epsg)
    neighbor_ids = set([t.id for t in tp.tile(1, 0, 0).get_neighbors()])
    control_ids = set([(1, 1, 0), (1, 0, 1), (1, 1, 1)])
    assert len(neighbor_ids.symmetric_difference(control_ids)) == 0
