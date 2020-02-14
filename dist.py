"""
Process is as follows:

1. Compile Nim file only and place into it's own build dir.
2. Copy the "nimbase.h" file over to that build dir.
3. Get list of all C files in build dir.
4. Append a Python C extension that uses list of C files.
"""

import pathlib, subprocess, shutil
from setuptools import Extension
from nimporter import NimCompiler

def find_nim_std_lib():
    nimexe = pathlib.Path(shutil.which('nim'))
    if not nimexe:
        return None
    result = nimexe.parent / '../lib'
    if not (result / 'system.nim').exists():
        result = nimexe.resolve().parent / '../lib'
        if not (result / 'system.nim').exists():
            return None
    return result.resolve()

nimc_args = "nim cc -c --opt:speed --gc:markAndSweep --app:lib -d:release --nimcache:build dist.nim".split()

process = subprocess.run(
    nimc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
out, err = process.stdout, process.stderr
out = out.decode() if out else ''
err = err.decode() if err else ''
output = out + err
warnings = [
    line
    for line in output.splitlines()
    if 'Warning:' in line
]
hints = [
    line
    for line in output.splitlines()
    if 'Hint:' in line
]

print(hints)
print(warnings)

NIMBASE = 'nimbase.h'
nimbase = find_nim_std_lib() / NIMBASE
build = pathlib.Path('.').resolve() / 'build'

shutil.copyfile(str(nimbase), str(build / NIMBASE))

csources = [str(c) for c in build.iterdir() if c.suffix == '.c']

# Parallel build?
extension = Extension(
    name='dist',
    sources=csources,
    include_dirs=[str(build)]
)

print(extension)

# Treat all Nim files as own extension.
# This closely matches real-world use case: speed
# However, it means you won't be able to import Nim files...

for nim_file in pathlib.Path().rglob('*.nim'):
    print(nim_file)


def __find_extensions(path, exclude_dirs=[]):
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
            nim_exts.extend(__find_extensions(item, exclude_dirs=exclude_dirs))

        elif item.suffix == '.nim':
            "Treat item as a Nim Extension."
            nim_exts.append(item)

    return nim_exts

def build_nim_extension(path):
    # It is known that this dir contains .nimble
    if extension.is_dir():
        return NimCompiler.compile_extension_library(path)
        
    # This is for sure a Nim extension file
    else:
        return NimCompiler.compile_extension_module(path)

def build_nim_extensions(exclude_dirs=[]):
    """
    Compiles Nim files to C and creates Extensions from them for distribution.
    """
    extensions = []

    for extension in __find_extensions(pathlib.Path(), exclude_dirs):
        ext = build_nim_extension(extension)
        if ext: extensions.append(ext)

    return dict(ext_modules=extensions)



# from setuptools import setup
# setup(
#     name='pebaz',
#     ext_modules=[extension]
# )

print('-' * 40)
for file in __find_extensions(pathlib.Path()):
    print(file)

print('done')
