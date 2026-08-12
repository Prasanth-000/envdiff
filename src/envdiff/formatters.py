"""Formatters: terminal table, JSON, Markdown. All machine output is raw
(newline-terminated) and uses ``sys.stdout.write`` at the output layer."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

from .core import DiffResult

_CONTROL_RE = re.compile(r"[\x00-\x1f]")


def _strip_control_chars(text: str) -> str:
    """Remove ASCII control characters (``[\\x00-\\x1f]``) from a string."""
    return _CONTROL_RE.sub("", text)


def _sanitize(obj: Any) -> Any:
    """Recursively strip control chars from all string values."""
    if isinstance(obj, str):
        return _strip_control_chars(obj)
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def _to_dict(result: DiffResult) -> dict[str, Any]:
    """Convert a DiffResult into a JSON-serialisable dict."""
    return {
        "added": result.added,
        "removed": result.removed,
        "changed": {k: {"old": v[0], "new": v[1]} for k, v in result.changed.items()},
        "unchanged": result.unchanged,
        "summary": {
            "added": len(result.added),
            "removed": len(result.removed),
            "changed": len(result.changed),
            "unchanged": len(result.unchanged),
            "clean": result.is_clean(),
        },
    }


# ANSI colour helpers (only applied when colour is enabled)
_RESET = "\033[0m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"


def _c(text: str, code: str, color: bool) -> str:
    if not color:
        return text
    return f"{code}{text}{_RESET}"


def format_terminal_table(result: DiffResult, color: bool = True) -> str:
    """Render a human-readable, sectioned terminal report."""
    lines: list[str] = []
    lines.append(_c("envdiff — environment drift report", _BOLD, color))
    lines.append("")
    lines.append(_c(f"  + ADDED    : {len(result.added)}", _GREEN, color))
    lines.append(_c(f"  - REMOVED  : {len(result.removed)}", _RED, color))
    lines.append(_c(f"  ~ CHANGED  : {len(result.changed)}", _YELLOW, color))
    lines.append(_c(f"  = UNCHANGED: {len(result.unchanged)}", _BLUE, color))
    lines.append("")

    if result.added:
        lines.append(_c("ADDED (present in target, missing from base):", _GREEN, color))
        for k in result.added:
            lines.append(f"  + {k}={result.added[k]}")
        lines.append("")

    if result.removed:
        lines.append(_c("REMOVED (present in base, missing from target):", _RED, color))
        for k in result.removed:
            lines.append(f"  - {k}={result.removed[k]}")
        lines.append("")

    if result.changed:
        lines.append(_c("CHANGED (value differs):", _YELLOW, color))
        for k in result.changed:
            old, new = result.changed[k]
            lines.append(f"  ~ {k}: {old}  ->  {new}")
        lines.append("")

    if result.is_clean():
        lines.append(_c("No drift detected. Sources are identical.", _BOLD, color))

    return "\n".join(lines)


def format_json(result: DiffResult) -> str:
    """Serialise the diff to a compact JSON string with control chars stripped."""
    payload = _sanitize(_to_dict(result))
    return json.dumps(payload, indent=2, sort_keys=True)


def format_markdown(result: DiffResult) -> str:
    """Render a Markdown report with one table per change category."""

    def _table(title: str, header: str, rows: Sequence[tuple[str, ...]]) -> str:
        out: list[str] = [f"## {title}", "", f"| {header} |", f"|{'-' * (len(header) + 2)}|"]
        for row in rows:
            out.append("| " + " | ".join(_strip_control_chars(c) for c in row) + " |")
        out.append("")
        return "\n".join(out)

    parts: list[str] = ["# envdiff report", ""]
    parts.append(
        f"ADDED: {len(result.added)} · "
        f"REMOVED: {len(result.removed)} · "
        f"CHANGED: {len(result.changed)} · "
        f"UNCHANGED: {len(result.unchanged)}"
    )
    parts.append("")

    if result.added:
        parts.append(_table("Added", "Key | Value", [(k, result.added[k]) for k in result.added]))
    if result.removed:
        rows = [(k, result.removed[k]) for k in result.removed]
        parts.append(_table("Removed", "Key | Value", rows))
    if result.changed:
        parts.append(
            _table(
                "Changed",
                "Key | Old | New",
                [(k, result.changed[k][0], result.changed[k][1]) for k in result.changed],
            )
        )
    if not result.total_changes:
        parts.append("No drift detected. Sources are identical.")

    return "\n".join(parts)
