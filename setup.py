#!/usr/bin/env python

from setuptools import setup

setup(
    name='tilematrix',
    version='0.1',
    description='helps handling tile pyramids',
    author='Joachim Ungar',
    author_email='joachim.ungar@gmail.com',
    url='https://github.com/ungarj/tilematrix',
    license='MIT',
    packages=['tilematrix'],
    install_requires=[
        'rasterio',
        'shapely',
        'affine',
        'numpy',
        'fiona',
        'pyproj',
        'six',
        'geoalchemy2'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ]
)
