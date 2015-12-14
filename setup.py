#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='tilematrix',
    version='0.1',
    description='helps handling tile pyramids',
    author='Joachim Ungar',
    author_email='joachim.ungar@gmail.com',
    url='https://github.com/ungarj/tilematrix',
    #   packages=[],
    #py_moduels=['src.tilematrix', 'src.tilematrix_io']
    package_dir = {'tilematrix': 'src'},
    packages=["tilematrix"]
)
