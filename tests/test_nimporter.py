"""
Test to make sure that libraries built with Nimporter can be used effectively.
"""

from pathlib import Path
import nimporter


def test_coherent_value():
    "Python object is returned from Nim function."

    # NOTE(pebaz): Importing a cached build artifact is fine in this case since
    # the test is whether or not it can be used, which will fail if it cannot ;)
    from pkg1 import mod1
    assert mod1.func1() == 1


def test_docstring():
    "Make sure a Nim library's docstring is maintained."

