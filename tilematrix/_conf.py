"""Package configuration parameters."""

from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info


# round coordinates
ROUND = 20

# bounds ratio vs shape ratio uncertainty
DELTA = 1e-6

# UTM default EOX settings
FIRST_UTM_STRIPE = 32600
LAST_UTM_STRIPE = 60

# Grid with width (x-dif) of 1310720 and height (y-dif) of 10485760
# This leads to exactly 10[m] grid at zoom 9 and shape at z0 8 high and 1 wide
UTM_STRIPE_SHAPE = (8, 1)
UTM_STRIPE_NORTH_BOUNDS = [166021.4431, 0.0000, 1476741.4431, 10485760]
UTM_STRIPE_SOUTH_BOUNDS = [441867.78, -485760.00, 1752587.78, 10000000.00]

# CAREFUL IRREGULAR GRIDS below
# Analog logic for S2 grid but the origin is shifted to match the S2 grid
# and the TileMatrix Definition is defined to be divisible by 60, 20 and 10
# width 1966080 to be divisible by 60, 20 and 10 and has 10[m] resolution
# height 15728640 to be divisible by 60, 20 and 10 and has 10[m] resolution
# S2 originally intended pyramid bounds [99960.00, 0.0000, 834000.00, 9000000]
# Tile size is 384x384[px]
# For the 60[m] grid the max/optimal zoom level is 7
# For the 10[m] and 20[m] grid the optimal zoom level is 9 and 8 respectively
UTM_STRIPE_S2_GRID_NORTH_BOUNDS = [
    99960.00, 0.0000, 99960 + 1966080, 15728640
]
UTM_STRIPE_S2_GRID_SOUTH_BOUNDS = [
    99960.00, -5728640, 99960 + 1966080, 10000000.00
]
UTM_S2_10M_GRID_TILE_SIZE = 384
UTM_S2_60M_GRID_TILE_SIZE = 256


def _get_utm_crs_list_from_bounds(
        bounds=(-180., -90., 180., 90.),
        datum_name="WGS 84"
):
    out_utm_epsg_list = []
    utm_pyproj_crs_list = query_utm_crs_info(
        datum_name=datum_name,
        area_of_interest=AreaOfInterest(
            west_lon_degree=bounds[0],
            south_lat_degree=bounds[1],
            east_lon_degree=bounds[2],
            north_lat_degree=bounds[3],
        )
    )
    for c in utm_pyproj_crs_list:
        out_utm_epsg_list.append(c.code)
    return out_utm_epsg_list


def _get_utm_pyramid_config(
        crs_epsg,
        utm_stripe_shape=UTM_STRIPE_SHAPE
):
    if crs_epsg.startswith("327"):
        grid_bounds = UTM_STRIPE_SOUTH_BOUNDS
    else:
        grid_bounds = UTM_STRIPE_NORTH_BOUNDS
    out_utm_config_dict = {}
    out_utm_config_dict[str(crs_epsg)] = {
        'shape': utm_stripe_shape,
        'bounds': grid_bounds,
        'srs': {"epsg": crs_epsg},
        'is_global': False,
        'tile_size': 256
    }
    return out_utm_config_dict


def _get_utm_pyramid_configs(bounds=[-180, -90, 180, 90]):
    out_dict = {}
    utm_epsg_list = _get_utm_crs_list_from_bounds(
        bounds=bounds
    )
    for utm_epsg in utm_epsg_list:
        out_dict.update(
            _get_utm_pyramid_config(crs_epsg=utm_epsg)
        )
    return out_dict


# supported pyramid types
PYRAMID_PARAMS = {
    "geodetic": {
        "shape": (1, 2),  # tile rows and columns at zoom level 0
        "bounds": (-180., -90., 180., 90.),  # pyramid bounds in pyramid CRS
        "is_global": True,  # if false, no antimeridian handling
        "srs": {
            "epsg": 4326  # EPSG code for CRS
        }
    },
    "mercator": {
        "shape": (1, 1),
        "bounds": (
            -20037508.3427892,
            -20037508.3427892,
            20037508.3427892,
            20037508.3427892
        ),
        "is_global": True,
        "srs": {
            "epsg": 3857
        }
    }
}

# Update Pyramid Parameters with UTM EPSG codes and pyramid setup
PYRAMID_PARAMS.update(_get_utm_pyramid_configs())
