#!/usr/bin/env python

import os
import rasterio
from rasterio.warp import *
import numpy as np
import numpy.ma as ma
from copy import deepcopy

from tilematrix import *

def read_raster_window(
    input_file,
    tile_pyramid,
    tile,
    pixelbuffer=0,
    resampling=RESAMPLING.nearest
    ):
    """
    Reads an input raster dataset with rasterio and resamples array to target
    tile. Returns a tuple of (metadata, data), where metadata is a rasterio
    meta dictionary and data a multidimensional numpy array.
    """

    try:
        assert (isinstance(tile_pyramid, TilePyramid) or
            isinstance(tile_pyramid, MetaTilePyramid))
    except:
        raise ValueError("no valid tile matrix given.")

    try:
        assert os.path.isfile(input_file)
    except:
        raise IOError("input file does not exist: %s" % input_file)

    zoom, row, col = tile

    src_bbox = raster_bbox(input_file, tile_pyramid.crs)
    dst_tile_size = tile_pyramid.tile_size + 2 * pixelbuffer
    dst_shape = (dst_tile_size, dst_tile_size)
    tile_geom = tile_pyramid.tile_bbox(zoom, row, col, pixelbuffer)
    with rasterio.open(input_file, "r") as src:
        out_meta = src.meta
        # return array filled with NAN values if tile does not intersect with
        # input data
        try:
            assert tile_geom.intersects(src_bbox)
        except:
            out_data = ()
            for i, dtype in zip(src.indexes, src.dtypes):
                out_data + (np.empty(shape=(dst_shape), dtype=dtype),)
            return out_meta, out_data


        # Compute target window in source file.
        left, bottom, right, top = tile_pyramid.tile_bounds(
            zoom,
            row,
            col,
            pixelbuffer
            )
        out_left, out_bottom, out_right, out_top = transform_bounds(
            tile_pyramid.crs,
            src.crs,
            left,
            bottom,
            right,
            top,
            densify_pts=21
            )
        # Compute target affine
        dst_affine = calculate_default_transform(
            src.crs,
            tile_pyramid.crs,
            dst_tile_size,
            dst_tile_size,
            out_left,
            out_bottom,
            out_right,
            out_top,
            resolution=(
                tile_pyramid.pixel_x_size(zoom),
                tile_pyramid.pixel_y_size(zoom)
            )
        )[0]

        # minrow, mincol = src.index(out_left, out_top)
        # maxrow, maxcol = src.index(out_right, out_bottom)
        # has rasterio indexing changed?
        minrow, maxcol = src.index(out_left, out_top)
        maxrow, mincol = src.index(out_right, out_bottom)
        window = (minrow, maxrow), (mincol, maxcol)
        window_vector_affine = src.affine.translation(
            mincol,
            minrow
            )
        window_affine = src.affine * window_vector_affine

        # Finally read data.
        out_data = ()
        for index, dtype, nodataval in zip(
            src.indexes,
            src.dtypes,
            src.nodatavals
            ):
            src_band_data = _read_band_to_tile(
                index,
                src,
                window
            )
            dst_band_data = np.empty(shape=(dst_shape), dtype=dtype)
            # quick fix because None nodata is not allowed
            if not nodataval:
                nodataval = 0
            try:
                reproject(
                    src_band_data,
                    dst_band_data,
                    src_transform=window_affine,
                    src_crs=src.crs,
                    src_nodata=nodataval,
                    dst_transform=dst_affine,
                    dst_crs=tile_pyramid.crs,
                    dst_nodata=nodataval,
                    resampling=resampling)
            except:
                raise
            dst_band_data = ma.masked_equal(dst_band_data, nodataval)
            out_data = out_data + (dst_band_data, )

        out_meta = src.meta
        out_meta['affine'] = dst_affine
        out_meta['transform'] = dst_affine.to_gdal()
        out_meta['height'] = dst_tile_size
        out_meta['width'] = dst_tile_size

    return out_meta, out_data


def write_raster_window(
    output_file,
    tile_pyramid,
    tile,
    metadata,
    bands,
    pixelbuffer=0):

    return None


# auxiliary

def raster_bbox(dataset, crs):
    """
    Returns the bounding box of a raster file in a given CRS.
    """

    with rasterio.open(dataset) as raster:

        out_left, out_bottom, out_right, out_top = transform_bounds(
            raster.crs, crs, raster.bounds.left,
            raster.bounds.bottom, raster.bounds.right, raster.bounds.top,
            densify_pts=21)

    tl = [out_left, out_top]
    tr = [out_right, out_top]
    br = [out_right, out_bottom]
    bl = [out_left, out_bottom]
    bbox = Polygon([tl, tr, br, bl])

    return bbox

def _read_band_to_tile(
    index,
    src,
    window
    ):
    """
    Reads window of a raster and if window is outside of input raster bounds,
    fills these values with numpy nan. Returns a metadata and data tuple.
    """

    (minrow, maxrow), (mincol, maxcol) = window
    window_offset_row = minrow
    window_offset_col = mincol
    minrow, minrow_offset = _clean_coord_offset(
        minrow,
        src.shape[0]
        )
    maxrow, maxrow_offset = _clean_coord_offset(
        maxrow,
        src.shape[0]
        )
    mincol, mincol_offset = _clean_coord_offset(
        mincol,
        src.shape[1]
        )
    maxcol, maxcol_offset = _clean_coord_offset(
        maxcol,
        src.shape[1]
        )
    rows = (minrow, maxrow)
    cols = (mincol, maxcol)

    window_data = src.read(index, window=(rows, cols), masked=True)
    if minrow_offset:
        nullarray = np.empty(
            (minrow_offset, window_data.shape[1]),
            dtype=window_data.dtype
            )
        # nullarray[:] = src.nodata
        newarray = np.concatenate((nullarray, window_data), axis=0)
        window_data = newarray
    if maxrow_offset:
        nullarray = np.empty(
            (maxrow_offset, window_data.shape[1]),
            dtype=window_data.dtype
            )
        # nullarray[:] = src.nodata
        newarray = np.concatenate((window_data, nullarray), axis=0)
        window_data = newarray
    if mincol_offset:
        nullarray = np.empty(
            (window_data.shape[0], mincol_offset),
            dtype=window_data.dtype
            )
        # nullarray[:] = src.nodata
        newarray = np.concatenate((nullarray, window_data), axis=1)
        window_data = newarray
    if maxcol_offset:
        nullarray = np.empty(
            (window_data.shape[0], maxcol_offset),
            dtype=window_data.dtype
            )
        # nullarray[:] = src.nodata
        newarray = np.concatenate((window_data, nullarray), axis=1)
        window_data = newarray

    return window_data



def _clean_coord_offset(px_coord, maximum):
    """
    Crops pixel coordinate to 0 and maximum (array.shape) if necessary. Returns
    new pixel value and an offset if necessary.
    """
    offset = None
    if px_coord < 0:
        offset = -px_coord
        px_coord = 0
    if px_coord > maximum:
        offset = px_coord - maximum
        px_coord = maximum
    return px_coord, offset
