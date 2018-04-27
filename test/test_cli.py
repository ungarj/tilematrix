from tilematrix import __version__, TilePyramid
from tilematrix.tmx.main import tmx

from click.testing import CliRunner


def test_version():
    result = CliRunner().invoke(tmx, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_bounds():
    zoom, row, col = 12, 0, 0
    for grid in ["geodetic", "mercator"]:
        _cli_tile(zoom, row, col, "bounds", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _cli_tile(zoom, row, col, "bounds", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _cli_tile(zoom, row, col, "bounds", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _cli_tile(zoom, row, col, "bounds", tile_size=tile_size)


def test_bbox():
    zoom, row, col = 12, 0, 0
    for grid in ["geodetic", "mercator"]:
        _cli_tile(zoom, row, col, "bbox", grid=grid)
    for metatiling in [1, 2, 4, 8, 16]:
        _cli_tile(zoom, row, col, "bbox", metatiling=metatiling)
    for pixelbuffer in [0, 1, 10]:
        _cli_tile(zoom, row, col, "bbox", pixelbuffer=pixelbuffer)
    for tile_size in [256, 512, 1024]:
        _cli_tile(zoom, row, col, "bbox", tile_size=tile_size)


def _cli_tile(
    zoom, row, col, command=None, grid="geodetic", metatiling=1, pixelbuffer=0,
    tile_size=256
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
        command, str(zoom), str(row), str(col)
    ])
    assert result.exit_code == 0
    if command == "bounds":
        validation = " ".join(map(str, tile.bounds(pixelbuffer)))
    else:
        validation = str(tile.bbox(pixelbuffer))
    assert result.output.strip() == validation
