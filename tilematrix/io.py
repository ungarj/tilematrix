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
    resampling=Resampling.nearest
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

    try:
        assert pixelbuffer >= 0
    except:
        raise ValueError("pixelbuffer must be 0 or greater")

    try:
        assert isinstance(pixelbuffer, int)
    except:
        raise ValueError("pixelbuffer must be an integer")

    zoom, row, col = tile

    src_bbox = raster_bbox(input_file, tile_pyramid.crs)
    dst_tile_size = tile_pyramid.tile_size + 2 * pixelbuffer
    dst_shape = (dst_tile_size, dst_tile_size)
    tile_geom = tile_pyramid.tile_bbox(zoom, row, col, pixelbuffer)
    with rasterio.open(input_file, "r") as src:
        out_meta = src.meta
        nodataval = src.nodata
        # Quick fix because None nodata is not allowed.
        if not nodataval:
            nodataval = 0

        # Return array filled with NAN values if tile does not intersect with
        # input raster.
        try:
            assert tile_geom.intersects(src_bbox)
        except:
            out_data = ()
            for i, dtype in zip(src.indexes, src.dtypes):
                out_data + (np.zeros(shape=(dst_shape), dtype=dtype),)
                out_data[:] = nodataval
            return out_meta, out_data

        # Get tile bounds including pixel buffer.
        tile_left, tile_bottom, tile_right, tile_top = tile_pyramid.tile_bounds(
            zoom,
            row,
            col,
            pixelbuffer
            )

        # Create tile affine
        px_size = tile_pyramid.pixel_x_size(zoom)
        tile_geotransform = (tile_left, px_size, 0.0, tile_top, 0.0, -px_size)
        tile_affine = Affine.from_gdal(*tile_geotransform)

        # Reproject tile bounds to source file SRS.
        src_left, src_bottom, src_right, src_top = transform_bounds(
            tile_pyramid.crs,
            src.crs,
            tile_left,
            tile_bottom,
            tile_right,
            tile_top,
            densify_pts=21
            )

        minrow, mincol = src.index(src_left, src_top)
        maxrow, maxcol = src.index(src_right, src_bottom)

        # Calculate new Affine object for read window.
        window = (minrow, maxrow), (mincol, maxcol)
        window_vector_affine = src.affine.translation(
            mincol,
            minrow
            )
        window_affine = src.affine * window_vector_affine

        # Finally read data per band and store it in tuple.
        out_data = ()
        for index, dtype in zip(
            src.indexes,
            src.dtypes
            ):
            src_band_data = _read_band_to_tile(
                index,
                src,
                window,
                nodataval
            )
            dst_band_data = np.zeros(shape=(dst_shape), dtype=dtype)
            dst_band_data[:] = nodataval
            try:
                reproject(
                    src_band_data,
                    dst_band_data,
                    src_transform=window_affine,
                    src_crs=src.crs,
                    src_nodata=nodataval,
                    dst_transform=tile_affine,
                    dst_crs=tile_pyramid.crs,
                    dst_nodata=nodataval,
                    resampling=resampling)
            except:
                raise
            dst_band_data = ma.masked_equal(dst_band_data, nodataval)
            out_data = out_data + (dst_band_data, )

        # Create output metadata
        out_meta = src.meta
        out_meta['nodata'] = nodataval
        out_meta['affine'] = tile_affine
        out_meta['transform'] = tile_geotransform
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
    """
    Writes numpy array into a TilePyramid tile.
    """
    try:
        assert (isinstance(tile_pyramid, TilePyramid) or
            isinstance(tile_pyramid, MetaTilePyramid))
    except:
        raise ValueError("no valid tile matrix given")

    try:
        assert pixelbuffer >= 0
    except:
        raise ValueError("pixelbuffer must be 0 or greater")

    try:
        assert isinstance(pixelbuffer, int)
    except:
        raise ValueError("pixelbuffer must be an integer")

    zoom, row, col = tile

    # get write window bounds (i.e. tile bounds plus pixelbuffer) in affine
    dst_left, dst_bottom, dst_right, dst_top = tile_pyramid.tile_bounds(zoom,
        row, col, pixelbuffer)

    dst_width = tile_pyramid.tile_size + (pixelbuffer * 2)
    dst_height = tile_pyramid.tile_size + (pixelbuffer * 2)
    pixel_x_size = tile_pyramid.pixel_x_size(zoom)
    pixel_y_size = tile_pyramid.pixel_y_size(zoom)
    dst_affine = calculate_default_transform(
        tile_pyramid.crs,
        tile_pyramid.crs,
        dst_width,
        dst_height,
        dst_left,
        dst_bottom,
        dst_right,
        dst_top,
        resolution=(
            tile_pyramid.pixel_x_size(zoom),
            tile_pyramid.pixel_y_size(zoom)
        ))[0]

    # convert to pixel coordinates
    affine = metadata["affine"]
    input_left, input_top = affine * (0, 0)
    input_right, input_bottom = affine * (metadata["width"], metadata["height"])
    ul = input_left, input_top
    ur = input_right, input_top
    lr = input_right, input_bottom
    ll = input_left, input_bottom
    px_left = int(round(((dst_left - input_left) / pixel_x_size), 0))
    px_bottom = int(round(((input_top - dst_bottom) / pixel_y_size), 0))
    px_right = int(round(((dst_right - input_left) / pixel_x_size), 0))
    px_top = int(round(((input_top - dst_top) / pixel_y_size), 0))
    window = (px_top, px_bottom), (px_left, px_right)

    dst_bands = []

    if tile_pyramid.format.name == "PNG_hillshade":
        zeros = np.zeros(bands[0][px_top:px_bottom, px_left:px_right].shape)
        for band in range(1,4):
            dst_bands.append(zeros)

    for band in bands:
        dst_bands.append(band[px_top:px_bottom, px_left:px_right])

    # write to output file
    dst_metadata = deepcopy(tile_pyramid.format.profile)
    dst_metadata["nodata"] = metadata["nodata"]
    dst_metadata["crs"] = tile_pyramid.crs['init']
    dst_metadata["width"] = dst_width
    dst_metadata["height"] = dst_height
    dst_metadata["affine"] = dst_affine
    dst_metadata["transform"] = dst_affine.to_gdal()
    dst_metadata["count"] = len(dst_bands)
    dst_metadata["dtype"] = dst_bands[0].dtype.name
    if tile_pyramid.format.name in ("PNG", "PNG_hillshade"):
        dst_metadata.update(dtype='uint8')
    with rasterio.open(output_file, 'w', **dst_metadata) as dst:
        for band, data in enumerate(dst_bands):
            dst.write_band(
                (band+1),
                data.astype(dst_metadata["dtype"])
            )


# Auxiliary functions
#####################

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
    window,
    nodataval
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
        nullarray = np.zeros(
            (minrow_offset, window_data.shape[1]),
            dtype=window_data.dtype
            )
        nullarray[:] = nodataval
        newarray = np.concatenate((nullarray, window_data), axis=0)
        window_data = newarray
    if maxrow_offset:
        nullarray = np.zeros(
            (maxrow_offset, window_data.shape[1]),
            dtype=window_data.dtype
            )
        nullarray[:] = nodataval
        newarray = np.concatenate((window_data, nullarray), axis=0)
        window_data = newarray
    if mincol_offset:
        nullarray = np.zeros(
            (window_data.shape[0], mincol_offset),
            dtype=window_data.dtype
            )
        nullarray[:] = nodataval
        newarray = np.concatenate((nullarray, window_data), axis=1)
        window_data = newarray
    if maxcol_offset:
        nullarray = np.zeros(
            (window_data.shape[0], maxcol_offset),
            dtype=window_data.dtype
            )
        nullarray[:] = nodataval
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
