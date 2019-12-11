import sys, importlib
from importlib.abc import SourceLoader
from importlib.machinery import FileFinder

class MyLoader(SourceLoader):
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path

    def get_filename(self, fullname):
        return self.path

    def get_data(self, filename):
        """exec_module is already defined for us, we just have to provide a way
        of getting the source code of the module"""
        with open(filename) as f:
            data = f.read()
        # do something with data ...
        # eg. ignore it... return "print('hello world')"
        return data

    def exec_module(self, module):
        print(module)
        print(module.__file__)
        # spec = importlib.util.spec_from_file_location(
        #     module.__name__,
        #     location=str(build_artifact.absolute())
        # )
        # module = importlib.util.module_from_spec(spec)

loader_details = MyLoader, [".nim"]
sys.path_hooks.insert(
    0,
    FileFinder.path_hook(loader_details
))

sys.path_importer_cache.clear()
importlib.invalidate_caches()

import bar
