from pathlib import Path
from nimporter.lib import *

root = Path('tests')

# for ext_path in find_extensions(root):
#     try:
#         ext = ExtLib(ext_path, root)
#     except Exception as e:
#         print(e)
#         continue

#     print(ext)

import tests.data.ext_mod_basic.ext_mod_basic as ext_mod_basic

print('200 + 300 =', ext_mod_basic.add(200, 300))
