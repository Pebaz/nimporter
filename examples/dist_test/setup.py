from setuptools import setup, find_packages

def package_nim_source():
    """
    Use this to distribute your Nim source code to the end user.
    Please note that in order for the end user to import the Nim module using
    Nimporter, they must install both a C compiler as well as the Nim compiler.
    """
    return dict(
        package_data={'': ['*.nim']},
        include_package_data=True,
        install_requires=['nimporter@git+https://github.com/Pebaz/Nimporter']
    )

setup(
    name='foofoo',
    version='0.1',
    description='A description.',
    packages=['foofoo'],
    **package_nim_source()
)
