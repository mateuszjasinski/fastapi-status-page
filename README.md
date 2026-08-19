# fastapi-status-page

[![CI](https://github.com/mateuszjasinski/fastapi-status-page/actions/workflows/ci.yml/badge.svg)](https://github.com/mateuszjasinski/fastapi-status-page/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

A simple, extensible status page for [FastAPI](https://fastapi.tiangolo.com/)
applications. Register health checks for your dependencies — databases, caches,
external APIs, anything your app relies on — and expose them on a single
`/status` endpoint as JSON or a ready-to-share HTML page.

Its main job is to give your infrastructure a truthful signal: the endpoint maps
your dependency health onto the right HTTP status code, so Kubernetes readiness
probes and load balancers can route traffic based on it out of the box.

![HTML status page](https://raw.githubusercontent.com/mateuszjasinski/fastapi-status-page/main/docs/screenshot.png)

## Features

- **Async & sync checks** — register `async def` checks or plain `def` ones;
  sync checks run in a threadpool so they never block the event loop.
- **Right HTTP status codes** — a healthy or degraded service returns `200`, a
  real outage returns `503`, and a broken check returns `500`. Perfect for
  Kubernetes probes and load balancer health checks.
- **Critical vs. non-critical dependencies** — a failing non-critical dependency
  marks the page *degraded* (still `200`) instead of taking you offline.
- **Per-check timeouts** — bound every check so one slow dependency cannot hang
  the endpoint.
- **Caching** — cache successful checks for a TTL to keep the endpoint cheap
  under frequent polling, with single-flight coalescing of concurrent requests.
- **JSON or HTML** — machine-readable JSON by default, a styled HTML page with
  `?format=html`.
- **Fully typed** — ships with `py.typed`; passes `mypy --strict`.

## Installation

```bash
pip install fastapi-status-page
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add fastapi-status-page
```

Requires Python 3.11+ and FastAPI 0.110+.

## Quickstart

```python
from fastapi import FastAPI
from fastapi_status_page import StatusPage

app = FastAPI()
status = StatusPage(app)  # mounts GET /status


@status.register_check("database")
async def check_database() -> bool:
    # Return True if the dependency is healthy, False otherwise.
    return await db.ping()


@status.register_check("redis", critical=False)
def check_redis() -> bool:
    # Sync checks are supported too — they run in a threadpool.
    return redis_client.ping()
```

Now `GET /status` returns:

```json
{
  "status": "ok",
  "checks": [
    { "name": "database", "status": "ok", "duration_ms": 1.87, "error": null, "critical": true },
    { "name": "redis",    "status": "ok", "duration_ms": 0.42, "error": null, "critical": false }
  ]
}
```

A check returns a plain `bool`: `True` means healthy, `False` means failing. Any
exception the check raises is caught and reported as a failure.

## How the overall status is decided

Each check produces a status, and the endpoint aggregates them into a single
overall status (worst wins) that determines the HTTP status code:

| Overall status        | When                                                        | HTTP |
|-----------------------|-------------------------------------------------------------|------|
| `ok`                  | Every check passed.                                          | 200  |
| `degraded`            | Only **non-critical** checks failed or are misconfigured.    | 200  |
| `fail`                | At least one **critical** check failed.                      | 503  |
| `configuration_error` | A **critical** check returned a non-`bool` value or errored during setup. | 500  |

This is why the default for a check is `critical=True`: a failing critical
dependency takes the endpoint to `503` so a load balancer stops routing to the
instance, while a failing non-critical dependency only reports `degraded` and
keeps serving traffic.

## Registering checks

There are two equivalent ways to register a check.

As a decorator:

```python
@status.register_check("database", timeout=2.0, critical=True, cache_ttl=15)
async def check_database() -> bool:
    return await db.ping()
```

Or imperatively, which is handy when the check is defined elsewhere:

```python
status.add_check("database", check_database, timeout=2.0, cache_ttl=15)
```

### Check options

Both `register_check` and `add_check` accept the same keyword arguments:

| Option      | Type            | Default | Description                                                                 |
|-------------|-----------------|---------|-----------------------------------------------------------------------------|
| `name`      | `str`           | —       | Unique name for the check. Registering the same name twice raises `ValueError`. |
| `timeout`   | `float \| None` | `None`  | Per-check timeout in seconds. Falls back to `global_timeout` when `None`.   |
| `critical`  | `bool`          | `True`  | Whether a failure marks the page `fail` (critical) or `degraded` (non-critical). |
| `cache_ttl` | `float \| None` | `None`  | Cache a **successful** result for this many seconds. `None` disables caching. |

> **Note on sync checks and timeouts.** `timeout` stops the endpoint from
> *waiting* on a sync check, but it cannot cancel the underlying worker thread —
> a hung sync check keeps occupying a thread in the background. Give sync checks
> their own internal timeout (e.g. a client-level socket timeout).

## Configuration

Configure the page when you construct it:

```python
from fastapi_status_page import StatusPage, ResponseFormat

status = StatusPage(
    app,
    path="/health",
    global_timeout=3.0,
    default_format=ResponseFormat.HTML,
    service_name="My API",
    enable_errors=False,
)
```

| Argument         | Type                        | Default               | Description                                                                 |
|------------------|-----------------------------|-----------------------|-----------------------------------------------------------------------------|
| `app`            | `FastAPI \| APIRouter`      | —                     | The app or router to mount the endpoint on.                                 |
| `path`           | `str`                       | `"/status"`           | Path the status endpoint is mounted at.                                     |
| `global_timeout` | `float`                     | `5`                   | Default timeout (seconds) for checks that don't set their own.              |
| `default_format` | `ResponseFormat`            | `ResponseFormat.JSON` | Format used when the request has no `?format=` query parameter.             |
| `service_name`   | `str`                       | `"Service"`           | Name shown on the HTML page.                                                |
| `enable_errors`  | `bool`                      | `True`                | Include exception messages in the response. Set `False` to avoid leaking internal details on a public endpoint. |

## HTML view

The endpoint renders a styled HTML page when you request it with
`?format=html`, or open it in a browser:

```bash
curl -s "localhost:8000/status?format=html"
```

To make HTML the default and let clients opt into JSON with `?format=json`,
pass `default_format=ResponseFormat.HTML` when constructing the page.

## Example

A runnable example lives in [`examples/`](./examples). It registers a few
simulated checks that exercise every status the page can report — no database or
network required:

```bash
uv run uvicorn examples.simple_app:app --reload
curl -s localhost:8000/status | python -m json.tool
```

See [`examples/README.md`](./examples/README.md) for a full walkthrough.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Create the environment and install dev dependencies
uv sync --extra dev

# Install git hooks
uv run pre-commit install

# Run the checks
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

## Tooling

- **Build/deps:** uv + hatchling
- **Lint/format:** Ruff
- **Types:** mypy (strict)
- **Tests:** pytest + pytest-asyncio + coverage
- **Hooks:** pre-commit
- **CI:** GitHub Actions (Python 3.11 – 3.13)

## License

[MIT](./LICENSE)
