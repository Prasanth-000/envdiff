"""Utility helpers for envdiff: line parsing, path safety, XDG resolution."""

from __future__ import annotations

import os
import re
from pathlib import Path

# Matches: KEY=VALUE  (optional surrounding quotes, trailing comment after #)
_ENV_LINE_RE = re.compile(
    r"""^\s*                      # leading whitespace
        (?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*  # identifier
        =                              # equals
        (?P<value>\S.*?)?\s*           # value (may be empty)
        (?P<comment>(?<!\\)\#.*)?\s*$ # optional trailing comment
    """,
    re.VERBOSE,
)

_SHELL_LINE_RE = re.compile(
    r"""^\s*export\s+
        (?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*
        (?P<value>.*?)\s*$""",
    re.VERBOSE,
)

_VAR_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse a single ``KEY=VALUE`` line.

    Returns ``(key, value)`` or ``None`` for blanks / comments / malformed lines.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = _ENV_LINE_RE.match(line)
    if not match:
        return None
    key = match.group("key")
    value = match.group("value") or ""
    return key, strip_quotes(value)


def strip_quotes(value: str) -> str:
    """Remove a single layer of surrounding single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def expand_env_value(value: str, env: dict[str, str]) -> str:
    """Expand ``${VAR}`` / ``$VAR`` references using the provided ``env`` dict.

    Unknown variables expand to an empty string (mirrors shell behaviour).
    """

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return env.get(name, "")

    return _VAR_REF_RE.sub(_replace, value)


def get_xdg_data_home() -> Path:
    """Return ``$XDG_DATA_HOME`` or the ``~/.local/share`` fallback."""
    raw = os.environ.get("XDG_DATA_HOME")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".local" / "share"


def is_safe_path(path: Path | str) -> bool:
    """Return True if ``path`` resolves inside an allowed root.

    Allowed roots: home directory, system temp dir, current working
    directory, and ``$XDG_DATA_HOME``. This prevents the tool from writing
    reports to arbitrary system locations.
    """
    resolved = Path(path).resolve(strict=False)
    allowed = [
        Path.home().resolve(),
        Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
        Path.cwd().resolve(),
        get_xdg_data_home().resolve(),
    ]
    for root in allowed:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False
