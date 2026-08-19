"""Shared pytest fixtures.

Scaffolding only — wire up a FastAPI app / TestClient here once the
implementation exists.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
