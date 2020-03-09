"""
Test to make sure that libraries built with Nimporter can be installed via Pip.
"""

import pytest
from pathlib import Path
import nimporter
from nimporter_cli import clean

@pytest.mark.integration_test
def test_create_sdist():
    "Test the successful creation of a source distribution"


@pytest.mark.integration_test
def test_create_bdist():
    pass


@pytest.mark.slow_integration_test
def test_install_sdist():
    pass


@pytest.mark.slow_integration_test
def test_install_bdist():
    pass
