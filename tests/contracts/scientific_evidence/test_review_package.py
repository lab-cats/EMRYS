"""Independent API and behavior tests for the neutral review-package contract."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from norad.contracts.scientific_evidence import review_package as REVIEW_PACKAGE

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = ROOT / "configs/step_09c_evidence_schemas"
REVIEW_PLAN_EXAMPLE = ROOT / "configs/step_09c_review_plan.example.tsv"

CONSTANT_NAMES = (
    "SCIENCE_STATUSES",
    "RESERVED_SCIENCE_STATUS",
    "EVIDENCE_STATUSES",
    "ORIENTATION_STATUSES",
    "IMPLEMENTATION_STATUSES",
    "LOCAL_TEST_STATUSES",
    "RUNTIME_VALIDATION_STATUSES",
    "CLUSTER_DRY_RUN_STATUSES",
    "CLUSTER_PROOF_STATUSES",
    "DECISION_STATUSES",
    "DECISION_DIMENSIONS",
    "RERUN_SCOPES",
    "REVIEW_PLAN_HEADER",
    "ORIENTATION_HEADER",
    "ANNOTATION_HEADER",
    "QC_FUNNEL_HEADER",
    "REPLICATE_EFFECTS_HEADER",
    "SENSITIVITY_HEADER",
    "LEAVE_ONE_OUT_HEADER",
    "CANDIDATE_SELECTION_HEADER",
    "CANDIDATE_ADJUDICATION_HEADER",
    "DECISIONS_HEADER",
    "LIMITATIONS_HEADER",
    "CATEGORY_HEADERS",
    "CATEGORY_ORDER",
    "ALLOWED_EVIDENCE_CATEGORIES",
    "EVIDENCE_INDEX_HEADER",
    "OUTPUT_SUFFIXES",
    "INPUT_ARTIFACT_KEYS",
    "REVIEW_SUMMARY_BASE_HEADER",
    "REVIEW_SUMMARY_EVIDENCE_HEADER",
    "REVIEW_SUMMARY_ARTIFACT_HEADER",
    "REVIEW_SUMMARY_TRAILING_HEADER",
    "REVIEW_SUMMARY_HEADER",
    "CONCORDANCE_STATUSES",
    "ANNOTATION_ASSIGNMENT_STATUSES",
    "ANNOTATION_AMBIGUITY_STATUSES",
    "ADJUDICATION_STATUSES",
    "AUDIT_COMPONENT_STATUSES",
)


def public_fingerprint(module: ModuleType) -> bytes:
    document = {
        "constants": {name: getattr(module, name) for name in CONSTANT_NAMES},
        "functions": {
            "aggregate_evidence_status": str(
                inspect.signature(module.aggregate_evidence_status)
            )
        },
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def tsv_header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        return tuple(next(reader))


def evidence_row(category: str, status: str) -> dict[str, str]:
    return {
        "evidence_category": category,
        "evidence_status": status,
    }


def test_public_contract_fingerprint_matches_selection_parent() -> None:
    fingerprint = public_fingerprint(REVIEW_PACKAGE)

    assert len(fingerprint) == 24_525
    assert hashlib.sha256(fingerprint).hexdigest() == (
        "fc23dfa0fc87a96d801db8989ac83a031d48f4fd1407afc40a41b7b4c87ab1db"
    )
    assert str(inspect.signature(REVIEW_PACKAGE.aggregate_evidence_status)) == (
        "(rows: 'Sequence[Mapping[str, str]]', category: 'str') -> 'str'"
    )


def test_neutral_contract_loads_without_step09c_policy() -> None:
    program = """
import builtins

real_import = builtins.__import__

def reject_step09c_policy(name, *args, **kwargs):
    if name == "norad.evidence.scientific_review_package" or name.startswith(
        "norad.evidence.scientific_review_package."
    ):
        raise AssertionError(f"neutral contract imported Step 09c policy: {name}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = reject_step09c_policy
from norad.contracts.scientific_evidence import review_package

assert callable(review_package.aggregate_evidence_status)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_closed_status_vocabularies_match_literal_oracle() -> None:
    expected: dict[str, Any] = {
        "SCIENCE_STATUSES": (
            "evidence_incomplete",
            "science_review_complete_exploratory",
        ),
        "RESERVED_SCIENCE_STATUS": "biological_interpretation_ready",
        "EVIDENCE_STATUSES": (
            "missing",
            "incomplete",
            "complete",
            "not_applicable",
        ),
        "ORIENTATION_STATUSES": (
            "provisional",
            "validated",
            "replacement_required",
        ),
        "IMPLEMENTATION_STATUSES": ("not_implemented", "implemented"),
        "LOCAL_TEST_STATUSES": ("not_run", "passed", "failed"),
        "RUNTIME_VALIDATION_STATUSES": (
            "not_run",
            "blocked",
            "passed",
            "failed",
        ),
        "CLUSTER_DRY_RUN_STATUSES": ("not_run", "passed", "failed"),
        "CLUSTER_PROOF_STATUSES": ("not_run", "proven", "failed"),
        "DECISION_STATUSES": ("pending", "recorded"),
        "DECISION_DIMENSIONS": (
            "orientation",
            "annotation",
            "thresholds",
            "background",
            "matched_dna",
            "orthogonal_evidence",
            "adjudication",
        ),
        "RERUN_SCOPES": (
            "none",
            "step09",
            "steps08_09",
            "steps07_09",
            "upstream_impact_review",
            "manual_only",
        ),
        "CONCORDANCE_STATUSES": (
            "concordant",
            "discordant",
            "ambiguous",
            "not_assessable",
        ),
        "ANNOTATION_ASSIGNMENT_STATUSES": (
            "match",
            "mismatch",
            "ambiguous",
            "not_assessable",
        ),
        "ANNOTATION_AMBIGUITY_STATUSES": (
            "unambiguous",
            "ambiguous",
            "not_assessable",
        ),
        "ADJUDICATION_STATUSES": (
            "pass",
            "flag",
            "fail",
            "not_assessed",
        ),
        "AUDIT_COMPONENT_STATUSES": (
            "pass",
            "flag",
            "fail",
            "not_assessed",
            "unavailable",
            "not_applicable",
        ),
    }

    assert {name: getattr(REVIEW_PACKAGE, name) for name in expected} == expected


def test_public_thirteen_file_roster_matches_literal_oracle() -> None:
    assert REVIEW_PACKAGE.OUTPUT_SUFFIXES == (
        ("review_plan", "step09c_review_plan.tsv"),
        ("evidence_index", "step09c_evidence_index.tsv"),
        ("orientation_locus_audit", "step09c_orientation_locus_audit.tsv"),
        ("annotation_audit", "step09c_annotation_audit.tsv"),
        ("qc_funnel", "step09c_qc_funnel.tsv"),
        ("replicate_effects", "step09c_replicate_effects.tsv"),
        ("sensitivity_matrix", "step09c_sensitivity_matrix.tsv"),
        ("leave_one_pair_out", "step09c_leave_one_pair_out.tsv"),
        ("candidate_selection", "step09c_candidate_selection.tsv"),
        (
            "candidate_adjudication",
            "step09c_candidate_adjudication.tsv",
        ),
        ("decisions", "step09c_decisions.tsv"),
        ("limitations", "step09c_limitations.tsv"),
        ("review_summary", "step09c_review_summary.tsv"),
    )
    assert len(REVIEW_PACKAGE.OUTPUT_SUFFIXES) == 13
    assert len({suffix for _, suffix in REVIEW_PACKAGE.OUTPUT_SUFFIXES}) == 13


def test_category_roster_and_header_values_are_exact() -> None:
    expected = (
        ("orientation_locus_audit", "ORIENTATION_HEADER"),
        ("annotation_audit", "ANNOTATION_HEADER"),
        ("qc_funnel", "QC_FUNNEL_HEADER"),
        ("replicate_effects", "REPLICATE_EFFECTS_HEADER"),
        ("sensitivity_matrix", "SENSITIVITY_HEADER"),
        ("leave_one_pair_out", "LEAVE_ONE_OUT_HEADER"),
        ("candidate_selection", "CANDIDATE_SELECTION_HEADER"),
        ("candidate_adjudication", "CANDIDATE_ADJUDICATION_HEADER"),
        ("decisions", "DECISIONS_HEADER"),
        ("limitations", "LIMITATIONS_HEADER"),
    )

    assert REVIEW_PACKAGE.CATEGORY_ORDER == tuple(category for category, _ in expected)
    assert REVIEW_PACKAGE.ALLOWED_EVIDENCE_CATEGORIES == (
        *REVIEW_PACKAGE.CATEGORY_ORDER,
        "computational_validation",
    )
    assert tuple(REVIEW_PACKAGE.CATEGORY_HEADERS) == (REVIEW_PACKAGE.CATEGORY_ORDER)
    for category, header_name in expected:
        assert REVIEW_PACKAGE.CATEGORY_HEADERS[category] == getattr(
            REVIEW_PACKAGE, header_name
        )


def test_public_headers_match_independent_tracked_tsv_contracts() -> None:
    schema_headers = {
        "orientation_locus_audit": REVIEW_PACKAGE.ORIENTATION_HEADER,
        "annotation_audit": REVIEW_PACKAGE.ANNOTATION_HEADER,
        "qc_funnel": REVIEW_PACKAGE.QC_FUNNEL_HEADER,
        "replicate_effects": REVIEW_PACKAGE.REPLICATE_EFFECTS_HEADER,
        "sensitivity_matrix": REVIEW_PACKAGE.SENSITIVITY_HEADER,
        "leave_one_pair_out": REVIEW_PACKAGE.LEAVE_ONE_OUT_HEADER,
        "candidate_selection": REVIEW_PACKAGE.CANDIDATE_SELECTION_HEADER,
        "candidate_adjudication": REVIEW_PACKAGE.CANDIDATE_ADJUDICATION_HEADER,
        "decisions": REVIEW_PACKAGE.DECISIONS_HEADER,
        "limitations": REVIEW_PACKAGE.LIMITATIONS_HEADER,
        "evidence_index": REVIEW_PACKAGE.EVIDENCE_INDEX_HEADER,
        "review_summary": REVIEW_PACKAGE.REVIEW_SUMMARY_HEADER,
    }

    assert REVIEW_PACKAGE.REVIEW_PLAN_HEADER == tsv_header(REVIEW_PLAN_EXAMPLE)
    for name, expected in schema_headers.items():
        assert expected == tsv_header(SCHEMA_ROOT / f"{name}.schema.tsv")


def test_review_summary_header_composition_is_exact() -> None:
    assert REVIEW_PACKAGE.REVIEW_SUMMARY_EVIDENCE_HEADER == tuple(
        f"{category}_status" for category in REVIEW_PACKAGE.CATEGORY_ORDER
    )
    assert REVIEW_PACKAGE.REVIEW_SUMMARY_ARTIFACT_HEADER == tuple(
        field
        for key in REVIEW_PACKAGE.INPUT_ARTIFACT_KEYS
        for field in (
            f"{key}_path",
            f"{key}_sha256",
            f"{key}_row_count",
        )
    )
    assert REVIEW_PACKAGE.REVIEW_SUMMARY_HEADER == (
        REVIEW_PACKAGE.REVIEW_SUMMARY_BASE_HEADER
        + REVIEW_PACKAGE.REVIEW_SUMMARY_EVIDENCE_HEADER
        + REVIEW_PACKAGE.REVIEW_SUMMARY_ARTIFACT_HEADER
        + REVIEW_PACKAGE.REVIEW_SUMMARY_TRAILING_HEADER
    )


@pytest.mark.parametrize(
    ("rows", "expected"),
    (
        ([], "missing"),
        (
            [
                evidence_row("candidate_selection", "missing"),
                evidence_row("candidate_selection", "missing"),
            ],
            "missing",
        ),
        (
            [
                evidence_row("candidate_selection", "missing"),
                evidence_row("candidate_selection", "complete"),
            ],
            "incomplete",
        ),
        (
            [
                evidence_row("candidate_selection", "incomplete"),
                evidence_row("candidate_selection", "complete"),
            ],
            "incomplete",
        ),
        (
            [
                evidence_row("candidate_selection", "not_applicable"),
                evidence_row("candidate_selection", "not_applicable"),
            ],
            "not_applicable",
        ),
        (
            [
                evidence_row("candidate_selection", "complete"),
                evidence_row("candidate_selection", "not_applicable"),
            ],
            "complete",
        ),
        (
            [
                evidence_row("candidate_selection", "complete"),
                evidence_row("limitations", "missing"),
            ],
            "complete",
        ),
    ),
)
def test_evidence_status_reduction_matches_frozen_transition_cases(
    rows: list[dict[str, str]], expected: str
) -> None:
    before = deepcopy(rows)

    actual = REVIEW_PACKAGE.aggregate_evidence_status(rows, "candidate_selection")

    assert actual == expected
    assert rows == before


@pytest.mark.parametrize(
    ("rows", "missing_key"),
    (
        ([{"evidence_status": "complete"}], "evidence_category"),
        ([{"evidence_category": "candidate_selection"}], "evidence_status"),
    ),
)
def test_evidence_status_reduction_preserves_missing_key_failures(
    rows: list[dict[str, str]], missing_key: str
) -> None:
    with pytest.raises(KeyError) as caught:
        REVIEW_PACKAGE.aggregate_evidence_status(rows, "candidate_selection")

    assert caught.value.args == (missing_key,)
