# Don't require Nimporter to be installed to run integration tests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import nimporter

import ext_mod_basic
import ext_lib_basic
import pkg1.pkg2.ext_mod_in_pack
import pkg1.pkg2.ext_lib_in_pack


def py_function():
    assert ext_mod_basic.add(1, 2) == 3
    assert ext_lib_basic.add(1, 2) == 3
    assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3
    assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

    return sum((
        ext_mod_basic.add(1, 2),
        ext_lib_basic.add(1, 2),
        pkg1.pkg2.ext_mod_in_pack.add(1, 2),
        pkg1.pkg2.ext_lib_in_pack.add(1, 2),
    ))
