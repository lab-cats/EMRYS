#!/usr/bin/env python3
"""Exercise the established HTML core independently of bundle publication."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src" / "norad" / "reporting"))

import render_run_report


if __name__ == "__main__":
    raise SystemExit(render_run_report.html_core_main())
