import nimpy
import tables

proc add(a: int, b: int): int {.exportpy.} =
    return a + b

proc getTable(): Table[string, int] {.exportpy.} =
    result = {
        "Hello" : 0,
        "SomeKey": 10,
        "OtherKey": 123,
        "FinalKey": 123456
    }.toTable
