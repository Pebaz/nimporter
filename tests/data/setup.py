# Don't require Nimporter to be installed to run integration tests.
# This is hacky but allows Nimporter library maintainers to not have to
# repeatedly install and uninstall Nimporter to take updates into account.
import os
import sys
from pathlib import Path

sys.path.append(
    os.getenv('NIMPORTER_DIR', str(Path(__file__).parent.parent.parent))
)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# ! This was what you were working on last:
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# if 'NIMPORTER_DIR' in os.environ:
#     raise Exception(os.environ['NIMPORTER_DIR'])

from setuptools import setup
from nimporter import *

setup(
    name='test_nimporter',
    py_modules=['py_module'],
    ext_modules=get_nim_extensions(
        platforms=[WINDOWS]#, LINUX, MACOS]
    )
)
