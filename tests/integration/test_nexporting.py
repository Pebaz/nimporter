import sys
import shlex
import shutil
import pkg_resources
from zipfile import ZipFile
from tests import run_nimporter_clean
from nimporter.lib import *
from nimporter.nexporter import *


PYTHON = 'python' if sys.platform == 'win32' else 'python3'
PIP = 'pip' if shutil.which('pip') else 'pip3'


def test_sdist_all_targets_builds_correctly(run_nimporter_clean):
    "Assert all targets are listed"

    with cd(Path('tests/data')):
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
            PLATFORMS = [WINDOWS, LINUX, MACOS]
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

            ALL_NAMES = set(archive.namelist())

            for important_name in important_names:
                assert important_name in ALL_NAMES, (
                    f'{important_name} was not included in the zip archive'
                )


def test_bdist_all_targets():
    "Assert all targets are listed"



def test_sdist_all_targets_installs_correctly(run_nimporter_clean):
    "Assert all items are correctly imported"
    try:
        with cd(Path('tests/data')):
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py sdist'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0

            (target,) = Path('dist').glob('test_nimporter*.tar.gz')


            # ! So this is where it gets weird.

            code, stdout, stderr = run_process(
                process_args=shlex.split(
                    f'{PYTHON} -m pip install dist/{target.name}'
                ),
                show_output='NIMPORTER_INSTRUMENT' in os.environ,
                environment={
                    **os.environ,

                    # This is hacky but allows Nimporter library maintainers to
                    # run the integration tests without repeatedly installing
                    # and uninstalling Nimporter to ensure any updates are
                    # taken into account.
                    'NIMPORTER_DIR': str(
                        # Path().parent.parent.resolve().absolute()
                        'C:/code/me/Nimporter'
                    )
                }
            )

            # assert code == 0
            if code:
                raise Exception(stdout + '\n\n\n' + stderr)

        # # This is really hacky but according to this post:
        # # https://stackoverflow.com/a/32478979/6509967
        # # It is possible to allow Python to import a package that was installed
        # # at runtime using this method:
        # import site
        # for site_dir in site.getsitepackages():
        #     test_nimporter = [*Path(site_dir).glob('*est_nimporter*')]
        #     if len(test_nimporter) > 0:
        #         sys.path.insert(0, str(test_nimporter[0].resolve().absolute()))
        #         break

        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3

        import ext_lib_basic
        assert ext_lib_basic.add(1, 2) == 3

        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

        import py_module
        assert py_module.py_function() == 12

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )



def test_setup_py_all_targets_installs_correctly(run_nimporter_clean):
    "After installing, ensure lib can be imported and can import itself."
    try:
        with cd(Path('tests/data')):
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py install'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0

        # This is really hacky but according to this post:
        # https://stackoverflow.com/a/32478979/6509967
        # It is possible to allow Python to import a package that was installed
        # at runtime using this method:
        import site
        for site_dir in site.getsitepackages():
            test_nimporter = [*Path(site_dir).glob('*est_nimporter*')]
            if len(test_nimporter) > 0:
                sys.path.insert(0, str(test_nimporter[0].resolve().absolute()))
                break

        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3

        import ext_lib_basic
        assert ext_lib_basic.add(1, 2) == 3

        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

        import py_module
        assert py_module.py_function() == 12

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

