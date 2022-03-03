import sys
import shutil
import pytest
from nimporter.lib import *

PYTHON = 'python' if sys.platform == 'win32' else 'python3'
PIP = 'pip' if shutil.which('pip') else 'pip3'

def test_sdist_all_targets():
    "Assert all targets are listed"

    # with cd(Path('tests/data')):
    #     subprocess.Popen(f'{PYTHON} setup.py sdist'.split()).wait()
    #     dist = Path('dist')
    #     egg = Path('project1.egg-info')
    #     try:
    #         assert dist.exists()
    #         assert egg.exists()
    #         targets = list(dist.glob('project1*'))
    #         assert len(targets) == 1
    #         assert targets[0].exists()

    #         # Make sure the appropriate compiler is being used
    #         for extension in Path('nim-extensions').iterdir():
    #             (nim_build_data_file,) = extension.glob('*json')
    #             nim_build_data = json.loads(nim_build_data_file.read_text())
    #             expected = nimporter.NimCompiler.get_compatible_compiler()
    #             installed_ccs = nimporter.NimCompiler.get_installed_compilers()
    #             if not expected:
    #                 warnings.warn(
    #                     f'No compatible C compiler installed: {installed_ccs}'
    #                 )
    #             else:
    #                 cc_path = installed_ccs[expected]
    #                 actual = nim_build_data['linkcmd'].split()[0].strip()
    #                 if not actual.startswith(cc_path.stem):
    #                     warnings.warn(
    #                         f'Nim used a different C compiler than what Python '
    #                         f'expects. Python uses {cc_path.stem} and Nim used '
    #                         f'{actual}'
    #                     )
    #     finally:
    #         shutil.rmtree(str(dist.absolute()))
    #         shutil.rmtree(str(egg.absolute()))


def test_sdist_specified_targets():
    "Assert only specified targets are listed"


def test_bdist_all_targets():
    "Assert all targets are listed"


def test_bdist_specified_targets():
    "Assert only specified targets are listed"




def test_sdist_all_targets_installs_correctly():
    "Assert all targets are listed"


def test_sdist_specified_targets_installs_correctly():
    "Assert only specified targets are listed"


def test_bdist_all_targets_installs_correctly():
    "Assert all targets are listed"


def test_bdist_specified_targets_installs_correctly():
    "Assert only specified targets are listed"
