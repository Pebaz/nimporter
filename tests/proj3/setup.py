from setuptools import setup
import nimporter

modules = nimporter.build_nim_extensions( exclude_dirs = ['EXCLUDE'] )

for module in modules :
    module.extra_compile_args.append("-w")

setup(
    name='project3',
    author='https://github.com/Pebaz',
    packages=['proj3'],
    # ext_modules=nimporter.build_nim_extensions(),
    ext_modules=modules,
)
