from pathlib import Path

from envdiff.utils import (
    expand_env_value,
    get_xdg_data_home,
    is_safe_path,
    parse_env_line,
    strip_quotes,
)


def test_parse_env_line_basic():
    assert parse_env_line("FOO=bar") == ("FOO", "bar")


def test_parse_env_line_quoted():
    assert parse_env_line('KEY="hello world"') == ("KEY", "hello world")
    assert parse_env_line("KEY='single'") == ("KEY", "single")


def test_parse_env_line_comment():
    assert parse_env_line("API=1 # trailing comment") == ("API", "1")


def test_parse_env_line_blank_and_comment_lines():
    assert parse_env_line("") is None
    assert parse_env_line("   ") is None
    assert parse_env_line("# just a comment") is None


def test_parse_env_line_malformed():
    assert parse_env_line("no equals sign") is None
    assert parse_env_line("1BAD=key") is None


def test_strip_quotes():
    assert strip_quotes('"x"') == "x"
    assert strip_quotes("'x'") == "x"
    assert strip_quotes("x") == "x"
    assert strip_quotes('""') == ""


def test_expand_env_value():
    env = {"BASE": "/opt", "NAME": "app"}
    assert expand_env_value("${BASE}/$NAME", env) == "/opt/app"
    assert expand_env_value("$MISSING", env) == ""


def test_get_xdg_data_home(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/share")
    assert get_xdg_data_home() == Path("/custom/share")


def test_get_xdg_data_home_fallback(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    assert get_xdg_data_home() == Path.home() / ".local" / "share"


def test_is_safe_path_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    # A path inside a faked home should be safe.
    target = tmp_path / "out" / "report.json"
    assert is_safe_path(target) is True


def test_is_safe_path_rejects_system(tmp_path):
    # /etc is outside allowed roots.
    assert is_safe_path("/etc/passwd") is False
