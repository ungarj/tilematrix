# IO

## reading data

**read_raster_window**
```python
read_raster_window(
    input_file,
    tile_pyramid,
    tile,
    pixelbuffer=0,
    resampling=RESAMPLING.nearest
    )
```
* ``input_file``: any raster source readable by ``rasterio``
* ``tile_pyramid``: a valid ``TilePyramid`` or ``MetaTilePyramid`` object
* ``tile``: a tile identifier (zoom, row, col)
* ``pixelbuffer``: extract tile including a buffer in tile pixels
* ``resampling``: resampling method (nearest, gauss, cubic, average, mode, average_magphase, none)

Reads an input raster dataset with rasterio and resamples array to target
tile. Returns a tuple of (metadata, data), where metadata is a rasterio
meta dictionary and data a multidimensional numpy array.

## writing data

**write_raster_window**
```python
write_raster_window(
    output_file,
    tile_pyramid,
    tile,
    metadata,
    bands,
    pixelbuffer=0)
```
* ``output_file``: output file path
* ``tile_pyramid``: a valid ``TilePyramid`` or ``MetaTilePyramid`` object with a ``format`` property
* ``tile``: a tile identifier (zoom, row, col)
* ``metadata``: metadata dictionary
* ``bands``: tuple of bands containing numpy arrays
* ``pixelbuffer``: writes tile including a buffer in tile pixels
Writes numpy array into a TilePyramid tile.
