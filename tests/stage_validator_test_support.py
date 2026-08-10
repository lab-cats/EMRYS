"""Neutral mechanics shared by independent stage-validator suites."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_exact_module(path: Path, name: str) -> ModuleType:
    """Load one file under a disposable, caller-owned module name."""
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not exact-load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module:
            sys.modules.pop(name, None)
        raise
    return module


def load_roster_oracle(root: Path) -> ModuleType:
    return load_exact_module(
        root
        / "tests"
        / "contract_integration"
        / "validation_rosters"
        / "validation_roster_expectations.py",
        "_norad_validation_roster_oracle",
    )


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))
