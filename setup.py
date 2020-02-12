"""
Usage:
	pip install nimporter

Upload to PyPi:
	python3 setup.py sdist
	twine upload dist/<archive>

Please note: In order to use Nimporter, you must have both Nim installed as well
as the [Nimpy](https://github.com/yglukhov/nimpy) library.

Make sure to star it on GitHub as well while you're up there. ;)
"""

import sys, shutil
from setuptools import setup

"""
Computer with Nim Installed

    pip install meowhash-nim                               # Works (Doesn't run Nim)
    pip install git+https://github.com/Pebaz/meowhash-nim  # Works (Runs Nim)

Computer without Nim Installed

    pip install meowhash-nim                               # Works (Runs Nim)
    pip install git+https://github.com/Pebaz/meowhash-nim  # Fails (Cannot run Nim)

"""

setup(
	name='nimporter',
	version='0.1.5',
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
