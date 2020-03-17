"""
Test to make sure that Nim code can be built and distributed.
"""

from setuptools import Extension
from pathlib import Path
import nimporter
from nimporter import Nimporter, NimCompiler


def test_find_extensions():
    "Make sure that all Nim modules and libraries can be found."
    gold = {
        Path('tests/proj1/proj1/lib1'),
        Path('tests/proj1/proj1/performance.nim')
    }
    for ext in Nimporter._find_extensions(Path('tests/proj1')):
        assert ext in gold



def test_build_extension_module():
    "Make sure A Nim module compiles to C and an Extension object is built."
    module = Path('tests/proj1/proj1/performance.nim')
    ext = Nimporter._build_nim_extension(module, Path('tests/proj1'))

    assert isinstance(ext, Extension)

    includes = set(Path(i) for i in ext.include_dirs)

    for source in ext.sources:
        src = Path(source)
        assert src.suffix == '.c'
        assert src.parent in includes

    assert ext.name == 'proj1.performance'


def test_build_extension_library():
    "Make sure a Nim library compiles to C and an Extension object is built."

    # assert isinstance(ext, Extension)


def test_build_all_extensions():
    "Make sure all extensions within a project are compiled correctly."
