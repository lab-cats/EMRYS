from __future__ import annotations

import argparse
import csv
import stat
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from norad.__main__ import main as norad_main
from norad.analyses.paired_cmh_candidate_ranking import validator
from norad.libraries.validation import Snapshot
from tests import scientific_evidence_test_support as fixture_builder
from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
RUNTIME_FAILURE = 2
REPORT_MODE = 0o644
INPUT_NAMES = (
    "sample_manifest",
    "partition_manifest",
    "step08_sites",
    "step08_inputs",
    "all_sites",
    "significant_sites",
    "summary",
    "mutation_spectrum",
    "mutation_spectrum_pdf",
    "depth_delta_pdf",
)
EXPECTED_PASS_REPORT = (
    b"step_id\tscope_id\tcheck_id\tstatus\tobserved\texpected\tdetail\n"
    b"09\tanalysis_primary\toutput_transaction\tpass\t"
    b"headers=validated; six regular snapshots\tfour exact TSV headers; "
    b"analysis-bound basenames; one parent; six distinct physical files\t"
    b"native Step 09 output transaction\n"
    b"09\tanalysis_primary\tupstream_identity_and_candidate_order\tpass\t"
    b"all=validated; significant=validated\tsafe analysis/cohort; provisional "
    b"policy; complete ordered Step 08 candidate universe\tids=validated; "
    b"sample=validated; partition=validated; inputs=validated; sites=validated\n"
    b"09\tanalysis_primary\tstatus_semantics\tpass\tvalidated\treconciled "
    b"target/test/call, depth, AF, background, and BH; CMH values not "
    b"independently recomputed\t"
    b"native Step 09 statistical-state contract\n"
    b"09\tanalysis_primary\tsignificant_subset\tpass\tvalidated\t"
    b"exact ordered significant subset\tall-sites versus significant-sites\n"
    b"09\tanalysis_primary\tsummary_count_reconciliation\tpass\tvalidated\t"
    b"one analysis/cohort-bound summary with exact counts and provenance\t"
    b"paths, hashes, pairings, context, policy, and thresholds\n"
    b"09\tanalysis_primary\tmutation_spectrum_reconciliation\tpass\tvalidated\t"
    b"canonical 12-SNV spectrum matching all-sites\tmutation counts, fractions, "
    b"and significant directions\n"
    b"09\tanalysis_primary\tpdf_structure\tpass\t"
    b"mutation=validated; depth=validated\ttwo structurally valid PDFs\t"
    b"plot output containers\n"
)
EXPECTED_DRY_STDOUT = (
    EXPECTED_PASS_REPORT + b"Dry-run complete; no output was written.\n"
)


@dataclass(frozen=True, slots=True)
class PairedCmhEvidence:
    sample_manifest: Path
    partition_manifest: Path
    step08_sites: Path
    step08_inputs: Path
    all_sites: Path
    significant_sites: Path
    summary: Path
    mutation_spectrum: Path
    mutation_spectrum_pdf: Path
    depth_delta_pdf: Path
    output: Path

    @property
    def input_paths(self) -> tuple[Path, ...]:
        return tuple(getattr(self, name) for name in INPUT_NAMES)


def _build_evidence(root: Path) -> PairedCmhEvidence:
    built = fixture_builder.build_fixture(root)
    analysis_id = fixture_builder.PRIMARY_ANALYSIS_ID
    validation_dir = root / "validation"
    validation_dir.mkdir()
    return PairedCmhEvidence(
        sample_manifest=built.sample_manifest,
        partition_manifest=built.partition_manifest,
        step08_sites=built.step08_sites,
        step08_inputs=built.step08_inputs,
        all_sites=built.step09_analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        significant_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        summary=built.step09_analysis_dir / f"{analysis_id}.cmh_summary.tsv",
        mutation_spectrum=(
            built.step09_analysis_dir / f"{analysis_id}.mutation_spectrum.tsv"
        ),
        mutation_spectrum_pdf=(
            built.step09_analysis_dir / f"{analysis_id}.mutation_spectrum.pdf"
        ),
        depth_delta_pdf=(built.step09_analysis_dir / f"{analysis_id}.depth_delta.pdf"),
        output=validation_dir / f"{analysis_id}.validation.tsv",
    )


def _arguments(evidence: PairedCmhEvidence, *extra: str) -> list[str]:
    return [
        "--analysis-id",
        fixture_builder.PRIMARY_ANALYSIS_ID,
        "--cohort-id",
        fixture_builder.COHORT_ID,
        "--sample-manifest",
        str(evidence.sample_manifest),
        "--partition-manifest",
        str(evidence.partition_manifest),
        "--step08-sites",
        str(evidence.step08_sites),
        "--step08-inputs",
        str(evidence.step08_inputs),
        "--all-sites",
        str(evidence.all_sites),
        "--significant-sites",
        str(evidence.significant_sites),
        "--summary",
        str(evidence.summary),
        "--mutation-spectrum",
        str(evidence.mutation_spectrum),
        "--mutation-spectrum-pdf",
        str(evidence.mutation_spectrum_pdf),
        "--depth-delta-pdf",
        str(evidence.depth_delta_pdf),
        "--output",
        str(evidence.output),
        *extra,
    ]


def _run(
    evidence: PairedCmhEvidence,
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
            "paired-cmh-candidate-ranking",
            *_arguments(evidence, *extra),
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _published_stdout(evidence: PairedCmhEvidence) -> str:
    return (
        EXPECTED_PASS_REPORT.decode("utf-8")
        + f"Published Step 09 validation report: {evidence.output}\n"
    )


def _assert_failed_check(evidence: PairedCmhEvidence, check_id: str) -> None:
    result = _run(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    rows = report_rows(evidence.output)
    assert {row["check_id"]: row["status"] for row in rows}[check_id] == "fail"
    assert result.stdout.encode("utf-8").startswith(evidence.output.read_bytes())


def _replace_tsv_cell(path: Path, column: str, value: str) -> None:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    rows[0][column] = value
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def test_arbitrary_cwd_dry_execute_repeat_byte_parity_has_no_residue(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path / "fixture")
    invocation_cwd = tmp_path / "arbitrary-cwd"
    invocation_cwd.mkdir()
    before = {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    }

    dry = _run(evidence, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.encode("utf-8") == EXPECTED_DRY_STDOUT
    assert not evidence.output.exists()

    first = _run(evidence, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    assert first.stdout == _published_stdout(evidence)
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    assert stat.S_IMODE(evidence.output.stat().st_mode) == REPORT_MODE
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "09")
    assert {row["status"] for row in rows} == {"pass"}

    second = _run(evidence, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == EXPECTED_PASS_REPORT
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in evidence.input_paths
    } == before
    assert list(invocation_cwd.iterdir()) == []
    assert set(evidence.output.parent.iterdir()) == {evidence.output}


def test_summary_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    _replace_tsv_cell(evidence.summary, "candidate_count", "999")
    _assert_failed_check(evidence, "summary_count_reconciliation")


def test_candidate_reordering_is_failed_upstream_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    lines = evidence.all_sites.read_text(encoding="utf-8").splitlines()
    lines[-2], lines[-1] = lines[-1], lines[-2]
    evidence.all_sites.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _assert_failed_check(evidence, "upstream_identity_and_candidate_order")


def test_wrong_cohort_is_failed_identity_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    result = _run(evidence, "--cohort-id", "wrong_cohort", "--execute")
    assert result.returncode == 0, result.stderr
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["upstream_identity_and_candidate_order"] == "fail"


def test_nonprovisional_orientation_policy_is_failed_identity_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    evidence.step08_inputs.write_text(
        evidence.step08_inputs.read_text(encoding="utf-8").replace(
            "legacy_provisional_v1",
            "unsupported_policy",
        ),
        encoding="utf-8",
    )
    _assert_failed_check(evidence, "upstream_identity_and_candidate_order")


def test_incorrect_bh_adjustment_is_failed_semantic_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    _replace_tsv_cell(evidence.all_sites, "cmh_fdr_bh", "0.002")
    _assert_failed_check(evidence, "status_semantics")


def test_fabricated_cmh_statistics_pvalues_bh_and_odds_ratios_all_pass(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    fabricated = {
        "FWD_like|1|10|T>C": {
            "cmh_statistic": "999999",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "999",
        },
        "REV_like|1|20|A>G": {
            "cmh_statistic": "0.000001",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "0.001",
        },
        "REV_like|2|60|A>G": {
            "cmh_statistic": "123456",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "1.1",
        },
    }
    for path in (evidence.all_sites, evidence.significant_sites):
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fieldnames = reader.fieldnames
            table = list(reader)
        assert fieldnames is not None
        for row in table:
            row.update(fabricated.get(row["candidate_id"], {}))
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(table)

    result = _run(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "09")
    by_check = {row["check_id"]: row for row in rows}
    status_row = by_check["status_semantics"]
    assert status_row["status"] == "pass", status_row
    assert {row["status"] for row in rows} == {"pass"}, by_check
    assert status_row["expected"] == (
        "reconciled target/test/call, depth, AF, background, and BH; CMH "
        "values not independently recomputed"
    )


@pytest.mark.parametrize("input_name", INPUT_NAMES)
def test_post_build_mutation_of_each_input_preserves_predecessor_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    input_name: str,
) -> None:
    evidence = _build_evidence(tmp_path)
    baseline = _run(evidence, "--execute")
    assert baseline.returncode == 0, baseline.stderr
    predecessor = evidence.output.read_bytes()
    before = {path: path.read_bytes() for path in evidence.input_paths}
    target = getattr(evidence, input_name)
    real_build = validator.build_validation_report

    def mutate_after_build(
        arguments: argparse.Namespace,
    ) -> tuple[bytes, dict[Path, Snapshot]]:
        built = real_build(arguments)
        target.write_bytes(before[target] + b"post-build mutation\n")
        return built

    monkeypatch.setattr(validator, "build_validation_report", mutate_after_build)
    status = norad_main(
        [
            "validate",
            "paired-cmh-candidate-ranking",
            *_arguments(evidence, "--execute"),
        ]
    )

    captured = capsys.readouterr()
    assert status == RUNTIME_FAILURE
    assert f"Input changed after validation: {target}" in captured.err
    assert evidence.output.read_bytes() == predecessor
    assert target.read_bytes() == before[target] + b"post-build mutation\n"
    assert {
        path: path.read_bytes() for path in evidence.input_paths if path != target
    } == {path: data for path, data in before.items() if path != target}
    assert set(evidence.output.parent.iterdir()) == {evidence.output}


def test_significant_subset_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    lines = evidence.significant_sites.read_text(encoding="utf-8").splitlines()
    evidence.significant_sites.write_text(
        "\n".join(lines[:-1]) + "\n",
        encoding="utf-8",
    )
    _assert_failed_check(evidence, "significant_subset")


def test_mutation_spectrum_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    _replace_tsv_cell(evidence.mutation_spectrum, "candidate_count", "999")
    _assert_failed_check(evidence, "mutation_spectrum_reconciliation")


def test_truncated_pdf_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    evidence.mutation_spectrum_pdf.write_bytes(b"%PDF-1.4\ntruncated\n")
    _assert_failed_check(evidence, "pdf_structure")


def test_analysis_bound_filename_mismatch_is_failed_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    wrong_name = evidence.all_sites.with_name("wrong.cmh_all_sites.tsv")
    evidence.all_sites.rename(wrong_name)
    _assert_failed_check(replace(evidence, all_sites=wrong_name), "output_transaction")


def test_cross_directory_member_is_failed_transaction_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    moved = other / evidence.depth_delta_pdf.name
    evidence.depth_delta_pdf.rename(moved)
    _assert_failed_check(
        replace(evidence, depth_delta_pdf=moved),
        "output_transaction",
    )


def test_hardlinked_pdf_members_are_failed_transaction_evidence(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    evidence.depth_delta_pdf.unlink()
    evidence.depth_delta_pdf.hardlink_to(evidence.mutation_spectrum_pdf)
    _assert_failed_check(evidence, "output_transaction")


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    evidence.all_sites.unlink()
    missing = _run(evidence, "--execute")
    assert missing.returncode == RUNTIME_FAILURE
    assert not evidence.output.exists()

    second = _build_evidence(tmp_path / "second")
    wrong_output = replace(second, output=second.output.parent / "wrong.tsv")
    rejected = _run(wrong_output, "--execute")
    assert rejected.returncode == RUNTIME_FAILURE
    assert not wrong_output.output.exists()


def test_invalid_utf8_all_sites_is_failed_evidence(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    evidence.all_sites.write_bytes(b"\xff")

    result = _run(evidence, "--execute")
    assert result.returncode == 0
    assert result.stderr == ""
    rows = report_rows(evidence.output)
    assert {row["check_id"]: row["status"] for row in rows} == {
        "output_transaction": "fail",
        "upstream_identity_and_candidate_order": "fail",
        "status_semantics": "fail",
        "significant_subset": "fail",
        "summary_count_reconciliation": "fail",
        "mutation_spectrum_reconciliation": "fail",
        "pdf_structure": "pass",
    }
    assert "invalid start byte" in evidence.output.read_text(encoding="utf-8")
    assert result.stdout.encode("utf-8").startswith(evidence.output.read_bytes())


def test_symlinked_input_fails_closed(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    target = evidence.mutation_spectrum_pdf.with_name("real.pdf")
    evidence.mutation_spectrum_pdf.rename(target)
    evidence.mutation_spectrum_pdf.symlink_to(target)

    result = _run(evidence, "--execute")
    assert result.returncode == RUNTIME_FAILURE
    assert not evidence.output.exists()


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")

    result = _run(evidence, "--execute")
    assert result.returncode == RUNTIME_FAILURE
    assert lock.read_text(encoding="utf-8") == "foreign\n"
