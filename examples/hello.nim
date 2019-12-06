import nimpy

proc say_hello_to(name: string): void {.exportpy.} =
    echo ("Hello ", name, "!")
