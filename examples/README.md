# Example: simple_app

A minimal FastAPI app that registers a few *simulated* dependency checks with
`fastapi-status-page`. No database or network required — it runs anywhere.

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

With the defaults you'll get **HTTP 200** and an overall `degraded` status:
`database` and `cache` are healthy, `payments` is a non-critical failure, and
`slow_report` exceeds its 0.25s timeout.

```json
{
  "status": "yellow",
  "checks": [
    { "name": "database",    "status": "ok",   "critical": true,  "error": null },
    { "name": "cache",       "status": "ok",   "critical": true,  "error": null },
    { "name": "payments",    "status": "fail", "critical": false, "error": null },
    { "name": "slow_report", "status": "fail", "critical": false, "error": "Timeout" }
  ]
}
```

## HTML view

The status page can also render as an HTML page. Add `?format=html` (or open
it in a browser):

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

| Check         | Kind  | Critical | Purpose                                   |
|---------------|-------|----------|-------------------------------------------|
| `database`    | async | yes      | Healthy critical dependency               |
| `cache`       | sync  | yes      | Sync check (runs off the event loop)      |
| `payments`    | async | no       | Non-critical failure -> degraded          |
| `slow_report` | async | no       | Per-check `timeout` -> reported as timeout |
