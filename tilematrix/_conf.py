"""Package configuration parameters."""

from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info


# round coordinates
ROUND = 20

# bounds ratio vs shape ratio uncertainty
DELTA = 1e-6

# UTM default settings
FIRST_UTM_STRIPE = 32600
LAST_UTM_STRIPE = 60

UTM_STRIPE_SHAPE = (8, 1)
UTM_STRIPE_BOUNDS = [166021.4431, 0.0000, 1476741.4431, 10485760]

UTM_DEFAULT_DICT = {
    '32600': {
        'grid': None,
        'shape': UTM_STRIPE_SHAPE,
        'bounds': UTM_STRIPE_BOUNDS,
        'crs': {
            "epsg": FIRST_UTM_STRIPE
        },
        'is_global': False
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
        utm_stripe_shape=UTM_STRIPE_SHAPE,
        grid_bounds=UTM_STRIPE_BOUNDS
):
    out_utm_config_dict = {}
    out_utm_config_dict[str(crs_epsg)] = {
        'shape': utm_stripe_shape,
        'bounds': grid_bounds,
        'srs': {"epsg": crs_epsg},
        'is_global': False
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
            -20037508.3427892, -20037508.3427892, 20037508.3427892,
            20037508.3427892),
        "is_global": True,
        "srs": {
            "epsg": 3857
        }
    }
}

# Update Pyramid Parameters with UTM EPSG codes and pyramid setup
PYRAMID_PARAMS.update(_get_utm_pyramid_configs())
