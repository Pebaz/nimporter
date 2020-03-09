"""
Test to make sure that the basic action of building Nim code works.
Do not import Nim files directly, rather, test to make sure that they can build.
"""

from pathlib import Path
import nimporter
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


def test_custom_build_switches():
    "Test to make sure custom build switches can be used"


def test_custom_build_switches_per_platform():
    "Test to make sure that different switches are returned per platform."


def test_ignore_cache():
    pass
