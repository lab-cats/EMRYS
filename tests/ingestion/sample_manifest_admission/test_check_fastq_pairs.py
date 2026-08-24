import gzip
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    REPO_ROOT
    / "src"
    / "emrys"
    / "ingestion"
    / "sample_manifest_admission"
    / "check_fastq_pairs.sh"
)


def fastq_text(read_ids: list[str], mate: int) -> str:
    records: list[str] = []
    for read_id in read_ids:
        records.extend((f"@{read_id}/{mate}", "ACGT", "+", "IIII"))
    return "\n".join(records) + "\n"


def write_fastq(
    path: Path,
    read_ids: list[str],
    mate: int,
    *,
    compressed: bool = False,
) -> Path:
    payload = fastq_text(read_ids, mate)
    if compressed:
        with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
            stream.write(payload)
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def tree_snapshot(root: Path) -> tuple[tuple[str, bytes | None], ...]:
    return tuple(
        (
            str(path.relative_to(root)),
            path.read_bytes() if path.is_file() else None,
        )
        for path in sorted(root.rglob("*"))
    )


def run_checker(
    *arguments: str,
    cwd: Path,
    direct: bool = False,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [str(SCRIPT)] if direct else ["/bin/bash", str(SCRIPT)]
    return subprocess.run(
        [*command, *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def expected_context(
    *,
    sample_id: str,
    r1: Path,
    r2: Path,
    num_reads: int,
) -> str:
    return (
        "FASTQ pair check context\n"
        f"  Sample ID: {sample_id}\n"
        f"  R1 FASTQ: {r1}\n"
        f"  R2 FASTQ: {r2}\n"
        f"  Read IDs checked: {num_reads}\n"
    )


@pytest.mark.parametrize(
    ("compressed", "direct"),
    ((False, False), (True, True)),
    ids=("plain-explicit-bash", "gzip-direct"),
)
def test_matching_pair_succeeds_without_side_effects(
    tmp_path: Path,
    compressed: bool,
    direct: bool,
) -> None:
    suffix = ".fastq.gz" if compressed else ".fastq"
    r1 = write_fastq(
        tmp_path / f"reads_R1{suffix}",
        ["read_001", "read_002"],
        1,
        compressed=compressed,
    )
    r2 = write_fastq(
        tmp_path / f"reads_R2{suffix}",
        ["read_001", "read_002"],
        2,
        compressed=compressed,
    )
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "sample_001",
        "--num-reads",
        "2",
        cwd=tmp_path,
        direct=direct,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == (
        expected_context(
            sample_id="sample_001",
            r1=r1,
            r2=r2,
            num_reads=2,
        )
        + "  R1 total reads: 2\n"
        + "  R2 total reads: 2\n"
        + "PASS: FASTQ pair check succeeded for 2 read IDs and matching "
        "total read counts.\n"
    )
    assert tree_snapshot(tmp_path) == before


def test_unequal_read_counts_fail_after_reporting_both_counts(
    tmp_path: Path,
) -> None:
    r1 = write_fastq(tmp_path / "reads_R1.fastq", ["read_001", "read_002"], 1)
    r2 = write_fastq(
        tmp_path / "reads_R2.fastq",
        ["read_001", "read_002", "read_003"],
        2,
    )
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "unequal",
        "--num-reads",
        "2",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == (
        expected_context(sample_id="unequal", r1=r1, r2=r2, num_reads=2)
        + "  R1 total reads: 2\n"
        + "  R2 total reads: 3\n"
    )
    assert result.stderr == (
        "Sample ID: unequal\nFAIL: FASTQ read counts differ: R1=2 R2=3\n"
    )
    assert tree_snapshot(tmp_path) == before


def test_read_id_mismatch_within_requested_prefix_fails(
    tmp_path: Path,
) -> None:
    r1 = write_fastq(tmp_path / "reads_R1.fastq", ["read_001", "read_002"], 1)
    r2 = write_fastq(tmp_path / "reads_R2.fastq", ["read_001", "other"], 2)
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "mismatch",
        "--num-reads",
        "2",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == (
        expected_context(sample_id="mismatch", r1=r1, r2=r2, num_reads=2)
        + "  R1 total reads: 2\n"
        + "  R2 total reads: 2\n"
    )
    assert result.stderr == (
        "FAIL: FASTQ read IDs mismatch\n"
        "Sample ID: mismatch\n"
        "Record number: 2\n"
        "R1 normalized ID: read_002\n"
        "R2 normalized ID: other\n"
    )
    assert tree_snapshot(tmp_path) == before


def test_fewer_records_than_requested_fails(
    tmp_path: Path,
) -> None:
    r1 = write_fastq(tmp_path / "reads_R1.fastq", ["read_001"], 1)
    r2 = write_fastq(tmp_path / "reads_R2.fastq", ["read_001"], 2)
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "short",
        "--num-reads",
        "2",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == (
        expected_context(sample_id="short", r1=r1, r2=r2, num_reads=2)
        + "  R1 total reads: 1\n"
        + "  R2 total reads: 1\n"
    )
    assert result.stderr == (
        "Sample ID: short\n"
        "FAIL: R1 FASTQ contains fewer than --num-reads records: have 1, "
        "need 2\n"
    )
    assert tree_snapshot(tmp_path) == before


def test_non_four_line_input_fails_before_read_counts_are_reported(
    tmp_path: Path,
) -> None:
    r1 = tmp_path / "reads_R1.fastq"
    r1.write_text("@read_001/1\nACGT\n+\n", encoding="utf-8")
    r2 = write_fastq(tmp_path / "reads_R2.fastq", ["read_001"], 2)
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "malformed",
        "--num-reads",
        "1",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == expected_context(
        sample_id="malformed",
        r1=r1,
        r2=r2,
        num_reads=1,
    )
    assert result.stderr == (
        "Sample ID: malformed\nFAIL: R1 FASTQ line count is not divisible by 4: 3\n"
    )
    assert tree_snapshot(tmp_path) == before


def test_gunzip_child_failure_propagates_without_checker_diagnostic(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_gunzip = fake_bin / "gunzip"
    fake_gunzip.write_text(
        "#!/bin/sh\nprintf 'synthetic gunzip failure\\n' >&2\nexit 37\n",
        encoding="utf-8",
    )
    fake_gunzip.chmod(0o755)
    r1 = tmp_path / "reads_R1.fastq.gz"
    r1.write_bytes(b"not inspected by the failing child\n")
    r2 = write_fastq(tmp_path / "reads_R2.fastq", ["read_001"], 2)
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(fake_bin), environment.get("PATH", "")))
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "child-failure",
        "--num-reads",
        "1",
        cwd=tmp_path,
        environment=environment,
    )

    assert result.returncode == 37
    assert result.stdout == expected_context(
        sample_id="child-failure",
        r1=r1,
        r2=r2,
        num_reads=1,
    )
    assert result.stderr == "synthetic gunzip failure\n"
    assert tree_snapshot(tmp_path) == before


def test_id_mismatch_after_requested_prefix_is_not_checked(
    tmp_path: Path,
) -> None:
    r1 = write_fastq(tmp_path / "reads_R1.fastq", ["read_001", "read_002"], 1)
    r2 = write_fastq(tmp_path / "reads_R2.fastq", ["read_001", "other"], 2)
    before = tree_snapshot(tmp_path)

    result = run_checker(
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "prefix-only",
        "--num-reads",
        "1",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == (
        expected_context(sample_id="prefix-only", r1=r1, r2=r2, num_reads=1)
        + "  R1 total reads: 2\n"
        + "  R2 total reads: 2\n"
        + "PASS: FASTQ pair check succeeded for 1 read IDs and matching "
        "total read counts.\n"
    )
    assert tree_snapshot(tmp_path) == before
