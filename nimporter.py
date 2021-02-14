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
        if sys.platform == 'win32' and 'external' in msg:
            self.message = msg

        else:
            nim_module, error_msg = msg.split('Error:')
            nim_module = nim_module.splitlines()[-1]
            mod, (line_col) = nim_module.split('(')
            nim_module = Path(mod)
            src_line, col = line_col.split(',')
            src_line = int(src_line)
            col = int(col.replace(')', ''))
            message = error_msg + '\n'

            with open(nim_module, 'r') as mod:
                line = 0
                for each_line in mod:
                    line += 1

                    if line == src_line:
                        message += f' -> {each_line}'

                    elif line > src_line + 2:
                        break

                    elif line > src_line - 3:
                        message += f' |  {each_line}'

            self.message = message.rstrip() + (
                f'\n\nAt {nim_module.absolute()} '
                f'{line}:{col}'
            )

    def __str__(self):
        "Return the string representation of the given compiler error."
        return self.message


class NimInvokeException(NimporterException):
    "Exception for when a given CLI command fails."

    def __init__(self, cwd, cmd_line, errors, out=''):
        self.cwd = Path(cwd).resolve()
        self.cmd_line = cmd_line
        self.errors = errors
        self.out = out

    def get_output(self):
        "Return the output (if any) of the CLI command that caused the error."
        return self.out

    def __str__(self):
        "Return the string representation of the error."
        cmd = self.cmd_line[0]
        message = f'Failed to run command: {cmd}\n\n'
        message += f'Current Directory:\n    {self.cwd}\n\n'
        message += f'Error Message:\n'
        message += '\n    '.join(self.errors) + '\n\n'
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
     - Compile Nim files to C and bundle them as an Extension for distribution.

    Attributes:
        EXT(str): the extension to use for the importable build artifact.
        NIM_CLI_ARGS(list): compiler switches common to all builds.
    """
    EXT = '.pyd' if sys.platform == 'win32' else '.so'
    NIM_CLI_ARGS = [
        '--opt:speed',
        '--parallelBuild:0',
        '--gc:refc',
        '--threads:on',
        '--app:lib',
        '-d:release',
        '-d:strip',
        '-d:lto',
        '-d:ssl'
    ] + (['--cc:vcc'] if 'MSC' in sys.version else [])
    EXT_DIR = 'nim-extensions'

    @classmethod
    def get_python_c_compiler_version(cls):
        """
        Gets the compiler name and version that was used to compile Python.

        Returns:
            A string containing the compiler version, such as:

            > Clang 11.0.0 (clang-1100.0.33.16)
        """
        return sys.version.split('[').pop()[:-1]

    @classmethod
    def get_python_c_compiler_name(cls):
        """
        Gets only the compiler name used to compile Python.

        Useful for determining which compiler to invoke on Win32 for example.

        Returns:
            A string containing the compiler name, such as:

            > Clang
        """
        return cls.get_python_c_compiler_version().split()[0].lower()

    @classmethod
    def get_installed_compilers(cls):
        """
        Gets the list of installed compilers.

        Returns:
            A dict mapping the compiler name with the path to it. Compilers that
            are not installed are not included in the dict.
        """
        compilers = {
            'msc'  : shutil.which('vccexe'),
            'clang' : shutil.which('clang'),
            'gcc'   : shutil.which('gcc')
        }

        return {
            compiler : Path(path)
            for compiler, path in compilers.items()
            if path
        }

    @classmethod
    def get_compatible_compiler(cls):
        """
        Gets compatible compiler name for the running Python instance.

        Returns:
            A string containing the name of the compiler to use when compiling
            Nim code.
        """
        python_compiler = cls.get_python_c_compiler_name()
        if python_compiler in cls.get_installed_compilers():
            return python_compiler

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
        """
        Return the `__pycache__` directory as a Path.

        Works the same as Python's `__pycache__` directory except now it works
        with Nim extensions also. It works literally exactly like Python.

        Args:
            module_path(Path): the path to a given Nim module or library.

        Returns:
            The Path to the `__pycache__` directory that the build artifact
            should be stored.
        """
        if module_path.is_dir():
            return (module_path / '__pycache__').resolve()
        else:
            return (module_path.parent / '__pycache__').resolve()

    @classmethod
    def invoke_compiler(cls, nim_args: list):
        """
        Invokes the compiler (or any executable) and returns the output.

        While this can (and has been) used to call executables other than Nim
        and Nimble, it should be noted that the warnings and hints are artifacts
        of being mainly targeted as a Nim compiler invoker.

        Args:
            nim_args(list): the arg being the executable and the rest are args.

        Returns:
            A tuple containing any errors, warnings, or hints from the
            compilation process.
        """
        process = subprocess.run(
            nim_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.stdout, process.stderr
        out = out.decode(errors='ignore') if out else ''
        err = err.decode(errors='ignore') if err else ''
        lines = (out + err).splitlines()

        errors   = [line for line in lines if 'Error:' in line]
        warnings = [line for line in lines if 'Warning:' in line]
        hints    = [line for line in lines if 'Hint:' in line]

        return out, errors, warnings, hints

    @classmethod
    def ensure_nimpy(cls):
        """
        Makes sure that the Nimpy Nim library is installed.

        Verifies that the [Nimpy Library](https://github.com/yglukhov/nimpy) is
        installed and installs it otherwise.

        NOTE: Nimporter would not be possible without Nimpy. Thank you
        Yuriy Glukhov for making this project possible!
        """
        out, errors, _, _ = cls.invoke_compiler('nimble path nimpy'.split())

        if not out or errors:
            nimble_args = 'nimble install nimpy --accept'.split()
            out, errors, _, _ = cls.invoke_compiler(nimble_args)

        if errors: raise NimInvokeException(Path(), nimble_args, errors, out)

    @staticmethod
    def get_import_prefix(module_path, root):
        """
        Computes the proper name of a Nim module amid a given Python project.

        This method is needed because Nim Extensions do not automatically know
        where they are within a given Python namespace. This method is vital for
        recursing through an entire Python project to find every Nim Extension
        module and library while preserving the namespace containing each one.

        Args:
            module_path(Path): the module for which to determine its namespace.
            root(Path): the path to the Python project containing the Extension.

        Returns:
            A tuple of packages containing the given module.
        """
        root_path = root.resolve()
        full_path = module_path.resolve()

        assert full_path >= root_path, 'Extension path is not within root dir.'

        return full_path.parts[len(root_path.parts):]

    @classmethod
    def find_nim_std_lib(cls):
        """
        Finds the path to the `lib/` directory within a given Nim installation.

        Has the ability to find Nim's stdlib on Windows, MacOS, and Linux. Can
        also find the stdlib when Nim was installed via Choosenim. Additionally,
        it can even find the stdlib of the currently selected toolchain when
        using Choosenim.

        Returns:
            The Path to the Nim stdlib 'lib' directory if it exists and None
            otherwise.
        """
        # If Nim is not installed there's nothing to be done
        nimexe = shutil.which('nim')
        if not nimexe:
            return None

        # Installed via choosenim_install Pypi package
        choosenim_dir = Path('~/.choosenim/toolchains').expanduser().absolute()
        if choosenim_dir.exists:
            try:
                nim_ver = (subprocess.check_output(['nim', '-v'])
                    .decode(errors='ignore')
                    .splitlines()[0]
                )

                version_string = nim_ver.split()[3]
                stdlib = choosenim_dir / f'nim-{version_string}/lib'

                if (stdlib / 'system.nim').exists():
                    return stdlib.resolve().absolute()
            except:
                "Keep trying other methods"

        # Installed via ChooseNim
        if shutil.which('choosenim'):
            o, _, _, _ = cls.invoke_compiler(
                'choosenim show -y --nocolor'.split()
            )
            (choosenim,) = [i for i in o.splitlines() if 'Path:' in i]
            toolchain = Path(choosenim.split('Path:').pop().strip())
            stdlib = toolchain / 'lib'

            if (stdlib / 'system.nim').exists():
                return stdlib.resolve().absolute()

        # Installed manually
        nimexe = Path(nimexe)
        result = nimexe.parent / '../lib'
        if not (result / 'system.nim').exists():
            result = nimexe.resolve().parent / '../lib'

            if not (result / 'system.nim').exists():
                return None

        return result.resolve().absolute()

    @classmethod
    def get_switches(cls, switch_file, **global_scope):
        """
        Convenience function to return the switches from a given switchfile.

        Works by exposing a global scope to the switch file and then evaluating
        it. The resulting variable: `__switches__` should have been defined
        within the script which should contain the keys: "import" and "bundle".

        The "import" key should be a list of CLI args that should be passed to
        the Nim compiler when importing the given Nim library.

        The "bundle" key should be a list of CLI args that should be passed to
        the Nim compiler when creating an Extension object from the C sources.

        When evaluated, the switchfile can make use of a few global variables
        that allow it to make certain decisions regarding the outcome of the
        compilation:

         * **MODULE_PATH**: the path to the actual Nim source file to compile
         * **BUILD_ARTIFACT**: can be used when building a module
         * **BUILD_DIR**: can be used when building a library
         * **IS_LIBRARY**: used to determine if a library/module is being built.

        The reason for the switchfile being a Python script is that different
        platforms will require different compilation switches. The switchfile
        author can make use of `sys.platform` to query platform information.

        Returns:
            A dictionary containing the keys: "import" and "bundle", signifying
            the CLI arguments used when importing and building an extension
            module respectively.
        """
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
        library has (can have) dependencies specified in a Nimble file.

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

        # Coerce proper import path using root path
        import_prefix = cls.get_import_prefix(module_path.parent, root)
        module_part = tuple() if library else (module_name,)
        import_path = '.'.join(import_prefix + module_part)

        # Record results of build so it can be copied into source archive
        extension_dir = root / cls.EXT_DIR
        extension_dir.mkdir(parents=True, exist_ok=True)
        build_dir = extension_dir.absolute() / import_path
        build_dir.mkdir(exist_ok=True)
        build_dir_relative = extension_dir / import_path

        # Switches file found
        switch_file = library_path / 'switches.py'
        if switch_file.exists():
            switches = cls.get_switches(
                switch_file,
                MODULE_PATH=module_path,
                BUILD_DIR=build_dir,
                # Necessary for import/bundle compatibility
                BUILD_ARTIFACT=None,
                IS_LIBRARY=library
            )
            nim_args = switches['bundle']

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
                raise NimInvokeException(tmp_cwd, nim_args, errors, output)
            else:
                raise NimCompileException(errors[0])

        for warn in warnings: print(warn)

        csources = [
            str(c) for c in build_dir_relative.iterdir() if c.suffix == '.c'
        ]

        # Copy over needed header(s)
        NIMBASE = 'nimbase.h'
        nimbase = cls.find_nim_std_lib() / NIMBASE
        nimbase_dest = build_dir_relative / NIMBASE
        shutil.copyfile(nimbase, nimbase_dest)
        assert nimbase_dest.exists()

        # Properly handle bundling headers into the source distribution
        manifest = root / 'MANIFEST.in'
        if not manifest.exists():
            manifest.write_text('# NIMPORTER BUNDLE\n')

        with manifest.open('a') as file:
            file.write(f'include {nimbase_dest}\n')

        return Extension(
            name=import_path,
            sources=csources,
            include_dirs=[str(build_dir_relative)]
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
        library has (can have) dependencies specified in a Nimble file.
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
                raise NimInvokeException(tmp_cwd, nim_args, errors, output)
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
        """
        Gets the filename that should contain a given module's hash.

        Args:
            module_path(Path): the Nim module the hash file pertains to.

        Returns:
            The hash filename as a Path.
        """
        return (
            NimCompiler.pycache_dir(module_path) / (module_path.name + '.hash')
        )

    @classmethod
    def is_cache(cls, module_path):
        """
        Determines if the `__pycache__` dir for a given Nim module exists.

        Args:
            module_path(Path): the Nim module the `__pycache__` dir pertains to.

        Returns:
            A bool indicating whether or not a __pycache__ directory exists to
            store hashes and build artifacts.
        """
        return NimCompiler.pycache_dir(module_path).exists()

    @classmethod
    def is_hashed(cls, module_path):
        """
        Determines if a given Nim module has already been hashed.

        Args:
            module_path(Path): the Nim module for which to query hash existence.

        Returns:
            A bool indicating whether or not a given Nim file has already been
            hashed.
        """
        return cls.hash_filename(module_path).exists()

    @classmethod
    def is_built(cls, module_path):
        """
        Determines if a given Nim module has already been built.

        Args:
            module_path(Path): the Nim module for which to query for artifacts.

        Returns:
            A bool indicating whether or not a given Nim file has already been
            built.
        """
        return NimCompiler.build_artifact(module_path).exists()

    @classmethod
    def get_hash(cls, module_path):
        """
        Gathers the hash for a given Nim module.

        Args:
            module_path(Path): the Nim module for which to return its hash.

        Raises:
            NimporterException: if the module has not yet been hashed.

        Returns:
            The bytes of the hash for a given Nim module.
        """
        if not cls.is_hashed(module_path):
            path = module_path.absolute()
            raise NimporterException(f'Module {path} has not yet been hashed.')
        return cls.hash_filename(module_path).read_bytes()

    @classmethod
    def hash_changed(cls, module_path):
        """
        Determines if a module has been modified.

        Args:
            module_path(Path): the Nim module to check for modification.

        Returns:
            A bool indicating whether or not a given Nim file has changed since
            last hash. If the module has not yet been hashed, returns True.
        """
        if not cls.is_hashed(module_path):
            return True
        return cls.get_hash(module_path) != cls.hash_file(module_path)

    @staticmethod
    def hash_file(module_path):
        """
        Convenience function to hash a given file.

        Args:
            module_path(Path): the file to hash.

        Returns:
            The hash bytes of the Nim file.
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
        Updates the hash file associated with a given Nim module.

        This is commonly done after compilation to determine if recompilation is
        required upon subsequent imports. If the module's hash file has not yet
        been created, this method will create it and store it in the
        `__pycache__` dir for the module.

        Args:
            module_path(Path): the module which should have its hash updated.
        """
        hash_file = cls.hash_filename(module_path)
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        with hash_file.open('wb') as file:
            file.write(cls.hash_file(module_path))

    @classmethod
    def import_nim_module(cls, fullname, path:list=None, ignore_cache=None):
        """
        Convenience function to manually import a given Nim module or library.

        Can be used to explicitly import a module rather than using the `import`
        keyword. Allows the cache to be ignored to solve issues arising from
        caching one module when 10 other imported Nim libraries have changed.

        Example Use:

            # Rather than:
            import foo
            # You can say:
            foo = Nimporter.import_nim_module('foo', ['/some/random/dir'])

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
        """
        Search for, compile, and return Spec for module loaders.

        Used by both NimModImporter and NimLibImporter for their Spec-finding
        capabilities.

        Args:
            fullname(str): the name given when importing the module in Python.
            path(list): additional search paths.
            library(bool): indicates whether or not to compile as a library.

        Returns:
            A Spec object that can be used to import the (now compiled) Nim
            module or library.
        """
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

            spec = util.spec_from_file_location(
                fullname,
                location=str(build_artifact.absolute())
            )

            cls.__validate_spec(spec)

            return spec

    @classmethod
    def __validate_spec(cls, spec):
        """
        Validates that a given Nim extension can be successfully imported.

        Since a spec is used to import a module and the body of this function
        attempts an import, successful imports will imply importing the module
        twice. However, it's ok that the module will be imported twice because
        it's better to have good error messages than to be fast in this case.

        Args:
            spec(Spec): the spec to validate if its module can be imported.

        Raises:
            A NimporterException if the spec cannot be used to import the given
            Nim module/library.
        """
        try:
            util.module_from_spec(spec)

        except ImportError as import_error:
            py_ver = sys.version.replace('\n', '')

            try:
                nim_ver = (subprocess.check_output(['nim', '-v'])
                    .decode(errors='ignore')
                    .splitlines()[0]
                )
            except:
                nim_ver = '<Error getting version>'

            all_ccs = NimCompiler.get_installed_compilers()
            py_cc = NimCompiler.get_compatible_compiler()
            if py_cc:
                cc = all_ccs[py_cc]
                try:
                    if py_cc == 'msc':
                        cc_ver = subprocess.check_output([
                            'vccexe',
                            '--vccversion:0',
                            '--printPath',
                            '--noCommand'
                        ]).decode(errors='ignore').strip()
                    else:
                        cc_ver = (subprocess.check_output([cc.stem])
                            .decode(errors='ignore')
                        )
                except:
                    cc_ver = '<Error getting version>'
            else:
                cc_ver = '<No compatible C compiler installed>'

            error_message = (
                f'Error importing {spec.origin}\n'
                f'Error Message:\n\n    {import_error}\n\n'
                f'Python Version:\n\n    {py_ver}\n\n'
                f'Nim Version:\n\n    {nim_ver}\n\n'
                f'CC Version:\n\n    {cc_ver}\n\n'
                f'Installed CCs:\n\n    {all_ccs}\n\n'
                f'Please help improve Nimporter by opening a bug report at: '
                f'https://github.com/Pebaz/nimporter/issues/new and submit the '
                f'above information along with your description of the issue.\n'
            )

            raise NimporterException(error_message) from import_error

    @classmethod
    def should_compile(cls, module_path):
        """
        Determines if a module should be rebuilt using only the path to it.

        Factors included in the decision to compile a module include:

         * If `IGNORE_CACHE` is set
         * If the module has been modified since the last build
         * If the `__pycache__` directory does not exist
         * If there is no cached build artifact available in `__pycache__`

        Args:
            module_path(Path): the Nim module to potentially (re)compile.

        Returns:
            A bool indicating whether or not the module should be (re)built.
        """
        return any([
            cls.IGNORE_CACHE,
            cls.hash_changed(module_path),
            not cls.is_cache(module_path),
            not cls.is_built(module_path)
        ])

    @classmethod
    def _find_extensions(cls, path, exclude_dirs=set()):
        """
        Recurses through a given path to find all Nim modules or libraries.

        Args:
            path(Path): the path to begin recursing.
            exclude_dirs(list): the list of Paths to skip while searching.

        Returns:
            A list of Path objects. File Paths indicate a Nim Module. Folder
            Paths indicate Nim Libraries.
        """
        exclude_dirs = {Path(p).expanduser().absolute() for p in exclude_dirs}
        nim_exts = []

        for item in path.iterdir():
            absolute = item.expanduser().absolute()

            if absolute in exclude_dirs:
                continue

            elif any(str(absolute).startswith(str(p)) for p in exclude_dirs):
                continue

            if item.is_dir() and list(item.glob('*.nimble')):
                # Treat directory as one single Extension
                (nimble_file,) = item.glob('*.nimble')
                nim_file = nimble_file.parent / (nimble_file.stem + '.nim')

                # NOTE(pebaz): Folder must contain Nim file of exact same name.
                if nim_file.exists():
                    nim_exts.append(item)

            elif item.is_dir():
                # Treat item as directory
                nim_exts.extend(
                    cls._find_extensions(item, exclude_dirs=exclude_dirs)
                )

            elif item.suffix == '.nim':
                # Treat item as a Nim Extension.
                nim_exts.append(item)

        return nim_exts

    @classmethod
    def _build_nim_extension(cls, path, root):
        """
        Convenience function to create an Extension object from a given path.

        Args:
            path(Path): the path to the Nim module/library.
            root(tuple): the namespace to add the Extension to.

        Returns:
            An Extension object representing the Nim module or library that has
            successfully be compiled to C.
        """
        return NimCompiler.compile_nim_extension(
            path, root, library=path.is_dir()
        )

    @classmethod
    def check_nim_extensions(cls, root):
        """
        if not cls.check_nim_extensions(root):
            ...
        else:
            extensions = cls.get_nim_extensions(root)
        """
        return (root / NimCompiler.EXT_DIR).exists()

    @classmethod
    def get_nim_extensions(cls, root):
        """
        Convenience function to look for previously compiled Nim Extensions.

        When extensions are created, they are stored in the
        `<root>/build/nim-extensions` directory. The reason this is necessary is
        because `setup.py` runs the `setup()` function twice: once to gather
        info and once to actually compile/bundle everything. On the first pass,
        the extensions are compiled to C. On the second pass, they are compiled
        to Python-compatible shared objects.

        Args:
            root(Path): the root of the project.

        Returns:
            A list of Extensions that were compiled on the library maintainer's
            computer.
        """
        extension_dir = root / NimCompiler.EXT_DIR
        assert extension_dir.exists()

        # NOTE(pebaz): The include dir and C source file paths absolutely must
        # be relative paths or installing with Pip will not work on Windows.
        return [
            Extension(
                name=extension.name,
                sources=[str(c) for c in extension.glob('*.c')],
                include_dirs=[str(extension)]
            )
            for extension in extension_dir.iterdir()
        ]

    @classmethod
    def build_nim_extensions(cls, root=None, exclude_dirs=[], danger=False):
        """
        Gathers all Nim Extensions by recursing through a Python project.

        Compiles Nim modules and libraries to C and creates Extensions from them
        for source, binary, or wheel distribution.

        Automatically recurses through the project directory to find all the Nim
        modules and Nim libraries.

        NOTE: Since this method is the only method that should be used by
        consumers of the Nimporter API, it has to do a couple of things:

        1. Build all Nim modules and libraries into C Extensions.
        2. Compile all C Extensions with a C compiler on an end-user's machine.

        Case 1 happens when creating a source or binary distribution. Also, this
        can happen if installing via: `python setup.py install` after cloning
        from Git.

        Case 2 happens after the C files have been put into the source archive
        and shipped to the end user. When the end user runs the `setup()`
        function, the already-bundled C files need to be compiled as Extensions
        rather than trying to look for Nim files that have not been bundled.

        Although this is a complicated process, it can be illustrated here:

        * `python setup.py install`: Case 1 + 2
        * `pip install some-lib`: Case 2
        * `pip install git+https://github.com/some-lib`: Case 1 + 2

        Args:
            root(tuple): the namespace to add all extensions to.
            exclude_dirs(list): the Paths to skip while recursing the project.

        Returns:
            A list of Extensions that can be added to the setup() function's
            "ext_modules" keyword argument.
        """
        if danger: NimCompiler.NIM_CLI_ARGS.insert(3, '-d:danger')

        #root = (root or Path()).expanduser().absolute()
        root = root or Path()

        # Check for bundled C source files
        if cls.check_nim_extensions(root):

            if danger: NimCompiler.NIM_CLI_ARGS.pop(3)

            # NOTE(pebaz): Run only on end-user's machine.
            return cls.get_nim_extensions(root)

        extensions = []

        # Create extensions from the Nim files found within the project
        for extension in cls._find_extensions(root, exclude_dirs):

            # NOTE(pebaz): Run on author's machine or when building from source
            ext = cls._build_nim_extension(extension, root)
            if ext: extensions.append(ext)

        if danger: NimCompiler.NIM_CLI_ARGS.pop(3)

        return extensions


def register_importer(list_position):
    """
    Adds a given importer class to `sys.meta_path` at a given position.

    NOTE: The position in `sys.meta_path` is extremely relevant.

    Args:
        list_position(int): the index in `sys.meta_path` to place the importer.
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
