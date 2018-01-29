# tilematrix

The two base classes are ``TilePyramid`` which defines tile matrices in various zoom levels and its members, the``Tile`` objects. ``TilePyramid``

## TilePyramid

```python
TilePyramid(grid_definition, tile_size=256)
```
* ``grid_definition``: Either one of the predefined grids (``geodetic`` or
    ``mercator``) or a custom grid definition in form of a dictionary. For example:
    ```python
    {
        "shape": (1, 1),
        "bounds": (2426378.0132, 1528101.2618, 6293974.6215, 5395697.8701),
        "is_global": False,
        "epsg": 3035
    }
    ```
    * ``shape`` (width, height): Indicates the number of tiles per column and row at **zoom level 0**.
    * ``bounds`` (left, bottom, right, top): Units are CRS units.

    Please note that the aspect ratios of ``shape`` and ``bounds`` have to be the same.
    * Alternatively to ``epsg``, a custom ``proj`` string can be used:
    ```python
    "proj": """
        +proj=ortho
        +lat_0=-90
        +lon_0=0
        +x_0=0
        +y_0=0
        +ellps=WGS84
        +units=m +no_defs
    """
    ```
    * ``is_global``: Indicates whether the grid covers the whole globe or just a region.

* ``tile_size``: Optional, specifies the target resolution of each tile (i.e. each tile will have 256x256 px). Default is ``256``.

### Variables
* ``type``: The projection it was initialized with (``geodetic``, ``mercator`` or ``custom``).
* ``tile_size``: The pixelsize per tile it was initialized with (default ``256``).
* ``left``: Left boundary of tile matrix.
* ``top``: Top boundary of tile matrix.
* ``right ``: Right boundary of tile matrix.
* ``bottom ``: Bottom boundary of tile matrix.
* ``x_size``: Horizontal size of tile matrix in map coordinates.
* ``y_size``: Vertical size of tile matrix in map coordinates.
* ``crs``: ``rasterio.crs.CRS()`` object.
* ``srid``: Spatial reference ID (EPSG code) if available, else ``None``.

### Methods

#### Matrix properties
* ``matrix_width(zoom)``: Returns the number of columns in the current tile matrix.
    * ``zoom``: Zoom level.
* ``matrix_height(zoom)``: Returns the number of rows in the current tile matrix.
    * ``zoom``: Zoom level.

#### Geometry
* ``tile_x_size(zoom)``: Returns a float, indicating the width of each tile at this zoom level in ``TilePyramid`` CRS units.
    * ``zoom``: Zoom level.
* ``tile_y_size(zoom)``: Returns a floats, indicating the height of each tile at this zoom level in ``TilePyramid`` CRS units.
    * ``zoom``: Zoom level.
* ``pixel_x_size(zoom)``: Returns a float, indicating the vertical pixel size in ``TilePyramid`` CRS units.
    * ``zoom``: Zoom level.
* ``pixel_y_size(zoom)``: Returns a float, indicating the horizontal pixel size in ``TilePyramid`` CRS units.
    * ``zoom``: Zoom level.
* ``top_left_tile_coords(zoom, row, col)``: Returns a tuple of two floats, indicating the top left coordinates of the given tile.
    * ``zoom``: Zoom level.
    * ``row``: Row in ``TilePyramid``.
    * ``col``: Column in ``TilePyramid``.
* ``tile_bounds(zoom, row, col, pixelbuffer=None)``: Returns ``left``, ``bottom``, ``right``, ``top`` coordinates of given tile.
    * ``zoom``: Zoom level.
    * ``row``: Row in ``TilePyramid``.
    * ``col``: Column in ``TilePyramid``.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.
* ``tile_bbox(zoom, row, col, pixelbuffer=None)``: Returns the bounding box for given tile as a ``Polygon``.
    * ``zoom``: Zoom level.
    * ``row``: Row in ``TilePyramid``.
    * ``col``: Column in ``TilePyramid``.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.


#### Tiles
* ``intersecting(tile)``: Return all tiles intersecting with tile. This helps translating between TilePyramids with different metatiling settings.
    * ``tile``: ``Tile`` object.
* ``tiles_from_bbox(geometry, zoom)``: Returns tiles intersecting with the given bounding box at given zoom level.
    * ``geometry``: Must be a ``Polygon`` object.
    * ``zoom``: Zoom level.
* ``tiles_from_geom(geometry, zoom)``: Returns tiles intersecting with the given geometry at given zoom level.
    * ``geometry``: Must be one out of ``Polygon``, ``MultiPolygon``, ``LineString``, ``MultiLineString``, ``Point``, ``MultiPoint``.
    * ``zoom``: Zoom level.


## Tile

```python
Tile(tile_pyramid, zoom, row, col)
```
* ``tile_pyramid``: A ``TilePyramid`` this Tile belongs to.
* ``zoom``: Tile zoom level.
* ``row``: Tile row.
* ``col``: Tile column.

### Variables
After initializing, the object has the following properties:
* ``tile_pyramid`` or ``tp``: ``TilePyramid`` this Tile belongs to.
* ``crs``: ``rasterio.crs.CRS()`` object.
* ``srid``: Spatial reference ID (EPSG code) if available, else ``None``.
* ``zoom``: Zoom.
* ``row``: Row.
* ``col``: Col.
* ``x_size``: Horizontal size in SRID units.
* ``y_size``: Vertical size in SRID units.
* ``index`` or ``id``: Tuple of ``(zoom, col, row)``
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
* ``get_parent()``: Returns parent Tile.
* ``get_children()``: Returns children Tiles.
* ``get_neighbors(connectedness=8)``: Returns a maximum of 8 valid neighbor Tiles.
    * ``connectedness``: ``4`` or ``8``. Direct neighbors (up to 4) or corner neighbors (up to 8).
* ``intersecting(TilePyramid)``: Return all tiles from other TilePyramid intersecting with tile. This helps translating between TilePyramids with different metatiling
settings.
    * ``tilepyramid``: ``TilePyramid`` object.


#### Geometry
* ``bounds(pixelbuffer=0)``: Returns a tuple of ``(left, bottom, right, top)`` coordinates.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.
* ``bbox(pixelbuffer=0)``: Returns a ``Polygon`` geometry.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.
* ``affine(pixelbuffer=0)``: Returns an [``Affine``](https://github.com/sgillies/affine) object.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.



#### Other
* ``shape(pixelbuffer=0)``: Returns a tuple with ``(height, width)``.
    * ``pixelbuffer``: Optional buffer around tile boundaries in pixels.
* ``is_valid()``: Returns ``True`` if tile ID is valid in this tile matrix and ``False`` if it isn't.
