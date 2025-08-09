from pathlib import Path

from cntkn.config import _read_toml


def test_read_toml_missing_returns_empty(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"
    assert _read_toml(missing) == {}
