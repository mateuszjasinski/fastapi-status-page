# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-19

### Added

- `StatusPage` mounting a `/status` endpoint on a FastAPI app or router.
- Register health checks via the `@status.register_check(name, ...)` decorator or
  `status.add_check(name, func, ...)`.
- Async and sync checks (sync checks run in a threadpool).
- Per-check `timeout`, `critical` flag, and `cache_ttl` (successful results only,
  with single-flight coalescing of concurrent requests).
- Overall status aggregation mapped to HTTP codes: `ok`/`degraded` → 200,
  `fail` → 503, `configuration_error` → 500. Non-critical failures degrade
  instead of escalating to a 5xx.
- JSON response by default, styled self-contained HTML view via `?format=html`.
- Ships with `py.typed`.

[Unreleased]: https://github.com/mateuszjasinski/fastapi-status-page/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mateuszjasinski/fastapi-status-page/releases/tag/v0.1.0
