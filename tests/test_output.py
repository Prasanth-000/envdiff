from pathlib import Path

import pytest

from envdiff.core import DiffResult
from envdiff.formatters import format_json
from envdiff.output import (
    validate_output_path,
    write_json_file,
    write_markdown_file,
    write_terminal,
)


def test_validate_output_path_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert validate_output_path("report.json") == (tmp_path / "report.json")


def test_validate_output_path_rejects_system(tmp_path):
    with pytest.raises(ValueError):
        validate_output_path("/etc/secret.json")


def test_write_terminal(capsys):
    write_terminal("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_write_json_file_to_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = DiffResult(added={"K": "v"})
    write_json_file(Path("out.json"), format_json(result))
    content = (tmp_path / "out.json").read_text(encoding="utf-8")
    assert "K" in content


def test_write_json_file_stdout(capsys):
    write_json_file("-", '{"a": 1}')
    assert capsys.readouterr().out == '{"a": 1}\n'


def test_write_markdown_file_rejects_unsafe(tmp_path):
    with pytest.raises(ValueError):
        write_markdown_file("/etc/out.md", "# x")
