from tilematrix import TilePyramid


def test_geodetic():
    tp = TilePyramid("geodetic", metatiling=2)
    tp_dict = tp.to_dict()
    assert isinstance(tp_dict, dict)
    tp2 = TilePyramid.from_dict(tp_dict)
    assert tp == tp2


def test_mercator():
    tp = TilePyramid("mercator", metatiling=4)
    tp_dict = tp.to_dict()
    assert isinstance(tp_dict, dict)
    tp2 = TilePyramid.from_dict(tp_dict)
    assert tp == tp2


def test_custom(grid_definition_proj, grid_definition_epsg):
    for grid_def in [grid_definition_proj, grid_definition_epsg]:
        tp = TilePyramid(grid_def, metatiling=8)
        tp_dict = tp.to_dict()
        assert isinstance(tp_dict, dict)
        tp2 = TilePyramid.from_dict(tp_dict)
        assert tp == tp2
