from setuptools import Extension
import nimporter

def test_successful_module_import():
    "A Nim module can be imported."
    from pkg1 import mod1
    assert mod1

def test_successful_nested_module_import():
    "A Nim module can be imported."
    from pkg1.pkg2 import mod2
    assert mod2

def test_build_artifacts():
    "A hash file, shared library, and __pycache__ is created."

def test_coherent_value():
    "Python object is returned from Nim function."
    from pkg1 import mod1
    assert mod1.func1() == 1

def test_modify_module():
    "Module is rebuilt when the source file changes."
    # Print some code to file
    # Import file
    # Run file
    # Change file
    # Reimport file
    # Ensure different value returned

def test_hash_changes():
    "When a module is modified that it's hash does also."


def test_build_extension_module():
    "A Nim module compiles to C properly and that an Extension object is built."

    # assert isinstance(ext, Extension)


def test_successful_library_import():
    "A Nim library can be imported"


def test_successful_library_import():
    "A Nim library can be imported"
