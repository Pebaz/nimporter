"""
Test to make sure that the basic action of building Nim code works.
Do not import Nim files directly, rather, test to make sure that they can build.
"""

from pathlib import Path
import nimporter
from nimporter_cli import clean


def test_custom_build_switches():
    "Test to make sure custom build switches can be used"


def test_custom_build_switches_per_platform():
    "Test to make sure that different switches are returned per platform."
