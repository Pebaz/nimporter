import os
import sys
from typing import *
from pathlib import Path
from icecream import ic
from nimporter.lib import *
from distutils.extension import Extension
import shlex
import shutil
import subprocess


def get_host_extension_bundle(root: Path) -> List[Extension]:
    extensions = []
    ext_dir = root / EXT_DIR

    for extension_root in ext_dir.iterdir():
        platform, arch, cc = get_host_info()
        host_info = f'{platform}-{arch}-{cc}'
        host_extension = extension_root / host_info

        ic(host_extension)

        assert host_extension.exists(), (
            f'No extension found for host platform/arch: {host_info}.\n'
            f'Bundled extensions: {[i.name for i in ext_dir.iterdir()]}\n'
            f'Perhaps run "nimporter clean"?'
        )

        extensions.append(
            Extension(
                name=extension_root.name,
                sources=[str(c) for c in host_extension.glob('*.c')],
                include_dirs=[str(host_extension)],
            )
        )

    return ic(extensions)


def get_sdist_extension_bundle(root: Path) -> List[Extension]:
    """
    The goal of this function is to get every combination of platform,
    architecture, and compiler as it's own extension. The reason why is to make
    packaging into source distributions easier.
    """

    # ! In this case, the extension's name does not matter (which is why the)
    # ! platform/architecture info is added) because the extensions are added
    # ! to the source distribution just like how a Manifest would. On the
    # ! client machine, get_nim_extensions() will return
    # ! get_host_extension_bundle() instead which is just the Nim extensions
    # ! for the host platform.
    extensions = []

    for extension_root in (root / EXT_DIR).iterdir():
        for extension_per_target in extension_root.iterdir():
            all_files = [
                str(c) for c in extension_per_target.iterdir()
                if not c.suffix == '.json'
            ]

            extensions.append(
                Extension(
                    name=f'{extension_root.name}-{extension_per_target.name}',
                    sources=all_files,
                    include_dirs=[str(extension_per_target)]
                )
            )

    return ic(extensions)


def find_nim_std_lib() -> Optional[Path]:
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
    if not shutil.which('nim'):
        return # type: ignore[return-value]

    # Installed via choosenim_install Pypi package
    choosenim_dir = Path('~/.choosenim/toolchains').expanduser().absolute()
    if choosenim_dir.exists: # type: ignore[truthy-function]
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
        _, o, _ = run_process(
            shlex.split('choosenim show -y --nocolor')
        )

        (choosenim,) = [i for i in o.splitlines() if 'Path:' in i]
        toolchain = Path(choosenim.split('Path:').pop().strip()) # type: ignore[arg-type]
        stdlib = toolchain / 'lib'

        if (stdlib / 'system.nim').exists():
            return stdlib.resolve().absolute()

    # Installed manually
    nimexe: Path = Path(nimexe)
    result = nimexe.parent / '../lib'
    if not (result / 'system.nim').exists():
        result = nimexe.resolve().parent / '../lib'

        if not (result / 'system.nim').exists():
            return None

    return result.resolve().absolute()


def copy_headers(build_dir_relative: Path) -> Path:
    "Can't compile without nimbase.h"
    NIMBASE = 'nimbase.h'
    nimbase = find_nim_std_lib() / NIMBASE # type: ignore[operator]
    nimbase_dest = build_dir_relative / NIMBASE
    shutil.copyfile(nimbase, nimbase_dest)
    assert nimbase_dest.exists()
    return nimbase_dest


def is_run_from_python_setup_py_sdist() -> bool:
    """
    This is used to either bundle all possible Nim extensions compiled to C for
    every supported platform/architecture combo, or return just the Nim
    extension compiled to C for the host platform when not executing the
    `python setup.py sdist` command.
    """
    return Path(sys.argv[0]).name == 'setup.py' and 'sdist' in sys.argv


def get_nim_extensions(
    platforms: List[str],
    root: Optional[Path] = None
) -> List[Extension]:
    """
    Auto-discovers all Nim extensions in the project and returns them.

    This function will return 2 different sets of extensions depending on when
    it is called:

    1. If called on client via `pip install ...`, it will return the list of
       Nim extensions for the host platform running the Pip command.

    2. If called on the host via `python setup.py sdist`, it will return the
       entire list of all extensions per platform + architecture combo to
       ensure they exist for the client when they install the library.

    If nim-extensions doesn't exist:
        For each of the auto-discovered extensions:
            Build them once per platform-arch combo
                Place generated C code in nim-extensions
            Return the entire lot of them as extensions to be bundled

    If nim-extensions does exist (on 1. bdist_wheel or 2. client platform):
        For each of the auto-discovered extensions:
            Find exactly 1 that matches the platform-arch combo
            Return that one extension
    """
    root = root or Path()

    if is_run_from_python_setup_py_sdist():
        if not (root / EXT_DIR).exists():
            ic(f'Compiling for platforms: {platforms}')
            compile_extensions_to_c(platforms, root)
        return ic(get_sdist_extension_bundle(root))

    else:
        if not (root / EXT_DIR).exists():
            ic('Compiling for host platform only')
            compile_extensions_to_c([get_host_info()[0]], root)
        return ic(get_host_extension_bundle(root))


def iterate_target_triples(
    platforms: List[str]
) -> Iterator[Tuple[str, str, str]]:
    for platform in PLATFORM_TABLE:
        if platform not in platforms:
            continue
        for arch in ARCH_TABLE:
            for compiler in 'vcc', 'gcc':
                if platform != WINDOWS and compiler == 'vcc':
                    continue  # 😂
                yield platform, arch, compiler


def compile_extensions_to_c(platforms: List[str], root: Path) -> None:
    "Compile all extensions to C for bundling starting at a given path."

    ensure_nimpy()

    for extension_path in ic(find_extensions(root)):
        ext_dir = (root / EXT_DIR).absolute()
        ext_dir.mkdir(parents=True, exist_ok=True)

        with convert_to_lib_if_needed(extension_path) as compilation_dir:
            nim_module = compilation_dir / (extension_path.stem + '.nim')
            import_path = get_import_path(extension_path, root)

            with cd(compilation_dir) as tmp_cwd:
                for platform, arch, cc in iterate_target_triples(platforms):
                    nim_platform = PLATFORM_TABLE[platform]
                    nim_arch = ARCH_TABLE[arch]
                    target = f'{platform}-{arch}-{cc}'

                    ic(f'Compiling {import_path} for {target}')

                    out_dir = ext_dir / import_path / target
                    out_dir.mkdir(parents=True, exist_ok=True)

                    # Needed during compilation of the Nim extension on the
                    # client's machine that will not have Nim installed
                    copy_headers(out_dir)

                    cli_args = ALWAYS_ARGS + [
                        '--compileOnly',
                        f'--nimcache:{out_dir}',
                        f'--os:{nim_platform}',
                        f'--cpu:{nim_arch}',
                        f'--cc:{cc}',
                        nim_module.name
                    ]

                    ic(cli_args)

                    code, _, stderr = run_process(
                        cli_args,
                        'NIMPORTER_INSTRUMENT' in os.environ
                    )

                    if code:
                        raise CompilationFailedException(stderr)

                    prevent_win32_max_path_length_error(out_dir)
    return


def prevent_win32_max_path_length_error(path: Path) -> None:
    """
    Nim generates C files that contain `@` symbols to encode the original path
    to the Nim module. However, there are 2 problems with this:
        1. They contain the user's private directory structure
        2. They cause compilation to fail on Win32 MSVC (max path length 260)

    This function just removes the encoded path and adds a prefix so that users
    of Nimporter can tell who made that change.

    Turns this:
        @m..@s..@s..@s..@s..@s..@sUsers@s<USERNAME>@s.nimble@spkgs@snimpy-0.2.0@snimpy@spy_utils.nim.c
    Into:
        NIMPORTER@nimpy-0.2.0@nimpy@py_utils.nim.c

    That's a lot less characters!
    """

    def is_valid_identifier(string: str) -> Union[Match[str], None, bool]:
        import re
        match = re.search('^[A-Za-z_][A-Z-a-z0-9_\\-]*', string)
        return match and len(match.string) == len(string)

    def is_semver(string: str) -> bool:
        try:
            lib_name, lib_version = string.rsplit('-', maxsplit=1)
            assert is_valid_identifier(lib_name)

            major, minor, patch = lib_version.split('.')
            assert major.isdigit()
            assert minor.isdigit()
            assert patch.isdigit()

            return True
        except:
            return False

    for item in path.iterdir():
        if item.is_file() and item.name.startswith('@m'):

            # Bare module. Module not from library dependency
            if '@s' not in item.name:
                mod_name = item.name.replace('@m', '')

            # Module from a library dependency. Find the package the module
            # belongs to (if any)
            else:
                segments = item.name.replace('@m', '').split('@s')

                for segment in reversed(segments):
                    if is_semver(segment):
                        index = segments.index(segment)
                        mod_name = '@'.join(segments[index:])
                        break

            new_name = ic(f'NIMPORTER@{mod_name}')
            item.replace(item.with_name(new_name))
    return
