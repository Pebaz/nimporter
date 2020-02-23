"""
Iterates through all sub directories and removes any build artifacts and hashes.
"""

import sys, pathlib, argparse
from nimporter import NimCompiler

def clean(dir=pathlib.Path()):
    "Recursively clear hash files and extensions stored in __pycache__ folders."
    for folder in filter(lambda p: p.is_dir(), dir.iterdir()):
        if folder.name == '__pycache__':
            for item in folder.iterdir():
                if item.suffix in ('.hash', NimCompiler.EXT):
                    print('Deleted:'.ljust(19), item.resolve())
                    item.unlink()
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
