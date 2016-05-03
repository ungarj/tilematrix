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
