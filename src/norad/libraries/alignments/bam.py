"""Shared samtools execution and BAM-header validation helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from norad.libraries.validation import read_bytes


BAM_MAGIC_PREFIXES = {b"BAM\x01", b"\x1f\x8b\x08\x04"}
BAI_MAGIC_PREFIXES = {b"BAI\x01", b"CSI\x01"}


def validate_bam_bai_pair(
    bam: Path, bai: Path
) -> tuple[bool, bytes, bytes]:
    """Validate BAM/BAI magic signatures and return both observed signatures."""
    bam_magic = read_bam_prefix(bam)
    bai_magic = read_bai_prefix(bai)
    return (
        bam_magic_ok(bam_magic) and bai_magic_ok(bai_magic),
        bam_magic,
        bai_magic,
    )


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


def read_bam_prefix(path: Path) -> bytes:
    return read_bytes(path, "BAM file")[:4]


def read_bai_prefix(path: Path) -> bytes:
    return read_bytes(path, "BAI file")[:4]


def bam_magic_ok(prefix: bytes) -> bool:
    return prefix in BAM_MAGIC_PREFIXES


def bai_magic_ok(prefix: bytes) -> bool:
    return prefix in BAI_MAGIC_PREFIXES
