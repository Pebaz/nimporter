"""
Test to make sure that libraries built with Nimporter can be used effectively.
"""

from pathlib import Path
import nimporter
from nimporter_cli import clean


def test_coherent_value():
    "Python object is returned from Nim function."
    clean(Path('..'))
    from pkg1 import mod1
    assert mod1.func1() == 1


def test_docstring():
    "Make sure a Nim library's docstring is maintained."

