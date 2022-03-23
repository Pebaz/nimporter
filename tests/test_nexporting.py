import sys
import shlex
from zipfile import ZipFile
from tests import temporarily_install_nimporter
from nimporter.lib import *
from nimporter.nexporter import *


def test_sdist_all_targets_builds_correctly():
    "Assert all targets are listed"

    with temporarily_install_nimporter(), cd(Path('tests/data')):
        # Generate a zip file instead of tar.gz
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} setup.py sdist --formats=zip'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

        assert code == 0

        dist = Path('dist')
        egg = Path('test_nimporter.egg-info')

        assert dist.exists(), f'{dist} does not exist'
        assert egg.exists(), f'{egg} does not exist'

        targets = [*dist.glob('*.zip')]

        # Make sure the source distribution contains one for each platform
        with ZipFile(targets[0]) as archive:
            PLATFORMS = WINDOWS, MACOS, LINUX
            PREFIX = 'test_nimporter-0.0.0/nim-extensions'
            IMPORTANT_NAMES = {
                'ext_mod_basic',
                'ext_lib_basic',
                'pkg1.pkg2.ext_mod_in_pack',
                'pkg1.pkg2.ext_lib_in_pack',
            }

            important_names = set()

            for platform, arch, compiler in iterate_target_triples(PLATFORMS):
                triple = f'{platform}-{arch}-{compiler}'

                for important_name in IMPORTANT_NAMES:
                    important_names.add(
                        f'{PREFIX}/{important_name}/{triple}/nimbase.h'
                    )

            ALL_NAMES = {*archive.namelist()}

            for important_name in important_names:
                assert important_name in ALL_NAMES, (
                    f'{important_name} was not included in the zip archive'
                )


def test_bdist_wheel_all_targets_installs_correctly():
    "Assert all items are correctly imported"
    try:
        with temporarily_install_nimporter(), cd(Path('tests/data')):
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py bdist_wheel'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0

            (target,) = Path('dist').glob('test_nimporter*.whl')

            code, stdout, stderr = run_process(
                process_args=shlex.split(
                    f'{PYTHON} -m pip install dist/{target.name}'
                ),
                show_output='NIMPORTER_INSTRUMENT' in os.environ,
            )

            if code:
                raise Exception(stdout + '\n\n\n' + stderr)

        sys.modules.pop('ext_mod_basic', None)
        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3

        sys.modules.pop('ext_lib_basic', None)
        import ext_lib_basic
        assert ext_lib_basic.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_mod_in_pack', None)
        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_lib_in_pack', None)
        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

        sys.modules.pop('py_module', None)
        import py_module
        assert py_module.py_function() == 12

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )


def test_sdist_all_targets_installs_correctly():
    "Assert all items are correctly imported"
    try:
        with temporarily_install_nimporter(), cd(Path('tests/data')):
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py sdist'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0

            (target,) = Path('dist').glob('test_nimporter*.tar.gz')

            code, stdout, stderr = run_process(
                process_args=shlex.split(
                    f'{PYTHON} -m pip install dist/{target.name}'
                ),
                show_output='NIMPORTER_INSTRUMENT' in os.environ,
            )

            if code:
                raise Exception(stdout + '\n\n\n' + stderr)

        sys.modules.pop('ext_mod_basic', None)
        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3

        sys.modules.pop('ext_lib_basic', None)
        import ext_lib_basic
        assert ext_lib_basic.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_mod_in_pack', None)
        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_lib_in_pack', None)
        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

        sys.modules.pop('py_module', None)
        import py_module
        assert py_module.py_function() == 12

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )


def test_setup_py_all_targets_installs_correctly():
    "After installing, ensure lib can be imported and can import itself."
    try:
        with temporarily_install_nimporter(), cd(Path('tests/data')):
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py install'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0, f'{stdout}\n\n\n{stderr}'

        sys.modules.pop('ext_mod_basic', None)
        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3

        sys.modules.pop('ext_lib_basic', None)
        import ext_lib_basic
        assert ext_lib_basic.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_mod_in_pack', None)
        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        sys.modules.pop('pkg1.pkg2.ext_lib_in_pack', None)
        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

        sys.modules.pop('py_module', None)
        import py_module
        assert py_module.py_function() == 12

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )
