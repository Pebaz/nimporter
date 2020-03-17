"""
Test to make sure that Nim code can be built and distributed.
"""

from setuptools import Extension
from pathlib import Path
import nimporter
from nimporter import Nimporter, NimCompiler


def test_build_extension_module():
    "A Nim module compiles to C properly and that an Extension object is built."

    # assert isinstance(ext, Extension)


def test_find_extensions():
    "Make sure that all Nim modules and libraries can be found."
    gold = {
        Path('tests/proj1/proj1/lib1'),
        Path('tests/proj1/proj1/performance.nim')
    }
    for ext in Nimporter._find_extensions(Path('tests/proj1')):
        assert ext in gold
