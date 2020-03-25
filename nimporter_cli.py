"""
Iterates through all sub directories and removes any build artifacts and hashes.
"""

import sys, os, pathlib, argparse, tempfile, shutil
from nimporter import NimCompiler, Nimporter

def clean(dir=pathlib.Path()):
    "Recursively clear hash files and extensions stored in __pycache__ folders."

    # .exp and .lib are generated on Windows
    remove_these = NimCompiler.EXT, '.hash', '.exp', '.lib'

    for folder in filter(lambda p: p.is_dir(), dir.iterdir()):
        if folder.name == '__pycache__':
            for item in folder.iterdir():
                if not item.exists():
                    continue

                if item.suffix in remove_these:
                    os.remove(str(item.resolve()))
                    print('Deleted:'.ljust(19), item.resolve())

        elif folder.name == 'nim-extensions':
            shutil.rmtree(str(folder.absolute()))
            print('Deleted Folder:'.ljust(19), folder.absolute())

        else:
            if list(folder.glob('MANIFEST.in')):
                item = folder / 'MANIFEST.in'
                header = 'NIMPORTER BUNDLE'
                for line in item.read_text().splitlines():
                    if header in line:
                        os.remove(str(item.resolve()))
                        print('Deleted:'.ljust(19), item.resolve())
            clean(folder)


def main(args=None):
    parser = argparse.ArgumentParser(description='Nimporter CLI')
    subs = parser.add_subparsers(dest='cmd', required=True)

    subs.add_parser('clean')
    build = subs.add_parser('build')
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

    args = parser.parse_args(args or sys.argv[1:])

    if args.cmd == 'clean':
        cwd = pathlib.Path()
        print('Cleaning Directory:', cwd.resolve())
        clean(cwd)

    elif args.cmd == 'build':
        args.source = args.source.absolute()
        if not args.dest: args.dest = NimCompiler.build_artifact(args.source)
        module = args.source

        if args.source.is_dir():
            is_library = bool([*module.glob('*.nimble')])
        elif args.source.is_file():
            is_library = bool([*module.parent.glob('*.nimble')])
            if is_library: module = module.parent

        temp_build_dir = pathlib.Path('build')
        temp_build_dir.mkdir()
        artifact = temp_build_dir / args.dest.name
        try:
            NimCompiler.compile_nim_code(
                module, artifact, library=False
            )
            shutil.copy(artifact, args.dest.parent)
        finally:
            shutil.rmtree(temp_build_dir)


if __name__ == '__main__':
    main()
