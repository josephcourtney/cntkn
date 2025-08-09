from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


# "Configuration holder for cntkn; values are read-only at runtime."
@dataclass(frozen=True, slots=True)
class Config:
    default_model: str = "gpt-4o"
    color_mode: str = "auto"  # "auto" | "on" | "off"

    @staticmethod
    def _coerce_str(dct: dict[str, Any], key: str, default: str) -> str:
        value = dct.get(key, default)
        return value if isinstance(value, str) and value else default

    @staticmethod
    def _coerce_color(value: str, default: str = "auto") -> str:
        allowed = {"auto", "on", "off"}
        return value if value in allowed else default

    @classmethod
    def from_toml(cls, table: dict[str, Any]) -> Config:
        tool = table.get("tool", {})
        cntkn = tool.get("cntkn", {})
        default_model = cls._coerce_str(cntkn, "default_model", cls.default_model)
        color_raw = cls._coerce_str(cntkn, "color", cls.color_mode)
        return cls(default_model=default_model, color_mode=cls._coerce_color(color_raw))


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = path.read_bytes()
    return tomllib.loads(data.decode("utf-8"))


def _find_pyproject(start: Path) -> Path | None:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


@lru_cache(maxsize=16)
def load_config(cwd: Path | None = None) -> Config:
    """Load config from the nearest pyproject.toml with [tool.cntkn] table.

    Falls back to defaults if not present.
    """
    base = Config()  # defaults
    root = cwd or Path.cwd()
    pyproject = _find_pyproject(root)
    if pyproject is None:
        return base
    table = _read_toml(pyproject)
    return Config.from_toml(table)
