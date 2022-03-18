import pytest
from pathlib import Path
from nimporter.cli import nimporter_clean


@pytest.fixture
def run_nimporter_clean():
    nimporter_clean(Path())
