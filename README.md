# TilePyramid
Python module to help handling tile pyramids. The module is designed to help preprocessing of geodata for web maps by simplifying following steps:
1. translate between tile indices (zoom, row, column) and map coordinates (e.g. latitute, longitude), and
1. read and write data aligned to a predefined tile cache.

``TilePyramid`` supports metatiling as well and makes heavy use of [Fiona](https://github.com/Toblerity/Fiona), [shapely](https://github.com/Toblerity/shapely) and [rasterio](https://github.com/mapbox/rasterio).

# Documentation

* [navigate through a tile pyramid](doc/TilePyramid.md)
* [reading and writing data](doc/TilePyramid_io.md)
* [examples](doc/examples.md)

# TODO

* Tile pyramid projections other than WGS84 (EPSG 4326), specifically Google Mercator are planned but have to be implemented.
* If source raster data is loaded which is other than EPSG 4326 and has to be reprojected, there may be artefacts at the tile boundaries.
* Vector data support is planned, but not implemented yet.
