import sys

sys.path.append('tests/data')

# * Only need one instance of `run_nimporter_clean`
# * After that, they'll all be compiled
def test_ext_mod_basic():
    "Test building and importing a basic extension module works"
    sys.modules.pop('ext_mod_basic', None)
    import ext_mod_basic
    assert ext_mod_basic.add(1, 2) == 3


def test_ext_lib_basic():
    "Test building and importing a basic extension library works"
    sys.modules.pop('ext_lib_basic', None)
    import ext_lib_basic
    assert ext_lib_basic.add(1, 2) == 3


def test_ext_mod_in_pack():
    "Test building and importing a nested extension module works"
    sys.modules.pop('pkg1.pkg2.ext_mod_in_pack', None)
    import pkg1.pkg2.ext_mod_in_pack
    assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3


def test_ext_lib_in_pack():
    "Test building and importing a nested extension library works"
    sys.modules.pop('pkg1.pkg2.ext_lib_in_pack', None)
    import pkg1.pkg2.ext_lib_in_pack
    assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3


def test_cached_ext_mod_basic():
    "Test importing a basic extension module uses cached artifact"
    sys.modules.pop('ext_mod_basic', None)
    import ext_mod_basic
    assert ext_mod_basic.add(1, 2) == 3


def test_cached_ext_lib_basic():
    "Test importing a basic extension library uses cached artifact"
    sys.modules.pop('ext_lib_basic', None)
    import ext_lib_basic
    assert ext_lib_basic.add(1, 2) == 3


def test_excached_ext_mod_in_pack():
    "Test importing a nested extension module uses cached artifact"
    sys.modules.pop('pkg1.pkg2.ext_mod_in_pack', None)
    import pkg1.pkg2.ext_mod_in_pack
    assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3


def test_excached_ext_lib_in_pack():
    "Test importing a nested extension library uses cached artifact"
    sys.modules.pop('pkg1.pkg2.ext_lib_in_pack', None)
    import pkg1.pkg2.ext_lib_in_pack
    assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3
