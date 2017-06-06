"""Tile class."""

from shapely.geometry import box
from affine import Affine

from . import _conf, _funcs


class Tile(object):
    """
    A Tile is a square somewhere on Earth.

    Each Tile can be identified with the zoom, row, column index in a
    TilePyramid.

    Some tile functions can accept a tile buffer in pixels (pixelbuffer). A
    pixelbuffer value of e.g. 1 will extend the tile boundaries by 1 pixel.
    """

    def __init__(self, tile_pyramid, zoom, row, col):
        """Initialize Tile."""
        self.tile_pyramid = tile_pyramid
        self.crs = tile_pyramid.crs
        self.zoom = zoom
        self.row = row
        self.col = col
        try:
            assert self.is_valid()
        except AssertionError:
            raise ValueError("invalid tile index given: %s %s %s" % (
                zoom, row, col))
        self.index = (zoom, row, col)
        self.id = (zoom, row, col)
        self.pixel_x_size = self.tile_pyramid.pixel_x_size(self.zoom)
        self.pixel_y_size = self.tile_pyramid.pixel_y_size(self.zoom)
        self.left = float(round(
            self.tile_pyramid.left+((self.col)*self.x_size),
            _conf.ROUND)
        )
        self.top = float(round(
            self.tile_pyramid.top-((self.row)*self.y_size),
            _conf.ROUND)
        )
        self.right = self.left + self.x_size
        self.bottom = self.top - self.y_size
        self.srid = tile_pyramid.srid

    @property
    def width(self):
        """Calculate Tile width in pixels."""
        return self.tile_pyramid.tile_width(self.zoom)

    @property
    def height(self):
        """Calculate Tile height in pixels."""
        return self.tile_pyramid.tile_height(self.zoom)

    @property
    def x_size(self):
        """Width of tile in SRID units at zoom level."""
        return self.tile_pyramid.tile_x_size(self.zoom)

    @property
    def y_size(self):
        """Height of tile in SRID units at zoom level."""
        return self.tile_pyramid.tile_y_size(self.zoom)

    def bounds(self, pixelbuffer=0):
        """
        Return Tile boundaries.

        - pixelbuffer: tile buffer in pixels
        """
        left = self.left
        bottom = self.top - self.y_size
        right = self.left + self.x_size
        top = self.top
        if pixelbuffer > 0:
            assert isinstance(pixelbuffer, int)
            offset = self.pixel_x_size * float(pixelbuffer)
            left -= offset
            bottom -= offset
            right += offset
            top += offset
        if top > self.tile_pyramid.top:
            top = self.tile_pyramid.top
        if bottom < self.tile_pyramid.bottom:
            bottom = self.tile_pyramid.bottom
        return (left, bottom, right, top)

    def bbox(self, pixelbuffer=0):
        """
        Return Tile bounding box.

        - pixelbuffer: tile buffer in pixels
        """
        return box(*self.bounds(pixelbuffer=pixelbuffer))

    def affine(self, pixelbuffer=0):
        """
        Return an Affine object of tile.

        - pixelbuffer: tile buffer in pixels
        """
        left = self.bounds(pixelbuffer=pixelbuffer)[0]
        top = self.bounds(pixelbuffer=pixelbuffer)[3]
        return Affine.translation(left, top) * Affine.scale(
            self.pixel_x_size, -self.pixel_y_size)

    def shape(self, pixelbuffer=0):
        """
        Return a tuple of tile height and width.

        - pixelbuffer: tile buffer in pixels
        """
        height = self.height + 2 * pixelbuffer
        width = self.width + 2 * pixelbuffer
        if pixelbuffer:
            matrix_height = self.tile_pyramid.matrix_height(self.zoom)
            if self.row in [0, matrix_height-1]:
                height = self.height+pixelbuffer
            if matrix_height == 1:
                height = self.height
        return (height, width)

    def is_valid(self):
        """Return True if tile is available in tile pyramid."""
        try:
            assert isinstance(self.zoom, int)
            assert self.zoom >= 0
            assert isinstance(self.row, int)
            assert self.row >= 0
            assert isinstance(self.col, int)
            assert self.col >= 0
            assert self.col < self.tile_pyramid.matrix_width(self.zoom)
            assert self.row < self.tile_pyramid.matrix_height(self.zoom)
        except AssertionError:
            return False
        else:
            return True

    def get_parent(self):
        """Return tile from previous zoom level."""
        if self.zoom == 0:
            return None
        else:
            return self.tile_pyramid.tile(
                self.zoom-1, int(self.row/2), int(self.col/2))

    def get_children(self):
        """Return tiles from next zoom level."""
        return [
            self.tile_pyramid.tile(self.zoom+1, self.row*2, self.col*2),
            self.tile_pyramid.tile(self.zoom+1, self.row*2+1, self.col*2),
            self.tile_pyramid.tile(self.zoom+1, self.row*2, self.col*2+1),
            self.tile_pyramid.tile(self.zoom+1, self.row*2+1, self.col*2+1)
        ]

    def get_neighbors(self, connectedness=8, count=None):
        """
        Return tile neighbors.

        -------------
        | 8 | 1 | 5 |
        -------------
        | 4 | x | 2 |
        -------------
        | 7 | 3 | 6 |
        -------------

        - connectedness: [4 or 8] return four direct neighbors or all eight.
        """
        try:
            assert connectedness in [4, 8]
        except AssertionError:
            raise ValueError("only connectedness values 8 or 4 are allowed")
        if count:
            raise DeprecationWarning(
                "'count' parameter was replaced by 'connectedness'"
            )
        zoom, row, col = self.zoom, self.row, self.col
        neighbors = []
        # 4-connected neighbors
        for candidate in [
            self.tile_pyramid.tile(zoom, row-1, col),
            self.tile_pyramid.tile(zoom, row, col+1),
            self.tile_pyramid.tile(zoom, row+1, col),
            self.tile_pyramid.tile(zoom, row, col-1),
        ]:
            neighbor = self._clean_tile(candidate)
            if neighbor:
                neighbors.append(neighbor)
        # 8-connected neighbors
        if connectedness == 8:
            for candidate in [
                self.tile_pyramid.tile(zoom, row-1, col+1),
                self.tile_pyramid.tile(zoom, row+1, col+1),
                self.tile_pyramid.tile(zoom, row+1, col-1),
                self.tile_pyramid.tile(zoom, row-1, col-1)
            ]:
                neighbor = self._clean_tile(candidate)
                if neighbor:
                    neighbors.append(neighbor)

        return neighbors

    def intersecting(self, tilepyramid):
        """
        Return all tiles intersecting with tilepyramid.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tilepyramid: a TilePyramid object
        """
        return _funcs._tile_intersecting_tilepyramid(self, tilepyramid)

    def _clean_tile(self, tile):
        """
        Return valid neighbor over tile matrix bounds.

        By wrapping around the antimeridian if necessary or None if tile could
        not be cleaned.
        """
        zoom, row, col = tile.id
        # return None if tile is above or below tile matrix
        if row >= 0 and row < self.tile_pyramid.matrix_height(zoom):
            # fix if on eastern side of antimeridian
            if col < 0:
                col += self.tile_pyramid.matrix_width(zoom)
            # fix if on western side of antimeridian
            if col >= self.tile_pyramid.matrix_width(zoom):
                col -= self.tile_pyramid.matrix_width(zoom)
            out_tile = self.tile_pyramid.tile(zoom, row, col)
            # final validity check
            if out_tile.is_valid():
                return out_tile
            else:
                return None
        else:
            return None
