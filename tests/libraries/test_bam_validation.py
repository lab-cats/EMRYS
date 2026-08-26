from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from emrys.libraries.alignments import bam as BAM
from emrys.libraries.validation import inputs as INPUTS


def test_public_api_and_characterized_behavior(tmp_path: Path) -> None:
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
        BAM.run_tool(Path("/definitely/missing/emrys-tool"), "--probe")
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


@pytest.mark.parametrize(
    ("name", "magic", "reader"),
    (
        ("large.bam", b"\x1f\x8b\x08\x04", BAM.read_bam_prefix),
        ("large.bam.bai", b"BAI\x01", BAM.read_bai_prefix),
    ),
)
def test_signature_reads_are_bounded_for_sparse_files(
    name: str,
    magic: bytes,
    reader: Callable[[Path], bytes],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / name
    sparse_size = 8 * 1024**3
    with path.open("wb") as stream:
        stream.write(magic)
        stream.truncate(sparse_size)
    real_read = INPUTS.os.read
    requests: list[int] = []
    returned: list[int] = []

    def bounded_read(descriptor: int, size: int) -> bytes:
        requests.append(size)
        assert size <= BAM.MAGIC_PREFIX_BYTES
        data = real_read(descriptor, size)
        returned.append(len(data))
        return data

    monkeypatch.setattr(INPUTS.os, "read", bounded_read)

    assert reader(path) == magic
    assert requests[0] == BAM.MAGIC_PREFIX_BYTES
    assert sum(returned) == BAM.MAGIC_PREFIX_BYTES
    assert path.stat().st_size == sparse_size


def test_signature_reads_preserve_short_and_empty_file_behavior(
    tmp_path: Path,
) -> None:
    short = tmp_path / "short.bam"
    short.write_bytes(b"BA")
    assert BAM.read_bam_prefix(short) == b"BA"
    assert BAM.validate_bam_signature(short) == (False, b"BA")

    empty = tmp_path / "empty.bam"
    empty.touch()
    with pytest.raises(BAM.ValidationError, match="BAM file must be nonempty"):
        BAM.read_bam_prefix(empty)


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
