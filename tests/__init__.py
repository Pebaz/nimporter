import os
import sys
import shlex
import contextlib
import pytest
from pathlib import Path
from nimporter.lib import run_process, PYTHON
from nimporter.cli import nimporter_clean



@pytest.fixture
def run_nimporter_clean():
    """
    On Windows, a DLL (and therefore, a PYD) cannot be deleted while in use by
    a process. However, each new run of the unit tests needs to not rely on any
    leftover artifacts from the previous run. `nimporter_clean()` helps with
    this but throws an error when trying to delete an in-use PYD. To get around
    this, `run_nimporter_clean()` stores an attribute on itself that allows it
    to be used on every single unit test but only be run once. The advantage of
    this is that when there is only a single test running, it will still run
    `run_nimporter_clean()` the same as when all tests are running (don't need
    to run it for every test, so which tests call `run_nimporter_clean()`?)
    """
    if not getattr(run_nimporter_clean, 'invoked', None):
        setattr(run_nimporter_clean, 'invoked', True)
        nimporter_clean(Path())


@contextlib.contextmanager
def temporarily_install_nimporter():
    try:
        code, _, _ = run_process(
            shlex.split(f'{PYTHON} setup.py install'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

        assert code == 0, 'Nimporter failed to install'

        yield
    finally:
        code, _, _ = run_process(
            shlex.split(f'{PYTHON} -m pip uninstall nimporter -y'),
            'NIMPORTER_INSTRUMENT' in os.environ
        )

        sys.modules.pop('nimporter', None)
