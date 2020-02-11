"""
Process is as follows:

1. Compile Nim file only and place into it's own build dir.
2. Copy the "nimbase.h" file over to that build dir.
3. Get list of all C files in build dir.
4. Append a Python C extension that uses list of C files.
"""

import pathlib, subprocess, shutil

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

NIMBASE = 'nimbase.h'
nimbase = find_nim_std_lib() / NIMBASE
destination = pathlib.Path('.').resolve() / 'build' / NIMBASE

shutil.copyfile(str(nimbase), str(destination))

nimc_args = "nim cc -c --opt:speed --gc:markAndSweep --app:lib -d:release --nimcache:build dist.nim".split()

process = subprocess.run(
    nimc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
out, err = process.stdout, process.stderr
out = out.decode() if out else ''
err = err.decode() if err else ''
warnings = [
    line
    for line in err.splitlines()
    if 'Warning:' in line
]
hints = [
    line
    for line in err.splitlines()
    if 'Hint:' in line
]

print(out)
print(err)

print(hints)
print(warnings)
