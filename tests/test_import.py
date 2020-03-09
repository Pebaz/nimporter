"""
Test to make sure that Nim files can be built upon import successfully.
"""

from pathlib import Path
import nimporter
from nimporter_cli import clean


def test_manual_import():
    "Test import function manually."


def test_successful_module_import():
    "A Nim module can be imported."
    clean(Path('..'))
    from pkg1 import mod1
    assert mod1



def test_successful_nested_module_import():
    "A Nim module can be imported."
    clean(Path('..'))
    from pkg1.pkg2 import mod2
    assert mod2


def test_build_artifacts():
    "A hash file, shared library, and __pycache__ is created."
    clean(Path('..'))


def test_modify_module():
    "Module is rebuilt when the source file changes."
    clean(Path('..'))
    # Print some code to file
    # Import file
    # Run file
    # Change file
    # Reimport file
    # Ensure different value returned


def test_hash_changes():
    "When a module is modified that it's hash does also."
    clean(Path('..'))


def test_successful_library_import():
    "A Nim library can be imported"
    clean(Path('..'))


def test_register_importer():
    pass
