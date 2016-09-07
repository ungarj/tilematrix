# Changelog

# 0.0.1
* basic functionality

# 0.0.2
* fixed wrong link to github repository

# 0.0.3
* rewrote io module
* separated and enhanced OutputFormats

# 0.0.4
* introduced ``Tile`` object
* read_raster_window() is now a generator which returns only a numpy array
* read_vector_window() is a generator which returns a GeoJSON-like object with a geometry clipped to tile boundaries
* proper error handling (removed ``sys.exit(0)``)

# 0.1
* added Spherical Mercator support
* removed IO module (moved to [mapchete](https://github.com/ungarj/mapchete))
* removed deprecated ``OutputFormats``
* introduced ``get_parent()`` and ``get_children()`` functions for ``Tile``

# 0.2
* introduced handling of antimeridian:
    * get_neighbor() also gets tiles from other side
    * .shape() returns clipped tile shape
    * added tiles_from_bounds()
    * added clip_geometry_to_srs_bounds()

# 0.3
* fixed duplicate tile return in tiles_from_bounds()
* rasterio's CRS() class replaced CRS dict
