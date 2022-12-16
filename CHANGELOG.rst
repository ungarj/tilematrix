#########
Changelog
#########

2022.12.0 - 2022-12-16
----------------------
* make fit for `Shapely 2.0``


2022.11.3 - 2022-11-08
----------------------
* replace `setuptools` with `hatch``


2022.11.2 - 2022-11-08
----------------------
* remove `conda` build files
* `tilematrix-feedstock <https://github.com/conda-forge/tilematrix-feedstock>`_  `conda-forge feedstock` repository for releasing new versions on `conda-forge` 


2022.11.1 - 2022-11-03
----------------------
* fix `conda` & `pip ` builds


2022.11.0 - 2022-11-03
----------------------
* test also for python `3.9`
* renaming `master` branch to `main`
* add ``conda`` publish to github actions (workflows)


2022.3.0 - 2022-03-15
---------------------
* add option to exactly get intersection tiles using `TilePyramid.tiles_from_geom(exact=True)`


2021.11.0 - 2021-11-12
----------------------
* enable yielding tiles in batches by either row or column for following methods:
  * `TilePyramid.tiles_from_bounds()`
  * `TilePyramid.tiles_from_bbox()`
  * `TilePyramid.tiles_from_geom()`

* convert TilePyramid arguments into keyword arguments


0.21
----
* allow metatiling up to 512
* use GitHub actions instead of travis
* use black and flake8 pre-commit checks


0.20
----
* fixed pixel size calculation on irregular grids with metatiling (closing #33)
* ``TilePyramid.tile_x_size()``, ``TilePyramid.tile_y_size()``, ``TilePyramid.tile_height()``, ``TilePyramid.tile_width()`` are deprecated
* metatiles are clipped to ``TilePyramid.bounds`` but ``pixelbuffer`` of edge tiles can exceed them unless it is a global grid

0.19
----
* Python 2 not supported anymore
* ``TilePyramid.srid`` and ``TilePyramid.type``  are deprecated
* ``GridDefinition`` can now be loaded from package root
* ``GridDefinition`` got ``to_dict()`` and ``from_dict()`` methods


0.18
----
* order of ``Tile.shape`` swapped to ``(height, width)`` in order to match rasterio array interpretation

0.17
----
* make ``Tile`` iterable to enable ``tuple(Tile)`` return the tile index as tuple

0.16
----
* make ``Tile`` objects hashable & comparable

0.15
----
* add ``snap_bounds()`` function
* add ``snap_bounds`` command to ``tmx``
* add ``snap_bbox`` command to ``tmx``
* in ``tile_from_xy()`` add ``on_edge_use`` option specify behavior when point hits grid edges
* cleaned up ``_tiles_from_cleaned_bounds()`` and ``tile_from_xy()`` functions

------
0.14.2
------
* attempt to fix ``tmx`` command when installing tilematrix via pip

----
0.14
----
* add ``tmx`` CLI with subcommands:
  * `bounds`: Print bounds of given Tile.
  * `bbox`: Print bounding box geometry of given Tile.
  * `tile`: Print Tile covering given point.
  * `tiles`: Print Tiles covering given bounds.

----
0.13
----
* fixed ``tiles_from_geom()`` bug when passing on a Point (#19)
* add ``tile_from_xy()`` function

----
0.12
----
* added better string representations for ``Tile`` and ``TilePyramid``
* added ``GridDefinition`` to better handle custom grid parameters
* ``TilePyramid`` instances are now comparable by ``==`` and ``!=``

----
0.11
----
* custom grid defnitions enabled

---
0.10
---
* new tag for last version to fix Python 3 build

---
0.9
---
* added Python 3 support
* use NamedTuple for Tile index

---
0.8
---
* ``intersecting`` function fixed (rounding error caused return of wrong tiles)

---
0.7
---
* converted tuples for bounds and shape attributes to namedtuples

---
0.6
---
* added ``pytest`` and test cases
* fixed metatiling shape error on low zoom levels
* split up code into internal modules
* travis CI and coveralls.io integration

---
0.5
---
* ``intersection()`` doesn't return invalid tiles.
* Moved copyright to EOX IT Services

---
0.4
---
* Decision to remove ``MetaTilePyramid`` class (now returns a ``DeprecationWarning``).
* TilePyramid now has its own ``metatiling`` parameter.
* ``intersecting()`` function for ``Tile`` and ``TilePyramid`` to relate between ``TilePyramids`` with different ``metatiling`` settings.

---
0.3
---
* fixed duplicate tile return in tiles_from_bounds()
* rasterio's CRS() class replaced CRS dict

---
0.2
---
* introduced handling of antimeridian:
    * ``get_neighbor()`` also gets tiles from other side
    * ``.shape()`` returns clipped tile shape
    * added ``tiles_from_bounds()``
    * added ``clip_geometry_to_srs_bounds()``

---
0.1
---
* added Spherical Mercator support
* removed IO module (moved to `mapchete <https://github.com/ungarj/mapchete>`_)
* removed deprecated ``OutputFormats``
* introduced ``get_parent()`` and ``get_children()`` functions for ``Tile``

-----
0.0.4
-----
* introduced ``Tile`` object
* read_raster_window() is now a generator which returns only a numpy array
* read_vector_window() is a generator which returns a GeoJSON-like object with a geometry clipped to tile boundaries
* proper error handling (removed ``sys.exit(0)``)

-----
0.0.3
-----
* rewrote io module
* separated and enhanced OutputFormats

-----
0.0.2
-----
* fixed wrong link to github repository

-----
0.0.1
-----
* basic functionality
