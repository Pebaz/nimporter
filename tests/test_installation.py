"""
Test to make sure that libraries built with Nimporter can be installed via Pip.
"""

import sys, os, subprocess, shutil, pkg_resources, json
from pathlib import Path
import pytest
import nimporter

PYTHON = 'python' if sys.platform == 'win32' else 'python3'
PIP = 'pip' if shutil.which('pip') else 'pip3'

@pytest.mark.integration_test
def test_ensure_nimporter_installed():
    "Make sure that Nimporter is installed before running integration tests."
    libs = {lib.key.lower() for lib in pkg_resources.working_set}
    assert 'nimporter' in libs, (
        f'Nimporter is not installed. Please install via:'
        f'`{PIP} install .` before running the integration tests.'
    )

@pytest.mark.integration_test
def test_create_sdist():
    "Test the successful creation of a source distribution."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen(f'{PYTHON} setup.py sdist'.split()).wait()
        dist = Path('dist')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert egg.exists()
            targets = list(dist.glob('project1*'))
            assert len(targets) == 1
            assert targets[0].exists()

            # Make sure the appropriate compiler is being used
            for extension in Path('nim-extensions').iterdir():
                (nim_build_data_file,) = extension.glob('*json')
                nim_build_data = json.loads(nim_build_data_file.read_text())

                expected = nimporter.NimCompiler.get_compatible_compiler()
                assert expected, 'No compatible C compiler installed.'
                installed_compilers = nimporter.NimCompiler.get_installed_compilers()
                cc_path = installed_compilers[expected]
                assert nim_build_data['linkcmd'].startswith(cc_path.name), (
                    'Nim used a different C compiler than what Python expects.'
                )

        finally:
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(egg.absolute()))


@pytest.mark.integration_test
def test_create_bdist():
    "Test the successful create of a wheel."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen(f'{PYTHON} setup.py bdist_wheel'.split()).wait()
        dist = Path('dist')
        build = Path('build')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert build.exists()
            assert egg.exists()
            targets = list(Path('dist').glob('project1*.whl'))
            assert len(targets) == 1
            assert targets[0].exists()

            # Make sure the appropriate compiler is being used
            for extension in Path('nim-extensions').iterdir():
                (nim_build_data_file,) = extension.glob('*json')
                nim_build_data = json.loads(nim_build_data_file.read_text())

                expected = nimporter.NimCompiler.get_compatible_compiler()
                assert expected, 'No compatible C compiler installed.'
                installed_compilers = nimporter.NimCompiler.get_installed_compilers()
                cc_path = installed_compilers[expected]
                assert nim_build_data['linkcmd'].startswith(cc_path.name), (
                    'Nim used a different C compiler than what Python expects.'
                )

        finally:
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(build.absolute()))
            shutil.rmtree(str(egg.absolute()))


@pytest.mark.slow_integration_test
def test_install_sdist():
    "Make sure that the project can be installed by Pip"
    with nimporter.cd('tests/proj1'):
        subprocess.Popen(f'{PYTHON} setup.py sdist'.split()).wait()
        dist = Path('dist')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert egg.exists()
            targets = list(dist.glob('project1*'))
            assert len(targets) == 1
            assert targets[0].exists()

            subprocess.Popen(f'{PIP} install .'.split()).wait()

            import proj1
            assert proj1
            assert proj1.performance
            assert proj1.lib1
            assert proj1.foo
            assert proj1.bar
            assert proj1.baz
            assert proj1.baz() == 1

            subprocess.Popen(f'{PIP} uninstall project1 -y'.split()).wait()

        finally:
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(egg.absolute()))


@pytest.mark.slow_integration_test
def test_install_bdist():
    "Make sure that the wheel can be installed by Pip"
    with nimporter.cd('tests/proj1'):
        subprocess.Popen(f'{PYTHON} setup.py bdist_wheel'.split()).wait()
        dist = Path('dist')
        build = Path('build')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert build.exists()
            assert egg.exists()
            targets = list(Path('dist').glob('project1*.whl'))
            assert len(targets) == 1
            wheel = targets[0]
            assert wheel.exists()

            subprocess.Popen(f'{PIP} install {wheel}'.split()).wait()

            import proj1
            assert proj1
            assert proj1.performance
            assert proj1.lib1
            assert proj1.foo
            assert proj1.bar
            assert proj1.baz
            assert proj1.baz() == 1

            subprocess.Popen(f'{PIP} uninstall project1 -y'.split()).wait()

        finally:
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(build.absolute()))
            shutil.rmtree(str(egg.absolute()))
