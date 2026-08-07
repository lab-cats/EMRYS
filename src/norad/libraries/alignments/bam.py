"""Shared samtools execution and BAM-header validation helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_tool(tool: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(tool), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def parse_header(text: str, scope_id: str) -> tuple[bool, bool, str]:
    hd = [line for line in text.splitlines() if line.startswith("@HD\t")]
    rg = [line for line in text.splitlines() if line.startswith("@RG\t")]
    coordinate = len(hd) == 1 and "SO:coordinate" in hd[0].split("\t")
    matching = (
        len(rg) == 1
        and f"ID:{scope_id}" in rg[0].split("\t")
        and f"SM:{scope_id}" in rg[0].split("\t")
    )
    return coordinate, matching, f"HD={len(hd)} RG={len(rg)}"
