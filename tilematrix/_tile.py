"""Tile class."""

from affine import Affine
from shapely.geometry import box
import warnings

from ._conf import ROUND
from ._funcs import _tile_intersecting_tilepyramid
from ._types import TileIndex, Shape, Bounds


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
        self.tp = tile_pyramid
        self.crs = tile_pyramid.crs
        self.zoom = zoom
        self.row = row
        self.col = col
        self.is_valid()
        self.index = self.id = TileIndex(zoom, row, col)
        self.pixel_x_size = self.tile_pyramid.pixel_x_size(self.zoom)
        self.pixel_y_size = self.tile_pyramid.pixel_y_size(self.zoom)
        # base SRID size without pixelbuffer
        self._base_srid_size = Shape(
            height=self.pixel_y_size * self.tp.tile_size * self.tp.metatiling,
            width=self.pixel_x_size * self.tp.tile_size * self.tp.metatiling,
        )
        # base bounds not accounting for pixelbuffers but metatiles are clipped to
        # TilePyramid bounds
        self._top = round(self.tp.top - (self.row * self._base_srid_size.height), ROUND)
        self._bottom = max([self._top - self._base_srid_size.height, self.tp.bottom])
        self._left = round(
            self.tp.left + (self.col * self._base_srid_size.width), ROUND
        )
        self._right = min([self._left + self._base_srid_size.width, self.tp.right])
        # base shape without pixelbuffer
        self._base_shape = Shape(
            height=int(round((self._top - self._bottom) / self.pixel_y_size, 0)),
            width=int(round((self._right - self._left) / self.pixel_x_size, 0)),
        )

    @property
    def left(self):
        return self.bounds().left

    @property
    def bottom(self):
        return self.bounds().bottom

    @property
    def right(self):
        return self.bounds().right

    @property
    def top(self):
        return self.bounds().top

    @property
    def srid(self):
        warnings.warn(DeprecationWarning("'srid' attribute is deprecated"))
        return self.tp.grid.srid

    @property
    def width(self):
        """Calculate Tile width in pixels."""
        return self.shape().width

    @property
    def height(self):
        """Calculate Tile height in pixels."""
        return self.shape().height

    @property
    def x_size(self):
        """Width of tile in SRID units at zoom level."""
        return self.right - self.left

    @property
    def y_size(self):
        """Height of tile in SRID units at zoom level."""
        return self.top - self.bottom

    def bounds(self, pixelbuffer=0):
        """
        Return Tile boundaries.

        - pixelbuffer: tile buffer in pixels
        """
        left = self._left
        bottom = self._bottom
        right = self._right
        top = self._top
        if pixelbuffer:
            offset = self.pixel_x_size * float(pixelbuffer)
            left -= offset
            bottom -= offset
            right += offset
            top += offset
        # on global grids clip at northern and southern TilePyramid bound
        if self.tp.grid.is_global:
            top = min([top, self.tile_pyramid.top])
            bottom = max([bottom, self.tile_pyramid.bottom])
        return Bounds(left, bottom, right, top)

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
        return Affine(
            self.pixel_x_size,
            0,
            self.bounds(pixelbuffer).left,
            0,
            -self.pixel_y_size,
            self.bounds(pixelbuffer).top,
        )

    def shape(self, pixelbuffer=0):
        """
        Return a tuple of tile height and width.

        - pixelbuffer: tile buffer in pixels
        """
        # apply pixelbuffers
        height = self._base_shape.height + 2 * pixelbuffer
        width = self._base_shape.width + 2 * pixelbuffer
        if pixelbuffer and self.tp.grid.is_global:
            # on first and last row, remove pixelbuffer on top or bottom
            matrix_height = self.tile_pyramid.matrix_height(self.zoom)
            if matrix_height == 1:
                height = self._base_shape.height
            elif self.row in [0, matrix_height - 1]:
                height = self._base_shape.height + pixelbuffer
        return Shape(height=height, width=width)

    def is_valid(self):
        """Return True if tile is available in tile pyramid."""
        if not all(
            [
                isinstance(self.zoom, int),
                self.zoom >= 0,
                isinstance(self.row, int),
                self.row >= 0,
                isinstance(self.col, int),
                self.col >= 0,
            ]
        ):
            raise TypeError("zoom, col and row must be integers >= 0")
        cols = self.tile_pyramid.matrix_width(self.zoom)
        rows = self.tile_pyramid.matrix_height(self.zoom)
        if self.col >= cols:
            raise ValueError("col (%s) exceeds matrix width (%s)" % (self.col, cols))
        if self.row >= rows:
            raise ValueError("row (%s) exceeds matrix height (%s)" % (self.row, rows))
        return True

    def get_parent(self):
        """Return tile from previous zoom level."""
        return (
            None
            if self.zoom == 0
            else self.tile_pyramid.tile(self.zoom - 1, self.row // 2, self.col // 2)
        )

    def get_children(self):
        """Return tiles from next zoom level."""
        next_zoom = self.zoom + 1
        return [
            self.tile_pyramid.tile(
                next_zoom, self.row * 2 + row_offset, self.col * 2 + col_offset
            )
            for row_offset, col_offset in [
                (0, 0),  # top left
                (0, 1),  # top right
                (1, 1),  # bottom right
                (1, 0),  # bottom left
            ]
            if all(
                [
                    self.row * 2 + row_offset < self.tp.matrix_height(next_zoom),
                    self.col * 2 + col_offset < self.tp.matrix_width(next_zoom),
                ]
            )
        ]

    def get_neighbors(self, connectedness=8):
        """
        Return tile neighbors.

        Tile neighbors are unique, i.e. in some edge cases, where both the left
        and right neighbor wrapped around the antimeridian is the same. Also,
        neighbors ouside the northern and southern TilePyramid boundaries are
        excluded, because they are invalid.

        -------------
        | 8 | 1 | 5 |
        -------------
        | 4 | x | 2 |
        -------------
        | 7 | 3 | 6 |
        -------------

        - connectedness: [4 or 8] return four direct neighbors or all eight.
        """
        if connectedness not in [4, 8]:
            raise ValueError("only connectedness values 8 or 4 are allowed")

        unique_neighbors = {}
        # 4-connected neighborsfor pyramid
        matrix_offsets = [
            (-1, 0),  # 1: above
            (0, 1),  # 2: right
            (1, 0),  # 3: below
            (0, -1),  # 4: left
        ]
        if connectedness == 8:
            matrix_offsets.extend(
                [
                    (-1, 1),  # 5: above right
                    (1, 1),  # 6: below right
                    (1, -1),  # 7: below left
                    (-1, -1),  # 8: above left
                ]
            )

        for row_offset, col_offset in matrix_offsets:
            new_row = self.row + row_offset
            new_col = self.col + col_offset
            # omit if row is outside of tile matrix
            if new_row < 0 or new_row >= self.tp.matrix_height(self.zoom):
                continue
            # wrap around antimeridian if new column is outside of tile matrix
            if new_col < 0:
                if not self.tp.is_global:
                    continue
                new_col = self.tp.matrix_width(self.zoom) + new_col
            elif new_col >= self.tp.matrix_width(self.zoom):
                if not self.tp.is_global:
                    continue
                new_col -= self.tp.matrix_width(self.zoom)
            # omit if new tile is current tile
            if new_row == self.row and new_col == self.col:
                continue
            # create new tile
            unique_neighbors[(new_row, new_col)] = self.tp.tile(
                self.zoom, new_row, new_col
            )

        return unique_neighbors.values()

    def intersecting(self, tilepyramid):
        """
        Return all Tiles from intersecting TilePyramid.

        This helps translating between TilePyramids with different metatiling
        settings.

        - tilepyramid: a TilePyramid object
        """
        return _tile_intersecting_tilepyramid(self, tilepyramid)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tp == other.tp
            and self.id == other.id
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "Tile(%s, %s)" % (self.id, self.tp)

    def __hash__(self):
        return hash(repr(self))

    def __iter__(self):
        yield self.zoom
        yield self.row
        yield self.col
