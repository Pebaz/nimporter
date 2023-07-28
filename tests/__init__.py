"""
! See conftest.py for `pytest_sessionfinish` hook to uninstall Nimporter.
"""

import os
import sys
import time
import shlex
import pytest
import pathlib

# * It's actually pretty important that the local version of Nimporter is used
# * to run tests.

# current_path = pathlib.Path().expanduser().resolve().absolute()
# try:
#     os.chdir('..')
#     import nimporter

#     project_root = (pathlib.Path(__file__)
#         .expanduser()
#         .resolve()
#         .absolute()
#         .parent
#         .parent
#     )
#     nimporter_path = pathlib.Path(nimporter.__file__)

#     assert nimporter_path.is_relative_to(project_root), (
#         f'Accidentally imported system version of Nimporter: '
#         f'{nimporter.__file__} != {project_root}'
#     )
# except ImportError:
#     "Expected case"
# finally:
#     os.chdir(current_path)

from nimporter.lib import run_process, PYTHON


@pytest.fixture(scope='session')
def temporarily_install_nimporter():
    # Hopefully prevent permission denied errors in CI when deleting artifacts
    time.sleep(5)

    try:
        code, out, err = run_process(
            shlex.split(f'{PYTHON} setup.py install --force'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

        assert code == 0, (
            f'Nimporter failed to install:\nstdout: {out}\nstderr: {err}'
        )
    except Exception as e:
        print('Failed to install Nimporter:', e)
        raise
