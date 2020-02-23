import nimpy

#import this_doesnt_exist

proc foo(): void {.exportpy.} =
    echo "Hello World!"
