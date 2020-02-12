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

import sys, shutil
from setuptools import setup


# tar -tf dist/nimporter-0.1.5.tar.gz
# Discern between SourceDist and Pip Install
# When Nim installed, create SourceDist
# When Nim not installed, user is trying to Pip install.

def check():
	"""
	Only compile extension modules when 'sdist', 'bdist', or 'bdist_wheel' are
	in sys.argv.
	"""
	pip_install = '--python-tag' in sys.argv
	nim_installed = bool(shutil.which('nim'))
	add_list_of_extensions = False
	acceptable_cmds = 'sdist', 'bdist', 'bdist_wheel'

	if not pip_install and any(cmd in sys.argv for cmd in acceptable_cmds):
		add_list_of_extensions = True

	with open('/Users/wildsamu/coding/github/nimporter/foo.txt', 'w') as file:
		file.write(shutil.which('nim') or 'Nim Not Installed.')
		file.writelines(i + '\n' for i in sys.argv)
		file.write('add_list_of_extensions: ' + str(add_list_of_extensions))

	#if not nim_installed:
	#	raise Exception('Nim must be installed to build Nim extensions.')

	return {
		'ext_modules' : []
	}

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
	},
	**check()
)
