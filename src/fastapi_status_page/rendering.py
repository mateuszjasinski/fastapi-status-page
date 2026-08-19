"""HTML rendering for the status page.

Kept separate from :mod:`fastapi_status_page.page` so the presentation layer
can evolve independently of the check/aggregation logic. To avoid a circular
import, this module keys everything off the *string* status value
(``status.value``) rather than importing the ``Status`` enum at runtime; the
model types are only referenced for type checking.
"""

from __future__ import annotations

import html as html_lib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi_status_page.models import CheckResponse

# Per-status palette (color / background / border / focus ring), keyed by the
# serialized status value so we stay decoupled from the Status enum.
_PALETTE: dict[str, dict[str, str]] = {
    "ok": {"color": "#1a8f4c", "bg": "#e9f6ee", "border": "#c3e6d1", "ring": "#d4efdd"},
    "fail": {"color": "#c73338", "bg": "#fceceb", "border": "#f2c9c8", "ring": "#f7dedd"},
    "degraded": {"color": "#9a5a12", "bg": "#fbf1e2", "border": "#f0dcbd", "ring": "#f5e6cf"},
    "configuration_error": {
        "color": "#8a4fbf",
        "bg": "#f4edfb",
        "border": "#e3d3f2",
        "ring": "#ece0f7",
    },
    "unknown": {"color": "#6b6d7c", "bg": "#f1f1f5", "border": "#e0e0e8", "ring": "#eaeaef"},
}

_LABELS = {
    "ok": "Operational",
    "fail": "Failing",
    "degraded": "Degraded",
    "configuration_error": "Misconfigured",
    "unknown": "Unknown",
}

# Self-contained: only system font stacks, so the page renders identically
# offline / air-gapped and makes no external requests (no CDN, CSP-friendly).
_SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
_MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace"

_HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service status</title>
<style>
  body { margin: 0; }
  *, *::before, *::after { box-sizing: border-box; }
</style>"""


def _palette_for(status_value: str) -> dict[str, str]:
    return _PALETTE.get(status_value, _PALETTE["unknown"])


def _th(label: str, align: str = "left") -> str:
    return (
        f'<th style="text-align: {align}; font-size: 11px; font-weight: 600; '
        "letter-spacing: 0.06em; text-transform: uppercase; color: #8a8c99; "
        f'padding: 12px 16px; border-bottom: 1px solid #ececf2;">{label}</th>'
    )


def _render_row(
    name: str, status_value: str, critical: bool, duration_ms: float, error: str | None
) -> str:
    pal = _palette_for(status_value)
    status_label = _LABELS.get(status_value, status_value.replace("_", " ").title())
    critical_label = "Yes" if critical else "No"
    critical_color = "#3a3c49" if critical else "#a0a2ae"
    error_text = html_lib.escape(error) if error else "—"

    return (
        '<tr style="border-bottom: 1px solid #f2f2f6;">'
        f'<td style="padding: 14px 16px; border-left: 3px solid {pal["color"]};">'
        f'<span style="font-family: {_MONO}; font-weight: 500; font-size: 14px;">'
        f"{html_lib.escape(name)}</span></td>"
        '<td style="padding: 14px 16px;">'
        '<span style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; '
        f"font-weight: 600; letter-spacing: 0.02em; color: {pal['color']}; background: {pal['bg']}; "
        f"border: 1px solid {pal['border']}; padding: 3px 10px; border-radius: 999px; "
        'text-transform: uppercase;">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background: {pal["color"]};">'
        f"</span>{status_label}</span></td>"
        f'<td style="padding: 14px 16px; color: {critical_color}; font-weight: 500;">{critical_label}</td>'
        f'<td style="padding: 14px 16px; text-align: right; font-family: {_MONO}; color: #3a3c49;">'
        f"{duration_ms:.1f} ms</td>"
        f'<td style="padding: 14px 16px; color: #b5312f; font-family: {_MONO}; font-size: 13px;">'
        f"{error_text}</td>"
        "</tr>"
    )


def render_html(
    response: CheckResponse, *, service_name: str = "service", checked_at: datetime | None = None
) -> str:
    """Render a :class:`CheckResponse` as a standalone HTML status page."""
    if checked_at is None:
        checked_at = datetime.now(UTC)
    checked_full = checked_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    overall_value = response.status.value
    opal = _palette_for(overall_value)
    overall_label = _LABELS.get(overall_value, overall_value.replace("_", " ").title())

    total = len(response.checks)
    passing = sum(1 for c in response.checks if c.status.value == "ok")
    summary = f"{passing} / {total} passing"

    rows = "".join(
        _render_row(c.name, c.status.value, c.critical, c.duration_ms, c.error)
        for c in response.checks
    )

    header_cells = "".join(
        [
            _th("Check"),
            _th("Status"),
            _th("Critical"),
            _th("Duration", "right"),
            _th("Error"),
        ]
    )

    body = f"""<div style="min-height: 100vh; background: #f5f5f8; font-family: {_SANS}; color: #1a1b23; padding: 40px 20px; -webkit-font-smoothing: antialiased;">
  <div style="max-width: 940px; margin: 0 auto;">

    <div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 20px;">
      <div>
        <div style="font-size: 12px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: #8a8c99;">{html_lib.escape(service_name)}</div>
        <div style="font-size: 22px; font-weight: 600; margin-top: 4px; letter-spacing: -0.01em;">Service status</div>
      </div>
      <div style="font-size: 13px; color: #6b6d7c; text-align: right;">
        <div style="letter-spacing: 0.04em; text-transform: uppercase; font-size: 11px; font-weight: 500; color: #a0a2ae;">Last checked</div>
        <div style="margin-top: 2px; font-family: {_MONO}; font-size: 13px; color: #4a4c59;">{checked_full}</div>
      </div>
    </div>

    <div style="display: flex; align-items: center; gap: 14px; background: {opal["bg"]}; border: 1px solid {opal["border"]}; border-radius: 10px; padding: 18px 22px; margin-bottom: 28px;">
      <span style="width: 12px; height: 12px; border-radius: 50%; background: {opal["color"]}; box-shadow: 0 0 0 4px {opal["ring"]}; flex: none;"></span>
      <div style="flex: 1; min-width: 0;">
        <div style="font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: #8a8c99;">Overall status</div>
        <div style="font-size: 20px; font-weight: 600; color: {opal["color"]}; margin-top: 2px; letter-spacing: -0.01em;">{overall_label}</div>
      </div>
      <div style="font-size: 13px; color: #6b6d7c; font-family: {_MONO}; white-space: nowrap;">{summary}</div>
    </div>

    <div style="background: #ffffff; border: 1px solid #e7e7ee; border-radius: 10px; overflow: hidden;">
      <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
          <tr style="background: #fafafc;">{header_cells}</tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

  </div>
</div>"""

    return f'<!DOCTYPE html>\n<html lang="en">\n<head>\n{_HEAD}\n</head>\n<body>\n{body}\n</body>\n</html>'
