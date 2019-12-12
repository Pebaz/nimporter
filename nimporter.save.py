import sys, importlib
from pathlib import Path
from importlib.abc import SourceLoader
from importlib.machinery import FileFinder, PathFinder


import sys, subprocess, importlib, hashlib
from pathlib import Path

class NimCompilerException(Exception):
    """
    Indicates that the invocation of the Nim compiler has failed.
    Displays the line of code that caused the error as well as the error message
    returned from Nim as a Python Exception.
    """
    def __init__(self, msg):
        try:
            nim_module, error_msg = msg.split(' Error: ')
            nim_module = nim_module.splitlines()[-1]
            mod, (line_col) = nim_module.split('(')
            self.nim_module = Path(mod)
            line, col = line_col.split(',')
            self.line = int(line)
            self.col = int(col[:-1])
            self.error_msg = error_msg
        except Exception as e:
            # Raise the original exception if anything went wrong during parsing
            raise Exception(msg).with_traceback(e.__traceback__) from e
        
    def __str__(self):
        """
        Return the string representation of the given compiler error.
        """
        message = self.error_msg + '\n'
        
        with open(self.nim_module, 'r') as mod:
            line = 0
            for each_line in mod:
                line += 1

                if line == self.line:
                    message += f' -> {each_line}'
                    
                elif line > self.line + 2:
                    break
                
                elif line > self.line - 3:
                    message += f' |  {each_line}'

        message = message.rstrip() + (
            f'\n\nAt {self.nim_module.absolute()} '
            f'{self.line}:{self.col}'
        )
        
        return message


class NimCompiler:
    """
    Nim compiler invoker. Features:
     - Compile Nim files and return any failure messages as Python exceptions.
     - Store hashes of Nim source files to only recompile when module changes.
     - Stores hash in __pycache__ directory to not clutter up file system.
    
    Attributes:
        EXT(str): the extension to use for the importable build artifact.
    """
    EXT = '.pyd' if sys.platform == 'win32' else '.so'

    @classmethod
    def pycache_dir(cls, module_path):
        """Return the __pycache__ directory as a Path."""
        return module_path.parent / '__pycache__'

    @classmethod
    def hash_filename(cls, module_path):
        """Return the hash filename as a Path."""
        return cls.pycache_dir(module_path) / (module_path.name + '.hash')

    @classmethod
    def is_cache(cls, module_path):
        """
        Return whether or not a __pycache__ directory exists to store hashes and
        build artifacts.
        """
        return NimCompiler.pycache_dir(module_path).exists()

    @classmethod
    def is_hashed(cls, module_path):
        """Return whether or not a given Nim file has already been hashed."""
        return cls.hash_filename(module_path).exists()

    @classmethod
    def is_built(cls, module_path):
        """Return whether or not a given Nim file has already been hashed."""
        return NimCompiler.build_artifact(module_path).exists()

    @classmethod
    def get_hash(cls, module_path):
        """Returns the 128 bits of the hash for a given Nim module."""
        if not cls.is_hashed(module_path):
            path = module_path.absolute()
            raise Exception(f'Module {path} has not yet been hashed.')
        return cls.hash_filename(module_path).read_bytes()

    @classmethod
    def hash_changed(cls, module_path):
        """
        Return whether or not a given Nim file has changed since last hash. If
        the module has not yet been hashed, returns True.
        """
        if not NimCompiler.is_hashed(module_path):
            return True
        return cls.get_hash(module_path) != NimCompiler.hash_file(module_path)

    @classmethod
    def hash_file(cls, module_path):
        """
        Returns a 128 bit non-cryptographic hash of a given file using MD5.
        """
        block_size = 65536
        hasher = hashlib.md5()
        with module_path.open('rb') as file:
            buf = file.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(block_size)
        return hasher.digest()

    @classmethod
    def update_hash(cls, module_path):
        """
        Creates or updates the <mod-name>.nim.hash file within the __pycache__
        directory.
        """
        with cls.hash_filename(module_path).open('wb') as file:
            file.write(cls.hash_file(module_path))

    @classmethod
    def build_artifact(cls, module_path):
        """
        Returns the Path to the built .PYD or .SO. Does not imply it has already
        been built.
        """
        return cls.pycache_dir(module_path) / (module_path.stem + cls.EXT)

    @classmethod
    def compile(cls, module_path, release_mode=False):
        """
        Compiles a given Nim module and returns the path to the built artifact.
        Raises an exception if compilation fails for any reason.
        """
        build_artifact = cls.build_artifact(module_path)

        nimc_cmd = (
            f'nim c --threads:on --tlsEmulation:off --app:lib '
            f'--hints:off --parallelBuild:0 '
            f'{"-d:release" if release_mode else ""}'
            f'--out:{build_artifact} '
            f'{module_path}'
        )
        
        process = subprocess.run(
            nimc_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.stdout, process.stderr
        out = out.decode() if out else ''
        err = err.decode() if err else ''

        # Handle any compiler errors
        NIM_COMPILE_ERROR = ' Error: '
        if NIM_COMPILE_ERROR in err:
            raise NimCompilerException(err)

        elif NIM_COMPILE_ERROR in out:
            raise NimCompilerException(out)
        
        cls.update_hash(module_path)

        return build_artifact




class MyLoader(SourceLoader):
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path

    def get_filename(self, fullname):
        return self.path

    def get_data(self, filename):
        """Returns the source code of the Nim file."""
        return Path(filename).read_text()

    def exec_module(self, module):
        #importlib.util.source_hash()

        module_path = Path(module.__file__)

        should_compile = any([
            NimCompiler.hash_changed(module_path),
            not NimCompiler.is_cache(module_path),
            not NimCompiler.is_built(module_path)
        ])

        if should_compile:
            build_artifact = NimCompiler.compile(module_path)
        else:
            build_artifact = NimCompiler.build_artifact(module_path)
        
        spec = importlib.util.spec_from_file_location(
            module.__name__,
            location=str(build_artifact.absolute())
        )
        module = importlib.util.module_from_spec(spec)
        #spec.loader.exec_module(module)
        return module

'''
class SibilantPathFinder(PathFinder):
    """
    An overridden PathFinder which will hunt for sibilant files in
    sys.path. Uses storage in this module to avoid conflicts with the
    original PathFinder
    """
    @classmethod
    def invalidate_caches(cls):
        for finder in _path_importer_cache.values():
            if hasattr(finder, 'invalidate_caches'):
                finder.invalidate_caches()

    @classmethod
    def _path_hooks(cls, path):
        for hook in _path_hooks:
            try:
                return hook(path)
            except ImportError:
                continue
        else:
            return None

    @classmethod
    def _path_importer_cache(cls, path):
        if path == '':
            try:
                path = getcwd()
            except FileNotFoundError:
                # Don't cache the failure as the cwd can easily change to
                # a valid directory later on.
                return None
        try:
            finder = _path_importer_cache[path]
        except KeyError:
            finder = cls._path_hooks(path)
            _path_importer_cache[path] = finder
        return finder
'''

#importlib.machinery.SOURCE_SUFFIXES.insert(0, '.nim')
loader_details = MyLoader, ['.nim']
sys.path_hooks.insert(0,
    FileFinder.path_hook(loader_details)
)
# sys.meta_path.append(SibilantPathFinder)

sys.path_importer_cache.clear()
importlib.invalidate_caches()

# import bar
# print(bar.hello('world'))

# import foo
# import bazzle.buzzle
