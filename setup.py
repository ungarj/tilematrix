#!/usr/bin/env python
"""Installation recipe for tilematrix."""

from setuptools import setup

setup(
    name='tilematrix',
    version='0.11',
    description='helps handling tile pyramids',
    author='Joachim Ungar',
    author_email='joachim.ungar@gmail.com',
    url='https://github.com/ungarj/tilematrix',
    license='MIT',
    packages=['tilematrix'],
    install_requires=[
        'rasterio>=1.0a3',
        'shapely',
        'affine',
        'six'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
