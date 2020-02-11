import std/[os]
proc findNimStdLib*(): string =
  ## Tries to find a path to a valid "system.nim" file.
  ## Returns "" on failure.
  try:

    let nimexe = os.findExe("nim")
    if nimexe.len == 0: return ""
    result = nimexe.splitPath()[0] /../ "lib"
    if not fileExists(result / "system.nim"):
      when defined(unix):
        result = nimexe.expandSymlink.splitPath()[0] /../ "lib"
        if not fileExists(result / "system.nim"): return ""

  except OSError, ValueError:
    return ""
echo findNimStdLib() / "nimbase.h"
echo os.getCurrentDir().splitPath()