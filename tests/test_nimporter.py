"""
Test to make sure that libraries built with Nimporter can be used effectively.
"""

from pathlib import Path
from nimporter import (
    NimCompiler, Nimporter, NimporterException, NimLibImporter, NimModImporter
)
import nimporter


def test_coherent_value():
    "Python object is returned from Nim function."

    # NOTE(pebaz): Importing a cached build artifact is fine in this case since
    # the test is whether or not it can be used, which will fail if it cannot ;)
    from pkg1 import mod1
    assert mod1.func1() == 1


def test_docstring():
    "Make sure a Nim library's docstring is maintained."


def test_register_importer():
    "Make sure that the importers registered by Nimporter actually exist."
    assert sys.meta_path[0] == NimLibImporter
    assert sys.meta_path[-1] == NimModImporter


def test_hash():
    "Make sure when a module is modified it's hash is also."
    module = Path('tests/pkg1/mod2.nim')
    Nimporter.update_hash(module)
    original_hash = Nimporter.get_hash(module)
    original_text = module.read_text()
    module.write_text(original_text.replace('World', 'Pebaz'))
    assert Nimporter.hash_file(module) != original_hash
    module.write_text(original_text.replace('Pebaz', 'World'))
    assert Nimporter.hash_file(module) == original_hash


    # Build Once
    output = NimCompiler.build_artifact(module)
    artifact = NimCompiler.compile_nim_code(module, output, library=False)


def test_hash_coincides():
    "Make sure an imported Nim module's hash matches the actual source file."
    from pkg1 import mod1
    assert not Nimporter.hash_changed(Path('tests/pkg1/mod1.nim'))


def test_hash_not_there():
    "Make sure an exception is thrown when a module is not hashed."
    try:
        Nimporter.get_hash(Path('tests/lib4/lib4.nim'))
        assert False, 'Exception should have been thrown.'
    except NimporterException:
        "Expected case"


def test_should_compile():
    "Make sure that modules should be (re)compiled or not."
    filename = Path('tests/pkg4/mod4.nim')

    assert not Nimporter.is_hashed(filename)
    assert Nimporter.hash_changed(filename)
    assert not Nimporter.is_built(filename)
    assert not Nimporter.is_cache(filename)
    assert not NimCompiler.pycache_dir(filename).exists()
    assert not Nimporter.IGNORE_CACHE
    assert Nimporter.should_compile(filename)
