"""Main package entry point."""

from ._grid import GridDefinition
from ._funcs import clip_geometry_to_srs_bounds, snap_bounds
from ._tilepyramid import TilePyramid
from ._tile import Tile
from ._types import Bounds, Shape, TileIndex

__all__ = [
    'Bounds',
    'clip_geometry_to_srs_bounds',
    'GridDefinition',
    'Shape',
    'snap_bounds',
    'TilePyramid',
    'Tile',
    'TileIndex',
]


__version__ = "0.19"
