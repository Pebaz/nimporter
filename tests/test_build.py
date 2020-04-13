"""
Test to make sure that the basic action of building Nim code works.
Do not import Nim files directly, rather, test to make sure that they can build.
"""

import sys, os, shutil, io
from contextlib import redirect_stdout
from pathlib import Path
import nimporter
from nimporter import (
    NimCompiler, NimporterException, NimCompileException, NimInvokeException
)


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

    # NOTE: When ran in PowerShell, echo is a Cmdlet, not an executable ... :|
    if not shutil.which('echo'):
        return

    # Test that any program can be called
    gold_out = 'Hello World!' + ('\r\n' if sys.platform == 'win32' else '\n')
    out, err, war, hin = NimCompiler.invoke_compiler(['echo', gold_out.strip()])
    assert out == gold_out


def test_invoke_compiler_success():
    "Test that warnings are propagated"
    warn_file = Path('tests/pkg1/warn.nim').resolve()
    out_file = Path('tests/pkg1/warn' + NimCompiler.EXT).resolve()

    try:
        # Since we are full-on invoking the compiler for a working build here,
        # we gotta make sure it has the same flags as normal (for win32, etc.)
        # This also means Nimpy has to be installed prior to building.
        NimCompiler.ensure_nimpy()

        out, err, war, hin = NimCompiler.invoke_compiler([
            'nim',
            'c',
            *NimCompiler.NIM_CLI_ARGS,
            f'--out:{out_file}',
            str(warn_file)
        ])

        assert out_file.exists(), err
        assert any(
            "Warning: imported and not used: 'asyncstreams'" in i for i in war
        )
        assert any('Hint: system [Processing]' in i for i in hin)

    finally:
        if out_file.exists(): out_file.unlink()
    

def test_invoke_compiler_failure():
    "Make sure that the compiler fails on bad input."
    err_file = Path('tests/pkg1/error.nim').resolve()
    ext = '.exe' if sys.platform == 'win32' else ''
    out_file = Path('tests/pkg1/error' + ext).resolve()

    try:
        # Since this will fail at the Nim layer, no need to ensure all the same
        # flags are set per platform (since it won't ever get that far).
        out, err, war, hin = NimCompiler.invoke_compiler([
            'nim', 'c', *NimCompiler.NIM_CLI_ARGS, str(err_file)
        ])

        assert not out_file.exists(), err
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
    if out[1]:
        out = NimCompiler.invoke_compiler(
            'nimble uninstall nimpy --accept'.split()
        )

    # Install/verify it is already installed
    NimCompiler.ensure_nimpy()

    # Check installation code path
    NimCompiler.ensure_nimpy()

    # Verify that it is actuall installed according to Nimble
    out = NimCompiler.invoke_compiler('nimble path nimpy'.split())
    assert out[0] and not out[1]


def test_get_import_prefix():
    "Make sure that the right namespace is returned for a given module path."
    with nimporter.cd('tests') as tmpdir:
        module_path1 = Path('pkg1/mod1.nim')
        module_path2 = Path('pkg1/pkg2/mod2.nim')
        gold1 = 'pkg1', 'mod1.nim'
        gold2 = 'pkg1', 'pkg2', 'mod2.nim'
        assert NimCompiler.get_import_prefix(module_path1, Path()) == gold1
        assert NimCompiler.get_import_prefix(module_path2, Path()) == gold2


def test_find_nim_std_lib():
    "Make sure that Nim's standard library can be found."
    assert shutil.which('nim'), 'Nim compiler is not installed or not on path'
    assert NimCompiler.find_nim_std_lib(), (
        "Can't find Nim stdlib even though it is installed"
    )

    # Now test failure condition by making Nim disappear
    environ = os.environ.copy()
    try:
        os.environ['PATH'] = ''
        assert not shutil.which('nim')
        assert not NimCompiler.find_nim_std_lib()
    finally:
        os.environ.clear()
        os.environ.update(environ)


def test_custom_build_switches():
    "Test to make sure custom build switches can be used"

    switch_file = Path('tests/lib2/switches.py')
    scope = dict(
        MODULE_PATH=Path('foo/bar/baz.nim'),
        BUILD_ARTIFACT=Path('foo/bar/__pycache__/baz.' + NimCompiler.EXT),
        BUILD_DIR=None,
        IS_LIBRARY=False
    )
    switches = NimCompiler.get_switches(switch_file, **scope)
    old_import = switches['import'][:]
    old_bundle = switches['bundle'][:]

    assert switches
    assert old_import
    assert old_bundle

    # Make sure different platforms are handled correctly
    old_platform = sys.platform + ''
    sys.platform = 'darwin' if sys.platform == 'win32' else 'win32'

    try:
        switches = NimCompiler.get_switches(switch_file, **scope)
        
        assert switches
        assert old_import
        assert old_bundle
        assert old_import != switches['import']
        assert old_bundle != switches['bundle']
    finally:
        sys.platform = old_platform


def test_build_module():
    "Test that a given Nim module can produce a Python extension module."
    with nimporter.cd('tests'):
        module = Path('mod_a.nim')
        output = NimCompiler.build_artifact(module)

        f = io.StringIO()
        with redirect_stdout(f):
            artifact = NimCompiler.compile_nim_code(module, output, library=False)

        assert artifact.exists()
        assert artifact.parent == output.parent
        assert 'Warning:' in f.getvalue()


def test_build_library():
    "Test that a given Nim module can produce a Python extension library."
    with nimporter.cd('tests'):
        module = Path('lib1')
        output = NimCompiler.build_artifact(module)
        artifact = NimCompiler.compile_nim_code(module, output, library=True)

        assert artifact.exists()
        assert artifact.parent == output.parent
        assert artifact.suffix == output.suffix


def test_build_module_fails():
    "Test NimCompileException"

    # Build nonexistent file
    try:
        fake = Path('nonesense.nim')
        NimCompiler.compile_nim_code(fake, None, library=True)
        assert False, "Should throw exception. File doesn't exist: " + str(fake)
    except NimporterException:
        "Expected result"

    # Build module using library path
    try:
        NimCompiler.compile_nim_code(Path('tests/lib1'), None, library=False)
        assert False, 'Should throw exception.'
    except NimporterException:
        "Expected result"

    # Build a module that has an error
    try:
        module = Path('tests/pkg1/error.nim')
        output = NimCompiler.build_artifact(module)
        NimCompiler.compile_nim_code(module, output, library=False)
        assert False, 'Should throw exception.'
    except NimCompileException as e:
        assert str(e)


def test_build_library_fails():
    "Test NimInvokeException"

    # Build library using Nim module
    try:
        NimCompiler.compile_nim_code(
            Path('tests/mod_b.nim'), None, library=True
        )
        assert False, 'Should throw exception.'
    except NimporterException:
        "Expected result"

    # Build a library that has an error
    try:
        module = Path('tests/lib4')
        output = NimCompiler.build_artifact(module)
        NimCompiler.compile_nim_code(module, output, library=True)
        assert False, 'Should throw exception.'
    except NimInvokeException as e:
        assert str(e)
        assert e.get_output()

    # Build a library that doesn't have a Nimble file
    try:
        NimCompiler.compile_nim_code(Path('tests/lib3'), None, library=True)
        assert False, 'Should throw exception.'
    except NimporterException:
        "Expected result"
