"""Example FastAPI app wired up with fastapi-status-page.

Run it with::

    uv run uvicorn examples.simple_app:app --reload

Then hit the status page::

    curl -s localhost:8000/status | python -m json.tool

The checks below are *simulated* — no real database or network is required — so
the example runs anywhere. They are arranged to exercise every state the status
page can report:

* ``database``     -> healthy async check          (critical, cached for 15s)
* ``redis``        -> healthy sync check            (critical, runs in a threadpool)
* ``payments_api`` -> failing check, non-critical   -> overall "degraded"
* ``reporting``    -> exceeds its per-check timeout  -> reported as a timeout

With the defaults the critical checks pass, so the overall status is
``degraded`` (HTTP 200). Flip ``SIMULATE_FAILURE`` to make the critical
``database`` check fail and take the whole page to ``fail`` (HTTP 503).
"""

import asyncio

from fastapi import FastAPI

from fastapi_status_page import StatusPage

# Toggle to make the critical "database" check fail and see the page go to
# fail / HTTP 503 instead of a non-critical "degraded".
SIMULATE_FAILURE = False

app = FastAPI(title="fastapi-status-page example")

# global_timeout is the fallback for checks that don't set their own.
status_page = StatusPage(app, global_timeout=5.0, service_name="Example Service")


@app.get("/")
async def index() -> dict[str, str]:
    return {"hello": "world", "status_page": "/status"}


@status_page.register_check("database", cache_ttl=15)
async def check_database() -> bool:
    """Pretend to run ``SELECT 1`` against a database."""
    await asyncio.sleep(0.05)  # simulate a round-trip
    return not SIMULATE_FAILURE


@status_page.register_check("redis")
def check_redis() -> bool:
    """A synchronous check — the status page runs it in a threadpool."""
    # e.g. redis_client.ping()
    return True


@status_page.register_check("payments_api", critical=False)
async def check_payments_api() -> bool:
    """A non-critical dependency that is currently down.

    Because it is non-critical, its failure marks the page as *degraded* but the
    endpoint still returns HTTP 200.
    """
    await asyncio.sleep(0.02)
    return False


@status_page.register_check("reporting", timeout=0.25, critical=False)
async def check_reporting() -> bool:
    """Takes longer than its 0.25s timeout -> reported as a timeout failure."""
    await asyncio.sleep(1.0)
    return True


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("examples.simple_app:app", host="127.0.0.1", port=8000, reload=True)
