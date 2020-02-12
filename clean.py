"""
Iterates through all sub directories and removes any build artifacts and hashes.
"""

import sys, pathlib

EXT = '.pyd' if sys.platform == 'win32' else '.so'

def clean(dir=pathlib.Path()):
    "Recursively clear hash files and extensions stored in __pycache__ folders."
    for folder in filter(lambda p: p.is_dir(), dir.iterdir()):
        if folder.name == '__pycache__':
            for item in folder.iterdir():
                if item.suffix in ('.hash', EXT):
                    item.unlink()
        else:
            clean(folder)
