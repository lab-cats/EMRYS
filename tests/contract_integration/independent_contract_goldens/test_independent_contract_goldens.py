"""Independent golden oracles for critical serialized and evidence contracts."""

from __future__ import annotations

import copy
import csv
import importlib
import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from norad.analyses.paired_cmh_candidate_ranking import (
    validator as STEP09_VALIDATOR,
)
from norad.contracts.artifacts import api as ARTIFACT_CONTRACTS
from norad.evidence.scientific_review_package._scientific_review import (
    contracts as SCIENTIFIC_REVIEW,
)
from norad.evidence.scientific_review_package._scientific_review import (
    intake as SCIENTIFIC_REVIEW_INTAKE,
)
from norad.stages.cohort_candidate_preprocessing import validator as STEP08_VALIDATOR

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTING = REPO_ROOT / "src" / "norad" / "reporting"
GOLDENS = Path(__file__).resolve().parent
SCHEMAS = REPO_ROOT / "src" / "norad" / "contracts" / "schemas" / "artifacts" / "v1"

if str(REPORTING) not in sys.path:
    sys.path.insert(0, str(REPORTING))

ARTIFACT_INDEX = importlib.import_module("build_artifact_index")
ARTIFACT_INDEX_CONTEXT = importlib.import_module("_artifact_index.context")
RUN_SUMMARY = importlib.import_module("build_run_summary")
REPORT_BUNDLE = importlib.import_module("render_run_report_bundle")
STEP08_CONTRACT = ARTIFACT_INDEX.step08
STEP09_CONTRACT = ARTIFACT_INDEX.step09
SHARED_SCIENCE = RUN_SUMMARY.science
REVIEW_PACKAGE = ARTIFACT_INDEX.review_package


HEADER_MODULES: Mapping[str, ModuleType] = {
    "build_artifact_index": ARTIFACT_INDEX,
    "build_run_summary": RUN_SUMMARY,
    "render_run_report_bundle": REPORT_BUNDLE,
    "step_09c_scientific_validation": SCIENTIFIC_REVIEW,
}


def header_module(module_name: str, constant_name: str) -> ModuleType:
    if (
        module_name == "build_artifact_index"
        and constant_name == "ARTIFACT_INDEX_HEADER"
    ):
        return ARTIFACT_INDEX_CONTEXT
    if (
        module_name == "step_09c_scientific_validation"
        and constant_name == "REVIEW_PLAN_HEADER"
    ):
        return REVIEW_PACKAGE
    return HEADER_MODULES[module_name]


ARTIFACT_CONTRACT_LOADERS = (
    ARTIFACT_INDEX,
    SHARED_SCIENCE,
    REPORT_BUNDLE.html_report,
)
STEP08_CONTRACT_LOADERS = (
    STEP09_CONTRACT,
    SCIENTIFIC_REVIEW,
    STEP08_VALIDATOR,
    STEP09_VALIDATOR,
    ARTIFACT_INDEX,
)
STEP09_CONTRACT_LOADERS = (
    SCIENTIFIC_REVIEW,
    STEP09_VALIDATOR,
    ARTIFACT_INDEX,
)
REVIEW_PACKAGE_CONTRACT_LOADERS = (
    SCIENTIFIC_REVIEW,
    ARTIFACT_INDEX,
    SHARED_SCIENCE,
)


def test_contract_consumers_share_packaged_module_identities() -> None:
    assert all(
        loader.contracts is ARTIFACT_CONTRACTS for loader in ARTIFACT_CONTRACT_LOADERS
    )
    assert SCIENTIFIC_REVIEW.step08 is STEP08_CONTRACT
    assert STEP08_VALIDATOR.step08 is STEP08_CONTRACT
    assert STEP09_VALIDATOR.step08 is STEP08_CONTRACT
    assert ARTIFACT_INDEX.step08 is STEP08_CONTRACT
    assert STEP09_CONTRACT.step08 is STEP08_CONTRACT
    assert STEP09_VALIDATOR.step09 is STEP09_CONTRACT
    assert ARTIFACT_INDEX.review_package is REVIEW_PACKAGE
    assert SHARED_SCIENCE.review_package is REVIEW_PACKAGE
    assert SCIENTIFIC_REVIEW.review_package is REVIEW_PACKAGE


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_pointer(document: Any, pointer: str) -> Any:
    value = document
    for raw_token in pointer.removeprefix("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def set_pointer(document: Any, pointer: str, value: Any) -> None:
    tokens = pointer.removeprefix("/").split("/")
    parent = document
    for raw_token in tokens[:-1]:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(parent, list):
        parent[int(final)] = value
    else:
        parent[final] = value


def schema_documents() -> dict[str, Any]:
    contracts = load_json(GOLDENS / "schema_contracts.json")
    return {name: load_json(SCHEMAS / name) for name in contracts}


def assert_schema_contracts(documents: Mapping[str, Any]) -> None:
    contracts = load_json(GOLDENS / "schema_contracts.json")
    for schema_name, expectations in contracts.items():
        for expectation in expectations:
            actual = resolve_pointer(documents[schema_name], expectation["pointer"])
            assert actual == expectation["expected"], (
                f"{schema_name}{expectation['pointer']} differs from the "
                "independent schema oracle"
            )


def assert_header_contracts() -> None:
    contracts = load_json(GOLDENS / "headers.json")
    for module_name, headers in contracts.items():
        for constant_name, expected in headers.items():
            module = header_module(module_name, constant_name)
            actual = getattr(module, constant_name)
            assert tuple(actual) == tuple(expected), (
                f"{module_name}.{constant_name} differs from the independent "
                "ordered-header oracle"
            )


def assert_status_constants() -> None:
    expected = load_json(GOLDENS / "scientific_state_contracts.json")["constants"]
    for constant_name, value in expected.items():
        actual = getattr(REVIEW_PACKAGE, constant_name)
        if isinstance(value, list):
            actual = list(actual)
        assert actual == value, (
            f"review_package.{constant_name} differs from the independent status oracle"
        )
    assert REVIEW_PACKAGE.RESERVED_SCIENCE_STATUS not in REVIEW_PACKAGE.SCIENCE_STATUSES


def assert_canonical_json(
    serializer: Callable[[Any], bytes] = ARTIFACT_INDEX.canonical_json_bytes,
) -> None:
    expected = (GOLDENS / "canonical_object.json").read_bytes()
    value = json.loads(expected)
    assert serializer(value) == expected
    assert serializer(value) == serializer(copy.deepcopy(value))


def assert_report_receipt(
    serializer: Callable[[Mapping[str, Any]], bytes] = REPORT_BUNDLE._receipt_tsv_bytes,
) -> None:
    document = load_json(GOLDENS / "report_receipt_input.json")
    expected = (GOLDENS / "report_receipt.tsv").read_bytes()
    assert serializer(document) == expected
    assert serializer(document) == serializer(copy.deepcopy(document))


def assert_shared_science_policy() -> None:
    policy = load_json(GOLDENS / "scientific_state_contracts.json")["shared_policy"]
    context = SimpleNamespace(
        category_rows={
            "decisions": copy.deepcopy(policy["decision_rows"]),
            "limitations": [copy.deepcopy(policy["limitation_row"])],
        }
    )
    decisions = SHARED_SCIENCE._normalize_decisions(context)
    for dimension, expected in policy["decision_expected"].items():
        assert decisions[dimension] == expected, dimension
    assert SHARED_SCIENCE._normalize_limitations(context) == [
        policy["limitation_expected"]
    ]
    for case in policy["computational_status_cases"]:
        SHARED_SCIENCE._validate_computational_payload_status(
            evidence_id=case["evidence_id"],
            validation_scope=case["validation_scope"],
            validation_status=case["validation_status"],
            plan=case["plan"],
        )


def test_representative_public_schema_contracts_match_literal_oracles() -> None:
    assert_schema_contracts(schema_documents())


def test_mutated_public_schema_contract_is_rejected() -> None:
    documents = schema_documents()
    mutated = copy.deepcopy(documents)
    set_pointer(
        mutated["report_receipt.schema.json"],
        "/properties/validation_claimed/const",
        True,
    )
    with pytest.raises(AssertionError, match="validation_claimed"):
        assert_schema_contracts(mutated)


def test_representative_public_headers_match_literal_ordered_oracles() -> None:
    assert_header_contracts()


@pytest.mark.parametrize(
    ("module_name", "constant_name"),
    (
        ("build_artifact_index", "ARTIFACT_INDEX_HEADER"),
        ("build_run_summary", "RUN_SUMMARY_HEADER"),
        ("render_run_report_bundle", "RECEIPT_HEADER"),
        ("step_09c_scientific_validation", "REVIEW_PLAN_HEADER"),
    ),
)
def test_mutated_named_header_constant_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    constant_name: str,
) -> None:
    module = header_module(module_name, constant_name)
    original = getattr(module, constant_name)
    monkeypatch.setattr(module, constant_name, (*original[:-1], "mutated_field"))
    with pytest.raises(AssertionError, match=constant_name):
        assert_header_contracts()


def test_canonical_json_matches_exact_independent_utf8_golden() -> None:
    assert_canonical_json()


def test_mutated_canonical_json_serialization_is_rejected() -> None:
    def mutated_serializer(value: Any) -> bytes:
        return ARTIFACT_INDEX.canonical_json_bytes(value).replace(
            b'  "alpha"', b' "alpha"', 1
        )

    with pytest.raises(AssertionError):
        assert_canonical_json(mutated_serializer)


def test_step09c_tsv_writer_matches_exact_independent_utf8_golden(
    tmp_path: Path,
) -> None:
    expected_path = GOLDENS / "small_table.tsv"
    with expected_path.open(encoding="utf-8", newline="") as stream:
        values = list(csv.reader(stream, delimiter="\t"))
    header = values[0]
    rows = [dict(zip(header, row, strict=True)) for row in values[1:]]
    actual_path = tmp_path / "actual.tsv"
    SCIENTIFIC_REVIEW_INTAKE.write_tsv(actual_path, header, rows)
    assert actual_path.read_bytes() == expected_path.read_bytes()


def test_report_receipt_projection_matches_exact_independent_golden() -> None:
    assert_report_receipt()
    document = load_json(GOLDENS / "report_receipt_input.json")
    with (GOLDENS / "report_receipt.tsv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream, delimiter="\t"))
    assert json.loads(row["report_receipt_json"]) == document


def test_mutated_report_receipt_serialization_is_rejected() -> None:
    def mutated_serializer(document: Mapping[str, Any]) -> bytes:
        return REPORT_BUNDLE._receipt_tsv_bytes(document).replace(
            b"\ttrue\t", b"\tTRUE\t", 1
        )

    with pytest.raises(AssertionError):
        assert_report_receipt(mutated_serializer)


def test_scientific_status_constants_match_literal_oracle() -> None:
    assert_status_constants()


@pytest.mark.parametrize(
    "constant_name",
    (
        "SCIENCE_STATUSES",
        "RESERVED_SCIENCE_STATUS",
        "EVIDENCE_STATUSES",
        "RUNTIME_VALIDATION_STATUSES",
        "CLUSTER_PROOF_STATUSES",
    ),
)
def test_mutated_named_status_constant_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    constant_name: str,
) -> None:
    original = getattr(REVIEW_PACKAGE, constant_name)
    mutated: Any
    if isinstance(original, tuple):
        mutated = (*original[:-1], "mutated_status")
    else:
        mutated = "mutated_status"
    monkeypatch.setattr(REVIEW_PACKAGE, constant_name, mutated)
    with pytest.raises(AssertionError, match=constant_name):
        assert_status_constants()


def test_evidence_status_aggregation_matches_literal_transition_cases() -> None:
    contracts = load_json(GOLDENS / "scientific_state_contracts.json")
    for case in contracts["aggregations"]:
        actual = REVIEW_PACKAGE.aggregate_evidence_status(
            case["rows"], case["category"]
        )
        assert actual == case["expected"], case["name"]


def test_shared_science_policy_matches_independent_transition_oracle() -> None:
    assert_shared_science_policy()


def test_mutated_shared_decision_dimension_constant_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = REVIEW_PACKAGE.DECISION_DIMENSIONS
    monkeypatch.setattr(
        REVIEW_PACKAGE,
        "DECISION_DIMENSIONS",
        ("mutated_dimension", *original[1:]),
    )
    with pytest.raises((AssertionError, KeyError)):
        assert_shared_science_policy()


def test_mutated_computational_scope_policy_constant_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutated = dict(SHARED_SCIENCE.COMPUTATIONAL_SCOPE_PLAN_FIELDS)
    mutated["local_fixture_tests"] = "cluster_proof_status"
    monkeypatch.setattr(
        SHARED_SCIENCE,
        "COMPUTATIONAL_SCOPE_PLAN_FIELDS",
        mutated,
    )
    with pytest.raises(SHARED_SCIENCE.RunSummaryScienceError):
        assert_shared_science_policy()
