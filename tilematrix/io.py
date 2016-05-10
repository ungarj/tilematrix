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
from shapely.geometry import *
import ogr
from functools import partial
import pyproj

from tilematrix import *

RESAMPLING_METHODS = {
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
        for feature in vector.filter(
            bbox=tile.bounds(pixelbuffer=pixelbuffer)
        ):
            feature_geom = shape(feature['geometry'])
            geom = clean_geometry_type(
                feature_geom.intersection(
                    tile.bbox(pixelbuffer=pixelbuffer)
                ),
                feature_geom.geom_type
            )
            if geom:
                feature = {
                    'properties': feature['properties'],
                    'geometry': mapping(geom)
                }
                yield feature


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
                (tile.shape(pixelbuffer=pixelbuffer)),
                src.dtypes[index-1]
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
                resampling=RESAMPLING_METHODS[resampling]
            )
            dst_band = ma.masked_equal(dst_band, nodataval)
            dst_band = ma.masked_array(
                dst_band,
                mask=ma.fix_invalid(dst_band, fill_value=0).mask
            )
            dst_band.harden_mask()
            yield dst_band


def write_vector_window(
    output_file,
    tile,
    metadata,
    data,
    pixelbuffer=0):
    """
    Writes GeoJSON-like objects to GeoJSON.
    """
    try:
        assert pixelbuffer >= 0
    except:
        raise ValueError("pixelbuffer must be 0 or greater")

    try:
        assert isinstance(pixelbuffer, int)
    except:
        raise ValueError("pixelbuffer must be an integer")

    with fiona.open(
        output_file,
        'w',
        schema=metadata.schema,
        driver=metadata.driver,
        crs=tile.crs
        ) as dst:
        for feature in data:
            # clip with bounding box
            feature_geom = shape(feature["geometry"])
            clipped = feature_geom.intersection(
                tile.bbox(pixelbuffer)
            )
            out_geom = clipped
            target_type = metadata.schema["geometry"]
            if clipped.geom_type != target_type:
                cleaned = clean_geometry_type(clipped, target_type)
                out_geom = cleaned
            # write output
            if out_geom:
                feature.update(
                    geometry=mapping(out_geom)
                )
                dst.write(feature)


def write_raster_window(
    output_file,
    tile,
    metadata,
    bands,
    pixelbuffer=0):
    """
    Writes numpy array into a TilePyramid tile.
    """
    try:
        assert pixelbuffer >= 0
    except:
        raise ValueError("pixelbuffer must be 0 or greater")

    try:
        assert isinstance(pixelbuffer, int)
    except:
        raise ValueError("pixelbuffer must be an integer")

    # get write window bounds (i.e. tile bounds plus pixelbuffer) in affine
    dst_left, dst_bottom, dst_right, dst_top = tile.bounds(pixelbuffer)

    dst_width, dst_height = tile.shape(pixelbuffer)
    pixel_x_size = tile.pixel_x_size
    pixel_y_size = tile.pixel_y_size
    dst_affine = tile.affine(pixelbuffer)

    # determine pixelbuffer from shape and determine pixel window
    src_pixelbuffer = (bands[0].shape[0] - tile.width) / 2
    px_top, px_left = src_pixelbuffer, src_pixelbuffer
    other_bound = src_pixelbuffer + tile.width
    px_bottom, px_right = other_bound, other_bound

    window = (px_top, px_bottom), (px_left, px_right)

    dst_bands = []

    if tile.tile_pyramid.format.name == "PNG_hillshade":
        zeros = np.zeros(bands[0][px_top:px_bottom, px_left:px_right].shape)
        for band in range(1,4):
            band = np.clip(band, 0, 255)
            dst_bands.append(zeros)

    for band in bands:
        dst_bands.append(band[px_top:px_bottom, px_left:px_right])

    bandcount = tile.tile_pyramid.format.profile["count"]

    if tile.tile_pyramid.format.name == "PNG":
        for band in bands:
            band = np.clip(band, 0, 255)
        if tile.tile_pyramid.format.profile["nodata"]:
            nodata_alpha = np.zeros(bands[0].shape)
            nodata_alpha[:] = 255
            nodata_alpha[bands[0].mask] = 0
            dst_bands.append(nodata_alpha[px_top:px_bottom, px_left:px_right])
            bandcount += 1

    # write to output file
    dst_metadata = deepcopy(tile.tile_pyramid.format.profile)
    dst_metadata.pop("transform", None)
    dst_metadata["crs"] = tile.crs['init']
    dst_metadata["width"] = dst_width
    dst_metadata["height"] = dst_height
    dst_metadata["affine"] = dst_affine

    if tile.tile_pyramid.format.name in ("PNG", "PNG_hillshade"):
        dst_metadata.update(
            dtype='uint8',
            count=bandcount
        )

    assert len(dst_bands) == dst_metadata["count"]
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
    extension = os.path.splitext(input_file)[1][1:]
    if extension in ["shp", "geojson"]:
        with fiona.open(input_file) as inp:
            inp_crs = inp.crs
            left, bottom, right, top = inp.bounds
    else:
        with rasterio.open(input_file) as inp:
            inp_crs = inp.crs
            left = inp.bounds.left
            bottom = inp.bounds.bottom
            right = inp.bounds.right
            top = inp.bounds.top

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
        if (tile_pyramid.pixel_x_size(zoom) <= avg_resolution):
            return zoom-1

    raise ValueError("no fitting zoom level found")


def clean_geometry_type(geometry, target_type, allow_multipart=True):
    """
    Returns None if input geometry type differs from target type. Filters and
    splits up GeometryCollection into target types.
    allow_multipart allows multipart geometries (e.g. MultiPolygon for Polygon
    type and so on).
    """

    multipart_geoms = {
        "Point": MultiPoint,
        "LineString": MultiLineString,
        "Polygon": MultiPolygon,
        "MultiPoint": MultiPoint,
        "MultiLineString": MultiLineString,
        "MultiPolygon": MultiPolygon
    }
    multipart_geom = multipart_geoms[target_type]

    if geometry.geom_type == target_type:
        out_geom = geometry

    elif geometry.geom_type == "GeometryCollection":
        subgeoms = [
            clean_geometry_type(
                subgeom,
                target_type,
                allow_multipart=allow_multipart
            )
            for subgeom in geometry
        ]
        out_geom = multipart_geom(subgeoms)

    elif allow_multipart and isinstance(geometry, multipart_geom):
        out_geom = geometry

    elif multipart_geoms[geometry.geom_type] == multipart_geom:
        out_geom = geometry

    else:
        return None

    return out_geom
