#!/usr/bin/env python3
"""Compatibility facade for the static NORAD report-bundle command."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[2])
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.reporting._run_report import bundle as _owner

globals().update(
    {
        name: value
        for name, value in vars(_owner).items()
        if not name.startswith("__") and name != "main"
    }
)


def main(argv: Sequence[str] | None = None) -> int:
    return _owner.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
