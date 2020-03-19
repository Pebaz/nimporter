# NOTE(pebaz): Required to make unit tests use local Nimporter, not installed
from pathlib import Path
import sys; sys.path.append(str(Path('../../').resolve().absolute()))

from setuptools import setup
import nimporter

setup(
    name='project1',
    author='https://github.com/Pebaz',
    packages=['proj1'],
    ext_modules=nimporter.build_nim_extensions()
)
