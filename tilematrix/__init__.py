"""Main package entry point."""

from ._tilepyramid import TilePyramid
from ._tile import Tile
from ._funcs import clip_geometry_to_srs_bounds, snap_bounds, Shape, Bounds, TileIndex

__all__ = [
    'clip_geometry_to_srs_bounds', 'snap_bounds', 'Tile', 'TilePyramid', 'TileIndex',
    'Shape', 'Bounds'
]


__version__ = "0.16"
