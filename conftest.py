"""
These are Pytest hooks that are necessary to ensure that no build artifacts are
leftover from previous runs.
"""

import pathlib, nimporter_cli


def pytest_sessionstart(session):
    nimporter_cli.clean(pathlib.Path())
