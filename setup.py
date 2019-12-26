"""
Usage:
	pip install nimporter

Upload to PyPi:
	python3 setup.py sdist
	twine upload dist/*

Please note: In order to use Nimporter, you must have both Nim installed as well
as the [Nimpy](https://github.com/yglukhov/nimpy) library.

Make sure to star it on GitHub as well while you're up there. ;)
"""

from setuptools import setup

setup(
	name='nimporter',
	version='0.1.5',
	license="MIT",
	description='Compile Nim extensions for Python when imported!',
	long_description=open('README.md').read(),
	long_description_content_type='text/markdown',
	author='http://github.com/Pebaz',
	url='http://github.com/Pebaz/Nimporter',
    py_modules=['nimporter']
)
