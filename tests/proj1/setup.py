# NOTE(pebaz): Required to make unit tests use local Nimporter, not installed
import sys; sys.path.extend('../../')

from setuptools import setup
import nimporter

setup(
    name='project1',
    author='https://github.com/Pebaz',
    packages=['proj1'],
    ext_modules=nimporter.build_nim_extensions()
)
