import os
import sys
import shlex
import shutil
import hashlib
import tempfile
import platform
import sysconfig
import subprocess
import cpuinfo
from typing import *
from pathlib import Path
from contextlib import contextmanager
from icecream import ic

PathParts = Union[Tuple[str, str, str], Tuple[str], Tuple[str, str]]

PYTHON: str = 'python' if sys.platform == 'win32' else 'python3'
PIP: str = 'pip' if shutil.which('pip') else 'pip3'
PYTHON_LIB_EXT: str = sysconfig.get_config_var('EXT_SUFFIX')
WINDOWS: str = 'windows'
MACOS: str = 'darwin'
LINUX: str = 'linux'
EXT_DIR: str = 'nim-extensions'

PLATFORM_TABLE: Dict[str, str] = {  # Keys are known to Python and values are Nim-understood
    'windows': 'Windows',
    'darwin': 'MacOSX',
    'linux': 'Linux',
}

ARCH_TABLE: Dict[str, str] = {  # Keys are known to Python and values are Nim-understood
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

ALWAYS_ARGS: List['str'] = [
    'nimble',  # Installs dependencies :)
    'c',
    '--accept',  # Allow installing dependencies
    '--skipUserCfg',
    '--app:lib',
    '--backend:c',
    '--threads:on',
    '--warning[ProveInit]:off',  # https://github.com/Pebaz/nimporter/issues/41
]


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


def get_import_path(path: Path, root: Path) -> str:
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

    def get_import_prefix(module_path: Path, root: Path) -> PathParts:
        root_path = root.resolve()
        full_path = module_path.resolve()

        assert full_path >= root_path, 'Extension path is not within root dir.'

        return ic(full_path.parts[len(root_path.parts):])

    library = path.is_dir()
    module_name = path.stem
    module_path = path if path.is_file() else path / path.stem
    import_prefix = get_import_prefix(module_path.parent, root)
    module_part = tuple() if library else (module_name,)
    import_path = '.'.join(import_prefix + module_part)

    return ic(import_path)


@contextmanager
def convert_to_lib_if_needed(path: Path) -> Iterator[Path]:
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
    show_output: bool = False,
) -> Tuple[int, Union[bytes, Text], Union[bytes, Text]]:
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
        stderr=None if show_output else subprocess.PIPE,
    )

    code, out, err = process.returncode, process.stdout, process.stderr
    out = out.decode(errors='ignore') if out else '' # type: ignore[assignment]
    err = err.decode(errors='ignore') if err else '' # type: ignore[assignment]

    return code, out, err


@contextmanager
def cd(path: Path) -> Iterator[Path]:
    "Convenience function to step in and out of a directory temporarily."
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)


def get_c_compiler_used_to_build_python() -> str:
    "This func is included just to be a bit clearer as to its significance."
    return 'vcc' if 'MSC' in sys.version else 'gcc'


def get_host_info() -> Tuple[str, str, str]:
    """
    Returns the host platform, architecture, and C compiler used to build the
    running Python process.
    """
    # Calling get_cpu_info() is expensive
    if not getattr(get_host_info, 'host_arch', None):
        setattr(get_host_info, 'host_arch', cpuinfo.get_cpu_info()['arch'].lower())
        # get_host_info.host_arch = cpuinfo.get_cpu_info()['arch'].lower()

    return ic((
        platform.system().lower(),
        get_host_info.host_arch, # type: ignore[attr-defined]
        get_c_compiler_used_to_build_python()
    ))


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
    return


class NimporterException(Exception):
    "Base exception for Nimporter's exception hierarchy."
    pass


class CompilationFailedException(NimporterException):
    def __init__(self, stderr: Union[bytes, str]) -> None:
        super().__init__(
            f'Nim Compilation Failed. Rerun with NIMPORTER_INSTRUMENT for'
            f' full Nim output: {stderr}' # type: ignore[str-bytes-safe]
        )
        return


class ImportFailedException(NimporterException):
    "Custom exception for when compilation succeeds but importing fails."
    pass


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
        def walk_folder(path: Path) -> Iterator[Path]:
            for item in path.iterdir():
                if item.is_dir():
                    if item.stem == '__pycache__':
                        continue
                    for i in walk_folder(item):
                        yield i
                else:
                    yield item

        for item in walk_folder(module_path):
            digest.update(str(item).encode())
            digest.update(item.read_bytes())

    ic(digest.hexdigest())

    return digest.digest()


class ExtLib:
    """
    All extensions are assumed to be libraries only. Modules are convert to
    libraries as needed.
    """
    def __init__(self, path: Path, root: Path, library_hint: bool) -> None:
        """
        Args:
            path(str): the relative path to the Nim file (for both lib & mod).
        """
        self.library = all((
            any(path.parent.glob(f'{path.stem}.nim')),
            any(path.parent.glob(f'{path.stem}.nimble')),
            any(path.parent.glob(f'{path.stem}.nim.cfg'))
        ))

        assert library_hint and self.library if library_hint else True, (
            f'ExtLib must define: {path.stem}.nim, {path.stem}.nimble, and '
            f'{path.stem}.nim.cfg'
        )

        self.symbol = path.stem
        self.module_path = path

        if self.library:
            self.relative_path = path.parent
            self.full_path = path.parent.resolve().absolute()

        else:
            self.relative_path = path
            self.full_path = path.resolve().absolute()

        self.pycache = self.full_path.parent / '__pycache__'

        self.import_namespace = get_import_path(self.relative_path, root)
        self.hash_filename = self.pycache / f'{self.symbol}.hash'
        self.build_artifact = (
            self.pycache / f'{self.symbol}{PYTHON_LIB_EXT}'
        )
        return

    def __str__(self) -> str:
        return f'<ExtLib {self.import_namespace}>'

    def __repr__(self) -> str:
        return str(self)

    def __format__(self, *args, **kwargs) -> str: # type: ignore[no-untyped-def]
        return str(self)
