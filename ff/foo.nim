import nimpy

echo "apple-darwin"

proc hello(user: string): string {.exportpy.} =
    return "Hello " & user & "!"  # THIS IS AN ERROR
