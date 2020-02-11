import nimpy

proc add(a, b: int): int {.exportpy.} =
    return a + b
