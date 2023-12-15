"""Fixtures for test suite."""

import pytest
from shapely.geometry import Point, Polygon, shape

example_proj = """
        +proj=ortho
        +lat_0=-90
        +lon_0=0
        +x_0=0
        +y_0=0
        +ellps=WGS84
        +units=m +no_defs
    """


@pytest.fixture
def grid_definition_proj():
    """Custom grid definition using a proj string."""
    return {
        "shape": (1, 1),
        "bounds": (-4000000.0, -4000000.0, 4000000.0, 4000000.0),
        "is_global": False,
        "proj": example_proj,
    }


@pytest.fixture
def grid_definition_epsg():
    """Custom grid definition using an EPSG code."""
    return {
        "shape": (1, 1),
        "bounds": (2426378.0132, 1528101.2618, 6293974.6215, 5395697.8701),
        "is_global": False,
        "epsg": 3035,
    }


@pytest.fixture
def proj():
    return example_proj


@pytest.fixture
def wkt():
    return """
        PROJCS["ETRS89 / LAEA Europe",
        GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",
        SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],
        TOWGS84[0,0,0,0,0,0,0],
        AUTHORITY["EPSG","6258"]],
        PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4258"]],
        PROJECTION["Lambert_Azimuthal_Equal_Area"],
        PARAMETER["latitude_of_center",52],
        PARAMETER["longitude_of_center",10],
        PARAMETER["false_easting",4321000],
        PARAMETER["false_northing",3210000],
        UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
        AUTHORITY["EPSG","3035"]]
    """


@pytest.fixture
def invalid_geom():
    return Polygon(
        [
            (0, 0),
            (0, 3),
            (3, 3),
            (3, 0),
            (2, 0),
            (2, 2),
            (1, 2),
            (1, 1),
            (2, 1),
            (2, 0),
            (0, 0),
        ]
    )


@pytest.fixture
def grid_definition_irregular():
    return {
        "shape": [161, 315],
        "bounds": [141920, 89840, 948320, 502000],
        "is_global": False,
        "srs": {"epsg": 31259},
    }


@pytest.fixture
def tile_bbox():
    return Polygon(
        [
            [-163.125, 73.125],
            [-157.5, 73.125],
            [-157.5, 67.5],
            [-163.125, 67.5],
            [-163.125, 73.125],
        ]
    )


@pytest.fixture
def tile_bbox_buffer():
    return Polygon(
        [
            [-163.14697265625, 73.14697265625],
            [-157.47802734375, 73.14697265625],
            [-157.47802734375, 67.47802734375],
            [-163.14697265625, 67.47802734375],
            [-163.14697265625, 73.14697265625],
        ]
    )


@pytest.fixture
def tl_polygon():
    return shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (-174.35302734375, 84.35302734375),
                    (-174.35302734375, 90.0),
                    (-180.02197265625, 90.0),
                    (-180.02197265625, 84.35302734375),
                    (-174.35302734375, 84.35302734375),
                ),
            ),
        }
    )


@pytest.fixture
def bl_polygon():
    return shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (-174.35302734375, -90.0),
                    (-174.35302734375, -84.35302734375),
                    (-180.02197265625, -84.35302734375),
                    (-180.02197265625, -90.0),
                    (-174.35302734375, -90.0),
                ),
            ),
        }
    )


@pytest.fixture
def overflow_polygon():
    return shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (0.703125, -90.0),
                    (0.703125, 90.0),
                    (-180.703125, 90.0),
                    (-180.703125, -90.0),
                    (0.703125, -90.0),
                ),
            ),
        }
    )


@pytest.fixture
def point():
    return Point(16.36, 48.20)


@pytest.fixture
def multipoint():
    return shape(
        {
            "type": "MultiPoint",
            "coordinates": [
                (14.464033917048539, 50.08528287347832),
                (16.364693096743736, 48.20196113681686),
            ],
        }
    )


@pytest.fixture
def linestring():
    return shape(
        {
            "type": "LineString",
            "coordinates": [
                (8.219788038779399, 48.04680919045518),
                (8.553359409223447, 47.98081838641845),
                (9.41408206547689, 48.13835399026023),
                (10.71989383306024, 48.64871043557477),
                (11.683555942439085, 48.794127916044104),
                (12.032991977596737, 49.02749868427421),
            ],
        }
    )


@pytest.fixture
def multilinestring():
    return shape(
        {
            "type": "MultiLineString",
            "coordinates": [
                [
                    (8.219788038779399, 48.04680919045518),
                    (8.553359409223447, 47.98081838641845),
                    (9.41408206547689, 48.13835399026023),
                    (10.71989383306024, 48.64871043557477),
                    (11.683555942439085, 48.794127916044104),
                    (12.032991977596737, 49.02749868427421),
                ],
                [
                    (33.206893344868945, 0.261534735511418),
                    (33.18725630059802, 0.428191229652711),
                    (32.8931140479927, 1.31144481038541),
                    (32.80150465264725, 1.366544806316611),
                    (32.62475833510098, 1.471712805584616),
                    (32.51003665541302, 1.536754055177965),
                    (32.36248752211165, 1.606878973798047),
                ],
            ],
        }
    )


@pytest.fixture
def polygon():
    return shape(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    (8.219788038779399, 48.04680919045518),
                    (8.553359409223447, 47.98081838641845),
                    (9.41408206547689, 48.13835399026023),
                    (10.71989383306024, 48.64871043557477),
                    (11.683555942439085, 48.794127916044104),
                    (12.032991977596737, 49.02749868427421),
                    (8.219788038779399, 48.04680919045518),
                ]
            ],
        }
    )


@pytest.fixture
def multipolygon():
    return shape(
        {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        (8.219788038779399, 48.04680919045518),
                        (8.553359409223447, 47.98081838641845),
                        (9.41408206547689, 48.13835399026023),
                        (10.71989383306024, 48.64871043557477),
                        (11.683555942439085, 48.794127916044104),
                        (12.032991977596737, 49.02749868427421),
                    ]
                ],
                [
                    [
                        (33.206893344868945, 0.261534735511418),
                        (33.18725630059802, 0.428191229652711),
                        (32.8931140479927, 1.31144481038541),
                        (32.80150465264725, 1.366544806316611),
                        (32.62475833510098, 1.471712805584616),
                        (32.51003665541302, 1.536754055177965),
                        (32.36248752211165, 1.606878973798047),
                    ]
                ],
            ],
        }
    )


@pytest.fixture
def tile_bounds_polygon():
    return shape(
        {
            "type": "Polygon",
            "coordinates": [
                [(0, 0), (0, 45), (22.5, 45), (22.5, 22.5), (45, 22.5), (45, 0), (0, 0)]
            ],
        }
    )
