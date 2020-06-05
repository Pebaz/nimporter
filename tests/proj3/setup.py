from setuptools import setup
import nimporter

modules = nimporter.build_nim_extensions( exclude_dirs = ['EXCLUDE'] )

setup(
    name='project3',
    author='https://github.com/Pebaz',
    packages=['proj3'],
    ext_modules=modules,
)
