"""Focused integration tests for the Step 09c scientific-review contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "step_09c_scientific_validation.py"
FIXTURE_BUILDER = (
    REPO_ROOT / "tests" / "fixtures" / "step09c" / "build_fixture.py"
)


def load_fixture_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "norad_step09c_fixture_builder", FIXTURE_BUILDER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Step 09c fixture builder: {FIXTURE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FIXTURES = load_fixture_builder()


def build_fixture(
    root: Path,
    science_status: str = "evidence_incomplete",
) -> Any:
    return FIXTURES.build_fixture(root, science_status)


def run_validator(
    fixture: Any,
    *,
    execute: bool = False,
    output_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    arguments = fixture.command_args()
    if output_root is not None:
        output_index = arguments.index("--output-root") + 1
        arguments[output_index] = str(output_root)
    if execute:
        arguments.append("--execute")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_single_row(path: Path) -> dict[str, str]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    assert len(rows) == 1
    return dict(rows[0])


def rewrite_field(path: Path, column: str, value: str) -> None:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    assert len(rows) == 1
    rows[0][column] = value
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def rewrite_matching_row(
    path: Path,
    match_column: str,
    match_value: str,
    updates: dict[str, str],
) -> None:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    matches = [row for row in rows if row[match_column] == match_value]
    assert len(matches) == 1
    matches[0].update(updates)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_evidence_source(
    fixture: Any,
    evidence_id: str,
    source: Path,
    row_count: int,
) -> None:
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        evidence_id,
        {
            "source_sha256": sha256_file(source),
            "source_row_count": str(row_count),
        },
    )


def expected_output_names(review_id: str) -> set[str]:
    return {
        f"{review_id}.{suffix}"
        for _, suffix in FIXTURES.CONTRACT.OUTPUT_SUFFIXES
    }


def output_directory(output_root: Path, review_id: str) -> Path:
    return output_root / review_id


def summary_path(output_root: Path, review_id: str) -> Path:
    return (
        output_directory(output_root, review_id)
        / f"{review_id}.step09c_review_summary.tsv"
    )


def assert_failed_with(result: subprocess.CompletedProcess[str], token: str) -> None:
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert token.lower() in combined


def test_dry_run_validates_fixture_without_publishing(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")

    result = run_validator(fixture)

    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert fixture.review_id in result.stdout
    assert not fixture.output_root.exists()


def test_execute_publishes_exact_transaction_and_summary_marker(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")

    result = run_validator(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    assert {path.name for path in final_dir.iterdir()} == expected_output_names(
        fixture.review_id
    )
    summary = read_single_row(summary_path(fixture.output_root, fixture.review_id))
    assert summary["overall_science_status"] == "evidence_incomplete"
    assert summary["published_output_count"] == "13"
    assert summary["transaction_state"] == "complete"
    assert not list(fixture.output_root.glob(".*step09c*"))


def test_complete_evidence_does_not_auto_upgrade_requested_incomplete_state(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(
        tmp_path / "fixture",
        science_status="evidence_incomplete",
    )

    result = run_validator(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = read_single_row(summary_path(fixture.output_root, fixture.review_id))
    assert summary["overall_science_status"] == "evidence_incomplete"
    for category in FIXTURES.CONTRACT.CATEGORY_ORDER:
        assert summary[f"{category}_status"] == "complete"


def test_reserved_biological_interpretation_state_is_rejected(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_field(
        fixture.review_plan,
        "overall_science_status",
        "biological_interpretation_ready",
    )

    result = run_validator(fixture, execute=True)

    assert_failed_with(result, "reserved")
    assert not fixture.output_root.exists()


def test_unrelated_files_do_not_change_explicit_input_outputs(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first_output = tmp_path / "first-output"
    second_output = tmp_path / "second-output"
    first = run_validator(fixture, execute=True, output_root=first_output)
    assert first.returncode == 0, first.stderr

    (fixture.step09_analysis_dir / "unrelated.cmh_summary.tsv").write_text(
        "this\tmust\nnot\tbe read\n"
    )
    evidence_dir = fixture.evidence_manifest.parent / "evidence"
    (evidence_dir / "unrelated.tsv").write_text("unrelated\ncontent\n")

    second = run_validator(fixture, execute=True, output_root=second_output)

    assert second.returncode == 0, second.stderr
    first_dir = output_directory(first_output, fixture.review_id)
    second_dir = output_directory(second_output, fixture.review_id)
    assert {
        path.name: path.read_bytes() for path in first_dir.iterdir()
    } == {path.name: path.read_bytes() for path in second_dir.iterdir()}


def test_declared_input_hash_mutation_is_rejected(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    fixture.sample_manifest.write_text(
        fixture.sample_manifest.read_text() + "\n"
    )

    result = run_validator(fixture, execute=True)

    assert_failed_with(result, "hash")
    assert not fixture.output_root.exists()


def test_declared_evidence_hash_mutation_is_rejected(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    orientation_evidence = (
        fixture.evidence_manifest.parent
        / "evidence"
        / "orientation_locus_audit.tsv"
    )
    orientation_evidence.write_text(orientation_evidence.read_text() + "\n")

    result = run_validator(fixture, execute=True)

    assert_failed_with(result, "hash")
    assert not fixture.output_root.exists()


def test_source_backed_evidence_requires_evidence_date(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_qc",
        {"evidence_date": "NA"},
    )

    result = run_validator(fixture)

    assert_failed_with(result, "evidence_date")
    assert not fixture.output_root.exists()


def test_human_reviewer_and_owner_names_are_preserved(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_field(fixture.review_plan, "reviewer", "Jane Doe")
    rewrite_field(
        fixture.review_plan,
        "decision_owner",
        "Scientific Review Team",
    )
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_qc",
        {
            "reviewer": "Jane Doe",
            "owner": "Scientific Review Team",
        },
    )
    decisions = fixture.root / "evidence" / "decisions.tsv"
    rewrite_matching_row(
        decisions,
        "decision_dimension",
        "orientation",
        {"decision_owner": "Jane Doe"},
    )
    refresh_evidence_source(fixture, "e_decisions", decisions, 7)

    result = run_validator(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = read_single_row(summary_path(fixture.output_root, fixture.review_id))
    assert summary["reviewer"] == "Jane Doe"
    assert summary["decision_owner"] == "Scientific Review Team"
    published_decisions = (
        output_directory(fixture.output_root, fixture.review_id)
        / f"{fixture.review_id}.step09c_decisions.tsv"
    )
    orientation = next(
        row
        for row in FIXTURES.CONTRACT.read_tsv(
            "published decisions",
            published_decisions,
            FIXTURES.CONTRACT.DECISIONS_HEADER,
        ).rows
        if row["decision_dimension"] == "orientation"
    )
    assert orientation["decision_owner"] == "Jane Doe"


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("plan_version", "plan version 1"),
        ("git_commit", "commit with spaces"),
        ("orientation_policy", "policy with spaces"),
        ("candidate_selection_policy_version", "policy version 1"),
    ],
)
def test_review_plan_machine_identifiers_must_be_safe(
    tmp_path: Path,
    column: str,
    value: str,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_field(fixture.review_plan, column, value)

    result = run_validator(fixture)

    assert_failed_with(result, column)
    assert not fixture.output_root.exists()


def test_evidence_policy_version_must_be_safe(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_qc",
        {"policy_version": "policy version 1"},
    )

    result = run_validator(fixture)

    assert_failed_with(result, "policy_version")
    assert not fixture.output_root.exists()


def test_limitation_identifiers_and_statuses_match_review_schema(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "limitations.tsv"
    rewrite_matching_row(
        source,
        "limitation_id",
        "lim_orientation",
        {
            "limitation_id": "unsafe limitation",
            "limitation_status": "unsupported",
        },
    )
    refresh_evidence_source(fixture, "e_limitations", source, 3)

    result = run_validator(fixture)

    assert_failed_with(result, "limitation_id")
    assert not fixture.output_root.exists()


def test_superseded_and_sensitivity_analysis_ids_must_be_disjoint(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_field(
        fixture.review_plan,
        "superseded_analysis_ids",
        "analysis_sensitivity_dp",
    )

    result = run_validator(fixture)

    assert_failed_with(result, "must be disjoint")
    assert not fixture.output_root.exists()


def test_evidence_analysis_assignment_is_category_specific(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_annotation",
        {"analysis_id": "analysis_sensitivity"},
    )

    result = run_validator(fixture)

    assert_failed_with(result, "annotation_audit")
    assert_failed_with(result, "analysis_id")
    assert not fixture.output_root.exists()


def test_non_loo_payload_analysis_must_match_manifest(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "annotation_audit.tsv"
    rewrite_matching_row(
        source,
        "audit_id",
        "audit_cds",
        {"analysis_id": "analysis_sensitivity"},
    )
    refresh_evidence_source(fixture, "e_annotation", source, 8)

    result = run_validator(fixture)

    assert_failed_with(result, "different from its manifest")
    assert not fixture.output_root.exists()


def test_pending_decision_must_not_cite_supporting_evidence(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "decisions.tsv"
    rewrite_matching_row(
        source,
        "decision_dimension",
        "orientation",
        {
            "decision_status": "pending",
            "decision_value": "NA",
            "decision_date": "NA",
        },
    )
    refresh_evidence_source(fixture, "e_decisions", source, 7)

    result = run_validator(fixture)

    assert_failed_with(result, "must not cite supporting")
    assert not fixture.output_root.exists()


def test_recorded_decision_requires_complete_support(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "decisions.tsv"
    rewrite_matching_row(
        source,
        "decision_dimension",
        "orientation",
        {"supporting_evidence_ids": "e_annotation"},
    )
    refresh_evidence_source(fixture, "e_decisions", source, 7)
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_annotation",
        {"evidence_status": "incomplete"},
    )

    result = run_validator(fixture)

    assert_failed_with(result, "cannot cite missing or incomplete")
    assert not fixture.output_root.exists()


def test_recorded_decision_requires_nonempty_support(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "decisions.tsv"
    rewrite_matching_row(
        source,
        "decision_dimension",
        "orientation",
        {"supporting_evidence_ids": "NA"},
    )
    refresh_evidence_source(fixture, "e_decisions", source, 7)

    result = run_validator(fixture)

    assert_failed_with(result, "at least one supporting")
    assert not fixture.output_root.exists()


def test_decision_rerun_flag_and_scope_must_agree(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "decisions.tsv"
    rewrite_matching_row(
        source,
        "decision_dimension",
        "orientation",
        {
            "rerun_required": "TRUE",
            "rerun_scope": "none",
        },
    )
    refresh_evidence_source(fixture, "e_decisions", source, 7)

    result = run_validator(fixture)

    assert_failed_with(result, "rerun_required")
    assert not fixture.output_root.exists()


def test_computational_evidence_accepts_multiple_distinct_roles(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "computational_validation.tsv"
    with source.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None and len(rows) == 1
    rows.append(
        {
            **rows[0],
            "validation_scope": "runtime_validation",
            "validation_status": "blocked",
            "evidence_path": "NA",
            "evidence_sha256": "NA",
            "scheduler_state": "NA",
            "exit_code": "NA",
            "notes": "Synthetic runtime remains blocked.",
        }
    )
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    refresh_evidence_source(fixture, "e_computational", source, 2)

    result = run_validator(fixture)

    assert result.returncode == 0, result.stderr
    assert not fixture.output_root.exists()


def test_passed_runtime_requires_log_and_output_roles(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_field(
        fixture.review_plan,
        "runtime_validation_status",
        "passed",
    )
    source = fixture.root / "evidence" / "computational_validation.tsv"
    with source.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None and len(rows) == 1
    runtime_evidence = fixture.root / "runtime-output.tsv"
    runtime_evidence.write_text("synthetic runtime output\n")
    rows.append(
        {
            **rows[0],
            "validation_scope": "runtime_validation",
            "validation_status": "passed",
            "evidence_path": str(runtime_evidence),
            "evidence_sha256": sha256_file(runtime_evidence),
            "scheduler_state": "COMPLETED",
            "exit_code": "0",
            "notes": "Synthetic runtime output without its required log.",
        }
    )
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    refresh_evidence_source(fixture, "e_computational", source, 2)

    result = run_validator(fixture)

    assert_failed_with(result, "runtime_log")
    assert not fixture.output_root.exists()


def test_local_test_claim_requires_complete_computational_evidence(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_computational",
        {
            "source_path": "NA",
            "source_sha256": "NA",
            "source_row_count": "NA",
            "evidence_status": "missing",
            "not_applicable_reason": "NA",
            "evidence_date": "NA",
        },
    )

    result = run_validator(fixture)

    assert_failed_with(result, "local_test_status")
    assert not fixture.output_root.exists()


@pytest.mark.parametrize(
    ("updates", "token"),
    [
        ({"validation_scope": "arbitrary_scope"}, "must be one of"),
        ({"validation_status": "failed"}, "does not exactly support"),
    ],
)
def test_computational_scope_and_status_contract_is_closed(
    tmp_path: Path,
    updates: dict[str, str],
    token: str,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "computational_validation.tsv"
    rewrite_matching_row(
        source,
        "validation_scope",
        "local_fixture_tests",
        updates,
    )
    refresh_evidence_source(fixture, "e_computational", source, 1)

    result = run_validator(fixture)

    assert_failed_with(result, token)
    assert not fixture.output_root.exists()


def test_exploratory_completion_requires_and_preserves_complete_evidence(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(
        tmp_path / "fixture",
        science_status="science_review_complete_exploratory",
    )

    result = run_validator(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = read_single_row(summary_path(fixture.output_root, fixture.review_id))
    assert (
        summary["overall_science_status"]
        == "science_review_complete_exploratory"
    )
    assert summary["review_completed_date"] == "2026-01-10"
    assert summary["selected_candidate_count"] == "4"
    assert summary["adjudicated_candidate_count"] == "4"
    for category in FIXTURES.CONTRACT.CATEGORY_ORDER:
        assert summary[f"{category}_status"] == "complete"


def test_input_mutation_after_validation_aborts_before_publication(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    orientation_evidence = (
        fixture.evidence_manifest.parent
        / "evidence"
        / "orientation_locus_audit.tsv"
    )
    orientation_evidence.write_text(
        orientation_evidence.read_text() + "# changed after validation\n"
    )

    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="changed"):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    final_dir = output_directory(fixture.output_root, fixture.review_id)
    assert final_dir.is_dir()
    assert list(final_dir.iterdir()) == []


def test_first_publication_failure_removes_partial_outputs_and_owned_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    original_replace = FIXTURES.CONTRACT.os.replace
    failed = False

    def fail_one_publish(source: Any, destination: Any) -> None:
        nonlocal failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not failed
            and source_path.parent.name.endswith(".tmp")
            and destination_path.name.endswith("step09c_qc_funnel.tsv")
        ):
            failed = True
            raise OSError("synthetic publication failure")
        original_replace(source, destination)

    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", fail_one_publish)

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="synthetic publication failure",
    ):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    final_dir = output_directory(fixture.output_root, fixture.review_id)
    assert final_dir.is_dir()
    assert list(final_dir.iterdir()) == []


def test_replacement_failure_restores_byte_identical_prior_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    original_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }

    rewrite_field(
        fixture.review_plan,
        "notes",
        "Synthetic replacement that must be rolled back.",
    )
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    original_replace = FIXTURES.CONTRACT.os.replace
    failed = False

    def fail_one_publish(source: Any, destination: Any) -> None:
        nonlocal failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not failed
            and source_path.parent.name.endswith(".tmp")
            and destination_path.name.endswith("step09c_qc_funnel.tsv")
        ):
            failed = True
            raise OSError("synthetic replacement failure")
        original_replace(source, destination)

    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", fail_one_publish)

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="synthetic replacement failure",
    ):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    } == original_bytes


def test_tracked_examples_and_schema_headers_match_public_contract() -> None:
    contract = FIXTURES.CONTRACT
    plan_path = REPO_ROOT / "configs" / "step_09c_review_plan.example.tsv"
    manifest_path = (
        REPO_ROOT / "configs" / "step_09c_evidence_manifest.example.tsv"
    )
    plan_table, plan, analyses = contract.validate_review_plan(
        plan_path, "example_scientific_review"
    )
    assert plan_table.header == contract.REVIEW_PLAN_HEADER
    assert plan["overall_science_status"] == "evidence_incomplete"
    manifest, rows, payloads, _ = contract.validate_evidence_manifest(
        manifest_path,
        "example_scientific_review",
        plan,
        {},
    )
    assert manifest.header == contract.EVIDENCE_MANIFEST_HEADER
    assert [row["evidence_category"] for row in rows] == list(
        contract.CATEGORY_ORDER
    )
    assert all(not payloads[category] for category in contract.CATEGORY_ORDER)

    schema_root = REPO_ROOT / "configs" / "step_09c_evidence_schemas"
    expected_headers = {
        **contract.CATEGORY_HEADERS,
        "computational_validation": contract.COMPUTATIONAL_VALIDATION_HEADER,
        "evidence_index": contract.EVIDENCE_INDEX_HEADER,
        "review_summary": contract.REVIEW_SUMMARY_HEADER,
    }
    for category, expected_header in expected_headers.items():
        table = contract.read_tsv(
            f"{category} schema",
            schema_root / f"{category}.schema.tsv",
            expected_header,
        )
        assert table.rows == []


def test_incomplete_review_preserves_missing_incomplete_and_na_dimensions(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_replicates",
        {
            "source_path": "NA",
            "source_sha256": "NA",
            "source_row_count": "NA",
            "evidence_status": "missing",
        },
    )
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_annotation",
        {"evidence_status": "incomplete"},
    )
    rewrite_matching_row(
        fixture.evidence_manifest,
        "evidence_id",
        "e_limitations",
        {
            "source_path": "NA",
            "source_sha256": "NA",
            "source_row_count": "NA",
            "evidence_status": "not_applicable",
            "not_applicable_reason": "Synthetic review has no added limitation.",
        },
    )

    result = run_validator(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = read_single_row(summary_path(fixture.output_root, fixture.review_id))
    assert summary["overall_science_status"] == "evidence_incomplete"
    assert summary["replicate_effects_status"] == "missing"
    assert summary["annotation_audit_status"] == "incomplete"
    assert summary["limitations_status"] == "not_applicable"


def test_complete_zero_row_replicate_evidence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(
        tmp_path / "fixture",
        science_status="science_review_complete_exploratory",
    )
    source = fixture.root / "evidence" / "replicate_effects.tsv"
    source.write_text(source.read_text().splitlines()[0] + "\n")
    refresh_evidence_source(fixture, "e_replicates", source, 0)

    result = run_validator(fixture)

    assert_failed_with(result, "replicate-effects")


@pytest.mark.parametrize(
    ("evidence_id", "filename", "column", "value", "token"),
    [
        (
            "e_orientation",
            "orientation_locus_audit.tsv",
            "raw_ad",
            "11",
            "raw count",
        ),
        (
            "e_orientation",
            "orientation_locus_audit.tsv",
            "flag_group",
            "83",
            "mechanical orientation",
        ),
        (
            "e_annotation",
            "annotation_audit.tsv",
            "observed_gene_ids",
            "fabricated_gene",
            "candidate annotation",
        ),
        (
            "e_adjudication",
            "candidate_adjudication.tsv",
            "coverage_status",
            "fabricated_status",
            "coverage_status",
        ),
        (
            "e_adjudication",
            "candidate_adjudication.tsv",
            "coverage_status",
            "fail",
            "status=pass",
        ),
    ],
)
def test_malformed_scientific_evidence_is_rejected(
    tmp_path: Path,
    evidence_id: str,
    filename: str,
    column: str,
    value: str,
    token: str,
) -> None:
    fixture = build_fixture(
        tmp_path / "fixture",
        science_status="science_review_complete_exploratory",
    )
    source = fixture.root / "evidence" / filename
    with source.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None and rows
    rows[0][column] = value
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    refresh_evidence_source(fixture, evidence_id, source, len(rows))

    result = run_validator(fixture)

    assert_failed_with(result, token)


def test_cluster_proof_cannot_be_claimed_with_zero_computational_records(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    for column, value in (
        ("runtime_validation_status", "passed"),
        ("cluster_dry_run_status", "passed"),
        ("cluster_proof_status", "proven"),
    ):
        rewrite_field(fixture.review_plan, column, value)
    source = fixture.root / "evidence" / "computational_validation.tsv"
    source.write_text(source.read_text().splitlines()[0] + "\n")
    refresh_evidence_source(fixture, "e_computational", source, 0)

    result = run_validator(fixture)

    assert_failed_with(result, "computational-validation evidence")


def test_passed_computational_record_rejects_failed_scheduler_and_exit(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    source = fixture.root / "evidence" / "computational_validation.tsv"
    with source.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None and len(rows) == 1
    rows[0]["scheduler_state"] = "FAILED"
    rows[0]["exit_code"] = "99"
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    refresh_evidence_source(fixture, "e_computational", source, 1)

    result = run_validator(fixture)

    assert_failed_with(result, "exit_code=0")


def test_step09_target_status_inconsistency_is_rejected_mechanically(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, _ = FIXTURES.CONTRACT.build_context(arguments)
    rows = [dict(row) for row in context.step09_all_rows]
    non_target = next(row for row in rows if row["rna_ref"] == "C")
    non_target["test_status"] = "tested"
    non_target["call_status"] = "effect_not_met"

    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="target change"):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            rows,
            context.step09_summary,
            context.sample_rows,
        )

    non_target["test_status"] = "not_target_change"
    non_target["call_status"] = "not_tested"
    target = next(
        row
        for row in rows
        if row["test_status"] == "tested" and row["rna_ref"] == "A"
    )
    target["test_status"] = "missing_counts"
    target["call_status"] = "not_tested"
    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="availability/coverage",
    ):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            rows,
            context.step09_summary,
            context.sample_rows,
        )


def test_step09_reported_metrics_reconcile_with_immutable_counts(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, _ = FIXTURES.CONTRACT.build_context(arguments)

    wrong_depth = [dict(row) for row in context.step09_all_rows]
    tested = next(row for row in wrong_depth if row["test_status"] == "tested")
    tested["mean_analysis_dp"] = "999"
    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="depth metrics"):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            wrong_depth,
            context.step09_summary,
            context.sample_rows,
        )

    false_cmh = [dict(row) for row in context.step09_all_rows]
    untested = next(
        row for row in false_cmh if row["test_status"] == "low_coverage"
    )
    untested.update(
        {
            "cmh_statistic": "1",
            "cmh_degrees_freedom": "1",
            "cmh_p_value": "0.5",
            "cmh_fdr_bh": "0.5",
            "common_odds_ratio": "2",
        }
    )
    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="must use"):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            false_cmh,
            context.step09_summary,
            context.sample_rows,
        )
