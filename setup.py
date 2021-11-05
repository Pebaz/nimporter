"""
Usage:
	pip install nimporter

Upload to PyPi:
	python3 setup.py sdist
	twine upload dist/<archive>

Please note: In order to use Nimporter, you must have both Nim installed as well
as the [Nimpy](https://github.com/yglukhov/nimpy) library.

Libraries distributed using Nimporter have no restriction.

Make sure to star it on GitHub as well while you're up there. ;)
"""

import sys, shutil
from setuptools import setup

setup(
	name='nimporter',
	version='1.1.0',
	license="MIT",
	description='Compile Nim extensions for Python when imported!',
	long_description=open('README.md').read(),
	long_description_content_type='text/markdown',
	author='http://github.com/Pebaz',
	url='http://github.com/Pebaz/Nimporter',
    py_modules=['nimporter', 'nimporter_cli'],
	entry_points={
		'console_scripts' : [
			'nimporter=nimporter_cli:main'
		]
	}
)
