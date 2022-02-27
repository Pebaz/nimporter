import nimpy

proc func1(): string {.exportpy.} =
    return "Hello World!"
