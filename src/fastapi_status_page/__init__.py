"""FastAPI status page with pluggable dependency health checks.

Public API is re-exported here so consumers can::

    from fastapi_status_page import StatusPage, CheckResponse
"""

from __future__ import annotations

from fastapi_status_page.enums import ResponseFormat, Status
from fastapi_status_page.exceptions import ConfigurationError
from fastapi_status_page.models import CheckResponse, CheckResult
from fastapi_status_page.page import StatusPage

__version__ = "0.1.0"

__all__ = [
    "CheckResponse",
    "CheckResult",
    "ConfigurationError",
    "ResponseFormat",
    "Status",
    "StatusPage",
    "__version__",
]
