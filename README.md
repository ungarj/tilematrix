# tilematrix
Python module to help handling tile pyramids. The module is designed to easily translate between tile indices (zoom, row, column) and map coordinates (e.g. latitute, longitude).

``tilematrix`` supports metatiling as well and makes heavy use of [shapely](https://github.com/Toblerity/shapely).

It is very similar to [https://github.com/mapbox/mercantile](mercantile) but besides of supporting spherical mercator tile pyramids, it also supports geodetic (WGS84) tile pyramids.

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

* [API documentation](doc/tilematrix.md)
* [examples](doc/examples.md)
