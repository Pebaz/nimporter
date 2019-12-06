#[
    Simple calculator library written in Nim and made available for import via
    the Nimpy library for Nim.
]#

import nimpy

proc add(a: int, b: int): int {.exportpy.} =
    return a + b

proc subtract(a: int, b: int): int {.exportpy.} =
    return a - b

proc multiply(a: int, b: int): int {.exportpy.} =
    return a * b

proc divide(a: int, b: int): float {.exportpy.} =
    return a / b
