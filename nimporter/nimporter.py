"""
Registers 2 different import functions that allows the importer of this module
to directly import Nim extension modules & libraries.

Once imported, the importers will be cached in sys.meta_path so any Python
module can then directly import Nim extensions also. Technically, it's only
necessary to import Nimporter in the main Python file of a program or in the
root `__init__.py` of a library.
"""

import sys
import os
import shutil
import hashlib
from pathlib import Path
from setuptools.extension import Extension
from typing import *
from types import SimpleNamespace
from icecream import ic
from nimporter.lib import *

# NOTE(pbz): https://stackoverflow.com/questions/39660934/error-when-using-importlib-util-to-check-for-library/39661116
import importlib
from importlib import util
from _frozen_importlib import ModuleSpec
from _frozen_importlib_external import _NamespacePath


PYTHON_LIB_EXT = '.pyd' if sys.platform == 'win32' else '.so'


def compile_extensions_to_lib(root: Path) -> None:
    "Compile all extensions starting at a given path."

    for extension_path in ic(find_extensions(ic(root))):
        if not should_compile(extension_path):
            ic('Skipping', extension_path)
            continue

        compile_extension_to_lib(extension_path)



def compile_extension_to_lib(extension_path: Path) -> None:
    ensure_nimpy()

    pycache = extension_path.parent / '__pycache__'
    pycache.mkdir(parents=True, exist_ok=True)

    ic('Compiling', extension_path)

    with convert_to_lib_if_needed(extension_path) as compilation_dir:
        nim_module = compilation_dir / (extension_path.stem + '.nim')

        ic(nim_module)

        with cd(compilation_dir) as tmp_cwd:
            cli_args = ic(ALWAYS_ARGS + [nim_module.name])

            ic(cli_args)

            code, _, stderr = run_process(
                cli_args,
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            if code:
                raise CompilationFailedException(stderr)

        find_ext = '.dll' if sys.platform == 'win32' else '.so'

        # The only way the artifact wouldn't exist is if Nim failed to
        # compile the library but didn't write to the standard error stream
        # which is currently not how the Nim compiler behaves.
        # This shouldn't fail.
        build_artifact, = tmp_cwd.glob(f'*{find_ext}')

        final_artifact = pycache / (nim_module.stem + PYTHON_LIB_EXT)
        shutil.move(build_artifact, final_artifact)

        update_hash(extension_path)


def build_artifact(module_path: Path) -> Path:
    """
    Returns the Path to the built .PYD or .SO.

    Does not imply that it has already been built.

    Args:
        module_path(Path): the path to the module or library.

    Returns:
        The path to a build artifact if compilation were to succeed. If the
        module_path is a directory, an appropriate build artifact path
        within that directory is returned.
    """
    filename = module_path.stem + PYTHON_LIB_EXT
    return (pycache_dir(module_path) / filename)


def pycache_dir(module_path: Path) -> Path:
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
    return (module_path.parent / '__pycache__')


def hash_filename(module_path: Path) -> Path:
    """
    Gets the filename that should contain a given module's hash.

    Args:
        module_path(Path): the Nim module the hash file pertains to.

    Returns:
        The hash filename as a Path.
    """
    return pycache_dir(module_path) / (module_path.stem + '.hash')


def is_cache(module_path: Path) -> bool:
    """
    Determines if the `__pycache__` dir for a given Nim module exists.

    Args:
        module_path(Path): the Nim module the `__pycache__` dir pertains to.

    Returns:
        A bool indicating whether or not a __pycache__ directory exists to
        store hashes and build artifacts.
    """
    return pycache_dir(module_path).exists()


def is_hashed(module_path: Path) -> bool:
    """
    Determines if a given Nim module has already been hashed.

    Args:
        module_path(Path): the Nim module for which to query hash existence.

    Returns:
        A bool indicating whether or not a given Nim file has already been
        hashed.
    """
    return hash_filename(module_path).exists()


def is_built(module_path: Path) -> bool:
    """
    Determines if a given Nim module has already been built.

    Args:
        module_path(Path): the Nim module for which to query for artifacts.

    Returns:
        A bool indicating whether or not a given Nim file has already been
        built.
    """
    return build_artifact(module_path).exists()


def get_hash(module_path: Path) -> bytes:
    """
    Gathers the hash for a given Nim module.

    Args:
        module_path(Path): the Nim module for which to return its hash.

    Raises:
        NimporterException: if the module has not yet been hashed.

    Returns:
        The bytes of the hash for a given Nim module.
    """
    if not is_hashed(module_path):
        path = module_path.absolute()
        raise NimporterException(f'Module {path} has not yet been hashed.')

    return hash_filename(module_path).read_bytes()


def hash_changed(module_path: Path) -> bool:
    """
    Determines if a module has been modified.

    Args:
        module_path(Path): the Nim module to check for modification.

    Returns:
        A bool indicating whether or not a given Nim file has changed since
        last hash. If the module has not yet been hashed, returns True.
    """
    if not is_hashed(module_path):
        return True

    return get_hash(module_path) != hash_extension(module_path)


def hash_extension(module_path: Path) -> bytes:
    """
    Convenience function to hash an extension module or extension library.

    Args:
        module_path(Path): the file to hash.

    Returns:
        The hash bytes of the Nim file.
    """
    digest = hashlib.sha256()

    if module_path.is_file():
        block_size = 65536

        with module_path.open('rb') as file:
            buf = file.read(block_size)

            while len(buf) > 0:
                digest.update(buf)
                buf = file.read(block_size)

    else:
        def walk_folder(path):
            for item in path.iterdir():
                if item.is_dir():
                    for i in walk_folder(item):
                        yield i
                else:
                    yield item

        for item in walk_folder(module_path):
            digest.update(str(item).encode())
            digest.update(item.read_bytes())

    ic(digest.hexdigest())

    return digest.digest()


def update_hash(module_path: Path) -> None:
    """
    Updates the hash file associated with a given Nim module.

    This is commonly done after compilation to determine if recompilation is
    required upon subsequent imports. If the module's hash file has not yet
    been created, this method will create it and store it in the
    `__pycache__` dir for the module.

    Args:
        module_path(Path): the module which should have its hash updated.
    """
    hash_file = hash_filename(module_path)
    hash_file.parent.mkdir(parents=True, exist_ok=True)

    with hash_file.open('wb') as file:
        file.write(hash_extension(module_path))


def should_compile(module_path: Path) -> bool:
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
        hash_changed(module_path),
        not is_cache(module_path),
        not is_built(module_path)
    ])


def validate_spec(spec: ModuleSpec) -> None:
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
    except ImportError:
        msg = '''
        Failed to import Nim extension after successful compilation.

        This can be for a variety of reasons.

        First, ensure that {.exportpy.} is used for each function in the Nim
        extension according to how Nimpy is designed to be used:
            https://github.com/yglukhov/nimpy

        Second, make sure that the compiler used to compile the extension is the
        same one used to compile Python. For instance, using Clang to compile a
        Nim extension and importing it with an MSVC version of Python is not
        supported. The reason is because of binary incompatibilities. Since
        Nimporter was designed to bridge the Nim and Python communities, some
        concessions had to be made and this comes along with limitations.
        Although it might be technically possible to use Clang + MSVC binaries
        together, it is unreliable and therefore not supported by Nimporter.

        Third, make sure that the desired Nim extension binary was placed in
        the appropriate __pycache__ directory which can be found in:
            <folder containing the Nim extension>/__pycache__

        Fourth, rerun the compilation with this defined in the environment:
            NIMPORTER_INSTRUMENT
        This will show all the output from the Nim compilation. Just make sure
        it's not importing the cached build by either deleting the __pycache__/
        directory or running `nimporter clean`.

        Finally, if all else fails, please submit a bug report here with as
        many details as you possibly can (C compiler version, Python version,
        OS, Nim output, etc.):
            https://github.com/Pebaz/nimporter/issues/new
        '''
        raise ImportFailedException(msg)


def nimport(
    fullname: str,
    path: Optional[Union[List[str], _NamespacePath]],
    *,
    library: bool
) -> Optional[ModuleSpec]:
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

    # NOTE(pbz): Package is different based only on `library`
    package = '/'.join(parts)

    search_paths = {
        Path(i)
        for i in (path + sys.path + ['.'])
        if Path(i).is_dir()
    }

    for the_search_path in search_paths:
        search_path = (the_search_path / package)

        # Can't be a library without <libname>.nimble
        if library and not any(search_path.glob(f'{module}.nimble')):
            continue

        # Derive module path regardless of library or module
        module_path = search_path / module_file

        if not module_path.exists():
            continue

        ic(module_path)

        if library:
            dir_containing_lib_or_mod = module_path.parent.parent
        else:
            dir_containing_lib_or_mod = module_path.parent

        ic(dir_containing_lib_or_mod)

        # compile_extensions_to_lib(
        #     # * Had to prove the file existed using absolute paths. Now,
        #     # * convert it back to a relative path to not have the MANIFEST
        #     # * of the distribution contain the user's file system details.
        #     # * In addition, library hashing won't work with absolute
        #     # * paths.
        #     dir_containing_lib_or_mod.relative_to(the_search_path)
        # )

        # TODO(pbz): Caching isn't working with this

        # TODO(pbz): MAKE FORMAL SCRIPT TO TEST THIS WITHOUT PYTEST HARNESS

        compile_extension_to_lib(
            # * Had to prove the file existed using absolute paths. Now,
            # * convert it back to a relative path to not have the MANIFEST
            # * of the distribution contain the user's file system details.
            # * In addition, library hashing won't work with absolute
            # * paths.
            # dir_containing_lib_or_mod.relative_to(the_search_path)
            module_path
        )

        # Artifact has either already been built or was just built
        canonical_module_path = module_path.parent if library else module_path

        spec = util.spec_from_file_location(
            fullname,
            location=str(build_artifact(canonical_module_path).absolute())
        )

        ic(spec)

        validate_spec(spec)

        return spec


def register_importer(list_position: int, importer: Callable) -> None:
    "Convenience function to insert importers into Python's import machinery."
    sys.meta_path.insert(list_position, SimpleNamespace(find_spec=importer))

    # Ensure that Nim files won't be passed up because of other Importers.
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()


"""
Extends Python import machinery to be able to import Nim modules.

NOTE: Must be placed at the back of `sys.meta_path` because Python modules
should be given precedence over Nim modules.

Nim Modules can be placed anywhere that Python modules can. However, if a
Python module and a Nim module with the same name are in the same package, the
Python module will be imported.
"""
register_importer(
    -1,
    lambda fullname, path, _: nimport(fullname, path, library=False)
)


"""
Extends Python import machinery to be able to import Nim libraries.

NOTE: Must be placed at the front of `sys.meta_path` because of how Python
treats folders when imported.

Before NimLibImporter can attempt to find a folder containing a Nimble file
containing dependency info and a corresponding Nim module, Python's import
machinery imports the folder as a namespace module type.

The only way to allow NimLibImporter to get a chance to import Nim libraries is
to put it at the front of `sys.meta_path`. However, this has a small side
effect of making Nim libraries have precedence over Python namespaces. This
should never have any adverse effects since the criterion for a Nim library in
relation to Nimporter is to have a folder containing a Nim module and a Nimble
file with the same name as the folder. By placing both of those files into a
directory, it should be extremely clear that the given folder is a Nim library.
Additionally, this also means that a Nim library cannot contain any Python
modules.
"""
register_importer(
    0,
    lambda fullname, path, _: nimport(fullname, path, library=True)
)
