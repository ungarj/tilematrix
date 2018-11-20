from rasterio.crs import CRS
import six

from ._conf import PYRAMID_PARAMS
from ._funcs import _verify_shape_bounds
from ._types import Bounds, Shape


class GridDefinition(object):
    """Object representing the tile pyramid source grid."""

    def __init__(self, grid_definition, tile_size=256, metatiling=1):
        if metatiling not in (1, 2, 4, 8, 16):
            raise ValueError("metatling must be one of 1, 2, 4, 8, 16")
        if isinstance(grid_definition, dict):
            self.init_definition = dict(**grid_definition)
            self.type = "custom"
            if "shape" not in self.init_definition:
                raise AttributeError("grid shape not provided")
            self.shape = Shape(*self.init_definition["shape"])
            self.bounds = Bounds(*self.init_definition["bounds"])
            # verify that shape aspect ratio fits bounds apsect ratio
            _verify_shape_bounds(shape=self.shape, bounds=self.bounds)
            self.left, self.bottom, self.right, self.top = self.bounds
            self.is_global = self.init_definition.get("is_global", False)
            if all([i in self.init_definition for i in ["proj", "epsg"]]):
                raise ValueError("either 'epsg' or 'proj' are allowed.")
            if "epsg" in self.init_definition:
                self.crs = CRS().from_epsg(self.init_definition["epsg"])
                self.srid = self.init_definition["epsg"]
            elif "proj" in self.init_definition:
                self.crs = CRS().from_string(self.init_definition["proj"])
                self.srid = None
            else:
                raise AttributeError("either 'epsg' or 'proj' is required")
        elif isinstance(grid_definition, six.string_types):
            self.init_definition = grid_definition
            if self.init_definition not in PYRAMID_PARAMS:
                raise ValueError(
                    "WMTS tileset '%s' not found. Use one of %s" % (
                        self.init_definition, PYRAMID_PARAMS.keys()
                    )
                )
            self.type = self.init_definition
            self.shape = Shape(*PYRAMID_PARAMS[self.init_definition]["shape"])
            self.bounds = Bounds(*PYRAMID_PARAMS[self.init_definition]["bounds"])
            self.left, self.bottom, self.right, self.top = self.bounds
            self.is_global = PYRAMID_PARAMS[self.init_definition]["is_global"]
            self.srid = PYRAMID_PARAMS[self.init_definition]["epsg"]
            self.crs = CRS().from_epsg(self.srid)
        elif isinstance(grid_definition, GridDefinition):
            self.__init__(
                grid_definition.init_definition, tile_size=tile_size,
                metatiling=metatiling
            )
        else:
            raise TypeError("invalid grid definition type: %s" % type(grid_definition))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.init_definition == other.init_definition
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'GridDefinition(init_definition=%s)' % self.init_definition

    def __hash__(self):
        return hash(repr(self))
