from __future__ import annotations

import tomllib
from importlib import resources
from typing import Any


def _load_bytes_from_package(rel_path: str) -> bytes:
    # We keep defaults inside the package so wheels/sdists carry them.
    pkg = "cntkn.resources"
    with resources.as_file(resources.files(pkg) / rel_path) as p:
        return p.read_bytes()


def package_defaults() -> dict[str, Any]:
    """Load defaults shipped with the package."""
    raw = _load_bytes_from_package("default.toml")
    return tomllib.loads(raw.decode("utf-8"))
