# The tilematrix objects

## Tile

**Create a Tile object**
```python
Tile(tile_pyramid, zoom, row, col)
```
* ``self.type``: A ``TilePyramid`` or ``MetaTilePyramid`` this tile inherits certain attributes from.
* ``self.zoom``: Tile zoom level.
* ``self.row``: Tile row.
* ``self.col``: Tile column.

After initializing, the object has the following properties:
* ``self.tile_pyramid``: ``TilePyramid`` or ``MetaTilePyramid`` it was initialized with.
* ``self.crs``: Coordinate reference system.
* ``self.zoom``: Zoom.
* ``self.row``: Row.
* ``self.col``: Col.
* ``self.x_size``: Horizontal size in SRID units.
* ``self.y_size``: Vertical size in SRID units.
* ``self.id``: Tuple of ``(zoom, col, row)``
* ``self.pixel_x_size``: Horizontal pixel size in SRID units.
* ``self.pixel_y_size``: Vertical pixel size in SRID units.
* ``self.left``: Left coordinate.
* ``self.top``: Top coordinate.
* ``self.right``: Right coordinate.
* ``self.bottom``: Bottom coordinate.
* ``self.width``: Horizontal size in pixels.
* ``self.height``: Vertical size in pixels.

**Get tile bounds**
```python
bounds(self, pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a tuple of ``(left, bottom, right, top)`` coordinates.

**Get tile bounding box**
```python
bbox(self, pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a ``Polygon`` geometry.

**Get affine matrix**
```python
affine(self, pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns an ``affine`` object.

**Get tile shape**
```python
shape(self, pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a tuple with ``(width, height)``.

**Check validity**
```python
is_valid(self)
```

Returns ``True`` if tile ID is valid in this tile matrix and ``False`` if it isn't.

**Get tile neighbors**
```python
bbox(self, count=0)
```
* ``count``: Number of neighbors to be returned (maximum 8).

Returns neighbor tiles.

## TilePyramid

**Create a TilePyramid object**
```python
TilePyramid(projection, tile_size=256)
```
* ``type``: One out of ``geodetic`` or ``mercator``, although currently only ``geodetic`` is supported.
* ``tile_size``: Optional, specifies the target resolution of each tile (i.e. each tile will have 256x256 px). Default is ``256``.

After that, the object has the following properties:
* ``self.type``: The projection it was initialized with (either ``geodetic`` or ``mercator``).
* ``self.tile_size``: The pixelsize per tile it was initialized with (default ``256``).
* ``self.left``: Left boundary of tile matrix.
* ``self.top``: Top boundary of tile matrix.
* ``self.right ``: Right boundary of tile matrix.
* ``self.bottom ``: Bottom boundary of tile matrix.
* ``self.x_size``: Horizontal size of tile matrix in map coordinates.
* ``self.y_size``: Vertical size of tile matrix in map coordinates.
* ``self.crs``: CRS (e.g. ``{'init': u'EPSG:4326'}``)
* ``self.format``: Output format. Set to ``None`` in the beginning.

**Define output format/profile**
```python
set_format(self, output_format, dtype=None)
```
* ``output_format``: Currently the following formats are avaliable: ``"GTiff"``, ``"PNG"``, ``"PNG_hillshade"`` and ``"GeoJSON"``.
* ``dtype``: For ``"GTiff"``, the output datadype can be defined as well (e.g. ``"uInt16"``, ``"uInt8"``, etc.). ``None`` keeps the datatyp from the input file.

**Get tile matrix width (number of columns) at zoom level**
```python
matrix_width(self, zoom)
```
* ``zoom``: Zoom level.
Returns the number of columns in the current tile matrix.

**Get tile matrix height (number of rows) at zoom level**
```python
matrix_height(self, zoom)
```
Returns the number of rows in the current tile matrix.

**Get width of tile in SRID units at zoom level**
```python
tile_x_size(self, zoom)
```
Returns a float, indicating the width of each tile at this zoom level in TilePyramid CRS units

**Get height of tile in SRID units at zoom level**
```python
tile_y_size(self, zoom)
```
Returns a floats, indicating the height of each tile at this zoom level in TilePyramid CRS units.

**Get vertical pixelsize in SRID units at zoom level**
```python
pixel_x_size(self, zoom)
```
Returns a float, indicating the vertical pixel size in TilePyramid CRS units.

**Get horizontal pixelsize in SRID units at zoom level**
```python
pixel_y_size(self, zoom)
```
Returns a float, indicating the horizontal pixel size in TilePyramid CRS units.

**Get top left tile coordinates**
```python
top_left_tile_coords(self, zoom, row, col)
```
* ``row``: Row in TilePyramid.
* ``col``: Column in TilePyramid.

Returns a tuple of two floats, indicating the top left coordinates of the given tile.

**Get tile bounds**
```python
tile_bounds(self, zoom, row, col, pixelbuffer=None)
```
* ``pixelbuffer``: Optional, integer defining the width of the additional margin to take into account (e.g. ``pixelbuffer=1`` increases the tile size to 258x258px).

Returns ``left``, ``bottom``, ``right``, ``top`` coordinates of given tile.

**Get tile bounding box**
```python
tile_bbox(self, zoom, row, col, pixelbuffer=None)
```
Returns the bounding box for given tile as a ``Polygon``.

**Get all tiles within bounding box**
```python
tiles_from_bbox(self, geometry, zoom)
```
* ``geometry``: Must be a ``Polygon`` object.

Returns tiles intersecting with the given bounding box at given zoom level.

**Get all tiles intersecting with geometry**
```python
tiles_from_geom(self, geometry, zoom):
```
* ``geometry``: Must be one out of ``Polygon``, ``MultiPolygon``, ``LineString``, ``MultiLineString``, ``Point``, ``MultiPoint``.

Returns tiles intersecting with the given geometry at given zoom level.


## MetaTilePyramid

A ``MetaTilePyramid`` object needs a ``TilePyramid`` object to be initialized and shares all its attributes and functions. It is basically a commen tile matrix with bigger tiles. This is usefull, as processing bigger tiles increases the performance.

**Create a MetaTilePyramid object**
```python
MetaTilePyramid(TilePyramid, metatiles=1)
```
* ``TilePyramid``: The ``TilePyramid`` it builds on.
* ``metatiles``: Defines the metatile size. A value of 2 for example concatenates 2x2 ``TilePyramid`` tiles into one metatile. It should have one of these values: 2, 4, 8, 16. Note: a ``metatile`` value of 1 means no metatiling, i.e. the MetaTilePyramid is equal to the TilePyramid.

In addition to the basic properties it inherits from the source ``TilePyramid``, it inherits the following:
* ``self.tilepyramid``: The ``TilePyramid`` it builds on.
* ``self.metatiles``: The ``metatiles`` value it was initialized with.
