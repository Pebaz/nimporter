from pathlib import Path
from nimporter import NimCompiler

e = NimCompiler.compile_extension(Path('dist.nim'))

