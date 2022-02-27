import nimpy

proc func1(): void {.exportpy.} =
    echo "Hello World!"
