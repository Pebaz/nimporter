import sys
import os
from icecream import ic, colorama

ic.configureOutput(
    includeContext=True,
    prefix=f'{colorama.Fore.CYAN}ic|{colorama.Fore.RESET} ',

    # https://github.com/gruns/icecream/issues/35#issuecomment-908730426
    outputFunction=lambda *args: print(*args)
)

ic.enabled = 'NIMPORTER_INSTRUMENT' in os.environ

from nimporter.lib import (
    WINDOWS, MACOS, LINUX, EXT_DIR, PLATFORM_TABLE, ARCH_TABLE
)

import nimporter.nimporter  # Register importers

from nimporter.nexporter import get_nim_extensions
