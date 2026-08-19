import asyncio
import logging
from collections.abc import Callable
from time import monotonic, perf_counter
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query
from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, JSONResponse, Response

from fastapi_status_page.enums import ResponseFormat, Status
from fastapi_status_page.exceptions import ConfigurationError
from fastapi_status_page.models import Check, CheckFunc, CheckResponse, CheckResult
from fastapi_status_page.rendering import render_html
from fastapi_status_page.utils import is_async_callable, worst_of

logger = logging.getLogger("fastapi_status_page")

# HTTP status code per overall status. Degraded still serves traffic (200);
# a real outage is 503; a broken check (misconfiguration) is a server error.
_STATUS_CODES: dict[Status, int] = {
    Status.OK: 200,
    Status.DEGRADED: 200,
    Status.FAIL: 503,
    Status.CONFIGURATION_ERROR: 500,
}


class StatusPage:
    def __init__(
        self,
        app: FastAPI | APIRouter,
        *,
        global_timeout: float = 5,
        default_format: ResponseFormat = ResponseFormat.JSON,
        enable_errors: bool = True,
        service_name: str = "Service",
        path: str = "/status"
    ):
        self._checks: dict[str, Check] = {}
        self._global_timeout = global_timeout
        self._default_format = default_format
        self._enable_errors = enable_errors
        self._service_name = service_name

        # Mount endpoint
        app.add_api_route(path, self._endpoint)

    def add_check(
        self,
        func: CheckFunc,
        name: str,
        *,
        timeout: float | None = None,
        critical: bool = True,
        cache_ttl: float | None = None,
    ) -> None:
        """Register a health check.

        ``func`` may be async or a plain sync callable returning ``bool``; sync
        checks run in a threadpool. Note: ``timeout`` stops *waiting* on a sync
        check but cannot cancel the underlying thread — a hung sync check keeps
        occupying a worker thread, so give such checks their own internal timeout.
        """
        if name in self._checks:
            raise ValueError(f"Check with name {name} already exists")
        self._checks[name] = Check(
            func=func, timeout=timeout, critical=critical, cache_ttl=cache_ttl
        )

    def register_check(
        self,
        name: str,
        *,
        timeout: float | None = None,
        critical: bool = True,
        cache_ttl: float | None = None,
    ) -> Callable[[CheckFunc], CheckFunc]:
        def decorator(func: CheckFunc) -> CheckFunc:
            self.add_check(func, name, timeout=timeout, critical=critical, cache_ttl=cache_ttl)
            return func

        return decorator

    async def _endpoint(
        self,
        format: Annotated[ResponseFormat | None, Query(alias="format")] = None,
    ) -> Response:
        results = await asyncio.gather(
            *(self._run_one(name, check) for name, check in self._checks.items())
        )
        overall = worst_of(results)
        response = CheckResponse(status=overall, checks=results)
        status_code = _STATUS_CODES[overall]

        if (format or self._default_format) == ResponseFormat.HTML:
            return HTMLResponse(
                content=render_html(response, service_name=self._service_name),
                status_code=status_code,
            )
        return JSONResponse(content=response.model_dump(), status_code=status_code)

    async def _run_one(self, name: str, check: Check) -> CheckResult:
        if check._cached is not None and monotonic() < check._expires_at:
            return check._cached

        # Single-flight: coalesce concurrent misses onto one execution instead
        # of serializing them on the lock and re-running the check per request.
        # The lock is only held to inspect the cache and hand out the shared
        # task — never while the check itself runs.
        async with check._lock:
            if check._cached is not None and monotonic() < check._expires_at:
                return check._cached

            if check._inflight is None:
                check._inflight = asyncio.create_task(self._run_and_store(name, check))
            task = check._inflight

        return await task

    async def _run_and_store(self, name: str, check: Check) -> CheckResult:
        try:
            result = await self._execute(name, check)

            if check.cache_ttl is not None and result.status == Status.OK:
                check._cached = result
                check._expires_at = monotonic() + check.cache_ttl
            else:
                check._cached = None  # never cache non-OK
            return result
        finally:
            async with check._lock:
                check._inflight = None

    async def _execute(self, name: str, check: Check) -> CheckResult:
        start = perf_counter()
        timeout = self._global_timeout if check.timeout is None else check.timeout
        try:
            async with asyncio.timeout(timeout):
                if is_async_callable(check.func):
                    ok = await check.func()
                else:
                    ok = await run_in_threadpool(check.func)

            # TODO Validate response from function (either bool or custom response).
            if not isinstance(ok, bool):
                raise ConfigurationError(f"Invalid response from dependency check - {name}")

            status = Status.OK if ok else Status.FAIL
            error = None
        except TimeoutError:
            status, error = Status.FAIL, "Timeout"
            if not is_async_callable(check.func):
                # A threadpool worker cannot be cancelled: the sync check keeps
                # running in the background even though we stopped waiting.
                logger.warning(
                    "Sync check %r exceeded its %.3gs timeout; its worker thread "
                    "cannot be cancelled and may keep running. Give sync checks "
                    "their own internal timeout.",
                    name,
                    timeout,
                )
        except ConfigurationError as e:
            status, error = Status.CONFIGURATION_ERROR, str(e)
        except Exception as exc:
            status, error = Status.FAIL, str(exc) if self._enable_errors else "Unknown error"
        return CheckResult(
            name=name,
            status=status,
            error=error,
            duration_ms=round((perf_counter() - start) * 1000, 2),
            critical=check.critical,
        )
