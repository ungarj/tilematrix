"""Fixtures for test suite."""

import pytest


@pytest.fixture
def grid_definition_proj():
    """Custom grid definition using a proj string."""
    return {
        "shape": (1, 1),
        "bounds": (-4000000., -4000000., 4000000., 4000000.),
        "is_global": False,
        "proj": """
            +proj=ortho
            +lat_0=-90
            +lon_0=0
            +x_0=0
            +y_0=0
            +ellps=WGS84
            +units=m +no_defs
        """}


@pytest.fixture
def grid_definition_epsg():
    """Custom grid definition using an EPSG code."""
    return {
        "shape": (1, 1),
        "bounds": (2426378.0132, 1528101.2618, 6293974.6215, 5395697.8701),
        "is_global": False,
        "epsg": 3035
    }
