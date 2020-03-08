from setuptools import setup
import nimporter

setup(
    name='nimext',
    packages=['nimext'],
    ext_modules=nimporter.build_nim_extensions()
)
