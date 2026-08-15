"""Independent golden oracles for critical serialized and evidence contracts."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from norad.contracts.artifacts import api as ARTIFACT_CONTRACTS

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDENS = Path(__file__).resolve().parent
SCHEMAS = REPO_ROOT / "src" / "norad" / "contracts" / "schemas" / "artifacts"

ARTIFACT_INDEX_CORE = importlib.import_module(
    "norad.reporting._artifact_index.core",
)
ARTIFACT_INDEX_MODELS = importlib.import_module(
    "norad.reporting._artifact_index.models",
)
ARTIFACT_INDEX_RECORDS = importlib.import_module(
    "norad.reporting._artifact_index.records",
)
RUN_SUMMARY = importlib.import_module("norad.reporting._run_summary.models")
REPORT = importlib.import_module("norad.reporting.report")
REPORT_VALIDATION = importlib.import_module("norad.reporting._run_report.validation")
REPORT_VIEW = importlib.import_module("norad.reporting._run_report.view")


HEADER_MODULES: Mapping[str, ModuleType] = {
    "build_artifact_index": ARTIFACT_INDEX_MODELS,
    "build_run_summary": RUN_SUMMARY,
    "build_report": REPORT,
}


def header_module(module_name: str, constant_name: str) -> ModuleType:
    return HEADER_MODULES[module_name]


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
    schema_versions = {
        "artifact_record.schema.json": "v2",
        "common.schema.json": "v1",
        "report_receipt.schema.json": "v3",
        "run_summary.schema.json": "v2",
    }
    return {
        name: load_json(SCHEMAS / schema_versions[name] / name) for name in contracts
    }


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


def assert_canonical_json(
    serializer: Callable[[Any], bytes] = ARTIFACT_INDEX_CORE.canonical_json_bytes,
) -> None:
    expected = (GOLDENS / "canonical_object.json").read_bytes()
    value = json.loads(expected)
    assert serializer(value) == expected
    assert serializer(value) == serializer(copy.deepcopy(value))


def assert_report_receipt(
    serializer: Callable[[Mapping[str, Any]], bytes] = REPORT.serialize_receipt,
) -> None:
    document = load_json(GOLDENS / "report_receipt_input.json")
    expected = (GOLDENS / "report_receipt.tsv").read_bytes()
    assert serializer(document) == expected
    assert serializer(document) == serializer(copy.deepcopy(document))


def report_html_bytes(document: Mapping[str, Any]) -> bytes:
    summary = load_json(REPO_ROOT / document["summary_fixture"])
    assert not ARTIFACT_CONTRACTS.schema_errors("run-summary", summary)
    ARTIFACT_CONTRACTS.validate_run_summary_semantics(
        summary,
        source_root=REPO_ROOT,
    )
    view = REPORT_VIEW.build_view(
        summary,
        document["metadata"],
    )
    return REPORT_VALIDATION.render_html(view, document["css"])


def assert_report_html(document: Mapping[str, Any]) -> None:
    expected = (GOLDENS / "report_html.sha256").read_text(encoding="ascii").strip()
    actual = hashlib.sha256(report_html_bytes(document)).hexdigest()
    assert actual == expected, (
        "rendered report HTML differs from the independent oracle"
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
        ("build_report", "RECEIPT_HEADER"),
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
        return ARTIFACT_INDEX_CORE.canonical_json_bytes(value).replace(
            b'  "alpha"', b' "alpha"', 1
        )

    with pytest.raises(AssertionError):
        assert_canonical_json(mutated_serializer)


def test_artifact_tsv_writer_matches_exact_independent_utf8_golden() -> None:
    expected_path = GOLDENS / "small_table.tsv"
    with expected_path.open(encoding="utf-8", newline="") as stream:
        values = list(csv.reader(stream, delimiter="\t"))
    header = values[0]
    rows = [dict(zip(header, row, strict=True)) for row in values[1:]]
    assert ARTIFACT_INDEX_RECORDS.tsv_bytes(header, rows) == expected_path.read_bytes()


def test_report_receipt_projection_matches_exact_independent_golden() -> None:
    assert_report_receipt()
    document = load_json(GOLDENS / "report_receipt_input.json")
    with (GOLDENS / "report_receipt.tsv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream, delimiter="\t"))
    assert json.loads(row["report_receipt_json"]) == document


def test_mutated_report_receipt_serialization_is_rejected() -> None:
    def mutated_serializer(document: Mapping[str, Any]) -> bytes:
        return REPORT.serialize_receipt(document).replace(b"\ttrue\t", b"\tTRUE\t", 1)

    with pytest.raises(AssertionError):
        assert_report_receipt(mutated_serializer)


def test_report_html_matches_exact_independent_sha256_golden() -> None:
    assert_report_html(load_json(GOLDENS / "report_html_input.json"))


def test_mutated_report_html_input_is_rejected() -> None:
    mutated = load_json(GOLDENS / "report_html_input.json")
    mutated["metadata"]["run_summary_sha256"] = "d" * 64
    with pytest.raises(AssertionError, match="independent oracle"):
        assert_report_html(mutated)
