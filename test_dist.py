from pathlib import Path
from nimporter import NimCompiler

print(NimCompiler.compile_extension_module(Path('dist.nim')))

print(NimCompiler.compile_extension_library(Path('mylib')))

print(NimCompiler.compile_extension_library(Path('myext')))

try:
    NimCompiler.compile_extension_library(Path('mynot'))
except Exception as e:
    print(e)
