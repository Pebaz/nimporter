# type: ignore[attr-defined]
"""
Iterates through all sub directories and removes any build artifacts and hashes.
"""

import os
import sys
import time
import shutil
import pathlib
import argparse
import subprocess
from pathlib import Path
from nimporter.lib import EXT_DIR, find_extensions


SETUPPY_TEMPLATE = f"""
# Setup.py tutorial:
# https://github.com/navdeep-G/setup.py
# Edit `packages=` to fit your requirements

import setuptools, pathlib, sysconfig
from setuptools.command.build_ext import build_ext
import nimporter


class NoSuffixBuilder(build_ext):
    \"\"\"
    Optional.

    Removes the target platform, architecture, and Python version from the
    final artifact.

    Example:
        The artifact: `module.linux-x86_64.cpython.3.8.5.so`
        Becomes: `module.so`
    \"\"\"
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        return filename.replace(ext_suffix, "") + pathlib.Path(filename).suffix


setuptools.setup(
    name="{ pathlib.Path().absolute().name }",
    packages=[..],  # Please read the above tutorial
    ext_modules=nimporter.build_nim_extensions()
    cmdclass={{"build_ext": NoSuffixBuilder}},
)
"""


def nimporter_list():
    for extension in find_extensions(Path()):
        print(extension)


def nimporter_clean(path: Path):
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

    # Build command
    build = subs.add_parser(
        'build',
        help=(
            'Builds a Nim module/library into an importable Python extension'
        )
    )
    build.add_argument(
        'source',
        type=pathlib.Path,
        help='the Nim module/library to compile'
    )
    build.add_argument(
        '--dest',
        type=pathlib.Path,
        help='the folder to store the build artifact'
    )

    # Bundle command
    bundle_parser = subs.add_parser(
        'bundle',
        help=(
            'Convenience command for running: '
            'python setup.py sdist/bdist_wheel'
        )
    )
    bundle = bundle_parser.add_subparsers(dest='exp', required=True)
    bin_ = bundle.add_parser('bin')
    src = bundle.add_parser('src')

    # Compile command
    compile_ = subs.add_parser(
        'compile',
        help=(
            'Clean project and then recurse through and build all Nim '
            'modules/libraries'
        )
    )

    # Init command
    build = subs.add_parser(
        'init',
        help='Initializes the folder structure of a new extension'
    )
    build.add_argument(
        'extension-type',
        type=str,
        help=(
            'Either `mod` or `lib`. Extension modules are single files, '
            'extension libraries are are fully configurable mini Nim projects'
        )
    )
    # build.add_argument(
    #     '--dest',
    #     type=pathlib.Path,
    #     help='the folder to store the build artifact'
    # )

    return parser


def main(cli_args=None):

    # # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # if 'list' in cli_args:
    #     nimporter_list()

    # elif 'clean' in cli_args:
    #     nimporter_clean(Path())

    # elif 'build' in cli_args:
    #     nimporter_build()

    # return
    # # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    args = build_parser().parse_args(cli_args or sys.argv[1:])

    if args.cmd == 'list':
        nimporter_list()

    elif args.cmd == 'clean':
        # cwd = pathlib.Path()
        # print('Cleaning Directory:', cwd.resolve())
        # clean(cwd)
        nimporter_clean(Path().resolve().absolute())

    elif args.cmd == 'build':
        args.source = args.source.absolute()

        if not args.dest:
            args.dest = NimCompiler.build_artifact(args.source).parent

        else:
            assert args.dest.is_dir(), (
                'Cannot specify output filename since extensions change per '
                'platform. Please specify an output directory such as ".".'
            )

        args.dest.mkdir(exist_ok=True)

        module = args.source

        if args.source.is_dir():
            is_library = bool([*module.glob('*.nimble')])
            assert is_library, 'Library dir must contain <libname>.nimble file'

        elif args.source.is_file():
            is_library = bool([*module.parent.glob('*.nimble')])
            if is_library: module = module.parent

        temp_build_dir = pathlib.Path('build').absolute()
        temp_build_dir.mkdir(exist_ok=True)
        artifact = temp_build_dir / (args.source.stem + NimCompiler.EXT)

        try:
            NimCompiler.compile_nim_code(
                module, artifact, library=is_library
            )
            shutil.copy(artifact, args.dest)
            module_name = args.source.stem + '.nim'
            Nimporter.update_hash(args.dest.parent / module_name)
        finally:
            shutil.rmtree(temp_build_dir)

    elif args.cmd == 'bundle':
        setup = pathlib.Path('setup.py')

        if not setup.exists():
            print('No setup.py found in dir, would you like to generate one?')

            answer = 'a'
            while answer not in 'YN':
                answer = input('  Y/N: ').upper() or 'a'

            if answer == 'Y':
                setup.write_text(SETUPPY_TEMPLATE)

                print('Generated reference setup.py')
                print('Modify setup.py to point to your modules/packages.')

                bundle_type = 'source' if args.exp == 'src' else 'binary'

                print(
                    f'Once you have finished, run `{" ".join(cli_args)}` '
                    f'again to create a {bundle_type} distribution package.'
                )
        else:
            pyexe = 'python' if sys.platform == 'win32' else 'python3'

            if args.exp == 'bin':
                subprocess.Popen(
                    f'{pyexe} setup.py bdist_wheel'.split()
                ).wait()

            elif args.exp == 'src':
                subprocess.Popen(f'{pyexe} setup.py sdist'.split()).wait()

    elif args.cmd == 'compile':
        clean()

        CTM = lambda: round(time.time() * 1000)
        start = CTM()
        extensions = Nimporter._find_extensions(pathlib.Path())

        for extension in extensions:
            is_lib = extension.is_dir()

            print(
                f'Building Extension {"Lib" if is_lib else "Mod"}: '
                f'{extension.name}'
            )

            NimCompiler.compile_nim_code(
                extension.absolute(),
                NimCompiler.build_artifact(extension.absolute()),
                library=is_lib
            )

            if is_lib:
                Nimporter.update_hash(extension / (extension.name + '.nim'))
            else:
                Nimporter.update_hash(extension)

        print('Done.')
        print(
            f'Built {len(extensions)} Extensions In '
            f'{(CTM() - start) / 1000.0} secs'
        )

    elif args.cmd == 'init':
        print('Initializing new extension')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
