# tilematrix
Python module to help handling tile pyramids. The module is designed to help preprocessing of geodata for web maps by simplifying following steps:
1. translate between tile indices (zoom, row, column) and map coordinates (e.g. latitute, longitude), and
1. read and write data aligned to a predefined tile cache.

``tilematrix`` supports metatiling as well and makes heavy use of [Fiona](https://github.com/Toblerity/Fiona), [shapely](https://github.com/Toblerity/shapely) and [rasterio](https://github.com/mapbox/rasterio).

# Installation
```shell
pip install numpy
pip install tilematrix
```

In case there are problems installing GDAL/OGR for ``virtualenv``, try the following (from [here](https://gist.github.com/cspanring/5680334); works on Ubuntu 14.04):

```shell
sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install libgdal-dev
```

and run ``pip`` while also providing your GDAL version installed and the locations of the headers:

```shell
pip install gdal==1.11.2 --global-option=build_ext --global-option="-I/usr/include/gdal/"
```


# Documentation

* [navigate through a tile pyramid](doc/tilematrix.md)
* [reading and writing data](doc/tilematrix_io.md)
* [examples](doc/examples.md)

# TODO

* Tile pyramid projections other than WGS84 (EPSG 4326), specifically Google Mercator are planned but have to be implemented.
* If source raster data is loaded which is other than EPSG 4326 and has to be reprojected, there may be artifacts at the tile boundaries.
* Vector data support is planned, but not implemented yet.
