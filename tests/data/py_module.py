
# ! import nimporter
# ! import ext_mod_basic  <- Import all of them and sum them!

# import ext_mod_basic
# import ext_lib_basic
# import pkg1.pkg2.ext_mod_in_pack
# import pkg1.pkg2.ext_lib_in_pack


def py_function():
    # assert ext_mod_basic.add(1, 2) == 3
    # assert ext_lib_basic.add(1, 2) == 3
    # assert pkg1.pkg2.ext_mod_in_pack.add(1, 2) == 3
    # assert pkg1.pkg2.ext_lib_in_pack.add(1, 2) == 3

    # return sum((
    #     ext_mod_basic.add(1, 2),
    #     ext_lib_basic.add(1, 2),
    #     pkg1.pkg2.ext_mod_in_pack.add(1, 2),
    #     pkg1.pkg2.ext_lib_in_pack.add(1, 2),
    # ))

    return 3.14
