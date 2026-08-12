import json

from envdiff.core import DiffResult
from envdiff.formatters import (
    _strip_control_chars,
    format_json,
    format_markdown,
    format_terminal_table,
)

CLEAN = DiffResult(unchanged={"A": "1"})
DIRTY = DiffResult(
    added={"NEW": "v"},
    removed={"OLD": "x"},
    changed={"CH": ("a", "b")},
    unchanged={"A": "1"},
)


def test_strip_control_chars():
    assert _strip_control_chars("a\tb\nc") == "abc"
    assert _strip_control_chars("clean") == "clean"


def test_format_terminal_table_clean():
    out = format_terminal_table(CLEAN, color=False)
    assert "No drift detected" in out
    assert "ADDED" in out


def test_format_terminal_table_dirty_no_color():
    out = format_terminal_table(DIRTY, color=False)
    assert "+ NEW=v" in out
    assert "- OLD=x" in out
    assert "~ CH: a  ->  b" in out


def test_format_terminal_table_color_codes():
    out = format_terminal_table(DIRTY, color=True)
    assert "\033[" in out  # ANSI escape present


def test_format_json_structure():
    data = json.loads(format_json(DIRTY))
    assert data["added"] == {"NEW": "v"}
    assert data["changed"]["CH"] == {"old": "a", "new": "b"}
    assert data["summary"]["clean"] is False
    # total_changes sum
    assert data["summary"]["added"] + data["summary"]["removed"] + data["summary"]["changed"] == 3


def test_format_json_strips_control_chars():
    dirty = DiffResult(added={"K": "val\twith\ttab"}, removed={}, changed={}, unchanged={})
    data = json.loads(format_json(dirty))
    assert "\t" not in data["added"]["K"]


def test_format_markdown():
    md = format_markdown(DIRTY)
    assert "# envdiff report" in md
    assert "## Added" in md
    assert "## Removed" in md
    assert "## Changed" in md
    assert "| Key | Old | New |" in md
