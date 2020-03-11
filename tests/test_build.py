"""
Test to make sure that the basic action of building Nim code works.
Do not import Nim files directly, rather, test to make sure that they can build.
"""

import sys, shutil
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


def test_invoke_compiler():
    "Make sure that you can invoke the compiler as well as any executable."

    # Test that any program can be called
    gold_out = 'Hello World!\n'
    out, err, war, hin = NimCompiler.invoke_compiler(['echo', gold_out.strip()])
    assert out == gold_out


def test_invoke_compiler_success():
    "Test that warnings are propagated"
    warn_file = Path('tests/pkg1/warn.nim').resolve()
    ext = '.exe' if sys.platform == 'win32' else ''
    out_file = Path('tests/pkg1/warn' + ext).resolve()

    try:
        out, err, war, hin = NimCompiler.invoke_compiler([
            'nim', 'c', str(warn_file)
        ])

        assert out_file.exists()
        assert any("Warning: imported and not used: 'tables'" in i for i in war)
        assert any('Hint: system [Processing]' in i for i in hin)

    finally:
        if out_file.exists(): out_file.unlink()
    

def test_invoke_compiler_failure():
    "Make sure that the compiler fails on bad input."
    err_file = Path('tests/pkg1/error.nim').resolve()
    ext = '.exe' if sys.platform == 'win32' else ''
    out_file = Path('tests/pkg1/error' + ext).resolve()

    try:
        out, err, war, hin = NimCompiler.invoke_compiler([
            'nim', 'c', str(err_file)
        ])

        assert not out_file.exists()
        assert any('Error: cannot open file: fallacy' in i for i in err)
        assert any('Hint: system [Processing]' in i for i in hin)

    finally:
        if out_file.exists(): out_file.unlink()


def test_ensure_nimpy():
    "Make sure that the Nimpy library can be installed."
    assert shutil.which('nim'), 'Nim compiler is not installed or not on path'

    # Make sure it is not installed
    out = NimCompiler.invoke_compiler('nimble path nimpy'.split())

    # Remove it
    if out[0]:
        out = NimCompiler.invoke_compiler('nimble uninstall nimpy --accept'.split())
        assert not out[1]

    # Install/verify it is already installed
    NimCompiler.ensure_nimpy()

    # Check installation code path
    NimCompiler.ensure_nimpy()

    # Verify that it is actuall installed according to Nimble
    out = NimCompiler.invoke_compiler('nimble path nimpy'.split())
    assert out[0] and not out[1]


def test_get_import_prefix():
    "Make sure that the right namespace is returned for a given module path."
    module_path1 = Path('pkg1/mod1.nim')
    module_path2 = Path('pkg1/pkg2/mod2.nim')
    gold1 = 'pkg1', 'mod1.nim'
    gold2 = 'pkg1', 'pkg2', 'mod2.nim'
    assert NimCompiler.get_import_prefix(module_path1, Path()) == gold1
    assert NimCompiler.get_import_prefix(module_path2, Path()) == gold2


def test_find_nim_std_lib():
    "Make sure that Nim's standard library can be found."




"Make sure the appropriate Exception is thrown for compilation failures."



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


