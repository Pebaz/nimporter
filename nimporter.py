"""
Contains classes to compile Python-Nim Extension modules, import those modules,
and generate exceptions where appropriate.
"""

import sys, os, subprocess, importlib, hashlib, tempfile, shutil
from pathlib import Path
from setuptools import Extension

# NOTE(pebaz): https://stackoverflow.com/questions/39660934/error-when-using-importlib-util-to-check-for-library/39661116
from importlib import util


# When True, will always trigger a rebuild of any Nim modules
# Can be set by the importer of this module
IGNORE_CACHE = False


'''
TODO:

[x] Ensure module and library extensions are properly namespaced.
[x] Move hashing/etc. methods to Nimporter class (it's the only one that needs).
[x] Create one single compile() method for Nimporter.
[x] Create compile_extension() method using compile() with different arguments.
[x] Create compile_module() method using compile() with different arguments.
[x] Create compile_library() method using compile() with different arguments.
[x] Modify the import system to be able to install dependencies from .nimble and
    make it so that Folders themselves can be imported.
[x] Don't support multiple library module names: (main.nim/lib.nim)
[ ] Cleanup and consolidate code


[ ] Allow fine-grained control over compiler switches. This can be configured by
    placing a `module-name.cfg` right next to the `.nimble` file. Single modules
    do not have the option of configuring compiler switches.
[ ] Add API to programatically import Nim file with exact compilation switches.
    [ ] Internally calls __compile()
'''



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

    @staticmethod
    def get_import_prefix(module_path, root):
        "Returns tuple of packages containing the given module."
        root_path = root.resolve()
        full_path = module_path.resolve()

        assert full_path >= root_path, 'Extension path is not within root dir.'

        return full_path.parts[len(root_path.parts):]

    @classmethod
    def compile_extension_module(cls, module_path, root):
        """Compile Nim to C and return Extension pointing to the C source files."""

        module_name = module_path.stem
        build_dir = Path(tempfile.mktemp())

        exe = 'nim cc -c'.split()
        nim_args = (
            exe + cls.NIM_CLI_ARGS +
            [f'--nimcache:{build_dir}', f'{module_path}']
        )

        output, errors, warnings, hints = cls.invoke_compiler(nim_args)

        for warn in warnings: print(warn)

        if errors: raise NimCompilerException(errors[0])

        csources = [str(c) for c in build_dir.iterdir() if c.suffix == '.c']

        # Copy over needed header(s)
        NIMBASE = 'nimbase.h'
        nimbase = cls.find_nim_std_lib() / NIMBASE
        shutil.copyfile(str(nimbase), str(build_dir / NIMBASE))

        # Coerce proper import path using root path
        import_prefix = cls.get_import_prefix(module_path.parent, root)
        import_path = '.'.join(import_prefix + (module_name,))

        return Extension(
            name=import_path,
            sources=csources,
            include_dirs=[str(build_dir)]
        )

    @classmethod
    def compile_extension_library(cls, library_path, root):
        """
        Compiles and returns an Extension and installs dependencies in .nimble.

        Libraries MUST have a Nim file named "main.nim" or "library.nim" at the
        project root as well as a file ending with ".nimble".

        Returns:
            An Extension upon successful compilation, else None.

        Raises:
            Exception if the library path does not contain the files listed
            above or any other compilation error.
        """

        library_path = library_path.resolve()
        module_name = library_path.name
        module_path = library_path / (module_name + '.nim')
        dot_nimble = library_path / (module_name + '.nimble')

        if module_path.exists() and dot_nimble.exists():
            build_dir = Path(tempfile.mktemp())

            exe = 'nimble cc -c'.split()
            nim_args = (
                exe + cls.NIM_CLI_ARGS +
                [f'--nimcache:{build_dir}', f'{module_path}']
            )

            cwd = Path().cwd()
            os.chdir(library_path)
            output, errors, warnings, hints = cls.invoke_compiler(nim_args)
            os.chdir(cwd)

            for warn in warnings: print(warn)

            if errors: raise NimCompilerException(errors[0])

            csources = [str(c) for c in build_dir.iterdir() if c.suffix == '.c']

            # Copy over needed header(s)
            NIMBASE = 'nimbase.h'
            nimbase = cls.find_nim_std_lib() / NIMBASE
            shutil.copyfile(str(nimbase), str(build_dir / NIMBASE))

            # Coerce proper import path using root path
            import_prefix = cls.get_import_prefix(library_path.parent, root)
            import_path = '.'.join(import_prefix + (module_name,))

            return Extension(
                name=import_path,
                sources=csources,
                include_dirs=[str(build_dir)]
            )

        raise Exception(
            f'Error: {library_path} is not formatted properly. It did not '
            f'contain any of these top-level filenames: '
            f'{[i + ".nim" for i in useable_mod_names] + [dot_nimble.name]}'
        )

    @classmethod
    def __find_extensions(cls, path, exclude_dirs=[]):
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
                    cls.__find_extensions(item, exclude_dirs=exclude_dirs)
                )

            elif item.suffix == '.nim':
                "Treat item as a Nim Extension."
                nim_exts.append(item)

        return nim_exts

    @classmethod
    def build_nim_extension(cls, path, root):
        # It is known that this dir contains .nimble
        if path.is_dir():
            return cls.compile_extension_library(path, root)
            
        # This is for sure a Nim extension file
        else:
            return cls.compile_extension_module(path, root)

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

        for extension in cls.__find_extensions(root, exclude_dirs):
            ext = cls.build_nim_extension(extension, root)
            if ext: extensions.append(ext)

        return extensions

    @classmethod
    def try_compile(cls, module_path, build_artifact):
        """
        Compiles a given Nim module and returns the path to the built artifact.
        Raises an exception if compilation fails for any reason.
        """
        if not module_path.exists():
            raise Exception(f'{module_path.absolute()} does not exist.')

        build_artifact = Nimporter.build_artifact(module_path)

        exe = 'nim c'.split()
        nim_args = (
            exe + cls.NIM_CLI_ARGS +
            [f'--out:{build_artifact}', f'{module_path}']
        )

        output, errors, warnings, hints = cls.invoke_compiler(nim_args)

        for warn in warnings: print(warn)

        if errors: raise NimCompilerException(errors[0])

        return build_artifact
    
    @classmethod
    def try_compile_library(cls, library_path, build_artifact):
        """
        Compiles a given Nim library and returns the path to the built artifact.
        Raises an exception if compilation fails for any reason.
        """
        library_path = library_path.resolve()
        module_name = library_path.name
        module_path = library_path / (module_name + '.nim')
        dot_nimble = library_path / (module_name + '.nimble')

        if not module_path.exists() or not dot_nimble.exists():
            raise Exception(
                f"{library_path} doesn't contain a .nimble or {module_name}.nim"
            )

        build_artifact = Nimporter.build_artifact(module_path)

        exe = 'nimble c'.split()
        nim_args = (
            exe + cls.NIM_CLI_ARGS +
            [f'--out:{build_artifact}', f'{module_path}']
        )

        cwd = Path().cwd()
        os.chdir(library_path)
        output, errors, warnings, hints = cls.invoke_compiler(nim_args)
        os.chdir(cwd)

        for warn in warnings: print(warn)

        if errors: raise NimCompilerException(errors[0])

        return build_artifact

    @classmethod
    def find_nim_std_lib(cls):
        nimexe = Path(shutil.which('nim'))
        if not nimexe:
            return None
        result = nimexe.parent / '../lib'
        if not (result / 'system.nim').exists():
            result = nimexe.resolve().parent / '../lib'
            if not (result / 'system.nim').exists():
                return None
        return result.resolve()


class Nimporter:
    """
    Python module finder purpose-built to find Nim modules on the Python PATH,
    compile them, hide them within the __pycache__ directory with other compiled
    Python files, and then return it as a full Python module.
    This Nimporter can only import Nim modules with procedures exposed via the
    [Nimpy](https://github.com/yglukhov/nimpy) library acting as a bridge.
    """
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
        return cls.pycache_dir(module_path).exists()

    @classmethod
    def is_hashed(cls, module_path):
        """Return whether or not a given Nim file has already been hashed."""
        return cls.hash_filename(module_path).exists()

    @classmethod
    def is_built(cls, module_path):
        """Return whether or not a given Nim file has already been hashed."""
        return cls.build_artifact(module_path).exists()

    @classmethod
    def get_hash(cls, module_path):
        """Returns the bits of the hash for a given Nim module."""
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
        if not cls.is_hashed(module_path):
            return True
        return cls.get_hash(module_path) != cls.hash_file(module_path)

    @classmethod
    def hash_file(cls, module_path):
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
        with cls.hash_filename(module_path).open('wb') as file:
            file.write(cls.hash_file(module_path))

    @classmethod
    def build_artifact(cls, module_path):
        """
        Returns the Path to the built .PYD or .SO. Does not imply it has already
        been built.
        """
        return (
            cls.pycache_dir(module_path) / (module_path.stem + NimCompiler.EXT)
        )

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        """
        Finds a Nim module and compiles it if it has changed.

        If the Nim module imports other Nim source files and those files change,
        the Nimporter will not be able to detect them and will reuse the cached
        version.

        Args:
            fullname(str): the module to import. Can be 'foo' or 'foo.bar.baz'
            path(list): a list of paths to search first.
            target(str): the target of the import.

        Returns:
            A useable spec object that will be passed to Python during import to
            actually create a Python Module object from the spec.
        """
        print('⭐️', fullname, path, target)

        parts = fullname.split('.')
        module = parts.pop()
        module_file = f'{module}.nim'
        path = list(path) if path else []  # Ensure that path is always a list
        package = '/'.join(parts)
        search_paths = {
            Path(i)
            for i in (path + sys.path + ['.'])
            if Path(i).is_dir()
        }

        for search_path in search_paths:
            # NOTE(pebaz): Found an importable/compileable module
            spath = (search_path / package).resolve()
            module_path = list(spath.glob(module_file))

            if module_path:
                (module_path,) = module_path

                if not module_path.exists(): continue

                should_compile = any([
                    IGNORE_CACHE,
                    cls.hash_changed(module_path),
                    not cls.is_cache(module_path),
                    not cls.is_built(module_path)
                ])

                build_artifact = cls.build_artifact(module_path)

                if should_compile:
                    NimCompiler.try_compile(module_path, build_artifact)
                    cls.update_hash(module_path)
                    
                return util.spec_from_file_location(
                    fullname,
                    location=str(build_artifact.absolute())
                )

            else:
                module_file = module + '.nim'

                # if not any(spath.glob(module)): continue

                # module_path = list((spath / module).glob(module_file))
                # nimble_path = list((spath / module).glob('*.nimble'))
                
                # # TODO(pebaz): FOUND A LIBRARY! :D
                # if module_path and nimble_path:
                #     (module_path,) = module_path
                #     (nimble_path,) = nimble_path

                #     should_compile = any([
                #         IGNORE_CACHE,
                #         cls.hash_changed(module_path),
                #         not cls.is_cache(module_path),
                #         not cls.is_built(module_path)
                #     ])

                #     build_artifact = cls.build_artifact(module_path)

                #     if should_compile:
                #         NimCompiler.try_compile_library(
                #             module_path.parent, build_artifact
                #         )

                #         cls.update_hash(module_path)
                        
                #     return util.spec_from_file_location(
                #         fullname,
                #         location=str(build_artifact.absolute())
                #     )

    @classmethod
    def import_nim_module(cls, fullname, path:list=None, ignore_cache=False):
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
        spec = cls.find_spec(fullname, path)

        # NOTE(pebaz): Compile the module anyway if ignore_cache is set.
        if ignore_cache:
            nim_module = Path(spec.origin).parent.parent / (spec.name + '.nim')
            build_artifact = cls.build_artifact(module_path)
            NimCompiler.try_compile(nim_module, build_artifact)
            sys.path_importer_cache.clear()
            importlib.invalidate_caches()
            if spec.name in sys.modules:
                sys.modules.pop(spec.name)
            spec = cls.find_spec(fullname, path)

        if spec:
            return util.module_from_spec(spec)
        else:
            raise ImportError(f'No module named {fullname}')

    @classmethod
    def compile_nim_module(cls, fullname, path:list=None, cli_args:list=None):
        """
        Import a Nim module after compiling it using exact command line given in
        the cli_args variable.
        """



class NimLibImporter:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        print('!', fullname, path, target)

        parts = fullname.split('.')
        #module = parts.pop()
        #module_file = f'{module}.nim'
        path = list(path) if path else []  # Ensure that path is always a list
        package = '/'.join(parts)
        search_paths = {
            Path(i)
            for i in (path + sys.path + ['.'])
            if Path(i).is_dir()
        }

        for search_path in search_paths:
            spath = search_path / package

            if spath.exists():
                module = parts[-1] + '.nim'

                # NOTE(pebaz): Found a Nim extension library
                if not any(spath.glob('*.nimble')) and not any(spath.glob(module)):
                    continue

                module_path = spath / module

                should_compile = any([
                    IGNORE_CACHE,
                    Nimporter.hash_changed(module_path),
                    not Nimporter.is_cache(module_path),
                    not Nimporter.is_built(module_path)
                ])

                build_artifact = Nimporter.build_artifact(module_path)

                if should_compile:
                    NimCompiler.try_compile_library(
                        module_path.parent, build_artifact
                    )

                    Nimporter.update_hash(module_path)
                    
                return util.spec_from_file_location(
                    fullname,
                    location=str(build_artifact.absolute())
                )


'''
By putting the Nimpoter at the end of the list of module loaders, it ensures
that Nim code files are imported only if there is not a Python module of the
same name somewhere on the path.
'''
sys.meta_path.append(Nimporter())
sys.meta_path.insert(0, NimLibImporter())

# Ensure that Nim files won't be passed up because of other Importers.
sys.path_importer_cache.clear()
importlib.invalidate_caches()
