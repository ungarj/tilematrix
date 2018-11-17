from collections import namedtuple


Bounds = namedtuple("Bounds", "left bottom right top")
Shape = namedtuple("Shape", "height width")
TileIndex = namedtuple("TileIndex", "zoom row col")
