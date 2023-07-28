"""
Pytest hook to ensure that no build artifacts are leftover from previous runs.
See the tests/README.md file for more info.
"""

import os
import sys
import shlex
import pathlib
import pytest

# Hilariously, this has a pretty important role in the testing of this project.
# Without this line, deeply nested tests importing the local development copy
# of `nimporter` would fail without some PYTHONPATH manipulation. Better to
# just import and cache it in `sys.modules` at the project root. ;)
from nimporter.cli import nimporter_clean
from nimporter.lib import run_process, PYTHON


def pytest_sessionstart(session):
    nimporter_clean(pathlib.Path())


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    try:
        code, _, _ = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

        sys.modules.pop('nimporter', None)
    except Exception as e:
        print('Failed to uninstall Nimporter after all tests completed:', e)
        raise
