from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

import pytest

from emrys.__main__ import main as emrys_main
from emrys.libraries.validation import Snapshot
from emrys.stages.partitioned_cohort_mpileup import (
    validator as partitioned_cohort_mpileup_validator,
)
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
EXPECTED_PASS_REPORT = (
    b"step_id\tscope_id\tcheck_id\tstatus\tobserved\texpected\tdetail\n"
    b"07\tcohort__p1\treceipt_structure\tpass\trows=2\t"
    b"exact header; FWD_like, REV_like rows\treceipt transaction\n"
    b"07\tcohort__p1\tvcf_structure\tpass\tFWD_like=2 REV_like=2 samples\t"
    b"valid VCFs with manifest sample order\texplicit VCF structure\n"
    b"07\tcohort__p1\tselector_reconciliation\tpass\tregion=1:1-10\t"
    b"declared valid selector in both rows\tpartition selector and FAI universe\n"
    b"07\tcohort__p1\tmanifest_identity_and_sample_order\tpass\tsamples=2\t"
    b"manifest hashes, count, and VCF order reconcile\timmutable manifest identity\n"
    b"07\tcohort__p1\tvcf_record_counts\tpass\tFWD_like=1 REV_like=0\t"
    b"receipt paths and counts match exact VCFs\ttransaction record counts\n"
)
EXPECTED_DRY_STDOUT = EXPECTED_PASS_REPORT + (
    b"Dry-run complete; no output was written.\n"
)


@dataclass(frozen=True, slots=True)
class PartitionedCohortMpileupEvidence:
    sample_manifest: Path
    partition_manifest: Path
    reference_fai: Path
    fwd_vcf: Path
    rev_vcf: Path
    receipt: Path
    output: Path

    @property
    def input_paths(self) -> tuple[Path, ...]:
        return (
            self.sample_manifest,
            self.partition_manifest,
            self.reference_fai,
            self.fwd_vcf,
            self.rev_vcf,
            self.receipt,
        )


@dataclass(frozen=True, slots=True)
class ReceiptOverrides:
    selector_type: str = "region"
    selector_value: str = "1:1-10"
    fwd_path: str | None = None
    rev_path: str | None = None
    fwd_count: int = 1
    rev_count: int = 0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_receipt(
    evidence: PartitionedCohortMpileupEvidence,
    overrides: ReceiptOverrides | None = None,
) -> None:
    values = overrides or ReceiptOverrides()
    evidence.receipt.write_text(
        "cohort_id\tpartition_id\tselector_type\tselector_value\torientation\t"
        "vcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\t"
        "sample_count\tvcf_record_count\n"
        f"cohort\tp1\t{values.selector_type}\t{values.selector_value}\tFWD_like\t"
        f"{values.fwd_path or evidence.fwd_vcf.resolve()}\t"
        f"{_sha256(evidence.sample_manifest)}\t"
        f"{_sha256(evidence.partition_manifest)}\t2\t{values.fwd_count}\n"
        f"cohort\tp1\t{values.selector_type}\t{values.selector_value}\tREV_like\t"
        f"{values.rev_path or evidence.rev_vcf.resolve()}\t"
        f"{_sha256(evidence.sample_manifest)}\t"
        f"{_sha256(evidence.partition_manifest)}\t2\t{values.rev_count}\n",
        encoding="utf-8",
    )


def build_validation_fixture(root: Path) -> PartitionedCohortMpileupEvidence:
    root.mkdir(parents=True, exist_ok=True)
    sample_manifest = root / "samples.tsv"
    sample_manifest.write_text(
        "sample_id\tcondition\nA\tx\nB\ty\n",
        encoding="utf-8",
    )
    partition_manifest = root / "partitions.tsv"
    partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\np1\tregion\t1:1-10\n",
        encoding="utf-8",
    )
    reference_fai = root / "ref.fa.fai"
    reference_fai.write_text("1\t100\t0\t80\t81\n", encoding="utf-8")
    header = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
    )
    fwd_vcf = root / "cohort.p1.FWD_like.mpileup.vcf"
    rev_vcf = root / "cohort.p1.REV_like.mpileup.vcf"
    fwd_vcf.write_text(
        header + "1\t2\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\n",
        encoding="utf-8",
    )
    rev_vcf.write_text(header, encoding="utf-8")
    receipt = root / "cohort.p1.step07_outputs.tsv"
    output_directory = root / "out"
    output_directory.mkdir()
    evidence = PartitionedCohortMpileupEvidence(
        sample_manifest=sample_manifest,
        partition_manifest=partition_manifest,
        reference_fai=reference_fai,
        fwd_vcf=fwd_vcf,
        rev_vcf=rev_vcf,
        receipt=receipt,
        output=output_directory / "cohort__p1.validation.tsv",
    )
    write_receipt(evidence)
    return evidence


def validator_arguments(
    evidence: PartitionedCohortMpileupEvidence,
    *extra: str,
) -> list[str]:
    return [
        "--cohort-id",
        "cohort",
        "--partition-id",
        "p1",
        "--sample-manifest",
        str(evidence.sample_manifest),
        "--partition-manifest",
        str(evidence.partition_manifest),
        "--reference-fai",
        str(evidence.reference_fai),
        "--fwd-vcf",
        str(evidence.fwd_vcf),
        "--rev-vcf",
        str(evidence.rev_vcf),
        "--receipt",
        str(evidence.receipt),
        "--output",
        str(evidence.output),
        *extra,
    ]


def run_validator(
    evidence: PartitionedCohortMpileupEvidence,
    *extra: str,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys",
            "validate",
            "partitioned-cohort-mpileup",
            *validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)

    result = run_validator(evidence)

    assert result.returncode == 0
    assert result.stdout == EXPECTED_DRY_STDOUT
    assert result.stderr == b""
    assert not evidence.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    assert result.stdout == EXPECTED_PASS_REPORT + (
        f"Published Step 07 validation report: {evidence.output}\n".encode()
    )
    assert result.stderr == b""
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "07")
    assert {row["status"] for row in rows} == {"pass"}


def test_explicit_report_scope_preserves_scientific_validation(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    scope_id = "scope-cohort-partition-content-bound"
    evidence = replace(
        evidence,
        output=evidence.output.with_name(f"{scope_id}.validation.tsv"),
    )

    result = run_validator(evidence, "--scope-id", scope_id, "--execute")

    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "07")
    assert {row["scope_id"] for row in rows} == {scope_id}
    assert {row["status"] for row in rows} == {"pass"}


def test_relative_receipt_paths_match_absolute_admitted_vcfs(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    write_receipt(
        evidence,
        ReceiptOverrides(
            fwd_path=os.path.relpath(evidence.fwd_vcf, ROOT),
            rev_path=os.path.relpath(evidence.rev_vcf, ROOT),
        ),
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    assert {row["status"] for row in report_rows(evidence.output)} == {"pass"}


def test_different_vcf_file_fails_physical_identity(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    different_vcf = tmp_path / "different.vcf"
    different_vcf.write_bytes(evidence.fwd_vcf.read_bytes())
    write_receipt(
        evidence,
        ReceiptOverrides(fwd_path=str(different_vcf.resolve())),
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert next(
        row["status"] for row in rows if row["check_id"] == "vcf_record_counts"
    ) == "fail"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    before = {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    }

    dry = run_validator(evidence, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stdout == EXPECTED_DRY_STDOUT
    assert dry.stderr == b""
    assert not evidence.output.exists()

    first = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stdout == EXPECTED_PASS_REPORT + (
        f"Published Step 07 validation report: {evidence.output}\n".encode()
    )
    assert first.stderr == b""
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "07")
    assert {row["status"] for row in rows} == {"pass"}

    second = run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stdout == first.stdout
    assert second.stderr == b""
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    } == before
    assert list(invocation_cwd.iterdir()) == []
    assert set(evidence.output.parent.iterdir()) == {evidence.output}


@pytest.mark.parametrize(
    ("case", "failed_check"),
    [
        ("receipt_scope", "receipt_structure"),
        ("vcf_sample_order", "vcf_structure"),
        ("selector_disagreement", "selector_reconciliation"),
        ("manifest_hash", "manifest_identity_and_sample_order"),
        ("record_count", "vcf_record_counts"),
    ],
)
def test_each_semantic_check_can_publish_failed_evidence(
    tmp_path: Path,
    case: str,
    failed_check: str,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    if case == "receipt_scope":
        evidence.receipt.write_text(
            evidence.receipt.read_text(encoding="utf-8").replace(
                "cohort\tp1", "other\tp1"
            ),
            encoding="utf-8",
        )
    elif case == "vcf_sample_order":
        evidence.fwd_vcf.write_text(
            evidence.fwd_vcf.read_text(encoding="utf-8").replace(
                "\tFORMAT\tA\tB\n", "\tFORMAT\tB\tA\n"
            ),
            encoding="utf-8",
        )
    elif case == "selector_disagreement":
        evidence.receipt.write_text(
            evidence.receipt.read_text(encoding="utf-8").replace("1:1-10", "1:1-11"),
            encoding="utf-8",
        )
    elif case == "manifest_hash":
        evidence.receipt.write_text(
            evidence.receipt.read_text(encoding="utf-8").replace(
                _sha256(evidence.sample_manifest), "0" * 64
            ),
            encoding="utf-8",
        )
    elif case == "record_count":
        evidence.receipt.write_text(
            evidence.receipt.read_text(encoding="utf-8").replace(
                "\t2\t1\n", "\t2\t9\n"
            ),
            encoding="utf-8",
        )
    else:
        raise AssertionError(f"Unhandled semantic-failure case: {case}")

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "07")
    by_check = {row["check_id"]: row["status"] for row in rows}
    assert by_check[failed_check] == "fail"


@pytest.mark.parametrize(
    "input_name",
    (
        "sample_manifest",
        "partition_manifest",
        "reference_fai",
        "fwd_vcf",
        "rev_vcf",
        "receipt",
    ),
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
    before = {path: path.read_bytes() for path in evidence.input_paths}
    target = cast(Path, getattr(evidence, input_name))
    real_build = partitioned_cohort_mpileup_validator.build_validation_report

    def mutate_after_build(
        arguments: argparse.Namespace,
    ) -> tuple[bytes, dict[Path, Snapshot]]:
        built = real_build(arguments)
        target.write_bytes(before[target] + b"post-build mutation\n")
        return built

    monkeypatch.setattr(
        partitioned_cohort_mpileup_validator,
        "build_validation_report",
        mutate_after_build,
    )
    status = emrys_main(
        [
            "validate",
            "partitioned-cohort-mpileup",
            *validator_arguments(evidence, "--execute"),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert f"Input changed after validation: {target}" in captured.err
    assert evidence.output.read_bytes() == predecessor
    assert target.read_bytes() == before[target] + b"post-build mutation\n"
    assert {
        path: path.read_bytes() for path in evidence.input_paths if path != target
    } == {path: data for path, data in before.items() if path != target}
    assert set(evidence.output.parent.iterdir()) == {evidence.output}


def test_compressed_regions_file_is_exit_zero_failed_selector_evidence(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    compressed_regions = tmp_path / "regions.bed.gz"
    with gzip.open(compressed_regions, "wt") as stream:
        stream.write("1\t0\t10\n")
    evidence.partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\n"
        "p1\tregions_file\tregions.bed.gz\n",
        encoding="utf-8",
    )
    write_receipt(
        evidence,
        ReceiptOverrides(
            selector_type="regions_file",
            selector_value="regions.bed.gz",
        ),
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert by_check["selector_reconciliation"] == "fail"


def test_out_of_bounds_bed_coordinates_are_a_current_false_pass(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    regions = tmp_path / "regions.bed"
    regions.write_text("1\t0\t1000\n", encoding="utf-8")
    evidence.partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\np1\tregions_file\tregions.bed\n",
        encoding="utf-8",
    )
    write_receipt(
        evidence,
        ReceiptOverrides(
            selector_type="regions_file",
            selector_value="regions.bed",
        ),
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    assert {row["status"] for row in report_rows(evidence.output)} == {"pass"}


def test_vcf_selector_ref_alt_and_format_semantics_are_current_false_passes(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.fwd_vcf.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
        "1\t99\t.\tNOT_REF\t<UNCHECKED>\t.\tFAIL\tBROKEN=1\tUNCHECKED\tbad\tbad\n",
        encoding="utf-8",
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    assert {row["status"] for row in report_rows(evidence.output)} == {"pass"}


def test_relative_receipt_vcf_paths_are_exit_zero_count_failure(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    write_receipt(
        evidence,
        ReceiptOverrides(
            fwd_path=evidence.fwd_vcf.name,
            rev_path=evidence.rev_vcf.name,
        ),
    )

    result = run_validator(evidence, "--execute")

    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert by_check["vcf_record_counts"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.fwd_vcf.unlink()
    assert run_validator(evidence, "--execute").returncode == 2

    evidence = build_validation_fixture(tmp_path / "second")
    wrong_output = replace(
        evidence,
        output=evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(wrong_output, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")

    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"
