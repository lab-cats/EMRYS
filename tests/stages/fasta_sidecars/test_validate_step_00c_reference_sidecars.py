"""Behavior protection for the Step 00c FASTA-sidecar validator."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster


@dataclass(frozen=True)
class ReferenceFixture:
    fasta: Path
    fai: Path
    dictionary: Path
    output: Path


def build_validation_fixture(root: Path) -> ReferenceFixture:
    root.mkdir(parents=True, exist_ok=True)
    fasta = root / "genome.fa"
    fasta.write_text(">1\nACGT\n>MT\nAA\n", encoding="utf-8")
    fai = root / "genome.fa.fai"
    fai.write_text("1\t4\t3\t4\t5\nMT\t2\t12\t2\t3\n", encoding="utf-8")
    dictionary = root / "genome.dict"
    dictionary.write_text(
        "@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n@SQ\tSN:MT\tLN:2\n",
        encoding="utf-8",
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return ReferenceFixture(
        fasta=fasta,
        fai=fai,
        dictionary=dictionary,
        output=output_directory / "novogene_ref.validation.tsv",
    )


def run_validator(
    reference: ReferenceFixture,
    *extra: str,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "fasta-sidecars",
            "--scope-id",
            "novogene_ref",
            "--reference-fasta",
            str(reference.fasta),
            "--reference-fai",
            str(reference.fai),
            "--reference-dict",
            str(reference.dictionary),
            "--output",
            str(reference.output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    assert run_validator(reference).returncode == 0
    assert not reference.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    result = run_validator(reference, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(reference.output)
    assert_exact_check_roster(rows, "00c")
    assert {row["status"] for row in rows} == {"pass"}


def test_sidecar_mismatch_is_failed_evidence(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    reference.fai.write_text(
        "1\t4\t3\t4\t5\nMT\t3\t12\t3\t4\n",
        encoding="utf-8",
    )
    assert run_validator(reference, "--execute").returncode == 0
    status_by_check = {
        row["check_id"]: row["status"] for row in report_rows(reference.output)
    }
    assert status_by_check["fai_contig_agreement"] == "fail"


def test_malformed_sidecar_is_role_local_failed_evidence(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    reference.fai.write_text("malformed\n", encoding="utf-8")
    result = run_validator(reference, "--execute")
    assert result.returncode == 0, result.stderr
    rows_by_check = {row["check_id"]: row for row in report_rows(reference.output)}
    assert rows_by_check["fasta_structure"]["status"] == "pass"
    assert rows_by_check["fai_structure"]["status"] == "fail"
    assert rows_by_check["fai_structure"]["observed"] == "FAI row 1 is malformed"
    assert rows_by_check["dict_structure"]["status"] == "pass"
    assert rows_by_check["fai_contig_agreement"]["status"] == "fail"
    assert rows_by_check["dict_contig_agreement"]["status"] == "pass"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    reference.fai.unlink()
    assert run_validator(reference, "--execute").returncode == 2

    second = build_validation_fixture(tmp_path / "second")
    wrong_output = ReferenceFixture(
        fasta=second.fasta,
        fai=second.fai,
        dictionary=second.dictionary,
        output=second.output.parent / "wrong.tsv",
    )
    assert run_validator(wrong_output, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    reference = build_validation_fixture(tmp_path)
    lock = reference.output.parent / f".{reference.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(reference, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_non_repository_cwd_dry_execute_repeat_is_deterministic(
    tmp_path: Path,
) -> None:
    reference = build_validation_fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    inputs = (reference.fasta, reference.fai, reference.dictionary)
    input_bytes_before = tuple(path.read_bytes() for path in inputs)

    dry_run = run_validator(reference, cwd=invocation_cwd)
    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stderr == ""
    assert not reference.output.exists()

    first = run_validator(reference, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    first_bytes = reference.output.read_bytes()
    first_rows = report_rows(reference.output)

    repeated = run_validator(reference, "--execute", cwd=invocation_cwd)
    assert repeated.returncode == 0, repeated.stderr
    assert repeated.stderr == ""
    assert reference.output.read_bytes() == first_bytes
    assert repeated.stdout == first.stdout
    assert [row["check_id"] for row in first_rows] == [
        "fasta_structure",
        "fai_structure",
        "dict_structure",
        "fai_contig_agreement",
        "dict_contig_agreement",
    ]
    assert {row["status"] for row in first_rows} == {"pass"}
    assert tuple(path.read_bytes() for path in inputs) == input_bytes_before
    assert not any(invocation_cwd.iterdir())
    assert list(reference.output.parent.iterdir()) == [reference.output]
