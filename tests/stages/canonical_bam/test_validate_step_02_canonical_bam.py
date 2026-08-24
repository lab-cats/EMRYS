from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
FAKE_SAMTOOLS_VARIABLES = (
    "QUICKCHECK_EXIT",
    "RG_ID",
    "RG_SM",
    "SORT_ORDER",
    "TAGGED",
    "TOTAL",
)


@dataclass(frozen=True, slots=True)
class CanonicalBamFixture:
    bam: Path
    bai: Path
    samtools: Path
    output: Path


def build_test_environment(**overrides: str) -> dict[str, str]:
    environment = os.environ.copy()
    for variable in FAKE_SAMTOOLS_VARIABLES:
        environment.pop(variable, None)
    environment.update(overrides)
    return environment


def build_validation_fixture(root: Path) -> CanonicalBamFixture:
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.sorted.bam"
    bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.sorted.bam.bai"
    bai.write_bytes(b"BAI\x01synthetic")
    tool = root / "samtools"
    tool.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case "$1 $2" in\n'
        "  'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        "  'view -H') printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        '"${SORT_ORDER:-coordinate}" "${RG_ID:-S}" "${RG_SM:-S}" ;;\n'
        "  'view -c')\n"
        '    if [[ "${3:-}" == -d ]]; then printf \'%s\\n\' "${TAGGED:-10}"; '
        "else printf '%s\\n' \"${TOTAL:-10}\"; fi ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)
    output_directory = root / "out"
    output_directory.mkdir()
    return CanonicalBamFixture(
        bam=bam,
        bai=bai,
        samtools=tool,
        output=output_directory / "S.validation.tsv",
    )


def run_validator(
    canonical_bam: CanonicalBamFixture,
    *extra: str,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys",
            "validate",
            "canonical-bam",
            "--scope-id",
            "S",
            "--bam",
            str(canonical_bam.bam),
            "--bai",
            str(canonical_bam.bai),
            "--samtools-bin",
            str(canonical_bam.samtools),
            "--output",
            str(canonical_bam.output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=build_test_environment() if env is None else env,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    canonical_bam = build_validation_fixture(tmp_path)
    assert run_validator(canonical_bam).returncode == 0
    assert not canonical_bam.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    canonical_bam = build_validation_fixture(tmp_path)
    result = run_validator(canonical_bam, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(canonical_bam.output)
    assert_exact_check_roster(rows, "02")
    assert {row["status"] for row in rows} == {"pass"}


def test_sort_rg_and_tag_failures_are_evidence(tmp_path: Path) -> None:
    canonical_bam = build_validation_fixture(tmp_path)
    env = build_test_environment(
        SORT_ORDER="queryname",
        RG_ID="wrong",
        TAGGED="9",
        QUICKCHECK_EXIT="1",
    )
    assert run_validator(canonical_bam, "--execute", env=env).returncode == 0
    status = {
        row["check_id"]: row["status"] for row in report_rows(canonical_bam.output)
    }
    assert status["samtools_quickcheck"] == "fail"
    assert status["coordinate_sorting"] == "fail"
    assert status["read_group_header"] == "fail"
    assert status["alignment_rg_tags"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    canonical_bam = build_validation_fixture(tmp_path)
    canonical_bam.bai.unlink()
    assert run_validator(canonical_bam, "--execute").returncode == 2
    valid_fixture = build_validation_fixture(tmp_path / "second")
    invalid_fixture = CanonicalBamFixture(
        bam=valid_fixture.bam,
        bai=valid_fixture.bai,
        samtools=valid_fixture.samtools,
        output=valid_fixture.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_fixture, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    canonical_bam = build_validation_fixture(tmp_path)
    lock = canonical_bam.output.parent / f".{canonical_bam.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(canonical_bam, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_exact(
    tmp_path: Path,
) -> None:
    canonical_bam = build_validation_fixture(tmp_path / "data")
    invocation = tmp_path / "invoke"
    invocation.mkdir()
    inputs = (canonical_bam.bam, canonical_bam.bai, canonical_bam.samtools)
    before = {path: (path.read_bytes(), path.stat().st_mode) for path in inputs}

    dry = run_validator(canonical_bam, cwd=invocation)
    assert dry.returncode == 0
    assert dry.stderr == ""
    assert not canonical_bam.output.exists()
    assert hashlib.sha256(dry.stdout.encode()).hexdigest() == (
        "e0edf8f70d40ffc6ca9ae6ef732c797ac00abd056ee16496ad22038e277c5c1f"
    )

    first = run_validator(canonical_bam, "--execute", cwd=invocation)
    assert first.returncode == 0
    assert first.stderr == ""
    first_bytes = canonical_bam.output.read_bytes()
    assert len(first_bytes) == 542
    assert hashlib.sha256(first_bytes).hexdigest() == (
        "0007c190b23071286fea72670f72d9cf98666c5c11fd76f1657715aa2d76a7c8"
    )
    assert_exact_check_roster(report_rows(canonical_bam.output), "02")

    second = run_validator(canonical_bam, "--execute", cwd=invocation)
    assert second.returncode == 0
    assert second.stderr == ""
    assert canonical_bam.output.read_bytes() == first_bytes
    assert {path: (path.read_bytes(), path.stat().st_mode) for path in inputs} == before
    assert list(invocation.iterdir()) == []
