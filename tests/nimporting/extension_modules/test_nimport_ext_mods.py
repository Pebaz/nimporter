import sys

def test_ext_mod():
    ext_path = 'tests/data/ext_mod_basic'
    try:
        sys.path.append(ext_path)
        import ext_mod_basic
        assert ext_mod_basic.add(1, 2) == 3
    finally:
        sys.path.remove(ext_path)

# sys.path.append('C:/code/me/nimporter')
# import nimporter
# sys.path.append('tests/data/ext_mod_basic')
# import ext_mod_basic
