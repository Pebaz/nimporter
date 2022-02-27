import sys
import nimporter

def test_ext_mod():
    sys.path.append('tests/data/ext_mod_basic')


    # ! This needs to only find `ext_mod_basic`, even if it's a folder

    import ext_mod_basic

    assert ext_mod_basic.add(1, 2) == 3
