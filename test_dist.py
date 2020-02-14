from pathlib import Path
from nimporter import NimCompiler

#e = NimCompiler.compile_extension(Path('dist.nim'))
#print(e)

el = NimCompiler.compile_library(Path('mylib'))
print(el)
