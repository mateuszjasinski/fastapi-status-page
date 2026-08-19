# Example: simple_app

A minimal FastAPI app that registers a few *simulated* dependency checks with
`fastapi-status-page`. No database or network is required — it runs anywhere.

## Run it

```bash
uv run uvicorn examples.simple_app:app --reload
```

Or directly:

```bash
uv run python -m examples.simple_app
```

## Try it

```bash
curl -s localhost:8000/status | python -m json.tool
```

With the defaults you get **HTTP 200** and an overall `degraded` status:
`database` and `redis` are healthy (critical), `payments_api` is a non-critical
failure, and `reporting` exceeds its 0.25s timeout (also non-critical). Because
no *critical* check failed, the page stays at `200`.

```json
{
  "status": "degraded",
  "checks": [
    { "name": "database",     "status": "ok",   "duration_ms": 51.2, "error": null,      "critical": true },
    { "name": "redis",        "status": "ok",   "duration_ms": 0.3,  "error": null,      "critical": true },
    { "name": "payments_api", "status": "fail", "duration_ms": 20.4, "error": null,      "critical": false },
    { "name": "reporting",    "status": "fail", "duration_ms": 250.1, "error": "Timeout", "critical": false }
  ]
}
```

(`duration_ms` values will differ from run to run.)

## HTML view

The status page can also render as an HTML page. Add `?format=html` (or open it
in a browser):

```bash
curl -s "localhost:8000/status?format=html"
```

To make HTML the default and let clients opt into JSON with `?format=json`,
construct the page with `StatusPage(app, default_format=ResponseFormat.HTML)`.

## See a critical failure (HTTP 503)

Set `SIMULATE_FAILURE = True` at the top of `simple_app.py` and reload. The
critical `database` check now fails, so the overall status becomes `fail` and
the endpoint returns **HTTP 503** — exactly what a load balancer or Kubernetes
readiness probe should act on.

## What each check demonstrates

| Check          | Kind  | Critical | Purpose                                     |
|----------------|-------|----------|---------------------------------------------|
| `database`     | async | yes      | Healthy critical dependency (cached for 15s)|
| `redis`        | sync  | yes      | Sync check (runs off the event loop)        |
| `payments_api` | async | no       | Non-critical failure -> degraded            |
| `reporting`    | async | no       | Per-check `timeout` -> reported as a timeout |
