"""
Test to make sure that Nim files can be built upon import successfully.
"""

import sys, time
from pathlib import Path
from nimporter import (
    NimCompiler, Nimporter, NimporterException, NimLibImporter, NimModImporter
)
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
    from pkg1 import mod1
    assert NimCompiler.pycache_dir(Path('tests/pkg1/mod1.nim')).exists()
    assert NimCompiler.build_artifact(Path('tests/pkg1/mod1.nim')).exists()
    assert Nimporter.hash_filename(Path('tests/pkg1/mod1.nim')).exists()


def test_successful_library_import():
    "A Nim library can be imported"
    import lib2
    assert lib2


def test_manual_import():
    "Test import function manually."

    mod = Nimporter.import_nim_module('pkg3.mod3')
    assert mod
    assert mod.func1

    lib = Nimporter.import_nim_module('pkg3.lib5', ['tests/pkg3/lib5'])
    assert lib
    assert lib.func1

    mod2 = Nimporter.import_nim_module('baz', ['tests/pkg3/foo/bar'])
    assert mod2
    assert mod2.func1


def test_ignore_cache():
    tenth = 100  # ms
    CTM = lambda: round(time.time() * tenth * 10)

    start = CTM()
    mod = Nimporter.import_nim_module('pkg3.mod4')
    assert mod
    assert mod.func1
    ellapsed = CTM() - start
    assert ellapsed > tenth, 'Module was loaded from __pycache__'

    start = CTM()
    mod = Nimporter.import_nim_module('pkg3.mod4', ignore_cache=True)
    assert mod
    assert mod.func1
    ellapsed2 = CTM() - start
    assert ellapsed2 > tenth, 'Module was loaded from __pycache__'

    Nimporter.IGNORE_CACHE = True
    start = CTM()
    mod = Nimporter.import_nim_module('pkg3.mod4')
    assert mod
    assert mod.func1
    ellapsed3 = CTM() - start
    assert ellapsed3 > tenth, 'Module was loaded from __pycache__'
    Nimporter.IGNORE_CACHE = False

    start = CTM()
    mod = Nimporter.import_nim_module('pkg3.mod4')
    assert mod
    assert mod.func1
    ellapsed4 = CTM() - start
    assert ellapsed4 < tenth, 'Module should have been loaded from __pycache__.'


def test_modify_module():
    "Module is rebuilt when the source file changes."
    mod_name = 'pkg3.mod5'
    filename = Path('tests/pkg3/mod5.nim')
    code = filename.read_text()
    mod = Nimporter.import_nim_module(mod_name)

    assert mod.func1() == 'Hello World!'
    
    try:
        filename.write_text(code.replace('World', 'Pebaz'))
        new_code = filename.read_text()

        assert code != new_code
        assert 'Pebaz' in new_code

        # NOTE(pebaz): There is no way to reload a Nim module after it has been
        # imported. Not even importlib.reload() works. This test will count as
        # passing if Nimporter.hash_changed() returns True.
        assert Nimporter.hash_changed(filename)
        
        mod = Nimporter.import_nim_module(
            mod_name,
            ignore_cache=True  # :/
        )
    finally:
        filename.write_text(code)


def test_importers():
    "Make sure that importers are returning specs"
    assert NimModImporter.find_spec('pkg3.mod3')
    assert NimLibImporter.find_spec('pkg3.lib5')
