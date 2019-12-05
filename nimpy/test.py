import nimpy  # Necessary to import before importing any Nim modules

# TEMPORARY: FOR TESTING PURPOSES ONLY
print(sys.path)
import math
import esper
import tkinter.messagebox
import raylib.colors

import bitmap
print(bitmap.greet('Pebaz'))
print(dir(bitmap))

from foo.bar import baz
print(baz('Purple Boo'))