# Examples

```python
from tilematrix import TilePyramid
from shapely.geometry import Polygon

# initialize TilePyramid
tile_pyramid = TilePyramid("geodetic")

some_polygon = Polygon([(0, 0), (1, 1), (1, 0)])
zoom = 8

```

Now, let's get all tile IDs (zoom, row, col) of tiles intersecting with our
example geometry:

```python
for tile in tile_pyramid.tiles_from_geom(some_polygon, zoom):
    print tile.id

```

output:
```python
(8, 126, 256)
(8, 126, 257)
(8, 127, 256)
(8, 127, 257)

```

Use the ``bbox()`` method to get the tile bounding box geometries:
```python
for tile in tile_pyramid.tiles_from_geom(some_polygon, zoom):
    print tile.bbox()
```

output:
```python
POLYGON ((0 1.40625, 0.703125 1.40625, 0.703125 0.703125, 0 0.703125, 0 1.40625))
POLYGON ((0.703125 1.40625, 1.40625 1.40625, 1.40625 0.703125, 0.703125 0.703125, 0.703125 1.40625))
POLYGON ((0 0.703125, 0.703125 0.703125, 0.703125 0, 0 0, 0 0.703125))
POLYGON ((0.703125 0.703125, 1.40625 0.703125, 1.40625 0, 0.703125 0, 0.703125 0.703125))
```

We can also create a buffer around the tiles, using the ``pixelbuffer`` argument. A value of 1 will create a 1 px buffer around the tile. This depends on the initial pixel "resolution" the ``TilePyramid`` was initialized with (default ``256``).
```python
for tile in tile_pyramid.tiles_from_geom(some_polygon, zoom):
    print tile.bbox(pixelbuffer=1)
```

output:
```python
POLYGON ((-0.00274658203125 1.40899658203125, 0.70587158203125 1.40899658203125, 0.70587158203125 0.70037841796875, -0.00274658203125 0.70037841796875, -0.00274658203125 1.40899658203125))
POLYGON ((0.70037841796875 1.40899658203125, 1.40899658203125 1.40899658203125, 1.40899658203125 0.70037841796875, 0.70037841796875 0.70037841796875, 0.70037841796875 1.40899658203125))
POLYGON ((-0.00274658203125 0.70587158203125, 0.70587158203125 0.70587158203125, 0.70587158203125 -0.00274658203125, -0.00274658203125 -0.00274658203125, -0.00274658203125 0.70587158203125))
POLYGON ((0.70037841796875 0.70587158203125, 1.40899658203125 0.70587158203125, 1.40899658203125 -0.00274658203125, 0.70037841796875 -0.00274658203125, 0.70037841796875 0.70587158203125))
```
