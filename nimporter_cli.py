"""
Iterates through all sub directories and removes any build artifacts and hashes.
"""

import sys, os, pathlib, argparse
from nimporter import NimCompiler

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
        else:
            clean(folder)


def main(args=None):
    parser = argparse.ArgumentParser(description='Nimporter CLI')
    parser.add_argument('--clean', action='store_true', required=True)
    args = parser.parse_args(args or sys.argv[1:])

    if args.clean:
        cwd = pathlib.Path()
        print('Cleaning Directory:', cwd.resolve())
        clean(cwd)


if __name__ == '__main__':
    main()
