"""
Test to make sure that libraries built with Nimporter can be installed via Pip.
"""

import pytest
from pathlib import Path
import subprocess
import nimporter


@pytest.mark.integration_test
def test_create_sdist():
    "Test the successful creation of a source distribution."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py sdist'.split())

        assert Path('dist').exists()
        assert Path('project1.egg-info').exists()
        targets = list(Path('dist').glob('project1*'))
        assert len(targets) == 1
        assert targets[0].exists()


@pytest.mark.integration_test
def test_create_bdist():
    "Test the successful create of a wheel."
    with nimporter.cd('tests/proj1'):
        subprocess.Popen('python3 setup.py bdist_wheel'.split())

        assert Path('dist').exists()
        assert Path('build').exists()
        assert Path('project1.egg-info').exists()
        targets = list(Path('dist').glob('project1*.whl'))
        assert len(targets) == 1
        assert targets[0].exists()


@pytest.mark.slow_integration_test
def test_install_sdist():
    pass


@pytest.mark.slow_integration_test
def test_install_bdist():
    pass
