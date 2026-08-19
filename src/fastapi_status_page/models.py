import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from pydantic import BaseModel

from fastapi_status_page.enums import Status

CheckFunc = Callable[[], bool | Awaitable[bool]]


class CheckResult(BaseModel):
    name: str
    status: Status
    duration_ms: float
    error: str | None
    critical: bool


class CheckResponse(BaseModel):
    status: Status
    checks: list[CheckResult]


@dataclass
class Check:
    func: CheckFunc
    timeout: float | None
    critical: bool
    cache_ttl: float | None

    _cached: "CheckResult | None" = field(default=None, init=False)
    _expires_at: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _inflight: "asyncio.Task[CheckResult] | None" = field(default=None, init=False)
