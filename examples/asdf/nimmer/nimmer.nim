import nimpy, algorithm

proc add(a, b: int): int {.exportpy.} =
    return a + b
