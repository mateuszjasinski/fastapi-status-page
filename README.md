# fastapi-status-page

A simple, extensible status page for [FastAPI](https://fastapi.tiangolo.com/)
applications. Exposes a `/status` endpoint and lets you register health checks
for your dependencies — databases, caches, external services, and anything else
your app relies on.

> ⚠️ **Scaffolding only.** This repository currently contains project setup,
> tooling, and test configuration. No functionality is implemented yet.

## Planned usage

```python
from fastapi import FastAPI
from fastapi_status_page import StatusPage

app = FastAPI()
status = StatusPage(app)  # mounts GET /status


@status.check("database")
async def check_database() -> bool: ...


@status.check("redis")
async def check_redis() -> bool: ...
```

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
