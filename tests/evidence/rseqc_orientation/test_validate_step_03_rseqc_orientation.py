from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from emrys.evidence.rseqc_orientation import validator
from emrys.libraries.validation import Snapshot
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster


@dataclass(frozen=True, slots=True)
class OrientationEvidence:
    report: Path
    output: Path


def build_orientation_fixture(root: Path) -> OrientationEvidence:
    root.mkdir(parents=True, exist_ok=True)
    report = root / "S.infer_experiment.txt"
    report.write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n',
        encoding="utf-8",
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return OrientationEvidence(
        report=report,
        output=output_directory / "S.validation.tsv",
    )


def validator_arguments(evidence: OrientationEvidence, *extra: str) -> list[str]:
    return [
        "--scope-id",
        "S",
        "--infer-report",
        str(evidence.report),
        "--output",
        str(evidence.output),
        *extra,
    ]


def parse_validator_arguments(
    evidence: OrientationEvidence,
    *extra: str,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    validator.configure_parser(parser)
    return parser.parse_args(validator_arguments(evidence, *extra))


def run_validator(
    evidence: OrientationEvidence,
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
            "rseqc-orientation",
            *validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    evidence = build_orientation_fixture(tmp_path)
    assert run_validator(evidence).returncode == 0
    assert not evidence.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    evidence = build_orientation_fixture(tmp_path)
    result = run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "03")
    assert {row["status"] for row in rows} == {"pass"}


def test_invalid_fraction_and_sum_are_failed_evidence(tmp_path: Path) -> None:
    evidence = build_orientation_fixture(tmp_path)
    evidence.report.write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 1.20\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n',
        encoding="utf-8",
    )
    assert run_validator(evidence, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["paired_orientation_fraction_a"] == "fail"
    assert status["fraction_sum"] == "fail"


def test_nonempty_malformed_producer_output_is_published_failed_evidence(
    tmp_path: Path,
) -> None:
    evidence = build_orientation_fixture(tmp_path)
    evidence.report.write_text(
        "This is PairEnd Data\nnonempty malformed orientation evidence\n",
        encoding="utf-8",
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "03")
    assert {row["status"] for row in rows} == {"fail"}


@pytest.mark.parametrize("tolerance", ("nan", "-0.001", "0.1001"))
def test_invalid_sum_tolerance_fails_closed(
    tmp_path: Path,
    tolerance: str,
) -> None:
    evidence = build_orientation_fixture(tmp_path)

    result = run_validator(
        evidence,
        "--sum-tolerance",
        tolerance,
        "--execute",
    )

    assert result.returncode == 2
    assert "--sum-tolerance must be finite and between 0 and 0.1" in result.stderr
    assert result.stdout == ""
    assert not evidence.output.exists()


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_orientation_fixture(tmp_path)
    evidence.report.unlink()
    assert run_validator(evidence, "--execute").returncode == 2
    valid_evidence = build_orientation_fixture(tmp_path / "second")
    invalid_evidence = OrientationEvidence(
        report=valid_evidence.report,
        output=valid_evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_evidence, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_orientation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_execute_repeat_is_exact_and_residue_free(
    tmp_path: Path,
) -> None:
    evidence = build_orientation_fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    input_before = (evidence.report.read_bytes(), evidence.report.stat().st_mode)

    dry = run_validator(evidence, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert hashlib.sha256(dry.stdout.encode()).hexdigest() == (
        "e63a31b9399386cdc60b1c4df27c50166808ca1e146fc7cdbcd7de25f54d80c8"
    )
    assert not evidence.output.exists()

    first = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_report = evidence.output.read_bytes()
    assert len(first_report) == 528
    assert hashlib.sha256(first_report).hexdigest() == (
        "6cc2a3f00c85bd68624f35b2554500424c45b3d182b80f865cd4d2000ef517e1"
    )
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "03")
    assert {row["status"] for row in rows} == {"pass"}

    second = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == first_report
    assert (
        evidence.report.read_bytes(),
        evidence.report.stat().st_mode,
    ) == input_before
    assert list(invocation_cwd.iterdir()) == []
    assert list(evidence.output.parent.iterdir()) == [evidence.output]


def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = build_orientation_fixture(tmp_path)
    first = run_validator(evidence, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = evidence.output.read_bytes()
    real_build = validator.build_validation_report

    def mutate_after_build(
        arguments: argparse.Namespace,
    ) -> tuple[bytes, dict[Path, Snapshot]]:
        built = real_build(arguments)
        evidence.report.write_text(
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
