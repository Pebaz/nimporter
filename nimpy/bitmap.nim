import nimpy

proc greet(name: string): string {.exportpy.} =
    return "Hello, " & name & "!"
