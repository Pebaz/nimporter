import nimpy, subber, algorithm

proc add(a, b: int): int {.exportpy.} =
    return a + b

proc sub(a, b: int): int {.exportpy.} =
    return subber.sub_this(a, b)
