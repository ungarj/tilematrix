"""TilePyramid creation."""

import math
import pytest
from shapely.geometry import box
from tilematrix import TilePyramid, GridDefinition, PYRAMID_PARAMS


def test_grid_init(grid_definition_proj):
    grid = GridDefinition(**dict(PYRAMID_PARAMS["geodetic"], grid="custom"))
    custom_grid = TilePyramid(grid_definition_proj).grid
    # make sure standard grid gets detected
    assert grid.type == "geodetic"
    # create grid from grid
    assert GridDefinition(grid)
    # create grid from dict
    assert GridDefinition.from_dict(grid.to_dict())
    # __repr__
    assert str(grid)
    assert str(custom_grid)
    # __hash__
    assert hash(grid)
    assert hash(custom_grid)


def test_deprecated():
    grid = TilePyramid("geodetic").grid
    assert grid.srid


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
        bounds=(2426378.0132, 1528101.2618, 6293974.6215, 5446513.5222)
    )
    with pytest.raises(ValueError):
        TilePyramid(grid_definition_epsg)


def test_neighbors(grid_definition_epsg):
    """Initialize with EPSG code."""
    tp = TilePyramid(grid_definition_epsg)
    neighbor_ids = set([t.id for t in tp.tile(1, 0, 0).get_neighbors()])
    control_ids = set([(1, 1, 0), (1, 0, 1), (1, 1, 1)])
    assert len(neighbor_ids.symmetric_difference(control_ids)) == 0


def test_irregular_grids(grid_definition_irregular):
    for metatiling in [1, 2, 4, 8]:
        for pixelbuffer in [0, 100]:
            tp = TilePyramid(grid_definition_irregular, metatiling=metatiling)
            assert tp.matrix_height(0) == math.ceil(161 / metatiling)
            assert tp.matrix_width(0) == math.ceil(315 / metatiling)
            assert tp.pixel_x_size(0) == tp.pixel_y_size(0)
            for tile in [
                tp.tile(0, 0, 0),
                tp.tile(0, 10, 0),
                tp.tile(0, tp.matrix_height(0) - 1, tp.matrix_width(0) - 1)
            ]:
                # pixel sizes have to be squares
                assert tile.pixel_x_size == tile.pixel_y_size
                assert tile.pixel_x_size == 10.
                # pixelbuffer yields different shape and bounds
                assert tile.shape(10) != tile.shape()
                assert tile.bounds(10) != tile.bounds()
                # without pixelbuffers, tile bounds have to be inside TilePyramid bounds
                assert tile.left >= tp.left
                assert tile.bottom >= tp.bottom
                assert tile.right <= tp.right
                assert tile.top <= tp.top

            # with pixelbuffers, some tile bounds have to be outside TilePyramid bounds
            if pixelbuffer:

                # tile on top left corner
                tile = tp.tile(0, 0, 0)
                assert tile.bounds(pixelbuffer).left < tp.left
                assert tile.bounds(pixelbuffer).top > tp.top

                # tile on lower right corner
                tile = tp.tile(0, tp.matrix_height(0) - 1, tp.matrix_width(0) - 1)
                print(tp)
                assert tile.bounds(pixelbuffer).bottom < tp.bottom
                assert tile.bounds(pixelbuffer).right > tp.right


def test_tiles_from_bounds(grid_definition_irregular):
    bounds = (755336.179, 300068.615, 791558.022, 319499.955)
    bbox = box(*bounds)
    tp = TilePyramid(grid_definition_irregular, metatiling=4)
    tiles_bounds = list(tp.tiles_from_bounds(bounds, 0))
    tiles_bbox = list(tp.tiles_from_bbox(bbox, 0))
    tiles_geom = list(tp.tiles_from_geom(bbox, 0))

    assert set(tiles_bounds) == set(tiles_bbox) == set(tiles_geom)
