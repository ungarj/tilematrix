import click
import geojson
from shapely.geometry import box

import tilematrix
from tilematrix import TilePyramid


@click.version_option(version=tilematrix.__version__, message="%(version)s")
@click.group()
@click.option(
    "--pixelbuffer",
    "-p",
    nargs=1,
    type=click.INT,
    default=0,
    help="Tile bounding box buffer in pixels. (default: 0)",
)
@click.option(
    "--tile_size",
    "-s",
    nargs=1,
    type=click.INT,
    default=256,
    help="Tile size in pixels. (default: 256)",
)
@click.option(
    "--metatiling",
    "-m",
    nargs=1,
    type=click.INT,
    default=1,
    help="TilePyramid metatile size. (default: 1)",
)
@click.option(
    "--grid",
    "-g",
    type=click.Choice(["geodetic", "mercator"]),
    default="geodetic",
    help="TilePyramid base grid. (default: geodetic)",
)
@click.option(
    "--output_format",
    "-f",
    type=click.Choice(["Tile", "WKT", "GeoJSON"]),
    default="Tile",
    help="Print Tile ID or Tile bounding box as WKT or GeoJSON. (default: Tile)",
)
@click.pass_context
def tmx(ctx, **kwargs):
    ctx.obj = dict(**kwargs)


@tmx.command(short_help="Tile bounds.")
@click.argument("TILE", nargs=3, type=click.INT, required=True)
@click.pass_context
def bounds(ctx, tile):
    """Print Tile bounds."""
    click.echo(
        "%s %s %s %s"
        % TilePyramid(
            ctx.obj["grid"],
            tile_size=ctx.obj["tile_size"],
            metatiling=ctx.obj["metatiling"],
        )
        .tile(*tile)
        .bounds(pixelbuffer=ctx.obj["pixelbuffer"])
    )


@tmx.command(short_help="Tile bounding box.")
@click.argument("TILE", nargs=3, type=click.INT, required=True)
@click.pass_context
def bbox(ctx, tile):
    """Print Tile bounding box as geometry."""
    geom = (
        TilePyramid(
            ctx.obj["grid"],
            tile_size=ctx.obj["tile_size"],
            metatiling=ctx.obj["metatiling"],
        )
        .tile(*tile)
        .bbox(pixelbuffer=ctx.obj["pixelbuffer"])
    )
    if ctx.obj["output_format"] in ["WKT", "Tile"]:
        click.echo(geom)
    elif ctx.obj["output_format"] == "GeoJSON":
        click.echo(geojson.dumps(geom))


@tmx.command(short_help="Tile from point.")
@click.argument("ZOOM", nargs=1, type=click.INT, required=True)
@click.argument("POINT", nargs=2, type=click.FLOAT, required=True)
@click.pass_context
def tile(ctx, point, zoom):
    """Print Tile containing POINT.."""
    tile = TilePyramid(
        ctx.obj["grid"],
        tile_size=ctx.obj["tile_size"],
        metatiling=ctx.obj["metatiling"],
    ).tile_from_xy(*point, zoom=zoom)
    if ctx.obj["output_format"] == "Tile":
        click.echo("%s %s %s" % tile.id)
    elif ctx.obj["output_format"] == "WKT":
        click.echo(tile.bbox(pixelbuffer=ctx.obj["pixelbuffer"]))
    elif ctx.obj["output_format"] == "GeoJSON":
        click.echo(
            geojson.dumps(
                geojson.FeatureCollection(
                    [
                        geojson.Feature(
                            geometry=tile.bbox(pixelbuffer=ctx.obj["pixelbuffer"]),
                            properties=dict(zoom=tile.zoom, row=tile.row, col=tile.col),
                        )
                    ]
                )
            )
        )


@tmx.command(short_help="Tiles from bounds.")
@click.argument("ZOOM", nargs=1, type=click.INT, required=True)
@click.argument("BOUNDS", nargs=4, type=click.FLOAT, required=True)
@click.pass_context
def tiles(ctx, bounds, zoom):
    """Print Tiles from bounds."""
    tiles = TilePyramid(
        ctx.obj["grid"],
        tile_size=ctx.obj["tile_size"],
        metatiling=ctx.obj["metatiling"],
    ).tiles_from_bounds(bounds, zoom=zoom)
    if ctx.obj["output_format"] == "Tile":
        for tile in tiles:
            click.echo("%s %s %s" % tile.id)
    elif ctx.obj["output_format"] == "WKT":
        for tile in tiles:
            click.echo(tile.bbox(pixelbuffer=ctx.obj["pixelbuffer"]))
    elif ctx.obj["output_format"] == "GeoJSON":
        click.echo("{\n" '  "type": "FeatureCollection",\n' '  "features": [')
        # print tiles as they come and only add comma if there is a next tile
        try:
            tile = next(tiles)
            while True:
                gj = "    %s" % geojson.Feature(
                    geometry=tile.bbox(pixelbuffer=ctx.obj["pixelbuffer"]),
                    properties=dict(zoom=tile.zoom, row=tile.row, col=tile.col),
                )
                try:
                    tile = next(tiles)
                    click.echo(gj + ",")
                except StopIteration:
                    click.echo(gj)
                    raise
        except StopIteration:
            pass
        click.echo("  ]\n" "}")


@tmx.command(short_help="Snap bounds to tile grid.")
@click.argument("ZOOM", nargs=1, type=click.INT, required=True)
@click.argument("BOUNDS", nargs=4, type=click.FLOAT, required=True)
@click.pass_context
def snap_bounds(ctx, bounds, zoom):
    """nap bounds to tile grid."""
    click.echo(
        "%s %s %s %s"
        % tilematrix.snap_bounds(
            bounds=bounds,
            tile_pyramid=TilePyramid(
                ctx.obj["grid"],
                tile_size=ctx.obj["tile_size"],
                metatiling=ctx.obj["metatiling"],
            ),
            zoom=zoom,
            pixelbuffer=ctx.obj["pixelbuffer"],
        )
    )


@tmx.command(short_help="Snap bbox to tile grid.")
@click.argument("ZOOM", nargs=1, type=click.INT, required=True)
@click.argument("BOUNDS", nargs=4, type=click.FLOAT, required=True)
@click.pass_context
def snap_bbox(ctx, bounds, zoom):
    """Snap bbox to tile grid."""
    click.echo(
        box(
            *tilematrix.snap_bounds(
                bounds=bounds,
                tile_pyramid=TilePyramid(
                    ctx.obj["grid"],
                    tile_size=ctx.obj["tile_size"],
                    metatiling=ctx.obj["metatiling"],
                ),
                zoom=zoom,
                pixelbuffer=ctx.obj["pixelbuffer"],
            )
        )
    )
