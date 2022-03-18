# Don't require Nimporter to be installed to run integration tests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from setuptools import setup
from nimporter import *

setup(
    name='test_nimporter',
    py_modules=['py_module'],
    ext_modules=get_nim_extensions(
        platforms=[WINDOWS, LINUX, MACOS]
    )
)
