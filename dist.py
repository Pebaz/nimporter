"""
Process is as follows:

1. Compile Nim file only and place into it's own build dir.
2. Copy the "nimbase.h" file over to that build dir.
3. Get list of all C files in build dir.
4. Append a Python C extension that uses list of C files.
"""

import pathlib, shutil

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

print(find_nim_std_lib())
print(find_nim_std_lib() / 'nimbase.h')
print((find_nim_std_lib() / 'nimbase.h').exists())
