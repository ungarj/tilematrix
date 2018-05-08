"""Installation recipe for tilematrix."""

from setuptools import setup

# get version number
# from https://github.com/mapbox/rasterio/blob/master/setup.py#L55
with open('tilematrix/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue

setup(
    name='tilematrix',
    version=version,
    description='helps handling tile pyramids',
    author='Joachim Ungar',
    author_email='joachim.ungar@gmail.com',
    url='https://github.com/ungarj/tilematrix',
    license='MIT',
    packages=['tilematrix', 'tilematrix.tmx'],
    entry_points={
        'console_scripts': ['tmx=tilematrix.tmx.main:tmx']
    },
    install_requires=[
        'affine',
        'click',
        'geojson',
        'rasterio>=1.0a3',
        'shapely',
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
