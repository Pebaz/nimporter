from setuptools import setup
import nimporter

setup(
    name='nimext',
    packages=['nimext'],
    ext_modules=nimporter.NimCompiler.build_nim_extensions()
)
