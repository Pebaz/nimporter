from setuptools import setup
from nimporter import *

setup(
    name='test_nimporter',
    py_modules=['py_module'],
    ext_modules=get_nim_extensions(
        platforms=[WINDOWS, LINUX, MACOS]
    )
)
