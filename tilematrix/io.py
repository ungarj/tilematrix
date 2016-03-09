#!/usr/bin/env python

import os
import fiona
import rasterio
from rasterio.warp import (
    transform_bounds,
    reproject,
    calculate_default_transform
    )
from rasterio.warp import RESAMPLING
from affine import Affine
import numpy as np
import numpy.ma as ma
from copy import deepcopy
from shapely.wkt import loads
from shapely.ops import transform
from shapely.validation import explain_validity
import ogr
from functools import partial
import pyproj

from tilematrix import *

resampling_methods = {
    "nearest": RESAMPLING.nearest,
    "bilinear": RESAMPLING.bilinear,
    "cubic": RESAMPLING.cubic,
    "cubic_spline": RESAMPLING.cubic_spline,
    "lanczos": RESAMPLING.lanczos,
    "average": RESAMPLING.average,
    "mode": RESAMPLING.mode
}

def read_vector_window(
    input_file,
    tile,
    pixelbuffer=0
    ):
    """
    Reads an input vector dataset with fiona using the tile bounding box as
    filter and clipping geometry. Returns a list of GeoJSON like features.
    """

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


    # TODO reproject tile_bounds to input file crs and reproject output clip to
    # tile_pyramid crs

    with fiona.open(input_file, 'r') as vector:
        features_clipped = [
            {
                'properties': feature['properties'],
                'geometry': mapping(
                    tile.bbox(pixelbuffer=pixelbuffer).intersection(
                        shape(feature['geometry'])
                    )
                )
            }
            for feature in vector.filter(
                bbox=tile.bounds(pixelbuffer=pixelbuffer)
            )
        ]

    return features_clipped

def read_raster_window(
    input_file,
    tile,
    indexes=None,
    pixelbuffer=0,
    resampling="nearest"
    ):
    """
    Generates numpy arrays from input raster.
    """
    try:
        assert os.path.isfile(input_file)
    except:
        raise IOError("input file not found %s" % input_file)
    with rasterio.open(input_file, "r") as src:

        if indexes:
            if isinstance(indexes, list):
                band_indexes = indexes
            else:
                band_indexes = [indexes]
        else:
            band_indexes = src.indexes

        # Reproject tile bounds to source file SRS.
        src_left, src_bottom, src_right, src_top = transform_bounds(
            tile.crs,
            src.crs,
            *tile.bounds(pixelbuffer=pixelbuffer),
            densify_pts=21
            )

        nodataval = src.nodata
        # Quick fix because None nodata is not allowed.
        if not nodataval:
            nodataval = 0

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
        bands = (
            src.read(index, window=window, masked=True, boundless=True)
            for index in band_indexes
            )
        for index in band_indexes:
            dst_band = np.ma.zeros(
                shape=(tile.shape(pixelbuffer=pixelbuffer)),
                dtype=src.dtypes[index-1]
            )
            dst_band[:] = nodataval
            reproject(
                next(bands),
                dst_band,
                src_transform=window_affine,
                src_crs=src.crs,
                src_nodata=nodataval,
                dst_transform=tile.affine(pixelbuffer=pixelbuffer),
                dst_crs=tile.crs,
                dst_nodata=nodataval,
                resampling=resampling_methods[resampling]
            )
            dst_band = ma.masked_equal(dst_band, nodataval)

            yield dst_band


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

    if tile_pyramid.format.name == "PNG":
        mask = ma.getmask(bands[0], )
        nodata_alpha = np.zeros(bands[0].shape)
        nodata_alpha[:] = 255
        nodata_alpha[mask] = 0
        dst_bands.append(nodata_alpha[px_top:px_bottom, px_left:px_right])


    # write to output file
    dst_metadata = deepcopy(tile_pyramid.format.profile)
    dst_metadata.pop("transform", None)
    dst_metadata["nodata"] = metadata["nodata"]
    dst_metadata["crs"] = tile_pyramid.crs['init']
    dst_metadata["width"] = dst_width
    dst_metadata["height"] = dst_height
    dst_metadata["affine"] = dst_affine
    dst_metadata["count"] = len(dst_bands)
    dst_metadata["dtype"] = dst_bands[0].dtype.name
    try:
        dst_metadata.update(compress=metadata["compress"])
    except:
        pass
    try:
        dst_metadata.update(predictor=metadata["predictor"])
    except:
        pass
    if tile_pyramid.format.name in ("PNG", "PNG_hillshade"):
        dst_metadata.update(dtype='uint8')
    with rasterio.open(output_file, 'w', **dst_metadata) as dst:
        for band, data in enumerate(dst_bands):
            data = np.ma.filled(data, dst_metadata["nodata"])
            dst.write(
                data.astype(dst_metadata["dtype"]),
                (band+1)
            )


# Auxiliary functions
#####################


def file_bbox(
    input_file,
    tile_pyramid
):
    """
    Returns the bounding box of a raster or vector file in a given CRS.
    """
    out_crs = tile_pyramid.crs
    # Read raster data with rasterio, vector data with fiona.
    try:
        with rasterio.open(input_file) as inp:
            inp_crs = inp.crs
            left = inp.bounds.left
            bottom = inp.bounds.bottom
            right = inp.bounds.right
            top = inp.bounds.top
    except IOError:
        with fiona.open(input_file) as inp:
            inp_crs = inp.srs
            left, bottom, right, top = inp.bounds

    # Create bounding box polygon.
    tl = [left, top]
    tr = [right, top]
    br = [right, bottom]
    bl = [left, bottom]
    bbox = Polygon([tl, tr, br, bl])
    out_bbox = bbox
    # If soucre and target CRSes differ, segmentize and reproject
    if inp_crs != out_crs:
        segmentize = _get_segmentize_value(input_file, tile_pyramid)
        try:
            ogr_bbox = ogr.CreateGeometryFromWkb(bbox.wkb)
            ogr_bbox.Segmentize(segmentize)
            segmentized_bbox = loads(ogr_bbox.ExportToWkt())
            bbox = segmentized_bbox
            project = partial(
                pyproj.transform,
                pyproj.Proj(inp_crs),
                pyproj.Proj(out_crs)
            )
            out_bbox = transform(project, bbox)
        except:
            raise
    else:
        out_bbox = bbox

    # Validate and, if necessary, try to fix output geometry.
    try:
        assert out_bbox.is_valid
    except:
        cleaned = out_bbox.buffer(0)
        try:
            assert cleaned.is_valid
        except:
            raise TypeError(cleaned.explain_validity)
        out_bbox = cleaned
    return out_bbox


def _get_segmentize_value(input_file, tile_pyramid):
    """
    Returns the recommended segmentize value in input file units.
    """
    with rasterio.open(input_file, "r") as input_raster:
        pixelsize = input_raster.affine[0]

    return pixelsize * tile_pyramid.tile_size


def get_best_zoom_level(input_file, tile_pyramid_type):
    """
    Determines the best base zoom level for a raster. "Best" means the maximum
    zoom level where no oversampling has to be done.
    """
    tile_pyramid = TilePyramid(tile_pyramid_type)
    dst_crs = tile_pyramid.crs
    with rasterio.open(input_file, "r") as input_raster:
        src_crs = input_raster.crs
        src_width = input_raster.width
        src_height = input_raster.height
        src_left, src_bottom, src_right, src_top = input_raster.bounds

    xmin, ymin, xmax, ymax = transform_bounds(
        src_crs,
        dst_crs,
        src_left,
        src_bottom,
        src_right,
        src_top
        )

    x_dif = xmax - xmin
    y_dif = ymax - ymin
    size = float(src_width + src_height)
    avg_resolution = (
        (x_dif / float(src_width)) * (float(src_width) / size) +
        (y_dif / float(src_height)) * (float(src_height) / size)
    )

    for zoom in range(0, 25):
        if (tile_pyramid.pixel_x_size(zoom) < avg_resolution):
            return zoom-1

    raise ValueError("no fitting zoom level found")
