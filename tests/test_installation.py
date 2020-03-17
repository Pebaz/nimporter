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
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(egg.absolute()))


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
            shutil.rmtree(str(dist.absolute()))
            shutil.rmtree(str(build.absolute()))
            shutil.rmtree(str(egg.absolute()))


@pytest.mark.slow_integration_test
def test_install_sdist():
    pass


@pytest.mark.slow_integration_test
def test_install_bdist():
    pass
