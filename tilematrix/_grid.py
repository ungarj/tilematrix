import warnings

from ._conf import PYRAMID_PARAMS
from ._funcs import _get_crs, _verify_shape_bounds
from ._types import Bounds, Shape


class GridDefinition(object):
    """Object representing the tile pyramid source grid."""

    def __init__(
        self, grid=None, shape=None, bounds=None, srs=None, is_global=False, **kwargs
    ):
        if isinstance(grid, str) and grid in PYRAMID_PARAMS:
            self.type = grid
            self.shape = Shape(*PYRAMID_PARAMS[grid]["shape"])
            self.bounds = Bounds(*PYRAMID_PARAMS[grid]["bounds"])
            self.is_global = PYRAMID_PARAMS[grid]["is_global"]
            self.crs = _get_crs(PYRAMID_PARAMS[grid]["srs"])
            self.left, self.bottom, self.right, self.top = self.bounds
        elif grid is None or grid == "custom":
            for i in ["proj", "epsg"]:
                if i in kwargs:
                    srs = {i: kwargs[i]} if srs is None else srs
                    warnings.warn(
                        DeprecationWarning(
                            "'%s' should be packed into a dictionary and passed to "
                            "'srs'" % i
                        )
                    )
            self.type = "custom"
            _verify_shape_bounds(shape=shape, bounds=bounds)
            self.shape = Shape(*shape)
            self.bounds = Bounds(*bounds)
            self.is_global = is_global
            self.crs = _get_crs(srs)
            self.left, self.bottom, self.right, self.top = self.bounds
            # check if parameters match with default grid type
            for default_grid_name in PYRAMID_PARAMS:
                default_grid = GridDefinition(default_grid_name)
                if self.__eq__(default_grid):
                    self.type = default_grid_name
        elif isinstance(grid, dict):
            if "type" in grid:
                warnings.warn(
                    DeprecationWarning("'type' is deprecated and should be 'grid'")
                )
                if "grid" not in grid:
                    grid["grid"] = grid.pop("type")
            self.__init__(**grid)
        elif isinstance(grid, GridDefinition):
            self.__init__(**grid.to_dict())
        else:
            raise ValueError("invalid grid definition: %s" % grid)

    @property
    def srid(self):
        warnings.warn(DeprecationWarning("'srid' attribute is deprecated"))
        return self.crs.to_epsg()

    def to_dict(self):
        return dict(
            bounds=self.bounds,
            is_global=self.is_global,
            shape=self.shape,
            srs=dict(wkt=self.crs.to_wkt()),
            type=self.type,
        )

    def from_dict(config_dict):
        return GridDefinition(**config_dict)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.shape == other.shape
            and self.bounds == other.bounds
            and self.is_global == other.is_global
            and self.crs == other.crs
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self.type in PYRAMID_PARAMS:
            return 'GridDefinition("%s")' % self.type
        else:
            return (
                "GridDefinition("
                '"%s", '
                "shape=%s, "
                "bounds=%s, "
                "is_global=%s, "
                "srs=%s"
                ")"
                % (
                    self.type,
                    tuple(self.shape),
                    tuple(self.bounds),
                    self.is_global,
                    self.crs,
                )
            )

    def __hash__(self):
        return hash(repr(self))
