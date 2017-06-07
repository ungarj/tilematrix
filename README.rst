==========
Tilematrix
==========

Tilematrix handles geographic web tiles and tile pyramids.

.. image:: https://badge.fury.io/py/tilematrix.svg
    :target: https://badge.fury.io/py/tilematrix

.. image:: https://travis-ci.org/ungarj/tilematrix.svg?branch=master
    :target: https://travis-ci.org/ungarj/tilematrix

.. image:: https://coveralls.io/repos/github/ungarj/tilematrix/badge.svg?branch=master
    :target: https://coveralls.io/github/ungarj/tilematrix?branch=master


The module is designed to translate between tile indices (zoom, row, column) and
map coordinates (e.g. latitute, longitude).

Tilematrix supports **metatiling** and **tile buffers**. Furthermore it makes
heavy use of shapely_ and it can also generate ``Affine`` objects per tile which
facilitates working with rasterio_ for tile based data reading and writing.

It is very similar to mercantile_ but besides of supporting spherical mercator
tile pyramids, it also supports geodetic (WGS84) tile pyramids.

.. _shapely: http://toblerity.org/shapely/
.. _rasterio: https://github.com/mapbox/rasterio
.. _mercantile: https://github.com/mapbox/mercantile

------------
Installation
------------

.. code-block:: shell

    pip install tilematrix

In case there are problems installing GDAL/OGR for ``virtualenv``, try the
following (from here_); works on Ubuntu 16.04):

.. _here: https://gist.github.com/cspanring/5680334

.. code-block:: shell

    sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
    sudo apt-get update
    sudo apt-get install libgdal-dev

and run ``pip`` while also providing your GDAL version installed and the
locations of the headers:

.. code-block:: shell

    pip install gdal==2.1.0 --global-option=build_ext --global-option="-I/usr/include/gdal/"

-------------
Documentation
-------------

* `API documentation <doc/tilematrix.md>`_
* `examples <doc/examples.md>`_

-------
License
-------

MIT License

Copyright (c) 2015, 2016, 2017 `EOX IT Services`_

.. _`EOX IT Services`: https://eox.at/
