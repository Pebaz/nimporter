import os
import sys
import time
import shlex
import contextlib
from nimporter.lib import run_process, PYTHON


@contextlib.contextmanager
def temporarily_install_nimporter():
    # Hopefully prevent permission denied errors in CI when deleting artifacts
    time.sleep(5)

    try:
        code, _, _ = run_process(
            shlex.split(f'{PYTHON} setup.py install --force'),
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
