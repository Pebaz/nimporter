from setuptools import setup
import nimporter

setup(
    name='project1',
    author='https://github.com/Pebaz',
    packages=['proj3'],
    ext_modules=nimporter.build_nim_extensions(
        danger=True,
        exclude_dirs=['proj3/EXCLUDE']
    )
)
