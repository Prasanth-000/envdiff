"""Core diffing logic for envdiff."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path

from .utils import parse_env_line


class SourceType(enum.Enum):
    """How two sources should be interpreted."""

    FILE_FILE = "file:file"
    FILE_SHELL = "file:shell"
    DIR_DIR = "dir:dir"


@dataclass
class DiffResult:
    """Result of comparing two environment dictionaries."""

    added: dict[str, str] = field(default_factory=dict)
    removed: dict[str, str] = field(default_factory=dict)
    changed: dict[str, tuple[str, str]] = field(default_factory=dict)
    unchanged: dict[str, str] = field(default_factory=dict)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def is_clean(self) -> bool:
        return self.total_changes == 0


def load_env_file(path: Path | str) -> dict[str, str]:
    """Parse a ``.env`` file into a dict.

    Supports ``KEY=VALUE``, ``# comments``, blank lines, and quoted values.
    """
    result: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8")
    for line in text.splitlines():
        parsed = parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        # Last definition wins, mirroring shell behaviour.
        result[key] = value
    return result


def load_shell_export(text: str) -> dict[str, str]:
    """Parse ``export KEY=VALUE`` lines from arbitrary shell text."""
    import re

    result: dict[str, str] = {}
    pattern = re.compile(
        r"""^\s*export\s+
            (?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*
            (?P<value>.*?)\s*$""",
        re.VERBOSE,
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key = match.group("key")
        value = match.group("value") or ""
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        result[key] = value
    return result


def load_env_dir(path: Path | str) -> dict[str, str]:
    """Merge all ``.env`` files in a directory (sorted by filename)."""
    base = Path(path)
    merged: dict[str, str] = {}
    for env_file in sorted(base.glob("*.env")):
        if env_file.is_file():
            merged.update(load_env_file(env_file))
    # Also pick up a plain `.env` if present.
    dot_env = base / ".env"
    if dot_env.is_file():
        merged.update(load_env_file(dot_env))
    return merged


def compute_diff(left: dict[str, str], right: dict[str, str]) -> DiffResult:
    """Compare two env dicts. ``left`` is the base, ``right`` is the target.

    - added: present in right, absent in left
    - removed: present in left, absent in right
    - changed: present in both, different values
    - unchanged: present in both, identical values
    """
    added: dict[str, str] = {}
    removed: dict[str, str] = {}
    changed: dict[str, tuple[str, str]] = {}
    unchanged: dict[str, str] = {}

    left_keys = set(left)
    right_keys = set(right)

    for key in sorted(right_keys - left_keys):
        added[key] = right[key]
    for key in sorted(left_keys - right_keys):
        removed[key] = left[key]
    for key in sorted(left_keys & right_keys):
        if left[key] == right[key]:
            unchanged[key] = left[key]
        else:
            changed[key] = (left[key], right[key])

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)
