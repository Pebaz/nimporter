"""
Test to make sure that Nim code can be built and distributed.
"""

from setuptools import Extension
from pathlib import Path
import nimporter
from nimporter_cli import clean

def test_build_extension_module():
    "A Nim module compiles to C properly and that an Extension object is built."
    clean(Path('..'))

    # assert isinstance(ext, Extension)

def test_find_extensions():
    pass
