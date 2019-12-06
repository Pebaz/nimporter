import nimpy
import tables

proc getTable(): Table[string, int] {.exportpy.} =
    result = {
        "Hello" : 0,
        "SomeKey": 10,
        "OtherKey": 123,
        "FinalKey": 123456
    }.toTable
