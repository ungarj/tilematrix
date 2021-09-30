"""Package configuration parameters."""

# round coordinates
ROUND = 20

# bounds ratio vs shape ratio uncertainty
DELTA = 1e-6

# supported pyramid types
PYRAMID_PARAMS = {
    "geodetic": {
        "shape": (1, 2),  # tile rows and columns at zoom level 0
        "bounds": (-180.0, -90.0, 180.0, 90.0),  # pyramid bounds in pyramid CRS
        "is_global": True,  # if false, no antimeridian handling
        "srs": {"epsg": 4326},  # EPSG code for CRS
    },
    "mercator": {
        "shape": (1, 1),
        "bounds": (
            -20037508.3427892,
            -20037508.3427892,
            20037508.3427892,
            20037508.3427892,
        ),
        "is_global": True,
        "srs": {"epsg": 3857},
    },
}
