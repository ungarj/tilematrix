# The tilematrix objects

## Tile

```python
Tile(tile_pyramid, zoom, row, col)
```
* ``tile_pyramid``: A ``TilePyramid`` or ``MetaTilePyramid`` this Tile belongs to.
* ``zoom``: Tile zoom level.
* ``row``: Tile row.
* ``col``: Tile column.

### Variables
After initializing, the object has the following properties:
* ``tile_pyramid``: ``TilePyramid`` or ``MetaTilePyramid`` it was initialized with.
* ``crs``: Coordinate reference system.
* ``zoom``: Zoom.
* ``row``: Row.
* ``col``: Col.
* ``x_size``: Horizontal size in SRID units.
* ``y_size``: Vertical size in SRID units.
* ``id``: Tuple of ``(zoom, col, row)``
* ``pixel_x_size``: Horizontal pixel size in SRID units.
* ``pixel_y_size``: Vertical pixel size in SRID units.
* ``left``: Left coordinate.
* ``top``: Top coordinate.
* ``right``: Right coordinate.
* ``bottom``: Bottom coordinate.
* ``width``: Horizontal size in pixels.
* ``height``: Vertical size in pixels.

### Methods

#### Get other Tiles
```python
get_parent(self)
```
Returns parent Tile.


```python
get_children(self)
```

Returns children Tiles.

```python
get_neighbors(connectedness=8)
```
* ``connectedness``: ``4`` or ``8``. Direct neighbors (up to 4) or corner neighbors (up to 8).

Returns a maximum of 8 valid neighbor Tiles.



#### Geometry
```python
bounds(pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a tuple of ``(left, bottom, right, top)`` coordinates.


```python
bbox(pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a ``Polygon`` geometry.


```python
affine(pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns an [``Affine``](https://github.com/sgillies/affine) object.


#### Other
```python
shape(pixelbuffer=0)
```
* ``pixelbuffer``: Optional buffer around tile boundaries in pixels.

Returns a tuple with ``(height, width)``.


```python
is_valid(self)
```

Returns ``True`` if tile ID is valid in this tile matrix and ``False`` if it isn't.


## TilePyramid

```python
TilePyramid(projection, tile_size=256)
```
* ``type``: One out of ``geodetic`` or ``mercator``.
* ``tile_size``: Optional, specifies the target resolution of each tile (i.e. each tile will have 256x256 px). Default is ``256``.

### Variables
* ``type``: The projection it was initialized with (either ``geodetic`` or ``mercator``).
* ``tile_size``: The pixelsize per tile it was initialized with (default ``256``).
* ``left``: Left boundary of tile matrix.
* ``top``: Top boundary of tile matrix.
* ``right ``: Right boundary of tile matrix.
* ``bottom ``: Bottom boundary of tile matrix.
* ``x_size``: Horizontal size of tile matrix in map coordinates.
* ``y_size``: Vertical size of tile matrix in map coordinates.
* ``crs``: CRS (e.g. ``{'init': u'EPSG:4326'}``)
* ``srid``: Spatial reference ID (e.g. ``4326``)

### Methods

#### Matrix properties
```python
matrix_width(zoom)
```
* ``zoom``: Zoom level.
Returns the number of columns in the current tile matrix.

```python
matrix_height(zoom)
```
Returns the number of rows in the current tile matrix.

#### Geometry
```python
tile_x_size(zoom)
```
Returns a float, indicating the width of each tile at this zoom level in ``TilePyramid`` CRS units

```python
tile_y_size(zoom)
```
Returns a floats, indicating the height of each tile at this zoom level in ``TilePyramid`` CRS units.

```python
pixel_x_size(zoom)
```
Returns a float, indicating the vertical pixel size in ``TilePyramid`` CRS units.

```python
pixel_y_size(zoom)
```
Returns a float, indicating the horizontal pixel size in ``TilePyramid`` CRS units.

```python
top_left_tile_coords(zoom, row, col)
```
* ``row``: Row in ``TilePyramid``.
* ``col``: Column in ``TilePyramid``.

Returns a tuple of two floats, indicating the top left coordinates of the given tile.

```python
tile_bounds(zoom, row, col, pixelbuffer=None)
```
* ``pixelbuffer``: Optional, integer defining the width of the additional margin to take into account (e.g. ``pixelbuffer=1`` increases the tile size to 258x258px).

Returns ``left``, ``bottom``, ``right``, ``top`` coordinates of given tile.

```python
tile_bbox(zoom, row, col, pixelbuffer=None)
```
Returns the bounding box for given tile as a ``Polygon``.

#### Tiles
```python
tiles_from_bbox(geometry, zoom)
```
* ``geometry``: Must be a ``Polygon`` object.

Returns tiles intersecting with the given bounding box at given zoom level.

```python
tiles_from_geom(geometry, zoom):
```
* ``geometry``: Must be one out of ``Polygon``, ``MultiPolygon``, ``LineString``, ``MultiLineString``, ``Point``, ``MultiPoint``.

Returns tiles intersecting with the given geometry at given zoom level.


## MetaTilePyramid

A ``MetaTilePyramid`` object needs a ``TilePyramid`` object to be initialized with. Basically, it is a tile matrix with bigger tiles. This is particularly useful as in some cases processing bigger tiles increases the performance.
It shares all its variables and methods with the underlying ``TilePyramid``.

```python
MetaTilePyramid(TilePyramid, metatiles=1)
```
* ``TilePyramid``: The ``TilePyramid`` it builds on.
* ``metatiles``: Defines the metatile size. A value of 2 for example concatenates 2x2 ``TilePyramid`` tiles into one metatile. It should have one of these values: 2, 4, 8, 16. Note: a ``metatile`` value of 1 means no metatiling, i.e. the MetaTilePyramid is equal to the TilePyramid.

In addition to the basic properties it inherits from the source ``TilePyramid``, it has the following variables:
* ``tile_pyramid``: The ``TilePyramid`` it builds on.
* ``metatiles``: The ``metatiles`` value it was initialized with.
