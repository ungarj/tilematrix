"""Main package entry point."""

from ._conf import PYRAMID_PARAMS
from ._funcs import clip_geometry_to_srs_bounds, snap_bounds, validate_zoom
from ._grid import GridDefinition
from ._tile import Tile
from ._tilepyramid import TilePyramid
from ._types import Bounds, Shape, TileIndex

__all__ = [
    "Bounds",
    "clip_geometry_to_srs_bounds",
    "GridDefinition",
    "PYRAMID_PARAMS",
    "Shape",
    "snap_bounds",
    "TilePyramid",
    "Tile",
    "TileIndex",
    "validate_zoom",
]


__version__ = "2024.11.0"
