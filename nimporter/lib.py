import os
import sys
import shlex
import shutil
import tempfile
import platform
import subprocess
import cpuinfo
from typing import *
from pathlib import Path
from contextlib import contextmanager
from icecream import ic

PathParts = Union[Tuple[str, str, str], Tuple[str], Tuple[str, str]]

WINDOWS = 'windows'
MACOS = 'macos'
LINUX = 'linux'

EXT_DIR = 'nim-extensions'

PLATFORM_TABLE = {  # Keys are known to Python and values are Nim-understood
    'windows': 'Windows',
    'macos': 'MacOSX',
    'linux': 'Linux',
}

ARCH_TABLE = {  # Keys are known to Python and values are Nim-understood
    'x86_32': 'i386',
    'x86_64': 'amd64',

    # ? Are these needed
    # 'arm_8': 'arm64',
    # 'arm_7': 'arm',
    # 'ppc_32': 'powerpc',
    # 'ppc_64': 'powerpc64',
    # 'sparc_32': 'sparc',
    # 'sparc_64': 'sparc64',
    # 'mips_32': 'mips',
    # 'mips_64': 'mips64',
    # 'riscv_32': 'riscv32',
    # 'riscv_64': 'riscv64',
}

ALWAYS_ARGS = [
    'nimble',  # Installs dependencies :)
    'c',
    '--skipParentCfg',  # Included because it won't be portable otherwise
    '--skipUserCfg',
    '--app:lib',
    '--backend:c',
    '--warning[ProveInit]:off',  # https://github.com/Pebaz/nimporter/issues/41
]

DEFAULT_CLI_ARGS = [
    '--opt:speed',
    '--parallelBuild:0',
    '--gc:refc',
    '--threads:on',
    '-d:release',
    '-d:strip',
    '-d:ssl',
# ? Can I take this out and it will use VCC by default?
] + (['--cc:vcc'] if 'MSC' in sys.version else [])


def invoke_nim_compiler(switches: List[str]):
    pass

def compile_ext_lib(root: Path, compile_only: bool) -> None:
    pass

def find_extensions(path: Path) -> List[Path]:
    nim_exts = []

    for item in path.iterdir():
        if item.is_dir() and list(item.glob('*.nimble')):
            # Treat directory as one single Extension
            (nimble_file,) = item.glob('*.nimble')

            # NOTE(pbz): Folder must contain .nimble file of exact same name
            nim_file = nimble_file.parent / (nimble_file.stem + '.nim')

            # NOTE(pbz): Folder must contain Nim file of exact same name.
            if nim_file.exists():
                nim_exts.append(item)

        elif item.is_dir():
            # Treat item as directory
            nim_exts.extend(find_extensions(item))

        elif item.suffix == '.nim':
            # Treat item as a Nim Extension.
            nim_exts.append(item)

    return nim_exts


def get_import_prefix(module_path: Path, root: Path) -> PathParts:
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

    return ic(full_path.parts[len(root_path.parts):])


def get_import_path(path: Path, root: Path):
    """
    Coerce proper import path using root path

    Args:
        library(bool): hint as to how to treat the `module_path` parameter.
        module_name(str): name of nim module.
        module_path(Path): path to nim module.
        root(Path): path to project root.

    Returns:
        str: Returns the path of the nim module.
    """
    library = path.is_dir()
    module_name = path.stem
    module_path = path if path.is_file() else path / path.stem
    import_prefix = get_import_prefix(module_path.parent, root)
    module_part = tuple() if library else (module_name,)
    import_path = '.'.join(import_prefix + module_part)

    return ic(import_path)


@contextmanager
def convert_to_lib_if_needed(path: Union[Path, str]) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as compilation_dir:
        if path.is_file():
            shutil.copy(path, compilation_dir)

            nimble = Path(compilation_dir) / path.with_suffix('.nimble').name
            nimble.write_text('requires "nimpy"\n')

            try:
                yield Path(compilation_dir)
            except:
                raise
            finally:
                nimble.unlink()
        else:
            yield path


def run_process(
    process_args: List[str],
    show_output: bool = False
) -> Tuple[int, str, str]:
    """
    Invokes the compiler (or any executable) and returns the output.

    While this can (and has been) used to call executables other than Nim
    and Nimble, it should be noted that the warnings and hints are artifacts
    of being mainly targeted as a Nim compiler invoker.

    Args:
        process_args(list): the arg being the executable and the rest are args.

    Returns:
        A tuple containing any errors, warnings, or hints from the
        compilation process.
    """
    process = subprocess.run(
        process_args,
        stdout=None if show_output else subprocess.PIPE,
        stderr=None if show_output else subprocess.PIPE
    )

    code, out, err = process.returncode, process.stdout, process.stderr
    out = out.decode(errors='ignore') if out else ''
    err = err.decode(errors='ignore') if err else ''

    return code, out, err


@contextmanager
def cd(path: Union[Path, str]) -> Iterator[Union[Path, str]]:
    "Convenience function to step in and out of a directory temporarily."
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)


def get_c_compiler_used_to_build_python():
    "This func is included just to be a bit clearer as to its significance."
    return 'vcc' if 'MSC' in sys.version else 'gcc'


def get_host_info() -> Tuple[str, str, str]:
    """
    Returns the host platform, architecture, and C compiler used to build the
    running Python process.
    """
    host_platform = platform.system().lower()
    host_arch = cpuinfo.get_cpu_info()['arch'].lower()
    return host_platform, host_arch, get_c_compiler_used_to_build_python()


def ensure_nimpy() -> None:
    """
    Makes sure that the Nimpy Nim library is installed.

    Verifies that the [Nimpy Library](https://github.com/yglukhov/nimpy) is
    installed and installs it otherwise.

    NOTE: Nimporter would not be possible without Nimpy. Thank you
    Yuriy Glukhov for making this project possible!
    """
    ic()

    show_output = 'NIMPORTER_INSTRUMENT' in os.environ
    code, *_ = run_process(shlex.split('nimble path nimpy'), show_output)

    if code != 0:
        ic()
        nimble_args = shlex.split('nimble install nimpy --accept')
        code, _, stderr = run_process(nimble_args, show_output)

        if code:
            raise CompilationFailedException(stderr)


class NimporterException(Exception):
    "Base exception for Nimporter's exception hierarchy."


class CompilationFailedException(NimporterException):
    def __init__(self, stderr):
        super().__init__(
            f"Nim Compilation Failed. Rerun with NIMPORTER_INSTRUMENT for"
            f" full Nim output: {stderr}"
        )


class ImportFailedException(NimporterException):
    "Custom exception for when compilation succeeds but importing fails."
