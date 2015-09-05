# tilematrix
Python module to handle WMTS-like tile matrices. The module is designed to simplify preprocessing of geodata for web maps by providing useful functions
* to translate between tile indices (zoom, row, column) and map coordinates (e.g. latitute, longitude), and
* to read and write data aligned to a predefined tile cache.

``tilematrix`` supports metatiling as well and makes heavy use of [Fiona](https://github.com/Toblerity/Fiona), [shapely](https://github.com/Toblerity/shapely) and [rasterio](https://github.com/mapbox/rasterio).

# Documentation

* [tilematrix](doc/tilematrix.md)
* [tilematrix_io](doc/tilematrix_io.md)
* [examples](doc/examples.md)