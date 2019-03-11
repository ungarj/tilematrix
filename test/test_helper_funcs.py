import pytest
from rasterio.crs import CRS
from shapely.geometry import box

from tilematrix import clip_geometry_to_srs_bounds, TilePyramid, validate_zoom
from tilematrix._funcs import _verify_shape_bounds, _get_crs


def test_antimeridian_clip(invalid_geom):
    """Clip on antimeridian."""
    tp = TilePyramid("geodetic")
    tp_bounds = box(tp.left, tp.bottom, tp.right, tp.top)

    # extends on the western side
    geometry = box(-183.125, 67.5, -177.5, 73.125)
    # get GeometryCollection
    out_geom = clip_geometry_to_srs_bounds(geometry, tp)
    assert out_geom.geom_type == "GeometryCollection"
    # get list
    out_geom = clip_geometry_to_srs_bounds(geometry, tp, multipart=True)
    assert isinstance(out_geom, list)
    for sub_geom in out_geom:
        assert sub_geom.within(tp_bounds)

    # extends on the eastern side
    geometry = box(177.5, 67.5, 183.125, 73.125)
    # get GeometryCollection
    out_geom = clip_geometry_to_srs_bounds(geometry, tp)
    assert out_geom.geom_type == "GeometryCollection"
    # get list
    out_geom = clip_geometry_to_srs_bounds(geometry, tp, multipart=True)
    assert isinstance(out_geom, list)
    for sub_geom in out_geom:
        assert sub_geom.within(tp_bounds)

    # extends on both sides
    geometry = box(-183.125, 67.5, 183.125, 73.125)
    # get GeometryCollection
    out_geom = clip_geometry_to_srs_bounds(geometry, tp)
    assert out_geom.geom_type == "GeometryCollection"
    # get list
    out_geom = clip_geometry_to_srs_bounds(geometry, tp, multipart=True)
    assert isinstance(out_geom, list)
    for sub_geom in out_geom:
        assert sub_geom.within(tp_bounds)
    assert len(out_geom) == 3

    # fail on invalid geometry
    with pytest.raises(ValueError):
        clip_geometry_to_srs_bounds(invalid_geom, tp)


def test_no_clip():
    """Geometry is within TilePyramid bounds."""
    tp = TilePyramid("geodetic")
    geometry = box(177.5, 67.5, -177.5, 73.125)

    # no multipart
    out_geom = clip_geometry_to_srs_bounds(geometry, tp)
    assert geometry == out_geom

    # multipart
    out_geom = clip_geometry_to_srs_bounds(geometry, tp, multipart=True)
    assert isinstance(out_geom, list)
    assert len(out_geom) == 1
    assert geometry == out_geom[0]


def test_validate_zoom():
    with pytest.raises(TypeError):
        validate_zoom(5.0)
    with pytest.raises(ValueError):
        validate_zoom(-1)


def test_verify_shape_bounds():
    # invalid shape
    with pytest.raises(TypeError):
        _verify_shape_bounds((1, 2, 3), (1, 2, 3, 4))
    # invalid bounds
    with pytest.raises(TypeError):
        _verify_shape_bounds((1, 2), (1, 2, 3, 4, 5))

    _verify_shape_bounds((2, 1), (1, 2, 3, 6))


def test_get_crs(proj, wkt):
    # no dictionary
    with pytest.raises(TypeError):
        _get_crs("no dict")
    # valid WKT
    assert isinstance(_get_crs(dict(wkt=wkt)), CRS)
    # valid EPSG
    assert isinstance(_get_crs(dict(epsg=3857)), CRS)
    # valid PROJ
    assert isinstance(_get_crs(dict(proj=proj)), CRS)
    # none of above
    with pytest.raises(TypeError):
        _get_crs(dict(something_else=None))
