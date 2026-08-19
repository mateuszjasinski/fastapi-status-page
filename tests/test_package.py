"""Smoke tests for the package scaffold.

Replace/extend these with real tests once the status endpoint and
dependency-check registration are implemented.
"""

from __future__ import annotations

import fastapi_status_page


def test_version_is_exposed() -> None:
    assert isinstance(fastapi_status_page.__version__, str)
    assert fastapi_status_page.__version__
