"""
Test to make sure that libraries built with Nimporter can be installed via Pip.
"""

import pytest
from pathlib import Path
import subprocess, shutil
import nimporter


@pytest.mark.integration_test
def test_create_sdist():
    "Test the successful creation of a source distribution."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py sdist'.split()).wait()
        dist = Path('dist')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert egg.exists()
            targets = list(dist.glob('project1*'))
            assert len(targets) == 1
            assert targets[0].exists()
        finally:
            if dist.exists(): shutil.rmtree(str(dist.absolute()))
            if egg.exists(): shutil.rmtree(str(egg.absolute()))


@pytest.mark.integration_test
def test_create_bdist():
    "Test the successful create of a wheel."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py bdist_wheel'.split()).wait()
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
        finally:
            if dist.exists(): shutil.rmtree(str(dist.absolute()))
            if build.exists(): shutil.rmtree(str(build.absolute()))
            if egg.exists(): shutil.rmtree(str(egg.absolute()))


@pytest.mark.slow_integration_test
def test_install_sdist():
    "Make sure that the project can be installed by Pip"
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py sdist'.split()).wait()
        dist = Path('dist')
        egg = Path('project1.egg-info')
        try:
            assert dist.exists()
            assert egg.exists()
            targets = list(dist.glob('project1*'))
            assert len(targets) == 1
            assert targets[0].exists()

            pip = 'pip' if shutil.which('pip') else 'pip3'
            subprocess.Popen(f'{pip} install .'.split()).wait()
        finally:
            if dist.exists(): shutil.rmtree(str(dist.absolute()))
            if egg.exists(): shutil.rmtree(str(egg.absolute()))

    import proj1
    assert proj1
    assert proj1.performance
    assert proj1.lib1
    assert proj1.foo
    assert proj1.bar
    assert proj1.baz
    assert proj1.baz() == 1

    subprocess.Popen(f'{pip} uninstall project1 -y'.split()).wait()


@pytest.mark.slow_integration_test
def test_install_bdist():
    "Make sure that the wheel can be installed by Pip"
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py bdist_wheel'.split()).wait()
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

            pip = 'pip' if shutil.which('pip') else 'pip3'
            subprocess.Popen(f'{pip} install {wheel}'.split()).wait()
        finally:
            if dist.exists(): shutil.rmtree(str(dist.absolute()))
            if build.exists(): shutil.rmtree(str(build.absolute()))
            if egg.exists(): shutil.rmtree(str(egg.absolute()))

    import proj1
    assert proj1
    assert proj1.performance
    assert proj1.lib1
    assert proj1.foo
    assert proj1.bar
    assert proj1.baz
    assert proj1.baz() == 1

    subprocess.Popen(f'{pip} uninstall project1 -y'.split()).wait()
