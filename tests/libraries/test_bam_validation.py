from __future__ import annotations

import inspect
import pickle
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from norad.libraries.alignments import bam as BAM


def test_public_api_and_characterized_behavior(tmp_path: Path) -> None:
    functions = {
        name
        for name, value in vars(BAM).items()
        if inspect.isfunction(value) and value.__module__ == BAM.__name__
    }
    assert functions == {
        "bai_magic_ok",
        "bam_magic_ok",
        "parse_header",
        "read_bai_prefix",
        "read_bam_prefix",
        "run_tool",
        "validate_bam_bai_pair",
        "validate_bam_signature",
        "validate_samtools_readiness",
    }
    assert pickle.loads(pickle.dumps(BAM.validate_bam_signature)) is (
        BAM.validate_bam_signature
    )

    bam = tmp_path / "sample.bam"
    bai = tmp_path / "sample.bam.bai"
    bam.write_bytes(b"\x1f\x8b\x08\x04payload")
    bai.write_bytes(b"BAI\x01payload")
    assert BAM.read_bam_prefix(bam) == b"\x1f\x8b\x08\x04"
    assert BAM.read_bai_prefix(bai) == b"BAI\x01"
    assert BAM.validate_bam_signature(bam) == (True, b"\x1f\x8b\x08\x04")
    assert BAM.validate_bam_bai_pair(bam, bai) == (
        True,
        b"\x1f\x8b\x08\x04",
        b"BAI\x01",
    )
    assert BAM.bam_magic_ok(b"BAM\x01")
    assert not BAM.bam_magic_ok(b"nope")
    assert BAM.bai_magic_ok(b"CSI\x01")
    assert not BAM.bai_magic_ok(b"nope")

    completed = BAM.run_tool(
        Path("/bin/sh"),
        "-c",
        "printf 'probe-out\\n'; printf 'probe-err\\n' >&2; exit 7",
    )
    assert completed.args == [
        "/bin/sh",
        "-c",
        "printf 'probe-out\\n'; printf 'probe-err\\n' >&2; exit 7",
    ]
    assert completed.returncode == 7
    assert completed.stdout == "probe-out\n"
    assert completed.stderr == "probe-err\n"
    with pytest.raises(FileNotFoundError) as raised:
        BAM.run_tool(Path("/definitely/missing/norad-tool"), "--probe")
    assert raised.value.errno == 2

    assert BAM.parse_header("@HD\tVN:1.6\tSO:coordinate\n@RG\tID:S\tSM:S\n", "S") == (
        True,
        True,
        "HD=1 RG=1",
    )
    assert BAM.parse_header("", "S") == (False, False, "HD=0 RG=0")
    assert BAM.parse_header(
        "@HD\tSO:coordinate\n@HD\tSO:coordinate\n@RG\tID:S\tSM:S\n@RG\tID:S\tSM:S\n",
        "S",
    ) == (False, False, "HD=2 RG=2")
    assert BAM.parse_header("@HD\tSO:coordinate\n@RG\tID:wrong\tSM:S\n", "S") == (
        True,
        False,
        "HD=1 RG=1",
    )


def test_validate_samtools_readiness_uses_quickcheck_and_header(tmp_path: Path) -> None:
    tool = tmp_path / "samtools"
    tool.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ $1 == quickcheck ]]; then exit 0; fi\n"
        "if [[ $1 == view && $2 == -H ]]; then\n"
        "  printf '@HD\\tSO:coordinate\\n@RG\\tID:S\\tSM:S\\n'\n"
        "  exit 0\n"
        "fi\n"
        "exit 9\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)

    assert BAM.validate_samtools_readiness(tool, tmp_path / "sample.bam", "S") == (
        True,
        "exit=0",
        True,
        True,
        "HD=1 RG=1",
    )
