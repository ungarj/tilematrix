from click.testing import CliRunner
import geojson
from shapely import wkt
from shapely.geometry import shape

from tilematrix import __version__, TilePyramid
from tilematrix.tmx.main import tmx


def test_version():
    result = CliRunner().invoke(tmx, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_bounds():
    zoom, row, col = 12, 0, 0
    for grid in ["geodetic", "mercator"]:
        _run_bbox_bounds(zoom, row, col, "bounds", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_bbox_bounds(zoom, row, col, "bounds", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_bbox_bounds(zoom, row, col, "bounds", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_bbox_bounds(zoom, row, col, "bounds", tile_size=tile_size)


def test_bbox():
    zoom, row, col = 12, 0, 0
    for grid in ["geodetic", "mercator"]:
        _run_bbox_bounds(zoom, row, col, "bbox", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_bbox_bounds(zoom, row, col, "bbox", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_bbox_bounds(zoom, row, col, "bbox", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_bbox_bounds(zoom, row, col, "bbox", tile_size=tile_size)
    for output_format in ["WKT", "GeoJSON"]:
        _run_bbox_bounds(zoom, row, col, "bbox", output_format=output_format)


def test_tile():
    point = [10, 20]
    zoom = 5
    for grid in ["geodetic", "mercator"]:
        _run_tile(zoom, point, grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_tile(zoom, point, metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_tile(zoom, point, pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_tile(zoom, point, tile_size=tile_size)
    for output_format in ["Tile", "WKT", "GeoJSON"]:
        _run_tile(zoom, point, output_format=output_format)


def test_tiles():
    bounds = (10, 20, 30, 40)
    zoom = 6
    for grid in ["geodetic", "mercator"]:
        _run_tiles(zoom, bounds, grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_tiles(zoom, bounds, metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_tiles(zoom, bounds, pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_tiles(zoom, bounds, tile_size=tile_size)
    for output_format in ["Tile", "WKT", "GeoJSON"]:
        _run_tiles(zoom, bounds, output_format=output_format)


def test_snap_bounds():
    zoom = 6
    bounds = (10, 20, 30, 40)
    for grid in ["geodetic", "mercator"]:
        _run_snap_bounds(zoom, bounds, "snap-bounds", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_snap_bounds(zoom, bounds, "snap-bounds", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_snap_bounds(zoom, bounds, "snap-bounds", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_snap_bounds(zoom, bounds, "snap-bounds", tile_size=tile_size)


def test_snap_bbox():
    zoom = 6
    bounds = (10, 20, 30, 40)
    for grid in ["geodetic", "mercator"]:
        _run_snap_bounds(zoom, bounds, "snap-bbox", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _run_snap_bounds(zoom, bounds, "snap-bbox", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _run_snap_bounds(zoom, bounds, "snap-bbox", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _run_snap_bounds(zoom, bounds, "snap-bbox", tile_size=tile_size)


def _run_bbox_bounds(
    zoom, row, col, command=None, grid="geodetic", metatiling=1, pixelbuffer=0,
    tile_size=256, output_format="WKT"
):
    tile = TilePyramid(
        grid,
        metatiling=metatiling,
        tile_size=tile_size
    ).tile(zoom, row, col)
    result = CliRunner().invoke(tmx, [
        "--pixelbuffer", str(pixelbuffer),
        "--metatiling", str(metatiling),
        "--grid", grid,
        "--tile_size", str(tile_size),
        "--output_format", output_format,
        command, str(zoom), str(row), str(col)
    ])
    assert result.exit_code == 0
    if command == "bounds":
        assert result.output.strip() == " ".join(map(str, tile.bounds(pixelbuffer)))
    elif output_format == "WKT":
        assert wkt.loads(result.output.strip()).almost_equals(tile.bbox(pixelbuffer))
    elif output_format == "GeoJSON":
        assert shape(
            geojson.loads(result.output.strip())
        ).almost_equals(tile.bbox(pixelbuffer))


def _run_tile(
    zoom, point, grid="geodetic", metatiling=1, pixelbuffer=0, tile_size=256,
    output_format="WKT"
):
    x, y, = point
    tile = TilePyramid(
        grid,
        metatiling=metatiling,
        tile_size=tile_size
    ).tile_from_xy(x, y, zoom)
    result = CliRunner().invoke(tmx, [
        "--pixelbuffer", str(pixelbuffer),
        "--metatiling", str(metatiling),
        "--grid", grid,
        "--tile_size", str(tile_size),
        "--output_format", output_format,
        "tile", str(zoom), str(x), str(y)
    ])
    assert result.exit_code == 0
    if output_format == "Tile":
        assert result.output.strip() == " ".join(map(str, tile.id))
    elif output_format == "WKT":
        assert wkt.loads(result.output.strip()).almost_equals(tile.bbox(pixelbuffer))
    elif output_format == "GeoJSON":
        feature = geojson.loads(result.output.strip())["features"][0]
        assert shape(feature["geometry"]).almost_equals(tile.bbox(pixelbuffer))


def _run_tiles(
    zoom, bounds, grid="geodetic", metatiling=1, pixelbuffer=0, tile_size=256,
    output_format="WKT"
):
    left, bottom, right, top = bounds
    tiles = list(
        TilePyramid(
            grid,
            metatiling=metatiling,
            tile_size=tile_size
        ).tiles_from_bounds(bounds, zoom)
    )
    result = CliRunner().invoke(tmx, [
        "--pixelbuffer", str(pixelbuffer),
        "--metatiling", str(metatiling),
        "--grid", grid,
        "--tile_size", str(tile_size),
        "--output_format", output_format,
        "tiles", str(zoom), str(left), str(bottom), str(right), str(top)
    ])
    assert result.exit_code == 0
    if output_format == "Tile":
        assert result.output.count('\n') == len(tiles)
    elif output_format == "WKT":
        assert result.output.count('\n') == len(tiles)
    elif output_format == "GeoJSON":
        features = geojson.loads(result.output.strip())["features"]
        assert len(features) == len(tiles)


def _run_snap_bounds(
    zoom, bounds, command=None, grid="geodetic", metatiling=1, pixelbuffer=0,
    tile_size=256
):
    left, bottom, right, top = bounds
    result = CliRunner().invoke(tmx, [
        "--pixelbuffer", str(pixelbuffer),
        "--metatiling", str(metatiling),
        "--grid", grid,
        "--tile_size", str(tile_size),
        command, str(zoom), str(left), str(bottom), str(right), str(top)
    ])
    assert result.exit_code == 0
