#!/usr/bin/env python
"""Tile geometries and tiles from geometries."""

from shapely.geometry import Polygon, shape

from tilematrix import TilePyramid


def test_top_left_coord():
    """Top left coordinate."""
    tp = TilePyramid("geodetic")
    tile = tp.tile(5, 3, 3)
    assert (tile.left, tile.top) == (-163.125, 73.125)


def test_tile_bbox():
    """Tile bounding box."""
    tp = TilePyramid("geodetic")
    tile = tp.tile(5, 3, 3)
    testpolygon = Polygon([
        [-163.125, 73.125], [-157.5, 73.125], [-157.5, 67.5], [-163.125, 67.5],
        [-163.125, 73.125]
    ])
    assert tile.bbox().equals(testpolygon)


def test_tile_bbox_buffer():
    """Tile bounding box with buffer."""
    tp = TilePyramid("geodetic")
    tile = tp.tile(5, 3, 3)
    testpolygon = Polygon([
        [-163.14697265625, 73.14697265625], [-157.47802734375, 73.14697265625],
        [-157.47802734375, 67.47802734375], [-163.14697265625, 67.47802734375],
        [-163.14697265625, 73.14697265625]
    ])
    assert tile.bbox(1).equals(testpolygon)


def test_tile_bounds():
    """Tile bounds."""
    tp = TilePyramid("geodetic")
    tile = tp.tile(5, 3, 3)
    assert tile.bounds() == (-163.125, 67.5, -157.5, 73.125)


def test_tile_bounds_buffer():
    """Tile bounds with buffer."""
    tp = TilePyramid("geodetic")
    tile = tp.tile(5, 3, 3)
    testbounds = (
        -163.14697265625, 67.47802734375, -157.47802734375, 73.14697265625
    )
    assert tile.bounds(1) == testbounds


def test_tiles_from_bounds():
    """Get tiles intersecting with given bounds."""
    tp = TilePyramid("geodetic")
    # valid bounds
    bounds = (-163.125, 67.5, -157.5, 73.125)
    control_tiles = {(5, 3, 3)}
    test_tiles = {tile.id for tile in tp.tiles_from_bounds(bounds, 5)}
    assert control_tiles == test_tiles
    # invalid bounds
    try:
        {tile.id for tile in tp.tiles_from_bounds((3, 5), 5)}
        raise Exception()
    except ValueError:
        pass
    # crossing the antimeridian
    bounds = (-183.125, 67.5, -177.5, 73.125)
    control_tiles = {(5, 3, 0), (5, 3, 63)}
    test_tiles = {tile.id for tile in tp.tiles_from_bounds(bounds, 5)}
    print len(test_tiles)
    assert control_tiles == test_tiles


def test_tiles_from_bbox():
    """Get tiles intersecting with bounding box."""
    test_bbox = shape({
        'type': 'Polygon', 'coordinates': [[
            (5.625, 61.875), (56.25, 61.875), (56.25, 28.125), (5.625, 28.125),
            (5.625, 28.125), (5.625, 61.875)
        ]]
    })
    test_tiles = {
        (5, 5, 33), (5, 6, 33), (5, 7, 33), (5, 8, 33), (5, 9, 33),
        (5, 10, 33), (5, 5, 34), (5, 6, 34), (5, 7, 34), (5, 8, 34),
        (5, 9, 34), (5, 10, 34), (5, 5, 35), (5, 6, 35), (5, 7, 35),
        (5, 8, 35), (5, 9, 35), (5, 10, 35), (5, 5, 36), (5, 6, 36),
        (5, 7, 36), (5, 8, 36), (5, 9, 36), (5, 10, 36), (5, 5, 37),
        (5, 6, 37), (5, 7, 37), (5, 8, 37), (5, 9, 37), (5, 10, 37),
        (5, 5, 38), (5, 6, 38), (5, 7, 38), (5, 8, 38), (5, 9, 38),
        (5, 10, 38), (5, 5, 39), (5, 6, 39), (5, 7, 39), (5, 8, 39),
        (5, 9, 39), (5, 10, 39), (5, 5, 40), (5, 6, 40), (5, 7, 40),
        (5, 8, 40), (5, 9, 40), (5, 10, 40), (5, 5, 41), (5, 6, 41),
        (5, 7, 41), (5, 8, 41), (5, 9, 41), (5, 10, 41)
    }
    tp = TilePyramid("geodetic")
    bbox_tiles = {tile.id for tile in tp.tiles_from_bbox(test_bbox, 5)}
    assert len(test_tiles) == len(bbox_tiles)
    for tile in test_tiles:
        assert tile in bbox_tiles
    for tile in bbox_tiles:
        assert tile in test_tiles


def test_tiles_from_point():
    """Get tile from point."""
    test_point = shape({
        'type': 'Point', 'coordinates': (16.364693096743736, 48.20196113681686)
    })
    test_tile = [(6, 14, 69)]
    tp = TilePyramid("geodetic")
    point_tile = [tile.id for tile in tp.tiles_from_geom(test_point, 6)]
    assert point_tile == test_tile


def test_tiles_from_multipoint():
    """Get tiles from multiple points."""
    test_multipoint = shape({
        'type': 'MultiPoint', 'coordinates': [
            (14.464033917048539, 50.08528287347832),
            (16.364693096743736, 48.20196113681686)
        ]
    })
    test_tiles = {(9, 113, 553), (9, 118, 558)}
    tp = TilePyramid("geodetic")
    multipoint_tiles = {
        tile.id for tile in tp.tiles_from_geom(test_multipoint, 9)
    }
    assert multipoint_tiles == test_tiles


def test_tiles_from_linestring():
    """Get tiles from LineString."""
    test_linestring = shape({
        'type': 'LineString',
        'coordinates': [
            (8.219788038779399, 48.04680919045518),
            (8.553359409223447, 47.98081838641845),
            (9.41408206547689, 48.13835399026023),
            (10.71989383306024, 48.64871043557477),
            (11.683555942439085, 48.794127916044104),
            (12.032991977596737, 49.02749868427421)
        ]
    })
    test_tiles = {
        (8, 58, 270), (8, 58, 271), (8, 58, 272), (8, 58, 273), (8, 59, 267),
        (8, 59, 268), (8, 59, 269), (8, 59, 270)
    }
    tp = TilePyramid("geodetic")
    linestring_tiles = {
        tile.id for tile in tp.tiles_from_geom(test_linestring, 8)
    }
    assert linestring_tiles == test_tiles


def test_tiles_from_multilinestring():
    """Get tiles from MultiLineString."""
    test_multilinestring = shape({
        'type': 'MultiLineString',
        'coordinates': [
            [
                (8.219788038779399, 48.04680919045518),
                (8.553359409223447, 47.98081838641845),
                (9.41408206547689, 48.13835399026023),
                (10.71989383306024, 48.64871043557477),
                (11.683555942439085, 48.794127916044104),
                (12.032991977596737, 49.02749868427421)
            ], [
                (33.206893344868945, 0.261534735511418),
                (33.18725630059802, 0.428191229652711),
                (32.8931140479927, 1.31144481038541),
                (32.80150465264725, 1.366544806316611),
                (32.62475833510098, 1.471712805584616),
                (32.51003665541302, 1.536754055177965),
                (32.36248752211165, 1.606878973798047)
            ]
        ]
    })
    test_tiles = {
        (8, 58, 270), (8, 58, 271), (8, 58, 272), (8, 58, 273), (8, 59, 267),
        (8, 59, 268), (8, 59, 269), (8, 59, 270), (8, 125, 302), (8, 126, 302),
        (8, 126, 303), (8, 127, 303)
    }
    tp = TilePyramid("geodetic")
    multilinestring_tiles = {
        tile.id for tile in tp.tiles_from_geom(test_multilinestring, 8)
    }
    assert multilinestring_tiles == test_tiles


def test_tiles_from_polygon():
    """Get tiles from Polygon."""
    test_polygon = shape({
        'type': 'Polygon',
        'coordinates': [
            [
                (8.219788038779399, 48.04680919045518),
                (8.553359409223447, 47.98081838641845),
                (9.41408206547689, 48.13835399026023),
                (10.71989383306024, 48.64871043557477),
                (11.683555942439085, 48.794127916044104),
                (12.032991977596737, 49.02749868427421),
                (8.219788038779399, 48.04680919045518),
            ]
        ]
    })
    test_tiles = {
        (9, 116, 544), (9, 116, 545), (9, 116, 546), (9, 117, 540),
        (9, 117, 541), (9, 117, 542), (9, 117, 543), (9, 117, 544),
        (9, 117, 545), (9, 118, 536), (9, 118, 537), (9, 118, 538),
        (9, 118, 539), (9, 118, 540), (9, 118, 541), (9, 119, 535),
        (9, 119, 536), (9, 119, 537), (9, 119, 538)
    }
    tp = TilePyramid("geodetic")
    polygon_tiles = {
        tile.id for tile in tp.tiles_from_geom(test_polygon, 9)
    }
    assert polygon_tiles == test_tiles


def test_tiles_from_multipolygon():
    """Get tiles from MultiPolygon."""
    test_multipolygon = shape({
        'type': 'MultiPolygon',
        'coordinates': [
            [[
                (8.219788038779399, 48.04680919045518),
                (8.553359409223447, 47.98081838641845),
                (9.41408206547689, 48.13835399026023),
                (10.71989383306024, 48.64871043557477),
                (11.683555942439085, 48.794127916044104),
                (12.032991977596737, 49.02749868427421)
            ]], [[
                (33.206893344868945, 0.261534735511418),
                (33.18725630059802, 0.428191229652711),
                (32.8931140479927, 1.31144481038541),
                (32.80150465264725, 1.366544806316611),
                (32.62475833510098, 1.471712805584616),
                (32.51003665541302, 1.536754055177965),
                (32.36248752211165, 1.606878973798047)
            ]]
        ]
    })
    test_tiles = {
        (9, 116, 544), (9, 116, 545), (9, 116, 546), (9, 117, 540),
        (9, 117, 541), (9, 117, 542), (9, 117, 543), (9, 117, 544),
        (9, 117, 545), (9, 118, 536), (9, 118, 537), (9, 118, 538),
        (9, 118, 539), (9, 118, 540), (9, 118, 541), (9, 119, 535),
        (9, 119, 536), (9, 119, 537), (9, 119, 538), (9, 251, 604),
        (9, 251, 605), (9, 252, 604), (9, 252, 605), (9, 253, 605),
        (9, 253, 606), (9, 254, 605), (9, 254, 606), (9, 255, 606)
    }
    tp = TilePyramid("geodetic")
    multipolygon_tiles = {
        tile.id for tile in tp.tiles_from_geom(test_multipolygon, 9)
    }
    assert multipolygon_tiles == test_tiles
