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


def worst_of(check_results: list[CheckResult]) -> Status:
    # Severity, highest to lowest: CONFIGURATION_ERROR > FAIL (critical)
    # > DEGRADED (non-critical fail) > OK. A configuration error means the
    # check itself is broken, so it outranks a real outage.
    global_status = Status.OK

    for check_result in check_results:
        if check_result.status == Status.CONFIGURATION_ERROR:
            return Status.CONFIGURATION_ERROR
        if check_result.status == Status.FAIL:
            if check_result.critical:
                global_status = Status.FAIL
            elif global_status != Status.FAIL:
                global_status = Status.DEGRADED
    return global_status
