import sys

def test_ext_lib():
    ext_path = 'tests/data'
    try:
        sys.path.append(ext_path)
        import ext_lib_in_deep_heirarchy.deep1.deep2.deep3.deep as deep
        assert deep.add(1, 2) == 3
    finally:
        sys.path.remove(ext_path)

# sys.path.append('C:/code/me/nimporter')
# import nimporter
# sys.path.append('tests/data/ext_mod_basic')
# import ext_mod_basic
