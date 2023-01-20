"""
Iterates through all sub folders and removes any build artifacts and hashes.
"""

import os
import sys
import time
import shutil
import pathlib
import argparse
import subprocess
from typing import *
from pathlib import Path
from cookiecutter.main import cookiecutter
from nimporter.lib import *
from nimporter.nimporter import *

# TODO(pbz): Need to move this to a doc/tutorial
SETUPPY_TEMPLATE: str = f'''
# Setup.py tutorial:
# https://github.com/navdeep-G/setup.py
# Edit `packages=` to fit your requirements

import setuptools, pathlib, sysconfig
from setuptools.command.build_ext import build_ext
import nimporter


class NoSuffixBuilder(build_ext):
    """
    Optional.

    Removes the target platform, architecture, and Python version from the
    final artifact.

    Example:
        The artifact: `module.linux-x86_64.cpython.3.8.5.so`
        Becomes: `module.so`
    """
    def get_ext_filename(self, ext_name: str) -> str:
        filename = super().get_ext_filename(ext_name)
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        return filename.replace(ext_suffix, '') + pathlib.Path(filename).suffix


setuptools.setup(
    name="{ pathlib.Path().absolute().name }",
    packages=[..],  # Please read the above tutorial
    ext_modules=nimporter.build_nim_extensions()
    cmdclass={{"build_ext": NoSuffixBuilder}},
)
'''


def nimporter_list() -> None:
    for extension in find_extensions(Path()):
        print(extension)
        return


def nimporter_clean(path: Path) -> None:
    for item in path.iterdir():
        item_full_path = item.resolve().absolute()

        if item.is_dir():
            DELETE_THESE_DIRS = {EXT_DIR, '__pycache__', '.pytest_cache'}

            if item.stem in DELETE_THESE_DIRS:
                print('Deleting', item_full_path)
                shutil.rmtree(item)

            elif item.name.endswith('.egg-info'):
                print('Deleting', item_full_path)
                shutil.rmtree(item)

            elif item.stem == 'dist' and (item.parent / 'setup.py').exists():
                print('Deleting', item_full_path)
                shutil.rmtree(item)

            elif item.stem == 'build' and (item.parent / 'setup.py').exists():
                print('Deleting', item_full_path)
                shutil.rmtree(item)

            else:
                nimporter_clean(item)
    return


def nimporter_init(extension_type: str, extension_name: str) -> None:
    print(f'Initializing new extension {extension_type} "{extension_name}"')

    if extension_type == 'mod':
        Path(f'{extension_name}.nim').write_text(
            'import nimpy\n\nproc add(a: int, b: int): int {.exportpy.} =\n'
            '    return a + b\n'
        )

    elif extension_type == 'lib':
        cookiecutter(
            template='https://github.com/Pebaz/template-nimporter-ext-lib',
            extra_context=dict(ext_name=extension_name),
            no_input=True
        )

    else:
        raise ValueError(
            f'Extension is not one of [`mod`, `lib`], got: {extension_type}'
        )
    return


def nimporter_compile() -> None:
    def current_time_ms() -> float:
        return round(time.time() * 1000)

    overall_start = current_time_ms()

    nimporter_clean(Path())

    for ext in find_extensions(Path()):
        print(
            f'Building Extension {"Lib" if ext.is_dir() else "Mod"}: '
            f'{ext.name}'
        )

        start = current_time_ms()
        module_path = ext if ext.is_file() else ext / f'{ext.name}.nim'
        compile_extension_to_lib(ExtLib(module_path, Path(), ext.is_dir()))
        print('  Completed in', current_time_ms() - start, 'ms')

    print(
        'Completed all in',
        (current_time_ms() - overall_start) / 1000.0,
        'seconds'
    )
    return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Nimporter CLI')
    subs = parser.add_subparsers(dest='cmd', required=True)

    # List command
    subs.add_parser('list', help='List Nim extensions starting in current dir')

    # Clean command
    subs.add_parser(
        'clean',
        help=(
            'Run in project root to recursively remove __pycache__, '
            '.egg-info, build, and dist folders used by Nimporter'
        )
    )

    # Init command
    init = subs.add_parser(
        'init',
        help='Initializes the folder structure of a new extension'
    )
    init.add_argument(
        'extension_type',
        type=str,
        help=(
            'Either `mod` or `lib`. Extension modules are single files, '
            'extension libraries are are fully configurable mini Nim projects'
        )
    )
    init.add_argument(
        'extension_name',
        type=str,
        help='The importable name of the extension module or library'
    )

    # Compile command
    subs.add_parser(
        'compile',
        help='Precompile all extensions exactly as if they were imported'
    )

    return parser


def main(cli_args: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(cli_args or sys.argv[1:])

    if args.cmd == 'list':
        nimporter_list()

    elif args.cmd == 'clean':
        # cwd = pathlib.Path()
        # print('Cleaning Directory:', cwd.resolve())
        # clean(cwd)
        nimporter_clean(Path().resolve().absolute())

    # elif args.cmd == 'bundle': # nimporter_bundle has nit been defined yet.
        # nimporter_bundle(args.exp)

    elif args.cmd == 'compile':
        nimporter_compile()

    elif args.cmd == 'init':
        nimporter_init(args.extension_type, args.extension_name)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
