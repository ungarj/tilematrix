# tilematrix

### Create a TileMatrix object
```python
TileMatrix(projection, px_per_tile=256)
```
* ``projection``: One out of ``4326`` and ``3857``, although currently only ``4326`` is supported.
* ``px_per_tile``: Optional, specifies the target resolution of each tile (i.e. each tile will have 256x256 px). Default is ``256``.

### Define output format/profile
```python
set_format(self, output_format, dtype=None)
```
* ``output_format``: Currently the following formats are avaliable: ``"GTiff"``, ``"PNG"``, ``"PNG_hillshade"`` and ``"GeoJSON"``.
* ``dtype``: For ``"GTiff"``, the output datadype can be defined as well (e.g. ``"uInt16"``, ``"uInt8"``, etc.). ``None`` keeps the datatyp from the input file.

### Get number of tiles for zoom level.
```python
tiles_per_zoom(self, zoom)
```
* ``zoom``: Zoom level.

Returns a tuple of two integers, indicating the number of tiles in each direction for the whole tilematrix.

### Get tilesize in coordinates for zoom level
```python
tilesize_per_zoom(self, zoom)
```
Returns a tuple of two floats, indicating the width and height of each tile at this zoom level in geographic coordinates.

### Get pixelsize in coordinates for zoom level
```python
pixelsize(self, zoom)
```
Returns a float, indicating the pixel resolution of the zoom level in geographic coordinates.

### Get top left tile coordinates
```python
top_left_tile_coords(self, zoom, row, col)
```
* ``row``: Row in tilematrix.
* ``col``: Column in tilematrix.

Returns a tuple of two floats, indicating the top left coordinates of the given tile.

### Get tile bounds
```python
tile_bounds(self, zoom, row, col, pixelbuffer=None)
```
* ``pixelbuffer``: Optional, integer defining the width of the additional margin to take into account (e.g. ``pixelbuffer=1`` increases the tile size to 258x258px).

Returns ``left``, ``bottom``, ``right``, ``top`` coordinates of given tile.

### Get tile bounding box
```python
tile_bbox(self, zoom, row, col, pixelbuffer=None)
```
Returns the bounding box for given tile as a ``Polygon``.

### Get all tiles within bounding box
```python
tiles_from_bbox(self, geometry, zoom)
```
* ``geometry``: Must be a ``Polygon`` object.

Returns tiles intersecting with the given bounding box at given zoom level.

### Get all tiles intersecting with geometry
```python
tiles_from_geom(self, geometry, zoom):
```
* ``geometry``: Must be one out of ``Polygon``, ``MultiPolygon``, ``LineString``, ``MultiLineString``, ``Point``, ``MultiPoint``.

Returns tiles intersecting with the given geometry at given zoom level.


