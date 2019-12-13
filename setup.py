"""
Usage:
pip install git+https://github.com/Pebaz/nimporter.git

Please note: In order to use Nimporter, you must have both Nim installed as well
as the [Nimpy](https://github.com/yglukhov/nimporter) library.

Make sure to star it on GitHub as well while you're up there. ;)
"""

from setuptools import setup, find_packages

setup(
	name='nimporter',
	version='0.1.1',
	license="MIT",
	description='Compile Nim extensions for Python when imported!',
	author='http://github.com/Pebaz',
    py_modules=['nimporter']
)
