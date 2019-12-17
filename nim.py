import sys, subprocess, importlib, hashlib
from pathlib import Path

class Nimporter:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        print(fullname, path, target)
        a = importlib.machinery.PathFinder.find_module(fullname)
        module_path = Path(a.path)
        build_artifact = (module_path.parent / '__pycache__') / (module_path.stem + '.so')
        return importlib.util.spec_from_file_location(
            fullname,
            location=str(build_artifact.absolute())
        )

importlib.machinery.SOURCE_SUFFIXES.insert(0, '.nim')
sys.meta_path.insert(0, Nimporter())

# _py_source_to_code = importlib.machinery.SourceFileLoader.source_to_code
# def _nimporter_source_to_code(self, data, path, _optimize=-1):
#     if Path(path).exists() and 
# importlib.machinery.SourceFileLoader.source_to_code = _nimporter_source_to_code

sys.path_importer_cache.clear()


import py
