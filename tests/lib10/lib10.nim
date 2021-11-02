import nimpy, progress

proc func1(): int {.exportpy.} =
    return 1
