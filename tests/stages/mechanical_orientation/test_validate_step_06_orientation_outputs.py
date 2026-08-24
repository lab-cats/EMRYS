from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from emrys.__main__ import main as emrys_main
from emrys.libraries.validation import Snapshot
from emrys.stages.mechanical_orientation import (
    validator as mechanical_orientation_validator,
)
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster


@dataclass(frozen=True, slots=True)
class MechanicalOrientationEvidence:
    fwd_bam: Path
    fwd_bai: Path
    rev_bam: Path
    rev_bai: Path
    counts: Path
    output: Path

    @property
    def input_paths(self) -> tuple[Path, ...]:
        return self.fwd_bam, self.fwd_bai, self.rev_bam, self.rev_bai, self.counts


def build_validation_fixture(root: Path) -> MechanicalOrientationEvidence:
    root.mkdir(parents=True, exist_ok=True)
    fwd_bam = root / "S.FWD_like.bam"
    fwd_bam.write_bytes(b"BAM\x01synthetic")
    fwd_bai = root / "S.FWD_like.bam.bai"
    fwd_bai.write_bytes(b"BAI\x01synthetic")
    rev_bam = root / "S.REV_like.bam"
    rev_bam.write_bytes(b"BAM\x01synthetic")
    rev_bai = root / "S.REV_like.bam.bai"
    rev_bai.write_bytes(b"BAI\x01synthetic")
    counts = root / "S.orientation_counts.tsv"
    counts.write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t5\t3\t8\t2\t0.800000\n",
        encoding="utf-8",
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return MechanicalOrientationEvidence(
        fwd_bam=fwd_bam,
        fwd_bai=fwd_bai,
        rev_bam=rev_bam,
        rev_bai=rev_bai,
        counts=counts,
        output=output_directory / "S.validation.tsv",
    )


def validator_arguments(
    evidence: MechanicalOrientationEvidence,
    *extra: str,
) -> list[str]:
    return [
        "--scope-id",
        "S",
        "--fwd-bam",
        str(evidence.fwd_bam),
        "--fwd-bai",
        str(evidence.fwd_bai),
        "--rev-bam",
        str(evidence.rev_bam),
        "--rev-bai",
        str(evidence.rev_bai),
        "--counts",
        str(evidence.counts),
        "--output",
        str(evidence.output),
        *extra,
    ]


def run_validator(
    evidence: MechanicalOrientationEvidence,
    *extra: str,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys",
            "validate",
            "mechanical-orientation",
            *validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    assert run_validator(evidence).returncode == 0
    assert not evidence.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "06")
    assert {row["status"] for row in rows} == {"pass"}


def test_count_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.counts.write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t6\t3\t8\t2\t0.700000\n",
        encoding="utf-8",
    )
    assert run_validator(evidence, "--execute").returncode == 0
    status_by_check = {
        row["check_id"]: row["status"] for row in report_rows(evidence.output)
    }
    assert status_by_check["fwd_count_arithmetic"] == "fail"
    assert status_by_check["assigned_count_arithmetic"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.fwd_bam.unlink()
    assert run_validator(evidence, "--execute").returncode == 2

    valid_evidence = build_validation_fixture(tmp_path / "second")
    invalid_evidence = replace(
        valid_evidence,
        output=valid_evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_evidence, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    invocation_directory = tmp_path / "invocation"
    invocation_directory.mkdir()
    input_states = {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    }

    dry_run = run_validator(evidence, cwd=invocation_directory)
    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stderr == ""
    dry_run_bytes = dry_run.stdout.encode()
    assert len(dry_run_bytes) == 730
    assert hashlib.sha256(dry_run_bytes).hexdigest() == (
        "1ecf8ed4e266686231520d6157ebfbc252ad8ff0b9be2969cf6a5d7580f3e178"
    )
    assert not evidence.output.exists()

    first = run_validator(evidence, "--execute", cwd=invocation_directory)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    report_bytes = evidence.output.read_bytes()
    assert len(report_bytes) == 689
    assert hashlib.sha256(report_bytes).hexdigest() == (
        "c51a3d07b584e5df6a2f7a85ec8d851aa2b22a6d7328d6245ad915370ab65790"
    )
    assert dry_run_bytes.startswith(report_bytes)
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "06")
    assert {row["status"] for row in rows} == {"pass"}

    second = run_validator(evidence, "--execute", cwd=invocation_directory)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == report_bytes
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    } == input_states
    assert list(invocation_directory.iterdir()) == []
    assert set(evidence.output.parent.iterdir()) == {evidence.output}


@pytest.mark.parametrize(
    "input_name",
    ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai"),
)
def test_invalid_container_magic_is_published_as_failed_evidence(
    tmp_path: Path,
    input_name: str,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    target = getattr(evidence, input_name)
    target.write_bytes(b"INVALID-container-magic")

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "06")
    rows_by_check = {row["check_id"]: row for row in rows}
    assert rows_by_check["output_containers"]["status"] == "fail"
    assert {row["status"] for row in rows} == {"pass", "fail"}


@pytest.mark.parametrize(
    "input_name",
    ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts"),
)
def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    input_name: str,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    initial = run_validator(evidence, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = evidence.output.read_bytes()
    input_bytes = {path: path.read_bytes() for path in evidence.input_paths}
    target = getattr(evidence, input_name)
    real_build = mechanical_orientation_validator.build_validation_report

    def mutate_after_build(
        arguments: argparse.Namespace,
    ) -> tuple[bytes, dict[Path, Snapshot]]:
        result = real_build(arguments)
        target.write_bytes(input_bytes[target] + b"post-build mutation\n")
        return result

    monkeypatch.setattr(
        mechanical_orientation_validator,
        "build_validation_report",
        mutate_after_build,
    )
    status = emrys_main(
        [
            "validate",
            "mechanical-orientation",
            *validator_arguments(evidence, "--execute"),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert f"Input changed after validation: {target}" in captured.err
    assert evidence.output.read_bytes() == predecessor
    assert target.read_bytes() == input_bytes[target] + b"post-build mutation\n"
    assert {
        path: path.read_bytes() for path in evidence.input_paths if path != target
    } == {path: data for path, data in input_bytes.items() if path != target}
    assert set(evidence.output.parent.iterdir()) == {evidence.output}
