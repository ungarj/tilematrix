# tilematrix
Python module to help handling tile pyramids. The module is designed to help preprocessing of geodata for web maps by simplifying following steps:
1. translate between tile indices (zoom, row, column) and map coordinates (e.g. latitute, longitude), and
1. read and write data aligned to a predefined tile cache.

``tilematrix`` supports metatiling as well and makes heavy use of [Fiona](https://github.com/Toblerity/Fiona), [shapely](https://github.com/Toblerity/shapely) and [rasterio](https://github.com/mapbox/rasterio).

# Documentation

* [navigate through a tile pyramid](doc/tilematrix.md)
* [reading and writing data](doc/tilematrix_io.md)
* [examples](doc/examples.md)

# (Known) Deficiencies

* Tile pyramid projections other than WGS84 (EPSG 4326), specifically Google Mercator are planned but have to be implemented.
* If source raster data is loaded which is other than EPSG 4326 and has to be reprojected, there may be artefacts at the tile boundaries.
* Vector data support is planned, but not implemented yet.
* Naming convention of methods, attributes and variable names have to be improved, i.e. be aligned with well-known concepts (tile matrix, tile pyramid, resolution, etc.).
