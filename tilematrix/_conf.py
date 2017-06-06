"""Package configuration parameters."""

# round coordinates
ROUND = 20

# supported pyramid types
PYRAMID_PARAMS = {
    "geodetic": {
        "shape": (2, 1),  # tile columns and rows at zoom level 0
        "bounds": (-180., 90., 180., -90.),  # pyramid bounds
        "is_global": True,  # if false, no antimeridian handling
        "epsg": 4326  # EPSG code
        },
    "mercator": {
        "shape": (1, 1),
        "bounds": (
            -20037508.3427892, 20037508.3427892, 20037508.3427892,
            -20037508.3427892),
        "is_global": True,
        "epsg": 3857
        }
    }
