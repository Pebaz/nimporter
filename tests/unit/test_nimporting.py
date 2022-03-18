import sys

def test_ext_lib():
    ext_path = 'tests/data'
    try:
        sys.path.append(ext_path)
        import pkg1.pkg2.ext_lib_in_pack
        assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3
    finally:
        sys.path.remove(ext_path)

# sys.path.append('C:/code/me/nimporter')
# import nimporter
# sys.path.append('tests/data/ext_mod_basic')
# import ext_mod_basic


import sys

def test_ext_mod():
    ext_path = 'tests/data/shallow'
    try:
        sys.path.append(ext_path)
        import pkg1.pkg2.ext_mod_in_pack
        assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3
    finally:
        sys.path.remove(ext_path)

# sys.path.append('C:/code/me/nimporter')
# import nimporter
# sys.path.append('tests/data/ext_mod_basic')
# import ext_mod_basic



def test_import_mod_shallow():
    "Simplest case"


def test_import_mod_deep():
    "Slightly more involved case"


def test_import_lib_shallow():
    "Simplest case"


def test_import_lib_deep():
    "Slightly more involved case"




def test_import_mod_shallow_in_package():
    "Simplest case"


def test_import_mod_deep_in_package():
    "Slightly more involved case"


def test_import_lib_shallow_in_package():
    "Simplest case"


def test_import_lib_deep_in_package():
    "Slightly more involved case"




def test_import_mod_shallow_is_cached():
    "Simplest case"


def test_import_mod_deep_is_cached():
    "Slightly more involved case"


def test_import_lib_shallow_is_cached():
    "Simplest case"


def test_import_lib_deep_is_cached():
    "Slightly more involved case"


def test_import_mod_shallow_in_package_is_cached():
    "Simplest case"


def test_import_mod_deep_in_package_is_cached():
    "Slightly more involved case"


def test_import_lib_shallow_in_package_is_cached():
    "Simplest case"


def test_import_lib_deep_in_package_is_cached():
    "Slightly more involved case"
