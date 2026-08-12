"""Typer CLI entry point for envdiff."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from . import __version__
from .core import (
    SourceType,
    compute_diff,
    load_env_dir,
    load_env_file,
    load_shell_export,
)
from .formatters import format_json, format_markdown, format_terminal_table
from .output import write_json_file, write_markdown_file, write_terminal

app = typer.Typer(
    add_completion=False,
    help="Compare two environment-variable sources and report the drift.",
)


def _version_callback(value: bool) -> None:
    if value:
        sys.stdout.write(f"envdiff {__version__}\n")
        raise typer.Exit(0)


def _resolve_source_type(value: str) -> SourceType:
    try:
        return SourceType(value)
    except ValueError:
        valid = ", ".join(t.value for t in SourceType)
        raise typer.BadParameter(f"--type must be one of: {valid}") from None


def _load_left(source: str, source_type: SourceType) -> dict[str, str]:
    if source_type in (SourceType.FILE_FILE, SourceType.FILE_SHELL):
        return load_env_file(source)
    return load_env_dir(source)


def _load_right(source: str, source_type: SourceType) -> dict[str, str]:
    if source_type == SourceType.FILE_FILE:
        return load_env_file(source)
    if source_type == SourceType.FILE_SHELL:
        return load_shell_export(Path(source).read_text(encoding="utf-8"))
    return load_env_dir(source)


@app.command()
def main(
    source_a: str = typer.Argument(
        ..., help="Base source: .env file, shell text file, or .env dir."
    ),
    source_b: str = typer.Argument(
        ..., help="Target source: .env file, shell text file, or .env dir."
    ),
    type: str = typer.Option(
        "file:file",
        "--type",
        "-t",
        help="Source interpretation: file:file | file:shell | dir:dir.",
    ),
    json_path: Path | None = typer.Option(
        None, "--json", "-j", help="Write a JSON report to this path ('-' for stdout)."
    ),
    markdown_path: Path | None = typer.Option(
        None, "--markdown", "-m", help="Write a Markdown report to this path."
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI colour in terminal output."
    ),
    version: bool | None = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """Detect environment-variable drift between two sources in one command."""
    color = not no_color
    source_type = _resolve_source_type(type)

    left = _load_left(source_a, source_type)
    right = _load_right(source_b, source_type)
    result = compute_diff(left, right)

    write_terminal(format_terminal_table(result, color=color), color=color)

    if json_path is not None:
        write_json_file(json_path, format_json(result))
    if markdown_path is not None:
        write_markdown_file(markdown_path, format_markdown(result))


if __name__ == "__main__":  # pragma: no cover
    main()
