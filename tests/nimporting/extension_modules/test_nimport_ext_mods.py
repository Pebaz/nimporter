import sys

def test_ext_mod():
    try:
        sys.path.append('tests/data/ext_mod_basic')
        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3
    finally:
        sys.path.remove('tests/data/ext_mod_basic')

# sys.path.append('C:/code/me/nimporter')
# import nimporter
# sys.path.append('tests/data/ext_mod_basic')
# import ext_mod_basic
