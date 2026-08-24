from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

import pytest

from emrys.__main__ import main as emrys_main
from emrys.contracts.scientific_evidence.step08 import (
    PARTITION_MANIFEST_HEADER,
    SAMPLE_MANIFEST_REQUIRED,
    STEP08_INPUTS_HEADER,
    STEP08_METADATA_HEADER,
    STEP08_SUMMARY_HEADER,
)
from emrys.libraries.validation import Snapshot
from emrys.stages.cohort_candidate_preprocessing import (
    validator as cohort_candidate_preprocessing_validator,
)
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
EXPECTED_PASS_REPORT = (
    b"step_id\tscope_id\tcheck_id\tstatus\tobserved\texpected\tdetail\n"
    b"08\tcohort\toutput_transaction\tpass\tvalidated\t"
    b"three exact Step 08 TSV headers\tsites, inputs, and summary\n"
    b"08\tcohort\tmanifest_annotation_identity\tpass\t"
    b"sample=validated; partition=validated\tcohort, manifest hashes, annotation "
    b"path/hash, provisional policy\tvalidated\n"
    b"08\tcohort\tinput_receipt_reconciliation\tpass\tvalidated\t"
    b"complete partition x orientation receipt\tordered inputs, types, hashes, "
    b"and per-row arithmetic\n"
    b"08\tcohort\tsites_order_uniqueness\tpass\tvalidated\ttyped unique candidates "
    b"and per-scope counts\tsites schema, sample columns, order, uniqueness, and "
    b"AF arithmetic\n"
    b"08\tcohort\tsummary_count_reconciliation\tpass\tvalidated\t"
    b"one exact aggregate row matching inputs and sites\tthree-output transaction "
    b"count reconciliation\n"
)
EXPECTED_DRY_STDOUT = (
    EXPECTED_PASS_REPORT + b"Dry-run complete; no output was written.\n"
)


@dataclass(frozen=True, slots=True)
class CohortCandidatePreprocessingEvidence:
    sample_manifest: Path
    partition_manifest: Path
    annotation_gtf: Path
    sites: Path
    inputs: Path
    summary: Path
    output: Path


def _write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _read_tsv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.reader(stream, delimiter="\t"))


def _replace_cell(path: Path, data_row: int, column: str, value: str) -> None:
    table = _read_tsv(path)
    table[data_row + 1][table[0].index(column)] = value
    _write_tsv(path, table[0], table[1:])


def _replace_column(path: Path, column: str, value: str) -> None:
    table = _read_tsv(path)
    index = table[0].index(column)
    for row in table[1:]:
        row[index] = value
    _write_tsv(path, table[0], table[1:])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_validation_fixture(root: Path) -> CohortCandidatePreprocessingEvidence:
    root.mkdir(parents=True, exist_ok=True)
    sample_manifest = root / "samples.tsv"
    _write_tsv(
        sample_manifest,
        SAMPLE_MANIFEST_REQUIRED,
        (("S", "/r1", "/r2", "reverse", "control", "1"),),
    )
    partition_manifest = root / "partitions.tsv"
    _write_tsv(
        partition_manifest,
        PARTITION_MANIFEST_HEADER,
        (("p1", "region", "1"),),
    )
    annotation_gtf = root / "annotation.gtf"
    annotation_gtf.write_text(
        '1\ts\tgene\t1\t10\t.\t+\t.\tgene_id "g";\n',
        encoding="utf-8",
    )
    sites = root / "cohort.step08_sites.tsv"
    _write_tsv(
        sites,
        STEP08_METADATA_HEADER + ("DP__S", "AD__S", "AF__S"),
        (
            (
                "p1\tc1\tFWD_like\t1\t2\t1\tA\tG\tA\tG\t+\tg\tt\tTRUE\tFALSE\t"
                "FALSE\tTRUE\tFALSE\t60\tPASS\t4\tlegacy_provisional_v1\t10\t2\t0.2"
            ).split("\t"),
            (
                "p1\tc2\tREV_like\t1\t3\t1\tC\tT\tG\tA\t-\tg\tt\tTRUE\tFALSE\t"
                "FALSE\tTRUE\tFALSE\t50\tPASS\t3\tlegacy_provisional_v1\t8\t1\t0.125"
            ).split("\t"),
        ),
    )

    sample_manifest_sha256 = _sha256(sample_manifest)
    partition_manifest_sha256 = _sha256(partition_manifest)
    annotation_gtf_sha256 = _sha256(annotation_gtf)

    def input_row(orientation: str, vcf_path: str) -> list[str]:
        return (
            f"cohort\tp1\tregion\t1\t{orientation}\t/step07/receipt.tsv\t{'1' * 64}\t"
            f"{vcf_path}\t{'2' * 64}\t{sample_manifest_sha256}\t"
            f"{partition_manifest_sha256}\t{annotation_gtf.resolve()}\t"
            f"{annotation_gtf_sha256}\t1\t1\t1\t1\t1\t0\t0\t1\tlegacy_provisional_v1"
        ).split("\t")

    inputs = root / "cohort.step08_inputs.tsv"
    _write_tsv(
        inputs,
        STEP08_INPUTS_HEADER,
        (
            input_row("FWD_like", "/step07/fwd.vcf"),
            input_row("REV_like", "/step07/rev.vcf"),
        ),
    )
    summary = root / "cohort.step08_summary.tsv"
    _write_tsv(
        summary,
        STEP08_SUMMARY_HEADER,
        (
            (
                "cohort\t1\t1\t2\t1\t2\t2\t2\t0\t0\t2\t"
                f"{sample_manifest_sha256}\t{partition_manifest_sha256}\t"
                f"{annotation_gtf.resolve()}\t{annotation_gtf_sha256}\t"
                "legacy_provisional_v1"
            ).split("\t"),
        ),
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return CohortCandidatePreprocessingEvidence(
        sample_manifest=sample_manifest,
        partition_manifest=partition_manifest,
        annotation_gtf=annotation_gtf,
        sites=sites,
        inputs=inputs,
        summary=summary,
        output=output_directory / "cohort.validation.tsv",
    )


def _validator_arguments(
    evidence: CohortCandidatePreprocessingEvidence,
    *extra: str,
) -> list[str]:
    return [
        "--cohort-id",
        "cohort",
        "--sample-manifest",
        str(evidence.sample_manifest),
        "--partition-manifest",
        str(evidence.partition_manifest),
        "--annotation-gtf",
        str(evidence.annotation_gtf),
        "--sites",
        str(evidence.sites),
        "--inputs",
        str(evidence.inputs),
        "--summary",
        str(evidence.summary),
        "--output",
        str(evidence.output),
        *extra,
    ]


def _run_validator(
    evidence: CohortCandidatePreprocessingEvidence,
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
            "cohort-candidate-preprocessing",
            *_validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        capture_output=True,
        check=False,
    )


def _published_stdout(evidence: CohortCandidatePreprocessingEvidence) -> bytes:
    return EXPECTED_PASS_REPORT + (
        f"Published Step 08 validation report: {evidence.output}\n".encode()
    )


def test_arbitrary_cwd_dry_execute_repeat_byte_parity_has_no_residue(
    tmp_path: Path,
) -> None:
    evidence = _build_validation_fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "arbitrary-cwd"
    invocation_cwd.mkdir()

    dry_run = _run_validator(evidence, cwd=invocation_cwd)
    assert dry_run.returncode == 0
    assert dry_run.stdout == EXPECTED_DRY_STDOUT
    assert dry_run.stderr == b""
    assert not evidence.output.exists()
    assert list(invocation_cwd.iterdir()) == []

    first = _run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0
    assert first.stdout == _published_stdout(evidence)
    assert first.stderr == b""
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    assert list(invocation_cwd.iterdir()) == []

    second = _run_validator(evidence, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0
    assert second.stdout == _published_stdout(evidence)
    assert second.stderr == b""
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    assert {path.name for path in evidence.output.parent.iterdir()} == {
        evidence.output.name
    }


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    evidence = _build_validation_fixture(tmp_path)
    result = _run_validator(evidence, "--execute")

    assert result.returncode == 0
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "08")
    assert {row["status"] for row in rows} == {"pass"}


def test_each_check_id_is_observable_as_exit_zero_failed_evidence(
    tmp_path: Path,
) -> None:
    check_ids = (
        "output_transaction",
        "manifest_annotation_identity",
        "input_receipt_reconciliation",
        "sites_order_uniqueness",
        "summary_count_reconciliation",
    )
    for check_id in check_ids:
        evidence = _build_validation_fixture(tmp_path / check_id)
        if check_id == "output_transaction":
            table = _read_tsv(evidence.sites)
            table[0][0] = "unexpected_partition_id"
            _write_tsv(evidence.sites, table[0], table[1:])
        elif check_id == "manifest_annotation_identity":
            _replace_column(
                evidence.inputs,
                "annotation_gtf",
                "/different/annotation.gtf",
            )
        elif check_id == "input_receipt_reconciliation":
            _replace_cell(evidence.inputs, 0, "orientation", "REV_like")
        elif check_id == "sites_order_uniqueness":
            _replace_cell(evidence.sites, 1, "candidate_id", "c1")
        else:
            _replace_cell(
                evidence.summary,
                0,
                "observed_vcf_record_count",
                "9",
            )

        result = _run_validator(evidence, "--execute")
        assert result.returncode == 0, (check_id, result.stderr)
        rows = report_rows(evidence.output)
        assert_exact_check_roster(rows, "08")
        statuses = {row["check_id"]: row["status"] for row in rows}
        assert statuses[check_id] == "fail"


def test_post_build_mutation_of_each_input_preserves_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_build = cohort_candidate_preprocessing_validator.build_validation_report
    for input_name in (
        "sample_manifest",
        "partition_manifest",
        "annotation_gtf",
        "sites",
        "inputs",
        "summary",
    ):
        evidence = _build_validation_fixture(tmp_path / input_name)
        baseline = _run_validator(evidence, "--execute")
        assert baseline.returncode == 0, baseline.stderr
        predecessor = evidence.output.read_bytes()
        target = cast(Path, getattr(evidence, input_name))
        original = target.read_bytes()

        def mutate_after_build(
            arguments: argparse.Namespace,
            target: Path = target,
            original: bytes = original,
        ) -> tuple[bytes, dict[Path, Snapshot]]:
            built = real_build(arguments)
            target.write_bytes(original + b"\n# changed after build\n")
            return built

        monkeypatch.setattr(
            cohort_candidate_preprocessing_validator,
            "build_validation_report",
            mutate_after_build,
        )
        status = emrys_main(
            [
                "validate",
                "cohort-candidate-preprocessing",
                *_validator_arguments(evidence, "--execute"),
            ]
        )

        captured = capsys.readouterr()
        assert status == 2, (input_name, captured.err)
        assert f"Input changed after validation: {target}" in captured.err
        assert evidence.output.read_bytes() == predecessor
        assert set(evidence.output.parent.iterdir()) == {evidence.output}


def test_equivalent_annotation_spelling_is_failed_identity_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_validation_fixture(tmp_path)
    alias = tmp_path / "equivalent"
    alias.mkdir()
    equivalent_annotation = alias / ".." / evidence.annotation_gtf.name
    _replace_column(evidence.inputs, "annotation_gtf", str(equivalent_annotation))
    _replace_column(evidence.summary, "annotation_gtf", str(equivalent_annotation))
    evidence = replace(evidence, annotation_gtf=equivalent_annotation)

    result = _run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "08")
    statuses = {row["check_id"]: row["status"] for row in rows}
    assert statuses["manifest_annotation_identity"] == "fail"


def test_arbitrary_candidate_ids_and_reversed_rows_are_false_passes(
    tmp_path: Path,
) -> None:
    evidence = _build_validation_fixture(tmp_path)
    table = _read_tsv(evidence.sites)
    candidate_index = table[0].index("candidate_id")
    table[1][candidate_index] = "arbitrary-unique-beta"
    table[2][candidate_index] = "arbitrary-unique-alpha"
    _write_tsv(evidence.sites, table[0], reversed(table[1:]))

    result = _run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "08")
    assert {row["status"] for row in rows} == {"pass"}


def test_summary_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_validation_fixture(tmp_path)
    text = evidence.summary.read_text(encoding="utf-8")
    evidence.summary.write_text(
        text.replace("\t2\t2\t2\t0\t0\t2\t", "\t9\t2\t2\t0\t0\t2\t"),
        encoding="utf-8",
    )

    result = _run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["summary_count_reconciliation"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = _build_validation_fixture(tmp_path)
    evidence.sites.unlink()
    assert _run_validator(evidence, "--execute").returncode == 2

    evidence = _build_validation_fixture(tmp_path / "second")
    wrong_output = replace(
        evidence,
        output=evidence.output.parent / "wrong.tsv",
    )
    assert _run_validator(wrong_output, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = _build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")

    assert _run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"
