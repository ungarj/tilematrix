"""TilePyramid creation."""

import pytest
from shapely.geometry import Point, box
from shapely.ops import unary_union
from types import GeneratorType

from tilematrix import TilePyramid, snap_bounds


def test_init():
    """Initialize TilePyramids."""
    for tptype in ["geodetic", "mercator"]:
        assert TilePyramid(tptype)
    with pytest.raises(ValueError):
        TilePyramid("invalid")
    with pytest.raises(ValueError):
        TilePyramid()
    assert hash(TilePyramid(tptype))


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
    intersect_tile = TilePyramid("geodetic").tile(4, 12, 31)
    control = {(4, 6, 15)}
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
    abounds.update(bounds=(-5000000.0, -5000000.0, 5000000.0, 5000000.0))
    assert TilePyramid(abounds) == TilePyramid(abounds)
    assert TilePyramid(gproj) != TilePyramid(abounds)
    # other type
    assert TilePyramid("geodetic") != "string"


def test_grid_compare(grid_definition_proj, grid_definition_epsg):
    """Comparison operators."""
    gproj, gepsg = grid_definition_proj, grid_definition_epsg
    # predefined
    assert TilePyramid("geodetic").grid == TilePyramid("geodetic").grid
    assert TilePyramid("geodetic").grid == TilePyramid("geodetic", metatiling=2).grid
    assert TilePyramid("geodetic").grid == TilePyramid("geodetic", tile_size=512).grid
    assert TilePyramid("mercator").grid == TilePyramid("mercator").grid
    assert TilePyramid("mercator").grid == TilePyramid("mercator", metatiling=2).grid
    assert TilePyramid("mercator").grid == TilePyramid("mercator", tile_size=512).grid
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
    abounds.update(bounds=(-5000000.0, -5000000.0, 5000000.0, 5000000.0))
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

    with pytest.raises(TypeError):
        tp.tile_from_xy(-180, 90, zoom, on_edge_use="lt")
    with pytest.raises(TypeError):
        tp.tile_from_xy(-180, 90, zoom, on_edge_use="rt")

    tile = tp.tile_from_xy(-180, 90, zoom, on_edge_use="rb")
    assert tile.id == (5, 0, 0)
    tile = tp.tile_from_xy(-180, 90, zoom, on_edge_use="lb")
    assert tile.id == (5, 0, 63)

    with pytest.raises(ValueError):
        tp.tile_from_xy(-180, 90, zoom, on_edge_use="invalid")


def test_tiles_from_bounds(grid_definition_proj):
    # global pyramids
    tp = TilePyramid("geodetic")
    parent = tp.tile(8, 5, 5)
    from_bounds = set([t.id for t in tp.tiles_from_bounds(parent.bounds(), 9)])
    children = set([t.id for t in parent.get_children()])
    assert from_bounds == children
    # non-global pyramids
    tp = TilePyramid(grid_definition_proj)
    parent = tp.tile(8, 0, 0)
    from_bounds = set([t.id for t in tp.tiles_from_bounds(parent.bounds(), 9)])
    children = set([t.id for t in parent.get_children()])
    assert from_bounds == children


def test_tiles_from_bounds_batch_by_row():
    tp = TilePyramid("geodetic")
    bounds = (0, 0, 90, 90)
    zoom = 8

    tiles = tp.tiles_from_bounds(bounds, zoom, batch_by="row")
    assert isinstance(tiles, GeneratorType)
    assert list(tiles)

    previous_row = None
    tiles = 0
    for tile_row in tp.tiles_from_bounds(bounds, zoom, batch_by="row"):
        assert isinstance(tile_row, GeneratorType)
        previous_tile = None
        for tile in tile_row:
            tiles += 1
            if previous_row is None:
                if previous_tile is not None:
                    assert tile.col == previous_tile.col + 1
            else:
                if previous_tile is not None:
                    assert tile.col == previous_tile.col + 1
                    assert tile.row == previous_tile.row
                    assert tile.row == previous_row + 1

            previous_tile = tile

        previous_row = tile.row

    assert tiles == len(list(tp.tiles_from_bounds(bounds, zoom)))


def test_tiles_from_bounds_batch_by_column():
    tp = TilePyramid("geodetic")
    bounds = (0, 0, 90, 90)
    zoom = 8

    tiles = tp.tiles_from_bounds(bounds, zoom, batch_by="column")
    assert isinstance(tiles, GeneratorType)
    assert list(tiles)

    previous_column = None
    tiles = 0
    for tile_column in tp.tiles_from_bounds(bounds, zoom, batch_by="column"):
        assert isinstance(tile_column, GeneratorType)
        previous_tile = None
        for tile in tile_column:
            tiles += 1
            if previous_column is None:
                if previous_tile is not None:
                    assert tile.row == previous_tile.row + 1
            else:
                if previous_tile is not None:
                    assert tile.row == previous_tile.row + 1
                    assert tile.col == previous_tile.col
                    assert tile.col == previous_column + 1

            previous_tile = tile

        previous_column = tile.col

    assert tiles == len(list(tp.tiles_from_bounds(bounds, zoom)))


def test_tiles_from_bounds_batch_by_row_antimeridian_bounds():
    tp = TilePyramid("geodetic")
    bounds = (0, 0, 185, 95)
    zoom = 8

    tiles = tp.tiles_from_bounds(bounds, zoom, batch_by="row")
    assert isinstance(tiles, GeneratorType)
    assert list(tiles)

    previous_row = None
    tiles = 0
    for tile_row in tp.tiles_from_bounds(bounds, zoom, batch_by="row"):
        assert isinstance(tile_row, GeneratorType)
        previous_tile = None
        for tile in tile_row:
            tiles += 1
            if previous_row is None:
                if previous_tile is not None:
                    assert tile.col > previous_tile.col
            else:
                if previous_tile is not None:
                    assert tile.col > previous_tile.col
                    assert tile.row == previous_tile.row
                    assert tile.row > previous_row

            previous_tile = tile

        previous_row = tile.row

    assert tiles == len(list(tp.tiles_from_bounds(bounds, zoom)))


def test_tiles_from_bounds_batch_by_row_both_antimeridian_bounds():
    tp = TilePyramid("geodetic")
    bounds = (-185, 0, 185, 95)
    zoom = 8

    tiles = tp.tiles_from_bounds(bounds, zoom, batch_by="row")
    assert isinstance(tiles, GeneratorType)
    assert list(tiles)

    previous_row = None
    tiles = 0
    for tile_row in tp.tiles_from_bounds(bounds, zoom, batch_by="row"):
        assert isinstance(tile_row, GeneratorType)
        previous_tile = None
        for tile in tile_row:
            tiles += 1
            if previous_row is None:
                if previous_tile is not None:
                    assert tile.col == previous_tile.col + 1
            else:
                if previous_tile is not None:
                    assert tile.col == previous_tile.col + 1
                    assert tile.row == previous_tile.row
                    assert tile.row == previous_row + 1

            previous_tile = tile

        previous_row = tile.row

    assert tiles == len(list(tp.tiles_from_bounds(bounds, zoom)))


def test_tiles_from_geom_exact(tile_bounds_polygon):

    tp = TilePyramid("geodetic")
    zoom = 3

    tiles = len(list(tp.tiles_from_geom(tile_bounds_polygon, zoom)))
    assert tiles == 4
    tiles = 0
    for batch in tp.tiles_from_geom(tile_bounds_polygon, zoom, batch_by="row"):
        tiles += len(list(batch))
    assert tiles == 4

    exact_tiles = len(list(tp.tiles_from_geom(tile_bounds_polygon, zoom, exact=True)))
    assert exact_tiles == 3
    tiles = 0
    for batch in tp.tiles_from_geom(
        tile_bounds_polygon, zoom, batch_by="row", exact=True
    ):
        tiles += len(list(batch))
    assert tiles == 3


def test_snap_bounds():
    bounds = (0, 1, 2, 3)
    tp = TilePyramid("geodetic")
    zoom = 8

    snapped = snap_bounds(bounds=bounds, tile_pyramid=tp, zoom=zoom)
    control = unary_union(
        [tile.bbox() for tile in tp.tiles_from_bounds(bounds, zoom)]
    ).bounds
    assert snapped == control

    pixelbuffer = 10
    snapped = snap_bounds(
        bounds=bounds, tile_pyramid=tp, zoom=zoom, pixelbuffer=pixelbuffer
    )
    control = unary_union(
        [tile.bbox(pixelbuffer) for tile in tp.tiles_from_bounds(bounds, zoom)]
    ).bounds
    assert snapped == control


def test_deprecated():
    tp = TilePyramid("geodetic")
    assert tp.type
    assert tp.srid
    assert tp.tile_x_size(0)
    assert tp.tile_y_size(0)
    assert tp.tile_height(0)
    assert tp.tile_width(0)
