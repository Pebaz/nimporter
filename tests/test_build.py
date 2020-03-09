"""
Test to make sure that the basic action of building Nim code works.
Do not import Nim files directly, rather, test to make sure that they can build.
"""

from pathlib import Path
import nimporter
from nimporter import NimCompiler
from nimporter_cli import clean


def test_temp_change_directory():
    "Test to see if the nimporter.cd function actually works."
    cwd = Path('.').absolute()
    temp_dir = Path('nim-temp').absolute()
    try:
        temp_dir.mkdir()     

        with nimporter.cd(temp_dir) as tmp:
            # Yields correct path name
            assert tmp == temp_dir

            # Actually CDs
            assert Path().resolve() == temp_dir
            assert Path().resolve() == tmp

        # CDs back
        assert Path().resolve() == cwd

    finally:
        temp_dir.rmdir()


def test_build_artifact_location():
    "Make sure that the expected location to the build artifact is returned."
    module_path = Path('tests/pkg1/mod1.nim').absolute()
    ext = NimCompiler.EXT
    expected_path = Path('tests/pkg1/__pycache__/mod1' + ext).absolute()

    assert NimCompiler.build_artifact(module_path).absolute() == expected_path


def test_pycache_dir():
    "Make sure that the correct path to the __pycache__ dir is returned."
    module_path = Path('tests/pkg1/mod1.nim').absolute()
    expected_pycache = Path('tests/pkg1/__pycache__').absolute()

    assert NimCompiler.pycache_dir(module_path).absolute() == expected_pycache


def test_custom_build_switches():
    "Test to make sure custom build switches can be used"


def test_custom_build_switches_per_platform():
    "Test to make sure that different switches are returned per platform."


def test_ignore_cache():
    pass


def test_build_module_fails():
    "Test NimCompileException"


def test_build_library_fails():
    "Test NimInvokeException"


def test_ensure_nimpy():
    "Make sure that Nimpy can be installed."


def test_find_nim_std_lib():
    "Make sure that Nim's standard library can be found."
