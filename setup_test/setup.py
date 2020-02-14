from setuptools import setup
import nimporter

setup(
    name='nimext',
    ext_modules=nimporter.NimCompiler.build_nim_extensions()
)
