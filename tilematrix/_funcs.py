"""Helper functions."""

from itertools import product, chain
from rasterio.crs import CRS
from shapely.geometry import Point, Polygon, GeometryCollection, box
from shapely.affinity import translate

from tilematrix._conf import DELTA, ROUND
from tilematrix._utm_coefs import *
from tilematrix._types import Bounds, Shape
from tilematrix._exceptions import OutOfRangeError
from tilematrix._utm import stripe_id_from_point


def validate_zoom(zoom):
    if not isinstance(zoom, int):
        raise TypeError("zoom must be an integer")
    if zoom < 0:
        raise ValueError("zoom must be greater or equal 0")


def clip_geometry_to_srs_bounds(geometry, pyramid, multipart=False):
    """
    Clip input geometry to SRS bounds of given TilePyramid.

    If geometry passes the antimeridian, it will be split up in a multipart
    geometry and shifted to within the SRS boundaries.
    Note: geometry SRS must be the TilePyramid SRS!

    - geometry: any shapely geometry
    - pyramid: a TilePyramid object
    - multipart: return list of geometries instead of a GeometryCollection
    """
    if not geometry.is_valid:
        raise ValueError("invalid geometry given")
    pyramid_bbox = box(*pyramid.bounds)

    # Special case for global tile pyramids if geometry extends over tile
    # pyramid boundaries (such as the antimeridian).
    if pyramid.is_global and not geometry.within(pyramid_bbox):
        inside_geom = geometry.intersection(pyramid_bbox)
        outside_geom = geometry.difference(pyramid_bbox)
        # shift outside geometry so it lies within SRS bounds
        if isinstance(outside_geom, Polygon):
            outside_geom = [outside_geom]
        all_geoms = [inside_geom]
        for geom in outside_geom:
            geom_bounds = Bounds(*geom.bounds)
            if geom_bounds.left < pyramid.left:
                geom = translate(geom, xoff=2*pyramid.right)
            elif geom_bounds.right > pyramid.right:
                geom = translate(geom, xoff=-2*pyramid.right)
            all_geoms.append(geom)
        if multipart:
            return all_geoms
        else:
            return GeometryCollection(all_geoms)

    else:
        if multipart:
            return [geometry]
        else:
            return geometry


def snap_bounds(bounds=None, tile_pyramid=None, zoom=None, pixelbuffer=0):
    """
    Extend bounds to be aligned with union of tile bboxes.

    - bounds: (left, bottom, right, top)
    - tile_pyramid: a TilePyramid object
    - zoom: target zoom level
    - pixelbuffer: apply pixelbuffer
    """
    bounds = Bounds(*bounds)
    validate_zoom(zoom)
    lb = _tile_from_xy(tile_pyramid, bounds.left, bounds.bottom, zoom, on_edge_use="rt")
    rt = _tile_from_xy(tile_pyramid, bounds.right, bounds.top, zoom, on_edge_use="lb")
    left, bottom, _, _ = lb.bounds(pixelbuffer)
    _, _, right, top = rt.bounds(pixelbuffer)
    return Bounds(left, bottom, right, top)


def _verify_shape_bounds(shape, bounds):
    """Verify that shape corresponds to bounds apect ratio."""
    if not isinstance(shape, (tuple, list)) or len(shape) != 2:
        raise TypeError(
            "shape must be a tuple or list with two elements: %s" % str(shape)
        )
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 4:
        raise TypeError(
            "bounds must be a tuple or list with four elements: %s" % str(bounds)
        )
    shape = Shape(*shape)
    bounds = Bounds(*bounds)
    shape_ratio = shape.width / shape.height
    bounds_ratio = (bounds.right - bounds.left) / (bounds.top - bounds.bottom)
    if abs(shape_ratio - bounds_ratio) > DELTA:
        min_length = min([
            (bounds.right - bounds.left) / shape.width,
            (bounds.top - bounds.bottom) / shape.height
        ])
        proposed_bounds = Bounds(
            bounds.left,
            bounds.bottom,
            bounds.left + shape.width * min_length,
            bounds.bottom + shape.height * min_length
        )
        raise ValueError(
            "shape ratio (%s) must equal bounds ratio (%s); try %s" % (
                shape_ratio, bounds_ratio, proposed_bounds
            )
        )


def _get_crs(srs):
    if not isinstance(srs, dict):
        raise TypeError("'srs' must be a dictionary")
    if "wkt" in srs:
        return CRS().from_wkt(srs["wkt"])
    elif "epsg" in srs:
        return CRS().from_epsg(srs["epsg"])
    elif "proj" in srs:
        return CRS().from_string(srs["proj"])
    else:
        raise TypeError("provide either 'wkt', 'epsg' or 'proj' definition")


def _tile_intersecting_tilepyramid(tile, tp):
    """Return all tiles from tilepyramid intersecting with tile."""
    if tile.tp.grid != tp.grid:
        raise ValueError("Tile and TilePyramid source grids must be the same.")
    tile_metatiling = tile.tile_pyramid.metatiling
    pyramid_metatiling = tp.metatiling
    multiplier = tile_metatiling / pyramid_metatiling
    if tile_metatiling > pyramid_metatiling:
        return [
            tp.tile(
                tile.zoom,
                int(multiplier) * tile.row + row_offset,
                int(multiplier) * tile.col + col_offset
            )
            for row_offset, col_offset in product(
                range(int(multiplier)), range(int(multiplier))
            )
        ]
    elif tile_metatiling < pyramid_metatiling:
        return [tp.tile(
            tile.zoom, int(multiplier * tile.row), int(multiplier * tile.col)
        )]
    else:
        return [tp.tile(*tile.id)]


def _global_tiles_from_bounds(tp, bounds, zoom):
    """Return also Tiles if bounds cross the antimeridian."""
    seen = set()

    # clip to tilepyramid top and bottom bounds
    left, right = bounds.left, bounds.right
    top = tp.top if bounds.top > tp.top else bounds.top
    bottom = tp.bottom if bounds.bottom < tp.bottom else bounds.bottom

    if left >= tp.left and right <= tp.right:
        for tile in _tiles_from_cleaned_bounds(tp, bounds, zoom):
            yield tile

    # bounds overlap on the Western side with antimeridian
    if left < tp.left:
        for tile in chain(
            # tiles west of antimeridian
            _tiles_from_cleaned_bounds(
                tp,
                Bounds(left + (tp.right - tp.left), bottom, tp.right, top),
                zoom
            ),
            # tiles east of antimeridian
            _tiles_from_cleaned_bounds(
                tp, Bounds(tp.left, bottom, right, top), zoom
            )
        ):
            # make output tiles unique
            if tile.id not in seen:
                seen.add(tile.id)
                yield tile

    # bounds overlap on the Eastern side with antimeridian
    if right > tp.right:
        for tile in chain(
            # tiles west of antimeridian
            _tiles_from_cleaned_bounds(
                tp, Bounds(left, bottom, tp.right, top), zoom
            ),
            # tiles east of antimeridian
            _tiles_from_cleaned_bounds(
                tp,
                Bounds(tp.left, bottom, right - (tp.right - tp.left), top),
                zoom
            )
        ):
            # make output tiles unique
            if tile.id not in seen:
                seen.add(tile.id)
                yield tile


def _tiles_from_cleaned_bounds(tp, bounds, zoom):
    """Return all tiles intersecting with bounds."""
    lb = _tile_from_xy(tp, bounds.left, bounds.bottom, zoom, on_edge_use="rt")
    rt = _tile_from_xy(tp, bounds.right, bounds.top, zoom, on_edge_use="lb")
    for tile_id in product([zoom], range(rt.row, lb.row + 1), range(lb.col, rt.col + 1)):
        yield tp.tile(*tile_id)


def _tile_from_xy(tp, x, y, zoom, on_edge_use="rb"):
    # determine row
    tile_y_size = round(tp.pixel_y_size(zoom) * tp.tile_size * tp.metatiling, ROUND)
    row = int((tp.top - y) / tile_y_size)
    if on_edge_use in ["rt", "lt"] and (tp.top - y) % tile_y_size == 0.:
        row -= 1

    # determine column
    tile_x_size = round(tp.pixel_x_size(zoom) * tp.tile_size * tp.metatiling, ROUND)
    col = int((x - tp.left) / tile_x_size)
    if on_edge_use in ["lb", "lt"] and (x - tp.left) % tile_x_size == 0.:
        col -= 1

    # handle Antimeridian wrapping
    if tp.is_global:
        # left side
        if col == -1:
            col = tp.matrix_width(zoom) - 1
        # right side
        elif col >= tp.matrix_width(zoom):
            col = col % tp.matrix_width(zoom)

    try:
        return tp.tile(zoom, row, col)
    except ValueError as e:
        raise ValueError(
                "on_edge_use '%s' results in an invalid tile: %s" % (on_edge_use, e)
            )


def mod_angle(value):
    """Returns angle in radians to be between -pi and pi"""
    return (value + math.pi) % (2 * math.pi) - math.pi


def in_bounds(x, lower, upper, upper_strict=False):
    return lower <= x < upper


def check_valid_zone(zone_number, zone_letter):
    if not 1 <= zone_number <= 60:
        raise OutOfRangeError(
            'zone number out of range (must be between 1 and 60)'
        )

    if zone_letter:
        zone_letter = zone_letter.upper()

        if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            raise OutOfRangeError(
                'zone letter out of range (must be between C and X)'
            )


def latlon_to_utm(
        latitude,
        longitude
):
    """This function converts Latitude and Longitude to UTM coordinate
        Parameters
        ----------
        latitude: float or NumPy array
            Latitude between 80 deg S and 84 deg N, e.g. (-80.0 to 84.0)
        longitude: float or NumPy array
            Longitude between 180 deg W and 180 deg E, e.g. (-180.0 to 180.0).
        Returns
        -------
        easting: float or NumPy array
            Easting value of UTM coordinates
        northing: float or NumPy array
            Northing value of UTM coordinates
    """
    if not in_bounds(latitude, -80, 84):
        raise OutOfRangeError(
            'latitude out of range (must be between 80 deg S and 84 deg N)'
        )
    if not in_bounds(longitude, -180, 180):
        raise OutOfRangeError(
            'longitude out of range (must be between 180 deg W and 180 deg E)'
        )

    lat_rad = math.radians(latitude)
    lat_sin = math.sin(lat_rad)
    lat_cos = math.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    zone_number = int(stripe_id_from_point(Point(longitude, latitude))[:2])

    lon_rad = math.radians(longitude)
    central_lon = (zone_number - 1) * 6 - 180 + 3
    central_lon_rad = math.radians(central_lon)

    n = R / math.sqrt(1 - E * lat_sin**2)
    c = E_P2 * lat_cos**2

    a = lat_cos * mod_angle(lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * math.sin(2 * lat_rad) +
             M3 * math.sin(4 * lat_rad) -
             M4 * math.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if latitude <= 0:
        northing += 10000000

    return easting, northing
