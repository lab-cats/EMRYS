"""Focused integration tests for the Step 09c scientific-review contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import multiprocessing
import signal
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


def publish_with_summary_barrier(
    context: Any,
    tables: Any,
    ready: Any,
    release: Any,
) -> None:
    contract = FIXTURES.CONTRACT
    original_replace = contract.os.replace
    summary = context.output_paths["review_summary"]
    barrier_reached = False

    def wait_after_summary(source: Any, destination: Any) -> None:
        nonlocal barrier_reached
        source_path = Path(source)
        destination_path = Path(destination)
        original_replace(source, destination)
        if (
            not barrier_reached
            and source_path.parent.name.endswith(".tmp")
            and destination_path == summary
        ):
            barrier_reached = True
            ready.set()
            if not release.wait(20):
                raise RuntimeError("summary barrier release timed out")

    contract.os.replace = wait_after_summary
    contract.publish_outputs(context, tables)


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


def expected_fixture_input_paths(fixture: Any) -> set[Path]:
    relative_paths = {
        "samples.tsv",
        "partitions.tsv",
        "step08/cohort.step08_sites.tsv",
        "step08/cohort.step08_inputs.tsv",
        "step08/cohort.step08_summary.tsv",
        "step09/analysis_primary/analysis_primary.cmh_all_sites.tsv",
        "step09/analysis_primary/analysis_primary.cmh_significant_sites.tsv",
        "step09/analysis_primary/analysis_primary.cmh_summary.tsv",
        "step09/analysis_primary/analysis_primary.mutation_spectrum.tsv",
        "step09/analysis_primary/analysis_primary.mutation_spectrum.pdf",
        "step09/analysis_primary/analysis_primary.depth_delta.pdf",
        "review_plan.tsv",
        "evidence_manifest.tsv",
        "evidence/orientation_locus_audit.tsv",
        "evidence/annotation_audit.tsv",
        "evidence/qc_funnel.tsv",
        "evidence/replicate_effects.tsv",
        "evidence/sensitivity_matrix.tsv",
        "evidence/leave_one_pair_out.tsv",
        "evidence/candidate_selection.tsv",
        "evidence/candidate_adjudication.tsv",
        "evidence/decisions.tsv",
        "evidence/limitations.tsv",
        "evidence/computational_validation.tsv",
        (
            "step09/analysis_sensitivity_dp/"
            "analysis_sensitivity_dp.cmh_summary.tsv"
        ),
        (
            "step09/analysis_sensitivity_effect/"
            "analysis_sensitivity_effect.cmh_summary.tsv"
        ),
        "step09/analysis_loo_2/analysis_loo_2.cmh_all_sites.tsv",
        "step09/analysis_loo_2/analysis_loo_2.cmh_summary.tsv",
        "step09/analysis_loo_3/analysis_loo_3.cmh_all_sites.tsv",
        "step09/analysis_loo_3/analysis_loo_3.cmh_summary.tsv",
        "step09/analysis_loo_4/analysis_loo_4.cmh_all_sites.tsv",
        "step09/analysis_loo_4/analysis_loo_4.cmh_summary.tsv",
    }
    assert len(relative_paths) == 32
    return {(fixture.root / relative).resolve() for relative in relative_paths}


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


def test_context_binds_exact_32_file_fixture_roster(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, _ = FIXTURES.CONTRACT.build_context(arguments)

    assert set(context.input_hashes) == expected_fixture_input_paths(fixture)
    assert len(context.input_hashes) == 32


@pytest.mark.parametrize(
    ("relative_path", "action", "expected_error"),
    [
        (
            "step09/analysis_primary/analysis_primary.depth_delta.pdf",
            "disappear",
            "disappeared",
        ),
        ("evidence/orientation_locus_audit.tsv", "mutate", "changed"),
        (
            "step09/analysis_sensitivity_dp/"
            "analysis_sensitivity_dp.cmh_summary.tsv",
            "mutate",
            "changed",
        ),
        (
            "step09/analysis_loo_2/analysis_loo_2.cmh_all_sites.tsv",
            "mutate",
            "changed",
        ),
    ],
)
def test_input_identity_change_aborts_before_publication_with_clean_owned_state(
    tmp_path: Path,
    relative_path: str,
    action: str,
    expected_error: str,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    changed_input = fixture.root / relative_path
    assert changed_input.resolve() in context.input_hashes
    if action == "disappear":
        changed_input.unlink()
    else:
        changed_input.write_bytes(changed_input.read_bytes() + b"changed\n")

    final_dir = output_directory(fixture.output_root, fixture.review_id)
    final_dir.mkdir(parents=True)
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")

    with pytest.raises(FIXTURES.CONTRACT.ContractError, match=expected_error):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert set(final_dir.iterdir()) == {unrelated}


def test_identical_byte_input_replacement_is_not_detected(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    target = (
        fixture.root
        / "step09"
        / "analysis_sensitivity_effect"
        / "analysis_sensitivity_effect.cmh_summary.tsv"
    )
    original_bytes = target.read_bytes()
    retained_original = target.with_name(f"{target.name}.original")
    target.rename(retained_original)
    target.write_bytes(original_bytes)
    assert target.stat().st_ino != retained_original.stat().st_ino

    FIXTURES.CONTRACT.confirm_inputs_unchanged(context.input_hashes)
    FIXTURES.CONTRACT.publish_outputs(context, tables)

    final_dir = output_directory(fixture.output_root, fixture.review_id)
    assert {path.name for path in final_dir.iterdir()} == expected_output_names(
        fixture.review_id
    )


def test_first_publication_moves_twelve_payloads_then_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    ordered_keys = [key for key, _ in FIXTURES.CONTRACT.OUTPUT_SUFFIXES]
    final_by_path = {path: key for key, path in context.output_paths.items()}
    original_replace = FIXTURES.CONTRACT.os.replace
    original_read_tsv = FIXTURES.CONTRACT.read_tsv
    original_confirm = FIXTURES.CONTRACT.confirm_inputs_unchanged
    published_reads: list[str] = []
    confirm_count = 0
    publication_order: list[str] = []
    barrier: dict[str, Any] = {}

    def observe_read_tsv(label: str, *args: Any, **kwargs: Any) -> Any:
        if label.startswith("Published Step 09c"):
            published_reads.append(label)
        return original_read_tsv(label, *args, **kwargs)

    def observe_confirm(input_hashes: Any) -> None:
        nonlocal confirm_count
        confirm_count += 1
        original_confirm(input_hashes)

    def observe_replace(source: Any, destination: Any) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        original_replace(source, destination)
        key = final_by_path.get(destination_path)
        if key is None or not source_path.parent.name.endswith(".tmp"):
            return
        publication_order.append(key)
        if key == "review_summary":
            output_dir = destination_path.parent
            temp_dirs = list(
                output_dir.glob(f".{fixture.review_id}.step09c.*.tmp")
            )
            barrier.update(
                finals={
                    output_key
                    for output_key, path in context.output_paths.items()
                    if path.is_file()
                },
                lock_is_file=(
                    output_dir / f".{fixture.review_id}.step09c.lock"
                ).is_file(),
                temp_dir_count=len(temp_dirs),
                temp_dir_entries=(
                    list(temp_dirs[0].iterdir()) if len(temp_dirs) == 1 else []
                ),
                backup_dir_count=len(
                    list(
                        output_dir.glob(
                            f".{fixture.review_id}.step09c.*.previous"
                        )
                    )
                ),
                published_read_count=len(published_reads),
                confirm_count=confirm_count,
            )

    monkeypatch.setattr(FIXTURES.CONTRACT, "read_tsv", observe_read_tsv)
    monkeypatch.setattr(
        FIXTURES.CONTRACT,
        "confirm_inputs_unchanged",
        observe_confirm,
    )
    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", observe_replace)

    FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert publication_order == ordered_keys
    assert barrier == {
        "finals": set(ordered_keys),
        "lock_is_file": True,
        "temp_dir_count": 1,
        "temp_dir_entries": [],
        "backup_dir_count": 0,
        "published_read_count": 0,
        "confirm_count": 1,
    }
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    assert {path.name for path in final_dir.iterdir()} == expected_output_names(
        fixture.review_id
    )


def test_replacement_backs_up_summary_first_then_publishes_summary_last(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    rewrite_field(fixture.review_plan, "notes", "Replacement publication order.")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    ordered_keys = [key for key, _ in FIXTURES.CONTRACT.OUTPUT_SUFFIXES]
    key_by_name = {path.name: key for key, path in context.output_paths.items()}
    final_by_path = {path: key for key, path in context.output_paths.items()}
    original_replace = FIXTURES.CONTRACT.os.replace
    original_read_tsv = FIXTURES.CONTRACT.read_tsv
    original_confirm = FIXTURES.CONTRACT.confirm_inputs_unchanged
    operations: list[tuple[str, str]] = []
    published_reads: list[str] = []
    confirm_count = 0
    barrier: dict[str, Any] = {}

    def observe_read_tsv(label: str, *args: Any, **kwargs: Any) -> Any:
        if label.startswith("Published Step 09c"):
            published_reads.append(label)
        return original_read_tsv(label, *args, **kwargs)

    def observe_confirm(input_hashes: Any) -> None:
        nonlocal confirm_count
        confirm_count += 1
        original_confirm(input_hashes)

    def observe_replace(source: Any, destination: Any) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        original_replace(source, destination)
        if destination_path.parent.name.endswith(".previous"):
            operations.append(("backup", key_by_name[destination_path.name]))
            return
        key = final_by_path.get(destination_path)
        if key is None or not source_path.parent.name.endswith(".tmp"):
            return
        operations.append(("publish", key))
        if key == "review_summary":
            backup_dirs = list(
                final_dir.glob(f".{fixture.review_id}.step09c.*.previous")
            )
            temp_dirs = list(
                final_dir.glob(f".{fixture.review_id}.step09c.*.tmp")
            )
            barrier.update(
                finals={
                    output_key
                    for output_key, path in context.output_paths.items()
                    if path.is_file()
                },
                backup_bytes=(
                    {
                        path.name: path.read_bytes()
                        for path in backup_dirs[0].iterdir()
                    }
                    if len(backup_dirs) == 1
                    else {}
                ),
                lock_is_file=(
                    final_dir / f".{fixture.review_id}.step09c.lock"
                ).is_file(),
                temp_dir_count=len(temp_dirs),
                temp_dir_entries=(
                    list(temp_dirs[0].iterdir()) if len(temp_dirs) == 1 else []
                ),
                published_read_count=len(published_reads),
                confirm_count=confirm_count,
            )

    monkeypatch.setattr(FIXTURES.CONTRACT, "read_tsv", observe_read_tsv)
    monkeypatch.setattr(
        FIXTURES.CONTRACT,
        "confirm_inputs_unchanged",
        observe_confirm,
    )
    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", observe_replace)

    FIXTURES.CONTRACT.publish_outputs(context, tables)

    expected_operations = [("backup", "review_summary")]
    expected_operations.extend(
        ("backup", key) for key in ordered_keys if key != "review_summary"
    )
    expected_operations.extend(
        ("publish", key) for key in ordered_keys if key != "review_summary"
    )
    expected_operations.append(("publish", "review_summary"))
    assert operations == expected_operations
    assert barrier["finals"] == set(ordered_keys)
    assert barrier["backup_bytes"] == predecessor_bytes
    assert barrier["lock_is_file"] is True
    assert barrier["temp_dir_count"] == 1
    assert barrier["temp_dir_entries"] == []
    assert barrier["published_read_count"] == 0
    assert barrier["confirm_count"] == 1
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert not list(final_dir.glob(f".{fixture.review_id}.step09c*"))


def test_late_input_mutation_after_summary_restores_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    rewrite_field(fixture.review_plan, "notes", "Late mutation replacement.")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    summary = context.output_paths["review_summary"]
    changed_input = fixture.root / "evidence" / "orientation_locus_audit.tsv"
    original_replace = FIXTURES.CONTRACT.os.replace
    barrier_observed = False

    def mutate_after_summary(source: Any, destination: Any) -> None:
        nonlocal barrier_observed
        source_path = Path(source)
        destination_path = Path(destination)
        original_replace(source, destination)
        if (
            not barrier_observed
            and source_path.parent.name.endswith(".tmp")
            and destination_path == summary
        ):
            barrier_observed = True
            assert all(path.is_file() for path in context.output_paths.values())
            assert len(
                list(final_dir.glob(f".{fixture.review_id}.step09c.*.previous"))
            ) == 1
            assert (
                final_dir / f".{fixture.review_id}.step09c.lock"
            ).is_file()
            changed_input.write_bytes(changed_input.read_bytes() + b"changed\n")

    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", mutate_after_summary)

    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="changed"):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert barrier_observed
    assert {
        path.name: path.read_bytes()
        for path in final_dir.iterdir()
        if path.name in predecessor_bytes
    } == predecessor_bytes
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert not list(final_dir.glob(f".{fixture.review_id}.step09c*"))


def test_post_summary_first_publication_failure_removes_all_owned_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    final_dir.mkdir(parents=True)
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    original_read_tsv = FIXTURES.CONTRACT.read_tsv
    observed_complete_new_set = False

    def fail_first_final_read(label: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal observed_complete_new_set
        if label.startswith("Published Step 09c"):
            observed_complete_new_set = all(
                path.is_file() for path in context.output_paths.values()
            )
            raise FIXTURES.CONTRACT.ContractError(
                "synthetic post-summary final validation failure"
            )
        return original_read_tsv(label, *args, **kwargs)

    monkeypatch.setattr(FIXTURES.CONTRACT, "read_tsv", fail_first_final_read)

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="post-summary final validation failure",
    ):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert observed_complete_new_set
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert set(final_dir.iterdir()) == {unrelated}


def test_post_summary_replacement_failure_restores_all_predecessors_summary_last(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    rewrite_field(fixture.review_plan, "notes", "Post-summary rollback.")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    key_by_name = {path.name: key for key, path in context.output_paths.items()}
    original_read_tsv = FIXTURES.CONTRACT.read_tsv
    original_replace = FIXTURES.CONTRACT.os.replace
    observed_complete_new_set = False
    restore_order: list[str] = []

    def fail_first_final_read(label: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal observed_complete_new_set
        if label.startswith("Published Step 09c"):
            observed_complete_new_set = all(
                path.is_file() for path in context.output_paths.values()
            )
            raise FIXTURES.CONTRACT.ContractError(
                "synthetic post-summary replacement failure"
            )
        return original_read_tsv(label, *args, **kwargs)

    def observe_restore(source: Any, destination: Any) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.parent.name.endswith(".previous"):
            restore_order.append(key_by_name[destination_path.name])
        original_replace(source, destination)

    monkeypatch.setattr(FIXTURES.CONTRACT, "read_tsv", fail_first_final_read)
    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", observe_restore)

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="post-summary replacement failure",
    ):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert observed_complete_new_set
    expected_restore_order = [
        key
        for key, _ in FIXTURES.CONTRACT.OUTPUT_SUFFIXES
        if key != "review_summary"
    ] + ["review_summary"]
    assert restore_order == expected_restore_order
    assert {
        path.name: path.read_bytes()
        for path in final_dir.iterdir()
        if path.name in predecessor_bytes
    } == predecessor_bytes
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert not list(final_dir.glob(f".{fixture.review_id}.step09c*"))


def test_incomplete_post_summary_restore_retains_exact_recovery_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    rewrite_field(fixture.review_plan, "notes", "Incomplete restore.")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    failed_key = "qc_funnel"
    failed_final = context.output_paths[failed_key]
    original_read_tsv = FIXTURES.CONTRACT.read_tsv
    original_replace = FIXTURES.CONTRACT.os.replace
    final_failure_injected = False
    restore_failure_injected = False

    def fail_first_final_read(label: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal final_failure_injected
        if label.startswith("Published Step 09c"):
            final_failure_injected = True
            raise FIXTURES.CONTRACT.ContractError(
                "synthetic post-summary incomplete-restore trigger"
            )
        return original_read_tsv(label, *args, **kwargs)

    def fail_one_restore(source: Any, destination: Any) -> None:
        nonlocal restore_failure_injected
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not restore_failure_injected
            and source_path.parent.name.endswith(".previous")
            and destination_path == failed_final
        ):
            restore_failure_injected = True
            raise OSError("synthetic predecessor restore failure")
        original_replace(source, destination)

    monkeypatch.setattr(FIXTURES.CONTRACT, "read_tsv", fail_first_final_read)
    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", fail_one_restore)

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="rollback was incomplete",
    ):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert final_failure_injected
    assert restore_failure_injected
    assert not failed_final.exists()
    for key, path in context.output_paths.items():
        if key != failed_key:
            assert path.read_bytes() == predecessor_bytes[path.name]
    lock = final_dir / f".{fixture.review_id}.step09c.lock"
    temp_dirs = list(final_dir.glob(f".{fixture.review_id}.step09c.*.tmp"))
    backup_dirs = list(
        final_dir.glob(f".{fixture.review_id}.step09c.*.previous")
    )
    recovery_notices = list(
        final_dir.glob(f".{fixture.review_id}.step09c.*.RECOVERY.txt")
    )
    assert lock.is_file()
    assert len(temp_dirs) == 1
    assert list(temp_dirs[0].iterdir()) == []
    assert len(backup_dirs) == 1
    assert {path.name for path in backup_dirs[0].iterdir()} == {
        failed_final.name
    }
    assert (
        backup_dirs[0] / failed_final.name
    ).read_bytes() == predecessor_bytes[failed_final.name]
    assert len(recovery_notices) == 1
    assert "synthetic predecessor restore failure" in recovery_notices[0].read_text()
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"


def test_term_after_summary_retains_unvalidated_replacement_and_backups(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    rewrite_field(fixture.review_plan, "notes", "TERM after summary.")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    process_context = multiprocessing.get_context("fork")
    ready = process_context.Event()
    release = process_context.Event()
    process = process_context.Process(
        target=publish_with_summary_barrier,
        args=(context, tables, ready, release),
    )
    process.start()
    if not ready.wait(10):
        release.set()
        process.join(10)
        pytest.fail(f"TERM summary barrier was not reached; exit={process.exitcode}")

    backup_dirs = list(
        final_dir.glob(f".{fixture.review_id}.step09c.*.previous")
    )
    temp_dirs = list(final_dir.glob(f".{fixture.review_id}.step09c.*.tmp"))
    lock = final_dir / f".{fixture.review_id}.step09c.lock"
    assert all(path.is_file() for path in context.output_paths.values())
    assert len(backup_dirs) == 1
    assert {
        path.name: path.read_bytes() for path in backup_dirs[0].iterdir()
    } == predecessor_bytes
    assert lock.is_file()
    assert len(temp_dirs) == 1
    assert list(temp_dirs[0].iterdir()) == []
    assert not list(
        final_dir.glob(f".{fixture.review_id}.step09c.*.RECOVERY.txt")
    )

    process.terminate()
    process.join(10)
    assert not process.is_alive()
    assert process.exitcode == -signal.SIGTERM
    assert all(path.is_file() for path in context.output_paths.values())
    assert len(
        list(final_dir.glob(f".{fixture.review_id}.step09c.*.previous"))
    ) == 1
    assert lock.is_file()
    assert len(list(final_dir.glob(f".{fixture.review_id}.step09c.*.tmp"))) == 1
    assert not list(
        final_dir.glob(f".{fixture.review_id}.step09c.*.RECOVERY.txt")
    )
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"


def test_keyboard_interrupt_after_summary_deletes_recovery_state_not_new_finals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    first = run_validator(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    predecessor_bytes = {
        path.name: path.read_bytes() for path in final_dir.iterdir()
    }
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    replacement_notes = "KeyboardInterrupt after summary."
    rewrite_field(fixture.review_plan, "notes", replacement_notes)
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    summary = context.output_paths["review_summary"]
    original_replace = FIXTURES.CONTRACT.os.replace
    barrier: dict[str, Any] = {}

    def interrupt_after_summary(source: Any, destination: Any) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        original_replace(source, destination)
        if (
            not barrier
            and source_path.parent.name.endswith(".tmp")
            and destination_path == summary
        ):
            barrier.update(
                finals=sum(
                    path.is_file() for path in context.output_paths.values()
                ),
                backups=sum(
                    1
                    for backup_dir in final_dir.glob(
                        f".{fixture.review_id}.step09c.*.previous"
                    )
                    for _ in backup_dir.iterdir()
                ),
                lock=(
                    final_dir / f".{fixture.review_id}.step09c.lock"
                ).is_file(),
            )
            raise KeyboardInterrupt("synthetic post-summary interrupt")

    monkeypatch.setattr(FIXTURES.CONTRACT.os, "replace", interrupt_after_summary)

    with pytest.raises(KeyboardInterrupt, match="post-summary interrupt"):
        FIXTURES.CONTRACT.publish_outputs(context, tables)

    assert barrier == {"finals": 13, "backups": 13, "lock": True}
    assert {path.name for path in context.output_paths.values()} == (
        expected_output_names(fixture.review_id)
    )
    assert all(path.is_file() for path in context.output_paths.values())
    assert read_single_row(context.output_paths["review_plan"])["notes"] == (
        replacement_notes
    )
    assert context.output_paths["review_plan"].read_bytes() != predecessor_bytes[
        context.output_paths["review_plan"].name
    ]
    assert not list(final_dir.glob(f".{fixture.review_id}.step09c*"))
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"


def test_same_review_contender_waits_for_admitted_winner_to_release_lock(
    tmp_path: Path,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, tables = FIXTURES.CONTRACT.build_context(arguments)
    final_dir = output_directory(fixture.output_root, fixture.review_id)
    final_dir.mkdir(parents=True)
    unrelated = final_dir / "unrelated.keep"
    unrelated.write_bytes(b"preserve unrelated bytes\n")
    process_context = multiprocessing.get_context("fork")
    ready = process_context.Event()
    release = process_context.Event()
    winner = process_context.Process(
        target=publish_with_summary_barrier,
        args=(context, tables, ready, release),
    )
    winner.start()
    if not ready.wait(10):
        release.set()
        winner.join(10)
        pytest.fail(
            f"concurrency summary barrier was not reached; exit={winner.exitcode}"
        )

    with pytest.raises(FIXTURES.CONTRACT.ContractError, match="locked"):
        FIXTURES.CONTRACT.publish_outputs(context, tables)
    assert (
        final_dir / f".{fixture.review_id}.step09c.lock"
    ).is_file()

    release.set()
    winner.join(10)
    assert not winner.is_alive()
    assert winner.exitcode == 0
    assert {path.name for path in context.output_paths.values()} == (
        expected_output_names(fixture.review_id)
    )
    assert all(path.is_file() for path in context.output_paths.values())
    assert unrelated.read_bytes() == b"preserve unrelated bytes\n"
    assert not list(final_dir.glob(f".{fixture.review_id}.step09c*"))


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


@pytest.mark.parametrize(
    ("background_status", "dp", "ad", "maximum"),
    [
        ("pass", "100", "0", "0"),
        ("fail_fraction", "100", "5", "0.05"),
        ("missing_counts", "NA", "NA", "NA"),
        ("low_coverage", "0", "0", "NA"),
    ],
)
def test_step09_enabled_background_reconciles_from_immutable_counts(
    tmp_path: Path,
    background_status: str,
    dp: str,
    ad: str,
    maximum: str,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, _ = FIXTURES.CONTRACT.build_context(arguments)
    summary = dict(context.step09_summary)
    summary["background_condition"] = "BACKGROUND"
    background_sample = dict(context.sample_rows[0])
    background_sample.update(
        {
            "sample_id": "BACKGROUND_1",
            "condition": "BACKGROUND",
            "replicate": "1",
        }
    )
    sample_rows = [*context.sample_rows, background_sample]
    rows = [dict(row) for row in context.step09_all_rows]
    for row in rows:
        row.update(
            {
                "background_condition": "BACKGROUND",
                "background_status": background_status,
                "max_background_af": maximum,
                "DP__BACKGROUND_1": dp,
                "AD__BACKGROUND_1": ad,
            }
        )
        if (
            row["test_status"] == "tested"
            and background_status != "pass"
        ):
            row["call_status"] = "background_not_passed"

    FIXTURES.CONTRACT.validate_step09_result_semantics(
        rows, summary, sample_rows
    )

    rows[0]["max_background_af"] = (
        "0.5" if maximum != "NA" else "0"
    )
    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="enabled-background",
    ):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            rows, summary, sample_rows
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("min_sample_dp", "0"),
        ("absolute_difference_threshold", "1.1"),
        ("background_max_fraction", "0"),
        ("background_max_fraction", "1"),
    ],
)
def test_step09_native_threshold_boundaries_are_enforced(
    tmp_path: Path,
    column: str,
    value: str,
) -> None:
    fixture = build_fixture(tmp_path / "fixture")
    arguments = FIXTURES.CONTRACT.parse_arguments(fixture.command_args())
    context, _ = FIXTURES.CONTRACT.build_context(arguments)
    summary = dict(context.step09_summary)
    summary[column] = value

    with pytest.raises(
        FIXTURES.CONTRACT.ContractError,
        match="thresholds",
    ):
        FIXTURES.CONTRACT.validate_step09_result_semantics(
            context.step09_all_rows,
            summary,
            context.sample_rows,
        )
