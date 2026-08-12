from envdiff.core import (
    SourceType,
    compute_diff,
    load_env_dir,
    load_env_file,
    load_shell_export,
)


def test_load_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("A=1\nB='two'\n# comment\nC=3\n\n", encoding="utf-8")
    result = load_env_file(f)
    assert result == {"A": "1", "B": "two", "C": "3"}


def test_load_env_file_last_wins(tmp_path):
    f = tmp_path / ".env"
    f.write_text("K=first\nK=second\n", encoding="utf-8")
    assert load_env_file(f) == {"K": "second"}


def test_load_shell_export():
    text = 'export FOO=bar\n# note\nexport BAZ="qux"\necho hi\n'
    result = load_shell_export(text)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_load_env_dir(tmp_path):
    (tmp_path / "a.env").write_text("X=1\n", encoding="utf-8")
    (tmp_path / "b.env").write_text("Y=2\n", encoding="utf-8")
    (tmp_path / ".env").write_text("Z=3\n", encoding="utf-8")
    result = load_env_dir(tmp_path)
    assert result == {"X": "1", "Y": "2", "Z": "3"}


def test_compute_diff_added_removed_changed_unchanged():
    left = {"A": "1", "B": "2", "C": "3"}
    right = {"A": "1", "B": "20", "D": "4"}
    result = compute_diff(left, right)
    assert result.unchanged == {"A": "1"}
    assert result.changed == {"B": ("2", "20")}
    assert result.removed == {"C": "3"}
    assert result.added == {"D": "4"}
    assert result.total_changes == 3
    assert not result.is_clean()


def test_compute_diff_clean():
    left = {"A": "1"}
    right = {"A": "1"}
    result = compute_diff(left, right)
    assert result.is_clean()
    assert result.total_changes == 0


def test_source_type_values():
    assert SourceType("file:file") == SourceType.FILE_FILE
    assert SourceType("file:shell") == SourceType.FILE_SHELL
    assert SourceType("dir:dir") == SourceType.DIR_DIR
