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

# Analog logic for S2 grid but the origin is shifted to match the S2 grid
# and the TileMatrix Definition is defined to be divisible by 60, 20 and 10
# width 737280 to be divisible by 60, 20 and 10 and has 10[m] resolution
# height 9584640 to be divisible by 60, 20 and 10 and has 10[m] resolution
# S2 originally intended pyramid bounds [99960.00, 0.0000, 834000.00, 9000000]
# For the 60[m] grid the max/optimal zoom level is 4
# For the 10[m] and 20[m] grid the optimal zoom level is 5 and 4 respectively

# 10[m] and 20[m] grid
UTM_STRIPE_S2_SHAPE = (117, 9)

# 60[m] grid
UTM_STRIPE_S2_60M_SHAPE = (39, 3)

UTM_STRIPE_S2_GRID_NORTH_BOUNDS = [145980, 0, 883260, 9584640.0]
UTM_STRIPE_S2_GRID_SOUTH_BOUNDS = [145980, 415360, 883260, 10000000.0]

# Availible UTM grids in TMX
UTM_GRIDS = {
    "EOX_UTM": {
        "shape": UTM_STRIPE_SHAPE,
        "north_bounds": UTM_STRIPE_NORTH_BOUNDS,
        "south_bounds": UTM_STRIPE_SOUTH_BOUNDS
    },
    "S2_10M_UTM": {
        "shape": UTM_STRIPE_S2_SHAPE,
        "north_bounds": UTM_STRIPE_S2_GRID_NORTH_BOUNDS,
        "south_bounds": UTM_STRIPE_S2_GRID_SOUTH_BOUNDS
    },
    "S2_60M_UTM": {
        "shape": UTM_STRIPE_S2_60M_SHAPE,
        "north_bounds": UTM_STRIPE_S2_GRID_NORTH_BOUNDS,
        "south_bounds": UTM_STRIPE_S2_GRID_SOUTH_BOUNDS
    }
}


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
        utm_grid="EOX_UTM"
):
    utm_grid_params = UTM_GRIDS[utm_grid]
    if crs_epsg.startswith("327"):
        grid_bounds = utm_grid_params["south_bounds"]
    else:
        grid_bounds = utm_grid_params["north_bounds"]
    out_utm_config_dict = {}
    out_utm_config_dict[f"{utm_grid}_{crs_epsg}"] = {
        'shape': utm_grid_params['shape'],
        'bounds': grid_bounds,
        'srs': {"epsg": crs_epsg},
        'is_global': False,
    }
    return out_utm_config_dict


def _get_utm_pyramid_configs(grids=UTM_GRIDS, bounds=[-180, -90, 180, 90]):
    out_dict = {}
    utm_epsg_list = _get_utm_crs_list_from_bounds(
        bounds=bounds
    )
    for utm_grid in grids.keys():
        for utm_epsg in utm_epsg_list:
            out_dict.update(
                _get_utm_pyramid_config(
                    crs_epsg=utm_epsg,
                    utm_grid=utm_grid
                )
            )
    # print(out_dict)
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
