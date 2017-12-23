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

.. image:: https://img.shields.io/pypi/pyversions/mapchete.svg


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

Use ``pip`` to install the latest stable version:

.. code-block:: shell

    pip install tilematrix

Manually install the latest development version

.. code-block:: shell

    pip install -r requirements.txt
    python setup.py install


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
