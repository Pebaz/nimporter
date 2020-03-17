"""
Contains classes to compile Python-Nim Extension modules, import those modules,
and generate exceptions where appropriate.

In addition, distribution of libraries using Nim code via Nimporter can easily
compile those modules to C and bundle into a source or binary distribution so
users of the library don't have to install a Nim compiler.
"""

import sys, os, subprocess, importlib, hashlib, tempfile, shutil
from pathlib import Path
from contextlib import contextmanager
from setuptools import Extension

# NOTE(pebaz): https://stackoverflow.com/questions/39660934/error-when-using-importlib-util-to-check-for-library/39661116
from importlib import util


@contextmanager
def cd(path):
    "Convenience function to step in and out of a directory temporarily."
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)


class NimporterException(Exception):
    "Catch-all for Nimporter exceptions"


class NimCompileException(NimporterException):
    """
    Indicates that the invocation of the Nim compiler has failed.
    Displays the line of code that caused the error as well as the error message
    returned from Nim as a Python Exception.

    NOTE: The provided message must contain the string: 'Error:'
    """
    def __init__(self, msg):
        nim_module, error_msg = msg.split('Error:')
        nim_module = nim_module.splitlines()[-1]
        mod, (line_col) = nim_module.split('(')
        self.nim_module = Path(mod)
        line, col = line_col.split(',')
        self.line = int(line)
        self.col = int(col.replace(')', ''))
        self.error_msg = error_msg
        
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


class NimInvokeException(NimporterException):
    "Exception for when a given CLI command fails."

    def __init__(self, cwd, cmd_line, err_msg, out=''):
        self.cwd = Path(cwd).resolve()
        self.cmd_line = cmd_line
        self.err_msg = err_msg
        self.out = out

    def get_output(self):
        return self.out

    def __str__(self):
        cmd = self.cmd_line[0]
        message = f'Failed to run command: {cmd}\n\n'
        message += f'Current Directory:\n    {self.cwd}\n\n'
        message += f'Error Message:\n    "{self.err_msg.strip()}"\n\n'
        #message += f'Command Line Arguments:\n    {" ".join(self.cmd_line)}'
        message += f'Command Line Arguments:\n    {cmd}\n'
        for arg in self.cmd_line[1:]:
            message += f'        {arg}\n'
        return message


class NimCompiler:
    """
    Nim compiler invoker. Features:
     - Compile Nim files and return any failure messages as Python exceptions.
     - Store hashes of Nim source files to only recompile when module changes.
     - Stores hash in __pycache__ directory to not clutter up file system.
    
    Attributes:
        EXT(str): the extension to use for the importable build artifact.
        NIM_CLI_ARGS(list): compiler switches common to all builds.
    """
    EXT = '.pyd' if sys.platform == 'win32' else '.so'
    NIM_CLI_ARGS = [
        '--opt:speed',
        '--parallelBuild:0',
        '--gc:markAndSweep',
        '--threads:on',
        '--app:lib',
        '-d:release',
        '-d:ssl'
    ]

    @classmethod
    def build_artifact(cls, module_path):
        """
        Returns the Path to the built .PYD or .SO. Does not imply it has already
        been built.

        Args:
            module_path(Path): the path to the module or library.

        Returns:
            The path to a build artifact if compilation were to succeed. If the
            module_path is a directory, an appropriate build artifact path
            within that directory is returned.
        """
        filename = module_path.stem + cls.EXT
        return (cls.pycache_dir(module_path) / filename).resolve()

    @classmethod
    def pycache_dir(cls, module_path):
        """Return the __pycache__ directory as a Path."""
        if module_path.is_dir():
            return (module_path / '__pycache__').resolve()
        else:
            return (module_path.parent / '__pycache__').resolve()

    @classmethod
    def invoke_compiler(cls, nim_args: list):
        """
        Returns a tuple containing any errors, warnings, or hints from the
        compilation process.
        """
        process = subprocess.run(
            nim_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.stdout, process.stderr
        out = out.decode() if out else ''
        err = err.decode() if err else ''
        lines = (out + err).splitlines()

        errors   = [line for line in lines if 'Error:' in line]
        warnings = [line for line in lines if 'Warning:' in line]
        hints    = [line for line in lines if 'Hint:' in line]

        return out, errors, warnings, hints

    @classmethod
    def ensure_nimpy(cls):
        "Makes sure that the Nimpy Nim library is installed."
        out, errors, _, _ = cls.invoke_compiler('nimble path nimpy'.split())

        if not out or errors:
            nimble_args = 'nimble install nimpy --accept'.split()
            out, errors, _, _ = cls.invoke_compiler(nimble_args)

        if errors: raise NimInvokeException(Path(), nimble_args, errors[0], out)

    @staticmethod
    def get_import_prefix(module_path, root):
        "Returns tuple of packages containing the given module."
        root_path = root.resolve()
        full_path = module_path.resolve()

        assert full_path >= root_path, 'Extension path is not within root dir.'

        return full_path.parts[len(root_path.parts):]

    @classmethod
    def find_nim_std_lib(cls):
        nimexe = shutil.which('nim')
        if not nimexe:
            return None
        nimexe = Path(nimexe)
        result = nimexe.parent / '../lib'
        if not (result / 'system.nim').exists():
            result = nimexe.resolve().parent / '../lib'
            if not (result / 'system.nim').exists():
                return None
        return result.resolve()

    @classmethod
    def get_switches(cls, switch_file, **global_scope):
        global_scope = global_scope.copy()
        assert switch_file.exists(), (
            'Cannot open nonexistent switch file: ' + str(switch_file)
        )
        exec(switch_file.read_text(), global_scope)
        return global_scope['__switches__']

    @classmethod
    def compile_nim_extension(cls, module_path, root, *, library: bool):
        """
        Compiles/returns an Extension and installs `.nimble` dependencies.

        Libraries MUST have a Nim file named "<library name>.nim" at the project
        root as well as a file ending with ".nimble".

        NOTE: The library parameter signifies (albeit subtly) that the given Nim
        library has (can have) dependencies (Nimble file).

        Args:
            module_path(Path): the path to the library directory or a Nim file.
            root(Path): the path to the directory containing the entire project.
            library(bool): hint as to how to treat the `module_path` parameter.

        Returns:
            An Extension upon successful compilation, else None.

        Raises:
            Exception if the library path does not contain the files listed
            above or any other compilation error.
        """

        if not module_path.exists():
            raise NimporterException(
                f'{module_path.absolute()} does not exist.'
            )

        module_name = module_path.stem
        build_dir = Path(tempfile.mktemp())

        if module_path.is_file():
            library_path = module_path.parent.resolve()
            
        elif module_path.is_dir():
            library_path = module_path.resolve()
            module_path = library_path / (library_path.name + '.nim')

        if library and not any(library_path.glob('*.nimble')):
            raise NimporterException(
            f"Library: {library_path} doesn't contain a .nimble file"
        )

        cls.ensure_nimpy()

        build_dir = Path(tempfile.mktemp())
        switch_file = library_path / 'switches.py'

        # Switches file found
        if switch_file.exists():
            switches = cls.get_switches(
                switch_file,
                MODULE_PATH=module_path,
                BUILD_DIR=build_dir,
                IS_LIBRARY=library
            )
            nim_args = switches['bundle']

            # switch_script = switch_file.read_text()
            # global_scope = {
            #     'MODULE_PATH' : module_path,
            #     'BUILD_DIR' : build_dir,
            #     'IS_LIBRARY' : library
            # }
            # exec(switch_script, global_scope)
            # nim_args = global_scope['__switches__']['bundle']

        # Use standard switches
        else:
            exe = ['nimble' if library else 'nim', 'cc', '-c']
            nim_args = (
                exe + cls.NIM_CLI_ARGS +
                [f'--nimcache:{build_dir}', f'{module_path}'] +
                (['--accept'] if library else [])
            )

        with cd(library_path if library else Path('.')) as tmp_cwd:
            output, errors, warnings, hints = cls.invoke_compiler(nim_args)

        if errors:
            if library:
                raise NimInvokeException(Path(), nim_args, errors[0], output)
            else:
                raise NimCompileException(errors[0])

        for warn in warnings: print(warn)

        csources = [str(c) for c in build_dir.iterdir() if c.suffix == '.c']

        # Copy over needed header(s)
        NIMBASE = 'nimbase.h'
        nimbase = cls.find_nim_std_lib() / NIMBASE
        shutil.copyfile(str(nimbase), str(build_dir / NIMBASE))

        # Coerce proper import path using root path
        import_prefix = cls.get_import_prefix(module_path.parent, root)
        module_part = tuple() if library else (module_name,)
        import_path = '.'.join(import_prefix + module_part)
        #import_path = '.'.join(import_prefix + (module_name,))

        return Extension(
            name=import_path,
            sources=csources,
            include_dirs=[str(build_dir)]
        )

    @classmethod
    def compile_nim_code(cls, module_path, build_artifact, *, library: bool):
        """
        Returns a Spec object so a Nim module/library can be directly imported.

        NOTE: The `module_path` keyword argument can be either a path to a Nim
        file (in the case of `library=False`) or a path to a directory (in the
        case of `library=True`). However, it has a third supported usage. It can
        be a Nim module when `library=True` and this method will search for the
        Nimble file alongside the given path.

        NOTE: The library parameter signifies (albeit subtly) that the given Nim
        library has (can have) dependencies (Nimble file).
        """

        if not module_path.exists():
            raise NimporterException(
                f'{module_path.absolute()} does not exist.'
            )

        if library and module_path.is_file():
            raise NimporterException(
                'Librarys are built using folder name, not specific Nim module'
            )

        elif not library and module_path.is_dir():
            raise NimporterException(
                'Modules are built using module name, not containing folder'
            )

        if module_path.is_file():
            library_path = module_path.parent.resolve()

        elif module_path.is_dir():
            library_path = module_path.resolve()
            module_path = library_path / (library_path.name + '.nim')

        if library and not any(library_path.glob('*.nimble')):
            raise NimporterException(
            f"Library: {library_path} doesn't contain a .nimble file"
        )

        cls.ensure_nimpy()

        build_artifact = cls.build_artifact(module_path)
        switch_file = library_path / 'switches.py'

        # Switches file found
        if switch_file.exists():
            switches = cls.get_switches(
                switch_file,
                MODULE_PATH=module_path,
                BUILD_ARTIFACT=build_artifact,
                BUILD_DIR=None,  # Necessary for import/bundle compatibility
                IS_LIBRARY=library
            )
            nim_args = switches['import']

            # switch_script = switch_file.read_text()
            # global_scope = {
            #     'MODULE_PATH' : module_path,
            #     'BUILD_ARTIFACT' : build_artifact,
            #     'BUILD_DIR' : None,  # Necessary for import/bundle compatibility
            #     'IS_LIBRARY' : library
            # }
            # exec(switch_script, global_scope)
            # nim_args = global_scope['__switches__']['import']

        # Use standard switches
        else:
            exe = [('nimble' if library else 'nim'), 'c']
            nim_args = (
                exe + cls.NIM_CLI_ARGS +
                [f'--out:{build_artifact}', f'{module_path}'] +
                (['--accept'] if library else [])
            )

        with cd(library_path if library else Path('.')) as tmp_cwd:
            output, errors, warnings, hints = cls.invoke_compiler(nim_args)

        if errors:
            if library:
                raise NimInvokeException(tmp_cwd, nim_args, errors[0], output)
            else:
                raise NimCompileException(errors[0])

        for warn in warnings: print(warn)

        return build_artifact


class Nimporter:
    """
    Python module finder purpose-built to find Nim modules on the Python PATH,
    compile them, hide them within the __pycache__ directory with other compiled
    Python files, and then return it as a full Python module.
    This Nimporter can only import Nim modules with procedures exposed via the
    [Nimpy](https://github.com/yglukhov/nimpy) library acting as a bridge.

    Atrributes:
        IGNORE_CACHE(bool): when True, will always trigger a rebuild of any Nim
            modules. Can be set by the importer of this module.
    """
    IGNORE_CACHE = False

    @classmethod
    def hash_filename(cls, module_path):
        """Return the hash filename as a Path."""
        return NimCompiler.pycache_dir(module_path) / (module_path.name + '.hash')

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
        """Returns the bits of the hash for a given Nim module."""
        if not cls.is_hashed(module_path):
            path = module_path.absolute()
            raise NimporterException(f'Module {path} has not yet been hashed.')
        return cls.hash_filename(module_path).read_bytes()

    @classmethod
    def hash_changed(cls, module_path):
        """
        Return whether or not a given Nim file has changed since last hash. If
        the module has not yet been hashed, returns True.
        """
        if not cls.is_hashed(module_path):
            return True
        return cls.get_hash(module_path) != cls.hash_file(module_path)

    @staticmethod
    def hash_file(module_path):
        """
        Returns the hash of the Nim file.
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
        hash_file = cls.hash_filename(module_path)
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        with hash_file.open('wb') as file:
            file.write(cls.hash_file(module_path))

    @classmethod
    def import_nim_module(cls, fullname, path:list=None, ignore_cache=None):
        """
        Can be used to explicitly import a module rather than using the `import`
        keyword. Allows the cache to be ignored to solve issues arising from
        caching one module when 10 other imported Nim libraries have changed.

        Example Use:

        >>> # Rather than:
        >>> import foo
        >>> # You can say:
        >>> foo = Nimporter.import_nim_module('foo', ['/some/random/dir'])

        Args:
            fullname(str): the module to import. Can be 'foo' or 'foo.bar.baz'
            path(list): a list of paths to search first.
            ignore_cache(bool): whether or not to use a cached build if found.

        Returns:
            The Python Module object representing the imported PYD or SO file.            
        """
        if ignore_cache != None:
            tmp = cls.IGNORE_CACHE
            cls.IGNORE_CACHE = ignore_cache

        try:
            spec = (
                cls.import_nim_code(fullname, path, library=False)
                or
                cls.import_nim_code(fullname, path, library=True)
            )
        finally:
            if ignore_cache != None:
                cls.IGNORE_CACHE = tmp

        if not spec:
            raise ImportError(f'No module named {fullname}')

        module = spec.loader.create_module(spec)
        return module

    @classmethod
    def import_nim_code(cls, fullname, path, *, library: bool):
        "Search for, compile, and return Spec for module loaders."
        parts = fullname.split('.')
        module = parts[-1] if library else parts.pop()
        module_file = f'{module}.nim'
        path = list(path) if path else []  # Ensure that path is always a list

        # NOTE(pebaz): Package is different based only on `library`
        package = '/'.join(parts)

        search_paths = {
            Path(i)
            for i in (path + sys.path + ['.'])
            if Path(i).is_dir()
        }

        for search_path in search_paths:
            spath = (search_path / package).resolve()

            # Derive module path regardless of library or module

            if library and not any(spath.glob('*.nimble')): continue

            module_path = spath / module_file

            if not module_path.exists(): continue

            build_artifact = NimCompiler.build_artifact(module_path)

            if cls.should_compile(module_path):
                NimCompiler.compile_nim_code(
                    module_path.parent if library else module_path,
                    build_artifact,
                    library=library
                )

                cls.update_hash(module_path)
            
            return util.spec_from_file_location(
                fullname,
                location=str(build_artifact.absolute())
            )

    @classmethod
    def should_compile(cls, module_path):
        "Determine if a module should be rebuilt using only the path to it."
        return any([
            cls.IGNORE_CACHE,
            cls.hash_changed(module_path),
            not cls.is_cache(module_path),
            not cls.is_built(module_path)
        ])

    @classmethod
    def _find_extensions(cls, path, exclude_dirs=[]):
        """
        Compiles Nim files to C and creates Extensions from them for distribution.
        """
        nim_exts = []

        for item in path.iterdir():
            if item.is_dir() and list(item.glob('*.nimble')):
                "Treat directory as one single Extension"
                (nimble_file,) = item.glob('*.nimble')
                nim_file = nimble_file.parent / (nimble_file.stem + '.nim')

                # NOTE(pebaz): Folder must contain Nim file of exact same name.
                if nim_file.exists():
                    nim_exts.append(item)

            elif item.is_dir():
                "Treat item as directory"
                nim_exts.extend(
                    cls._find_extensions(item, exclude_dirs=exclude_dirs)
                )

            elif item.suffix == '.nim':
                "Treat item as a Nim Extension."
                nim_exts.append(item)

        return nim_exts

    @classmethod
    def _build_nim_extension(cls, path, root):
        return NimCompiler.compile_nim_extension(
            path, root, library=path.is_dir()
        )

    @classmethod
    def build_nim_extensions(cls, exclude_dirs=[]):
        """
        Compiles Nim modules and libraries to C and creates Extensions from them
        for source, binary, or wheel distribution.

        Automatically recurses through the project directory to find all the Nim
        modules and Nim libraries.

        Returns:
            A list of Extensions that can be added to the setup() function's
            "ext_modules" keyword argument.
        """
        extensions = []
        root = Path()

        for extension in cls._find_extensions(root, exclude_dirs):
            ext = cls._build_nim_extension(extension, root)
            if ext: extensions.append(ext)

        return extensions


def register_importer(list_position):
    """
    Adds a given importer class to `sys.meta_path` at a given position.

    NOTE: The position in `sys.meta_path` is extremely relevant.
    """
    def decorator(importer):
        nonlocal list_position

        # Make the list_position act like how a list is normally indexed
        if list_position < 0:
            list_position = len(sys.meta_path) + 1 - list_position
 
        sys.meta_path.insert(list_position, importer)

        # Ensure that Nim files won't be passed up because of other Importers.
        sys.path_importer_cache.clear()
        importlib.invalidate_caches()

        return importer
    return decorator


@register_importer(-1)
class NimModImporter:
    """
    Extends Python import machinery to be able to import Nim modules.

    NOTE: Must be placed at the back of `sys.meta_path` because Python modules
    should be given precedence over Nim modules.

    Nim Modules can be placed anywhere that Python modules can. However, if a
    Python module and a Nim module with the same name are in the same package,
    the Python module will be imported.
    """

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        return Nimporter.import_nim_code(fullname, path, library=False)


@register_importer(0)
class NimLibImporter:
    """
    Extends Python import machinery to be able to import Nim libraries.

    NOTE: Must be placed at the front of `sys.meta_path` because of how Python
    treats folders when imported.

    Before NimLibImporter can attempt to find a folder containing a Nimble file
    containing dependency info and a corresponding Nim module, Python's import
    machinery imports the folder as a `namspace` type.

    The only way to allow NimLibImporter to get a chance to import Nim libraries
    is to put it at the front of `sys.meta_path`. However, this has a small side
    effect of making Nim libraries have precedence over Python namespaces.

    This should never have any adverse effects since the criterion for a Nim
    library in relation to Nimporter is to have a folder containing a Nim module
    and a Nimble file with the same name as the folder. By placing both of those
    files into a directory, it should be extremely clear that the given folder
    is a Nim library.

    Additionally, this also means that a Nim library cannot contain any Python
    modules.
    """

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        return Nimporter.import_nim_code(fullname, path, library=True)


# This should be the only real usage of the Nimporter module beyond importing it
build_nim_extensions = Nimporter.build_nim_extensions
__all__ = ['build_nim_extensions']
