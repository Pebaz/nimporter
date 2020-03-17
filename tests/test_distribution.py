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
    assert ext.name == 'proj1.performance'

    includes = set(Path(i) for i in ext.include_dirs)

    for source in ext.sources:
        src = Path(source)
        assert src.suffix == '.c'
        assert src.parent in includes



def test_build_extension_library():
    "Make sure a Nim library compiles to C and an Extension object is built."

    library = Path('tests/proj1/proj1/lib1')
    ext = Nimporter._build_nim_extension(library, Path('tests/proj1'))

    assert isinstance(ext, Extension)
    assert ext.name == 'proj1.lib1'

    includes = set(Path(i) for i in ext.include_dirs)

    for source in ext.sources:
        src = Path(source)
        assert src.suffix == '.c'
        assert src.parent in includes


def test_build_all_extensions():
    "Make sure all extensions within a project are compiled correctly."
