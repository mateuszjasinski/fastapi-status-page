import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypeGuard

from fastapi_status_page.enums import Status
from fastapi_status_page.models import CheckResult


def is_async_callable(obj: Any) -> TypeGuard[Callable[..., Awaitable[Any]]]:
    """Return True if calling ``obj`` produces a coroutine.

    Handles plain coroutine functions, ``functools.partial`` wrappers, and
    callable objects whose ``__call__`` is ``async`` — cases that
    ``asyncio.iscoroutinefunction`` alone misses. Typed as a ``TypeGuard`` so
    callers can ``await`` the narrowed callable without a cast.
    """
    while isinstance(obj, functools.partial):
        obj = obj.func
    return inspect.iscoroutinefunction(obj) or (
        callable(obj) and inspect.iscoroutinefunction(obj.__call__)
    )


# Overall-status severity, highest to lowest: CONFIGURATION_ERROR > FAIL
# > DEGRADED > OK. A configuration error means the check itself is broken, so it
# outranks a real outage.
_SEVERITY: dict[Status, int] = {
    Status.OK: 0,
    Status.DEGRADED: 1,
    Status.FAIL: 2,
    Status.CONFIGURATION_ERROR: 3,
}


def worst_of(check_results: list[CheckResult]) -> Status:
    """Aggregate individual check results into a single overall status.

    A check reports ``OK``, ``FAIL`` or ``CONFIGURATION_ERROR``. The ``critical``
    flag decides how a problem escalates: a **critical** failure or misconfiguration
    contributes its own status (``FAIL`` / ``CONFIGURATION_ERROR``), while a
    **non-critical** one only contributes ``DEGRADED`` — so a broken non-critical
    dependency never takes the whole endpoint to a 5xx. The overall status is the
    most severe contribution.
    """
    global_status = Status.OK

    for check_result in check_results:
        if check_result.status == Status.OK:
            continue
        # FAIL or CONFIGURATION_ERROR: escalate only if the check is critical.
        contribution = check_result.status if check_result.critical else Status.DEGRADED
        if _SEVERITY[contribution] > _SEVERITY[global_status]:
            global_status = contribution
    return global_status
