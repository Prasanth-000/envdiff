"""Output layer: write terminal text and report files safely.

Raw machine output (JSON / Markdown) is written with ``sys.stdout.write``
or ``Path.write_text`` — never through ``rich.console.print``, which would
corrupt markup / colour codes in piped output.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .utils import is_safe_path


def validate_output_path(path: Path | str) -> Path:
    """Confine an output path to allowed roots.

    Raises ``ValueError`` if the path resolves outside home / tmp / cwd /
    XDG-data roots.
    """
    resolved = Path(path).resolve(strict=False)
    if not is_safe_path(resolved):
        raise ValueError(
            f"Output path '{resolved}' is outside allowed roots " "(home, tmp, cwd, XDG_DATA_HOME)."
        )
    return resolved


def write_terminal(text: str, color: bool = True) -> None:
    """Print a human report to stdout. Colour is handled by the caller's text."""
    sys.stdout.write(text + "\n")


def write_json_file(path: Path | str, data: str) -> None:
    """Write raw JSON to a file, or to stdout when ``path`` is ``-``."""
    if str(path) == "-":
        sys.stdout.write(data + "\n")
        return
    safe = validate_output_path(path)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(data + "\n", encoding="utf-8")


def write_markdown_file(path: Path | str, data: str) -> None:
    """Write a Markdown report to a (validated) file."""
    safe = validate_output_path(path)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(data + "\n", encoding="utf-8")
