import nimpy, async

proc func1(): int {.exportpy.} =
    return 1
