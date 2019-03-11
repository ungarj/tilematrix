"""Fixtures for test suite."""

import pytest
from shapely.geometry import Polygon

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
        "bounds": (-4000000., -4000000., 4000000., 4000000.),
        "is_global": False,
        "proj": example_proj
    }


@pytest.fixture
def grid_definition_epsg():
    """Custom grid definition using an EPSG code."""
    return {
        "shape": (1, 1),
        "bounds": (2426378.0132, 1528101.2618, 6293974.6215, 5395697.8701),
        "is_global": False,
        "epsg": 3035
    }


@pytest.fixture
def proj():
    return example_proj


@pytest.fixture
def wkt():
    return '''
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
    '''


@pytest.fixture
def invalid_geom():
    return Polygon(
        [
            (0, 0), (0, 3), (3, 3), (3, 0), (2, 0), (2, 2),
            (1, 2), (1, 1), (2, 1), (2, 0), (0, 0)
        ]
    )
