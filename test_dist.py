from pathlib import Path
from nimporter import NimCompiler

#e = NimCompiler.compile_extension(Path('dist.nim'))
#print(e)

print(NimCompiler.compile_library(Path('mylib')))

print(NimCompiler.compile_library(Path('myext')))

try:
    NimCompiler.compile_library(Path('mynot'))
except Exception as e:
    print(e)
