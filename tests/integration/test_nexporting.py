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


# TODO(pbz): Get this working, that will help with the rest of the tests
# def run_nimporter_clean_before_executing(fn):
#     def wrapper(*args, **kwargs):
#         clean()
#         return fn(*args, **kwargs)
#     return wrapper


def test_ensure_nimporter_installed(run_nimporter_clean):
    "Make sure that Nimporter is installed before running integration tests."

    # TODO(pbz): How to make sure this works during normal development?
    # TODO(pbz): This only takes a couple seconds surprisingly
    # assert os.system('python setup.py install --force') == 0

    # libs = {lib.key.lower() for lib in pkg_resources.working_set}

    # if 'nimporter' not in libs:
    #     assert Path('setup.py').exists() and Path('nimporter').exists()
    #     assert os.system('python setup.py install --force') == 0

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # ! assert Path('setup.py').exists() and Path('nimporter').exists()
    # ! assert os.system('pip install . --force') == 0


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


def test_sdist_specified_targets():
    "Assert only specified targets are listed"


def test_bdist_all_targets():
    "Assert all targets are listed"


def test_bdist_specified_targets():
    "Assert only specified targets are listed"




def test_sdist_all_targets_installs_correctly(run_nimporter_clean):
    "Assert all items are correctly imported"

    try:
        with cd(Path('tests/data')):
            # Generate a zip file instead of tar.gz
            code, stdout, stderr = run_process(
                shlex.split(f'{PYTHON} setup.py install'),
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            assert code == 0

        import py_module
        assert py_module.py_function() == 3.14

        import shallow.ext_mod_basic
        assert shallow.ext_mod_basic.add(1, 2) == 3

        import shallow.ext_lib_in_shallow_heirarchy
        assert shallow.ext_lib_in_shallow_heirarchy.add(1, 2) == 3

        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3

        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

    finally:
        # On error this won't be installed so no worries about the exit code
        code, stdout, stderr = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall test_nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )



def test_sdist_specified_targets_installs_correctly():
    "Assert only specified targets are listed"


def test_bdist_all_targets_installs_correctly():
    "Assert all targets are listed"


def test_bdist_specified_targets_installs_correctly():
    "Assert only specified targets are listed"
