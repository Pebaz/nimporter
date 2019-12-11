#[
This is a test!
]#
import nimpy

proc hello(user: string): string {.exportpy.} =
    return "Hello " & user & "!"  # THIS IS AN ERROR
echo "one"
echo "two"
echo "three"
echo "four"
