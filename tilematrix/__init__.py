"""Main package entry point."""

from ._tilepyramid import TilePyramid
from ._tile import Tile
from ._funcs import clip_geometry_to_srs_bounds, snap_bounds
from ._types import Bounds, Shape, TileIndex

__all__ = [
    'TilePyramid',
    'Tile',
    'TileIndex',
    'Shape',
    'Bounds',
    'clip_geometry_to_srs_bounds',
    'snap_bounds'
]


__version__ = "0.18"
