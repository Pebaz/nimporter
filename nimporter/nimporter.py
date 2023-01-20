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


def compile_extensions_to_lib(root: Path) -> None:
    "Compile all extensions starting at a given path."

    for extension_path in ic(find_extensions(ic(root))):
        if not should_compile(extension_path):
            ic('Skipping', extension_path)
            continue

        compile_extension_to_lib(extension_path)
    return


def write_hash(ext: ExtLib) -> None:
    ext.hash_filename.parent.mkdir(parents=True, exist_ok=True)
    ext.hash_filename.write_bytes(hash_extension(ext.relative_path))
    return


def hash_changed(ext: ExtLib) -> bool:
    if not ext.hash_filename.exists():
        return True

    return hash_extension(ext.relative_path) != ext.hash_filename.read_bytes()


def should_compile(ext: ExtLib) -> bool:
    return hash_changed(ext) or not ext.build_artifact.exists()


def compile_extension_to_lib(ext: ExtLib) -> None:
    if not should_compile(ext):
        ic('Skipping', ext.full_path)
        return

    ic('Compiling', ext.full_path)

    ensure_nimpy()

    ext.pycache.mkdir(parents=True, exist_ok=True)

    with convert_to_lib_if_needed(ext.full_path) as compilation_dir:
        nim_module = compilation_dir / (ext.symbol + '.nim')
        ic(nim_module)

        with cd(compilation_dir) as tmp_cwd:
            cli_args = ALWAYS_ARGS + [
                # ! Nimporter decides the use of the C compiler that was used
                # ! to build Python itself to prevent incompatibilities. This
                # ! is similar to exporting where several C compilers are used.
                f'--cc:{get_c_compiler_used_to_build_python()}',
                nim_module.name
            ]

            ic(cli_args)

            code, _, stderr = run_process(
                cli_args,
                'NIMPORTER_INSTRUMENT' in os.environ
            )

            if code:
                raise CompilationFailedException(stderr)

            # Remove Windows debugging symbols if using MSVC on Win32
            for debug_ext in ['.exp', '.lib']:
                debug_file = compilation_dir / (ext.symbol + debug_ext)
                if debug_file.exists():
                    ic(debug_file).unlink()

        platform = get_host_info()[0]
        find_ext = {WINDOWS: '.dll', MACOS: '.dylib', LINUX: '.so'}[platform]

        # The only way the artifact wouldn't exist is if Nim failed to
        # compile the library but didn't write to the standard error stream
        # which is currently not how the Nim compiler behaves.
        # This shouldn't fail.
        (tmp_build_artifact,) = tmp_cwd.glob(f'*{find_ext}')

        shutil.move(tmp_build_artifact, ext.build_artifact)

        write_hash(ext)
    return


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

        Second, make sure that the compiler used to compile the extension is
        the same one used to compile Python. For instance, using Clang to
        compile a Nim extension and importing it with an MSVC version of Python
        is not supported. The reason is because of binary incompatibilities.
        Since Nimporter was designed to bridge the Nim and Python communities,
        some concessions had to be made and this comes along with limitations.
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
    return


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

        ext = ExtLib(module_path, Path(), library)
        ic(ext)

        compile_extension_to_lib(ext)

        spec = util.spec_from_file_location(
            fullname,
            location=str(ext.build_artifact.resolve().absolute())
        )

        ic(spec)
        ic(ext.__dict__)

        validate_spec(spec)

        return spec
    return # type: ignore[return-value]


def register_importer(list_position: int, importer: Callable) -> None: # type: ignore[type-arg]
    "Convenience function to insert importers into Python's import machinery."
    sys.meta_path.insert(list_position, SimpleNamespace(find_spec=importer))

    # Ensure that Nim files won't be passed up because of other Importers.
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()
    return


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
