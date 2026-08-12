from pathlib import Path

from typer.testing import CliRunner

from envdiff.cli import app

runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_cli_file_file_basic(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    _write(a, "X=1\nY=2\n")
    _write(b, "X=1\nY=20\nZ=3\n")
    result = runner.invoke(app, [str(a), str(b)])
    assert result.exit_code == 0
    assert "+ ADDED" in result.stdout
    assert "Z=3" in result.stdout
    assert "~ Y: 2  ->  20" in result.stdout


def test_cli_json_stdout_is_clean(tmp_path):
    # When --json - writes to stdout, the human table must NOT also print.
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    _write(a, "X=1\n")
    _write(b, "X=2\n")
    result = runner.invoke(app, [str(a), str(b), "--json", "-", "--no-color"])
    assert result.exit_code == 0
    out = result.stdout
    # Terminal table header must be absent when JSON goes to stdout.
    assert "envdiff — environment drift report" not in out
    # Output must be valid, jq-parseable JSON only.
    import json

    data = json.loads(out)
    assert data["changed"] == {"X": {"old": "1", "new": "2"}}


def test_cli_json_file(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    out = tmp_path / "report.json"
    _write(a, "X=1\n")
    _write(b, "X=2\n")
    result = runner.invoke(app, [str(a), str(b), "--json", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert '"changed"' in out.read_text(encoding="utf-8")


def test_cli_markdown_file(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    out = tmp_path / "report.md"
    _write(a, "X=1\n")
    _write(b, "X=2\n")
    result = runner.invoke(app, [str(a), str(b), "--markdown", str(out)])
    assert result.exit_code == 0
    assert "# envdiff report" in out.read_text(encoding="utf-8")


def test_cli_file_shell(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "exports.sh"
    _write(a, "X=1\n")
    _write(b, "export X=1\nexport Y=2\n")
    result = runner.invoke(app, [str(a), str(b), "--type", "file:shell"])
    assert result.exit_code == 0
    assert "Y=2" in result.stdout


def test_cli_dir_dir(tmp_path):
    da = tmp_path / "da"
    db = tmp_path / "db"
    da.mkdir()
    db.mkdir()
    _write(da / "x.env", "X=1\n")
    _write(db / "x.env", "X=1\n")
    _write(db / "y.env", "Y=2\n")
    result = runner.invoke(app, [str(da), str(db), "--type", "dir:dir"])
    assert result.exit_code == 0
    assert "Y=2" in result.stdout


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.startswith("envdiff")


def test_cli_bad_type(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    _write(a, "X=1\n")
    _write(b, "X=2\n")
    result = runner.invoke(app, [str(a), str(b), "--type", "bogus"])
    assert result.exit_code != 0
