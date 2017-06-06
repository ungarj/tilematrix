#!/usr/bin/env python
"""TilePyramid creation."""

from shapely.geometry import box

from tilematrix import clip_geometry_to_srs_bounds, TilePyramid


def test_antimeridian_clip():
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


def test_no_clip():
    """Geometry is within TilePyramid bounds."""
    tp = TilePyramid("geodetic")
    tp_bounds = box(tp.left, tp.bottom, tp.right, tp.top)
    geometry = box(177.5, 67.5, -177.5, 73.125)

    # no multipart
    out_geom = clip_geometry_to_srs_bounds(geometry, tp)
    assert geometry == out_geom

    # multipart
    out_geom = clip_geometry_to_srs_bounds(geometry, tp, multipart=True)
    assert isinstance(out_geom, list)
    assert len(out_geom) == 1
    assert geometry == out_geom[0]
