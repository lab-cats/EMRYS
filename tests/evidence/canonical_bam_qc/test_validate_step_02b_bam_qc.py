from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from emrys.evidence.canonical_bam_qc import validator
from emrys.libraries.validation import Snapshot
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster


@dataclass(frozen=True, slots=True)
class BamQcFixture:
    quickcheck: Path
    flagstat: Path
    output: Path


def build_validation_fixture(root: Path) -> BamQcFixture:
    root.mkdir(parents=True, exist_ok=True)
    quickcheck = root / "S.quickcheck.txt"
    quickcheck.write_text(
        "PASS: samtools quickcheck completed with no errors.\n",
        encoding="utf-8",
    )
    flagstat = root / "S.flagstat.txt"
    flagstat.write_text(
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "8 + 0 mapped (80.00% : N/A)\n",
        encoding="utf-8",
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return BamQcFixture(
        quickcheck=quickcheck,
        flagstat=flagstat,
        output=output_directory / "S.validation.tsv",
    )


def validator_arguments(evidence: BamQcFixture, *extra: str) -> list[str]:
    return [
        "--scope-id",
        "S",
        "--quickcheck",
        str(evidence.quickcheck),
        "--flagstat",
        str(evidence.flagstat),
        "--output",
        str(evidence.output),
        *extra,
    ]


def parse_validator_arguments(
    evidence: BamQcFixture,
    *extra: str,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    validator.configure_parser(parser)
    return parser.parse_args(validator_arguments(evidence, *extra))


def run_validator(
    evidence: BamQcFixture,
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
            "canonical-bam-qc",
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
    assert_exact_check_roster(rows, "02b")
    assert {row["status"] for row in rows} == {"pass"}


def test_bad_quickcheck_and_counts_are_failed_evidence(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.quickcheck.write_text("FAIL\n", encoding="utf-8")
    evidence.flagstat.write_text(
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "11 + 0 mapped (110.00% : N/A)\n",
        encoding="utf-8",
    )
    assert run_validator(evidence, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["quickcheck_structure"] == "fail"
    assert status["count_consistency"] == "fail"


def test_nonempty_producer_success_output_is_failed_quickcheck_evidence(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.quickcheck.write_text(
        "quickcheck success output\n",
        encoding="utf-8",
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["quickcheck_structure"] == "fail"
    assert {
        value for key, value in status.items() if key != "quickcheck_structure"
    } == {"pass"}


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.quickcheck.unlink()
    assert run_validator(evidence, "--execute").returncode == 2
    valid_evidence = build_validation_fixture(tmp_path / "second")
    invalid_evidence = BamQcFixture(
        quickcheck=valid_evidence.quickcheck,
        flagstat=valid_evidence.flagstat,
        output=valid_evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_evidence, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_execute_repeat_is_exact_and_residue_free(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    inputs = (evidence.quickcheck, evidence.flagstat)
    input_before = {path: (path.read_bytes(), path.stat().st_mode) for path in inputs}

    dry = run_validator(evidence, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert hashlib.sha256(dry.stdout.encode()).hexdigest() == (
        "a187f2b1781619e9b72bf4f8dcb963958f624bb28201b870ffd373c03a2e95f0"
    )
    assert not evidence.output.exists()

    first = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_report = evidence.output.read_bytes()
    assert len(first_report) == 546
    assert hashlib.sha256(first_report).hexdigest() == (
        "964050675afa68b9d15f8dbd37a3673b2e20d810f9aba338ef15f2dd14c89157"
    )
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "02b")
    assert {row["status"] for row in rows} == {"pass"}

    second = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == first_report
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in inputs
    } == input_before
    assert list(invocation_cwd.iterdir()) == []
    assert list(evidence.output.parent.iterdir()) == [evidence.output]


def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = build_validation_fixture(tmp_path)
    first = run_validator(evidence, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = evidence.output.read_bytes()
    real_build = validator.build_validation_report

    def mutate_after_build(
        arguments: argparse.Namespace,
    ) -> tuple[bytes, dict[Path, Snapshot]]:
        built = real_build(arguments)
        evidence.quickcheck.write_text(
            "changed after validation\n",
            encoding="utf-8",
        )
        return built

    monkeypatch.setattr(validator, "build_validation_report", mutate_after_build)
    status = validator.validate_from_args(
        parse_validator_arguments(evidence, "--execute")
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "Input changed after validation" in captured.err
    assert evidence.output.read_bytes() == predecessor
    assert list(evidence.output.parent.iterdir()) == [evidence.output]
