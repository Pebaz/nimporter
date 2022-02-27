import nimpy, asyncstreams

proc func1(): void {.exportpy.} =
    echo "Hello World!"
