"""Contract tests for the version-spanning artifact schema registry."""

from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from norad import __main__ as norad_main
from norad.contracts.artifacts import api as contracts
from norad.contracts.artifacts._artifact_contracts import (
    identity,
    run_summary_validation,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = (
    REPO_ROOT
    / "tests"
    / "contracts"
    / "artifacts"
    / "fixtures"
    / "artifact_schema_v2"
    / "valid"
)
INVENTORY = REPO_ROOT / "configs" / "artifact_inventory.example.tsv"
FIXTURES = {
    "artifact-record": FIXTURE_ROOT / "artifact_record.json",
    "run-summary": FIXTURE_ROOT / "run_summary.json",
    "report-receipt": FIXTURE_ROOT.parents[1] / "report_receipt_v4.json",
}
EXPECTED_INVENTORY_ARTIFACT_COUNT = 74


def test_validate_document_and_dispatcher_use_live_api_hooks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = norad_main.build_parser().parse_args(
        [
            "validate",
            "artifact-contracts",
            "--schema",
            "artifact-record",
            "--document",
            str(FIXTURES["artifact-record"]),
        ]
    )
    document_calls: list[tuple[str, dict[str, Any]]] = []

    def record_document(name: str, document: dict[str, Any]) -> None:
        document_calls.append((name, document))

    with monkeypatch.context() as patch:
        patch.setattr(contracts, "validate_document_semantics", record_document)
        result = arguments._command_handler(arguments)

    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == (
        f"JSON document passed artifact-record: {FIXTURES['artifact-record']}\n"
    )
    assert not captured.err
    document = read_json(FIXTURES["artifact-record"])
    assert document_calls == [("artifact-record", document)]

    artifact_calls: list[dict[str, Any]] = []
    with monkeypatch.context() as patch:
        patch.setattr(contracts, "validate_artifact_semantics", artifact_calls.append)
        contracts.validate_document_semantics("artifact-record", document)

    assert artifact_calls == [document]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict)
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_summary_with_complete_artifact() -> dict[str, Any]:
    summary = read_json(FIXTURES["run-summary"])
    artifact = read_json(FIXTURES["artifact-record"])
    summary["artifacts"] = [artifact]
    summary["attempts"] = copy.deepcopy(artifact["attempts"])
    summary["expected_scopes"][0].update(
        {
            "scope": copy.deepcopy(artifact["scope"]),
            "artifact_ids": [artifact["artifact_id"]],
            "aggregate_state": "complete",
        }
    )
    summary["inventory"]["row_count"] = 1
    summary["computational_rollup"].update(
        {
            "expected_artifact_count": 1,
            "complete_artifact_count": 1,
            "missing_artifact_count": 0,
        }
    )
    return summary


def schema_errors(name: str, document: dict[str, Any]) -> list[str]:
    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas[name],
        registry=registry,
        format_checker=FormatChecker(),
    )
    return [error.message for error in validator.iter_errors(document)]


def assert_schema_valid(name: str, document: dict[str, Any]) -> None:
    assert schema_errors(name, document) == []


def assert_schema_invalid(
    name: str,
    document: dict[str, Any],
    token: str,
) -> None:
    errors = schema_errors(name, document)
    assert errors
    assert token.lower() in "\n".join(errors).lower()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "artifact-contracts",
            *arguments,
        ],
        cwd=REPO_ROOT.parent,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_contract_failure(
    name: str,
    document: dict[str, Any],
    token: str,
) -> None:
    with pytest.raises(contracts.ContractValidationError, match=token):
        contracts.validate_document_semantics(name, document)


def test_all_tracked_schemas_are_valid_draft_2020_12_and_local_only() -> None:
    schemas, _ = contracts.load_schema_registry()

    assert set(schemas) == {
        "common",
        "artifact-record",
        "run-summary",
        "report-receipt",
    }
    for schema in schemas.values():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)

        stack: list[Any] = [schema]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                reference = value.get("$ref")
                if reference is not None:
                    assert reference.startswith(("urn:norad:", "#"))
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)

    report_schema = schemas["report-receipt"]
    assert report_schema["$id"] == "urn:norad:schema:artifacts:report-receipt:v4"
    assert report_schema["properties"]["schema_version"]["const"] == "4.0.0"
    historical = read_json(
        REPO_ROOT
        / "src/norad/contracts/schemas/artifacts/v3/report_receipt.schema.json"
    )
    assert historical["properties"]["schema_version"]["const"] == "3.0.0"


@pytest.mark.parametrize(("name", "path"), FIXTURES.items())
def test_valid_synthetic_fixtures_pass_public_validator(
    name: str,
    path: Path,
) -> None:
    result = run_cli("--schema", name, "--document", str(path))

    assert result.returncode == 0, result.stderr
    assert f"passed {name}" in result.stdout


def test_cli_checks_all_schemas_inventory_and_help() -> None:
    result = run_cli("--check-schemas", "--inventory", str(INVENTORY))
    help_result = run_cli("--help")

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Schema passed Draft 2020-12") == len(FIXTURES) + 1
    assert "Artifacts: 74" in result.stdout
    assert help_result.returncode == 0
    assert "--check-schemas" in help_result.stdout
    assert "--inventory" in help_result.stdout

    unsupported = run_cli(
        "--schema",
        "report-receipt",
        "--document",
        str(FIXTURES["report-receipt"]),
        "--inventory",
        str(INVENTORY),
    )
    assert unsupported.returncode != 0
    assert "unsupported" in unsupported.stderr


def test_artifact_schema_rejects_version_extra_property_hash_and_glob() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    wrong_version = copy.deepcopy(artifact)
    wrong_version["schema_version"] = "1.0.0"
    assert_schema_invalid("artifact-record", wrong_version, "2.0.0")

    extra = copy.deepcopy(artifact)
    extra["unexpected"] = True
    assert_schema_invalid("artifact-record", extra, "additional properties")

    bad_hash = copy.deepcopy(artifact)
    bad_hash["source"]["sha256"] = "not-a-sha256"
    assert_schema_invalid("artifact-record", bad_hash, "does not match")

    glob_path = copy.deepcopy(artifact)
    glob_path["expectation"]["source_path"] = "results/editing/*.tsv"
    assert_schema_invalid("artifact-record", glob_path, "does not match")


def test_artifact_schema_supports_explicit_unavailable_attempt_provenance() -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    artifact.update(
        {
            "availability_status": "missing",
            "completion_status": "incomplete",
            "state_reason": "Legacy execution attempt identity is unavailable.",
            "attempt_provenance_status": "unavailable",
            "attempts": [],
            "selected_attempt_id": None,
            "source": None,
            "members": [],
            "metrics": [],
        }
    )

    assert_schema_valid("artifact-record", artifact)
    contracts.validate_document_semantics("artifact-record", artifact)


def test_artifact_semantics_reject_duplicate_unknown_and_cyclic_attempts() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    duplicate = copy.deepcopy(artifact)
    duplicate_attempt = copy.deepcopy(duplicate["attempts"][0])
    duplicate_attempt["state"] = "failed"
    duplicate_attempt["exit_code"] = 1
    duplicate["attempts"].append(duplicate_attempt)
    assert_contract_failure("artifact-record", duplicate, "duplicate attempt_id")

    unknown_selected = copy.deepcopy(artifact)
    unknown_selected["selected_attempt_id"] = "attempt-999"
    assert_contract_failure(
        "artifact-record",
        unknown_selected,
        "does not name a recorded attempt",
    )

    cyclic = copy.deepcopy(artifact)
    cyclic["attempts"][0]["supersedes_attempt_id"] = "attempt-001"
    assert_contract_failure("artifact-record", cyclic, "cannot supersede itself")


def test_artifact_semantics_require_failure_and_incomplete_diagnostics() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    failed = copy.deepcopy(artifact)
    failed["completion_status"] = "failed"
    failed["state_reason"] = "Synthetic failed attempt."
    failed["attempts"][0]["state"] = "failed"
    failed["attempts"][0]["exit_code"] = 1
    failed["attempts"][0]["errors"] = [
        {
            "code": "attempt_failed",
            "message": "Synthetic attempt failure.",
            "related_artifact_ids": [failed["artifact_id"]],
            "evidence": [],
        }
    ]
    assert_schema_valid("artifact-record", failed)
    assert_contract_failure("artifact-record", failed, "at least one error")

    incomplete = copy.deepcopy(artifact)
    incomplete["completion_status"] = "incomplete"
    incomplete["state_reason"] = "Synthetic incomplete transaction."
    incomplete["attempts"][0].update(
        {
            "state": "blocked",
            "exit_code": None,
        }
    )
    incomplete["warnings"] = []
    assert_schema_valid("artifact-record", incomplete)
    assert_contract_failure(
        "artifact-record",
        incomplete,
        "at least one warning or error",
    )


def test_artifact_rejects_unresolved_paths_and_unproven_status_claims() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    template = copy.deepcopy(artifact)
    template["members"] = [
        {
            "member_id": "supplemental",
            "role": "supplemental",
            "path": "results/${RUN_ID}/all.tsv",
            "sha256": "e" * 64,
            "size_bytes": 1,
            "row_count": 1,
            "media_type": "text/tab-separated-values",
        }
    ]
    assert_schema_invalid("artifact-record", template, "does not match")

    traversal = copy.deepcopy(artifact)
    traversal["members"] = copy.deepcopy(template["members"])
    traversal["members"][0]["path"] = "results/run/../all.tsv"
    assert_schema_invalid("artifact-record", traversal, "does not match")

    unproven = copy.deepcopy(artifact)
    unproven["cluster_validation"].update(
        {
            "dry_run_status": "passed",
            "proof_status": "proven",
            "evidence": [],
        }
    )
    assert_schema_invalid("artifact-record", unproven, "non-empty")


def test_artifact_cluster_proof_requires_typed_inspected_evidence() -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    artifact["runtime_validation"] = {
        "status": "passed",
        "detail": None,
        "evidence": [
            {
                "evidence_id": "runtime_log",
                "role": "runtime_log",
                "path": "logs/runtime.log",
                "sha256": "a" * 64,
            },
            {
                "evidence_id": "runtime_output",
                "role": "runtime_output",
                "path": "results/runtime.tsv",
                "sha256": "b" * 64,
            },
        ],
    }
    artifact["cluster_validation"] = {
        "dry_run_status": "passed",
        "proof_status": "proven",
        "evidence": [
            {
                "evidence_id": "local_test_only",
                "role": "local_test",
                "path": "tests/contracts/artifacts/test_artifact_schema_contracts.py",
                "sha256": "c" * 64,
            }
        ],
    }
    assert_schema_valid("artifact-record", artifact)
    assert_contract_failure(
        "artifact-record",
        artifact,
        "cluster dry-run validation requires evidence roles",
    )

    repeated = copy.deepcopy(artifact)
    repeated["cluster_validation"]["evidence"] = [
        {
            "evidence_id": "same_evidence",
            "role": role,
            "path": "logs/same-evidence.txt",
            "sha256": "d" * 64,
        }
        for role in (
            "cluster_dry_run",
            "cluster_scheduler",
            "cluster_log",
            "cluster_output",
        )
    ]
    assert_schema_valid("artifact-record", repeated)
    assert_contract_failure(
        "artifact-record",
        repeated,
        "duplicate evidence evidence_id",
    )


def test_artifact_attempt_source_and_failed_rollup_are_consistent() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    failed_selected = copy.deepcopy(artifact)
    failed_selected["attempts"][0]["state"] = "failed"
    failed_selected["attempts"][0]["exit_code"] = 1
    assert_schema_invalid("artifact-record", failed_selected, "does not contain")

    conflicting_source = copy.deepcopy(artifact)
    conflicting_source["members"] = [
        {
            "member_id": "source_duplicate",
            "role": "supplemental",
            **copy.deepcopy(conflicting_source["source"]),
        }
    ]
    conflicting_source["members"][0]["sha256"] = "f" * 64
    assert_contract_failure(
        "artifact-record",
        conflicting_source,
        "same-path member disagree",
    )

    failed_missing = copy.deepcopy(artifact)
    failed_missing.update(
        {
            "availability_status": "missing",
            "completion_status": "failed",
            "state_reason": "Synthetic publication failed before the anchor.",
            "source": None,
        }
    )
    failed_missing["attempts"][0].update(
        {
            "state": "failed",
            "exit_code": 1,
            "errors": [
                {
                    "code": "attempt_failed",
                    "message": "Synthetic attempt failure.",
                    "related_artifact_ids": [failed_missing["artifact_id"]],
                    "evidence": [],
                }
            ],
        }
    )
    failed_missing["errors"] = [
        {
            "code": "publication_failed",
            "message": "Synthetic publication failure.",
            "related_artifact_ids": ["analysis.synthetic.cmh_summary"],
            "evidence": [],
        }
    ]
    assert_schema_valid("artifact-record", failed_missing)
    contracts.validate_document_semantics("artifact-record", failed_missing)
    assert contracts.artifact_rollup_state(failed_missing) == "failed"


def test_artifact_rejects_absent_source_claimed_by_member() -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    artifact.update(
        {
            "availability_status": "missing",
            "completion_status": "incomplete",
            "state_reason": "Synthetic incomplete artifact.",
            "attempt_provenance_status": "unavailable",
            "attempts": [],
            "selected_attempt_id": None,
            "source": None,
        }
    )
    artifact["members"] = [
        {
            "member_id": "contradictory_source",
            "role": "supplemental",
            "path": artifact["expectation"]["source_path"],
            "sha256": "f" * 64,
            "size_bytes": 10,
            "row_count": 1,
            "media_type": "text/tab-separated-values",
        }
    ]
    assert_schema_valid("artifact-record", artifact)
    assert_contract_failure(
        "artifact-record",
        artifact,
        "cannot claim the absent expected source",
    )


def test_attempt_states_are_temporally_and_graph_consistent() -> None:
    artifact = read_json(FIXTURES["artifact-record"])

    running = copy.deepcopy(artifact)
    running.update(
        {
            "completion_status": "in_progress",
            "state_reason": "Synthetic active attempt.",
        }
    )
    running["attempts"][0].update(
        {
            "state": "running",
            "finished_at": "2000-01-01T00:00:01Z",
            "exit_code": 0,
        }
    )
    assert_schema_invalid("artifact-record", running, "null")

    disconnected = copy.deepcopy(artifact)
    second = copy.deepcopy(disconnected["attempts"][0])
    second["attempt_id"] = "attempt-002"
    disconnected["attempts"].append(second)
    disconnected["selected_attempt_id"] = "attempt-002"
    assert_contract_failure(
        "artifact-record",
        disconnected,
        "connected retry chain",
    )


def test_run_contract_digest_is_canonical_and_recomputed() -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    assert (
        identity.canonical_run_contract_sha256(artifact["run_contract"])
        == artifact["run_contract"]["run_contract_sha256"]
    )

    changed = copy.deepcopy(artifact)
    changed["run_contract"]["sample_manifest_sha256"] = "f" * 64
    assert_contract_failure(
        "artifact-record",
        changed,
        "canonical component contract",
    )


def test_run_summary_reconciles_inventory_order_run_identity_and_rollups() -> None:
    summary = read_json(FIXTURES["run-summary"])

    wrong_run = copy.deepcopy(summary)
    wrong_run["artifacts"][0]["run_id"] = "different_run"
    assert_contract_failure("run-summary", wrong_run, "different run_id")

    omitted = copy.deepcopy(summary)
    omitted["expected_scopes"][0]["artifact_ids"].append("missing.artifact")
    assert_contract_failure("run-summary", omitted, "unknown artifact")

    bad_rollup = copy.deepcopy(summary)
    bad_rollup["computational_rollup"]["missing_artifact_count"] = 0
    assert_contract_failure("run-summary", bad_rollup, "expected 1")


def test_run_summary_supports_multiple_physical_artifacts_per_scope() -> None:
    summary = read_json(FIXTURES["run-summary"])
    second = copy.deepcopy(summary["artifacts"][0])
    second["artifact_id"] = "analysis.synthetic.cmh_limitations"
    second["expectation"]["source_path"] = (
        "tests/fixtures/artifact_schema_v1/source/results/editing/"
        "synthetic_analysis/synthetic_analysis.cmh_limitations.tsv"
    )
    second["warnings"][0]["related_artifact_ids"] = [second["artifact_id"]]
    summary["artifacts"].append(second)
    summary["expected_scopes"][0]["artifact_ids"].append(second["artifact_id"])
    summary["inventory"]["row_count"] = 2
    summary["computational_rollup"]["expected_artifact_count"] = 2
    summary["computational_rollup"]["missing_artifact_count"] = 2

    assert_schema_valid("run-summary", summary)
    contracts.validate_document_semantics("run-summary", summary)


def test_run_summary_reconciles_artifact_and_run_attempt_histories() -> None:
    summary = run_summary_with_complete_artifact()

    assert_schema_valid("run-summary", summary)
    contracts.validate_document_semantics("run-summary", summary)

    disconnected = copy.deepcopy(summary)
    disconnected["attempts"] = []
    assert_contract_failure(
        "run-summary",
        disconnected,
        "not represented identically",
    )

    forest = run_summary_with_complete_artifact()
    second = copy.deepcopy(forest["artifacts"][0])
    second["artifact_id"] = "analysis.synthetic.cmh_all_sites"
    second["adapter"] = "step09_cmh_all_sites_v1"
    second_path = (
        "tests/fixtures/artifact_schema_v1/source/results/editing/"
        "synthetic_analysis/synthetic_analysis.cmh_all_sites.tsv"
    )
    second["expectation"]["source_path"] = second_path
    second["source"].update(
        {
            "path": second_path,
            "sha256": "6" * 64,
            "size_bytes": 1000,
            "row_count": 2,
        }
    )
    second["attempts"][0]["attempt_id"] = "attempt-002"
    second["selected_attempt_id"] = "attempt-002"
    forest["artifacts"].append(second)
    forest["attempts"].append(copy.deepcopy(second["attempts"][0]))
    forest["expected_scopes"][0]["artifact_ids"].append(second["artifact_id"])
    forest["inventory"]["row_count"] = 2
    forest["computational_rollup"]["expected_artifact_count"] = 2
    forest["computational_rollup"]["complete_artifact_count"] = 2
    contracts.validate_document_semantics("run-summary", forest)


def test_run_summary_rejects_cross_artifact_physical_path_conflicts() -> None:
    summary = run_summary_with_complete_artifact()
    first = summary["artifacts"][0]
    second = copy.deepcopy(first)
    second.update(
        {
            "artifact_id": "analysis.synthetic.cmh_all_sites",
            "adapter": "step09_cmh_all_sites_v1",
        }
    )
    second_path = (
        "tests/fixtures/artifact_schema_v1/source/results/editing/"
        "synthetic_analysis/synthetic_analysis.cmh_all_sites.tsv"
    )
    second["expectation"]["source_path"] = second_path
    second["source"].update(
        {
            "path": second_path,
            "sha256": "6" * 64,
            "size_bytes": 1000,
            "row_count": 2,
        }
    )
    first["members"] = [
        {
            "member_id": "contradictory_all_sites",
            "role": "supplemental",
            "path": second_path,
            "sha256": "f" * 64,
            "size_bytes": 1000,
            "row_count": 2,
            "media_type": "text/tab-separated-values",
        }
    ]
    summary["artifacts"].append(second)
    summary["expected_scopes"][0]["artifact_ids"].append(second["artifact_id"])
    summary["inventory"]["row_count"] = 2
    summary["computational_rollup"]["expected_artifact_count"] = 2
    summary["computational_rollup"]["complete_artifact_count"] = 2

    assert_schema_valid("run-summary", summary)
    assert_contract_failure(
        "run-summary",
        summary,
        "disagree on physical path",
    )


def test_run_summary_rejects_duplicate_artifact_ids() -> None:
    summary = read_json(FIXTURES["run-summary"])

    duplicate = copy.deepcopy(summary)
    duplicate["artifacts"].append(copy.deepcopy(duplicate["artifacts"][0]))
    assert_contract_failure("run-summary", duplicate, "duplicate artifact_id")


def test_run_summary_rejects_computational_overclaims() -> None:
    summary = read_json(FIXTURES["run-summary"])

    scope_overclaim = copy.deepcopy(summary)
    scope_overclaim["expected_scopes"][0]["cluster_dry_run_status"] = "passed"
    scope_overclaim["expected_scopes"][0]["cluster_proof_status"] = "proven"
    assert_schema_valid("run-summary", scope_overclaim)
    assert_contract_failure(
        "run-summary",
        scope_overclaim,
        "cluster_dry_run_status",
    )

    rollup_overclaim = copy.deepcopy(summary)
    rollup_overclaim["computational_rollup"]["runtime_validation_status"] = "passed"
    assert_schema_valid("run-summary", rollup_overclaim)
    assert_contract_failure(
        "run-summary",
        rollup_overclaim,
        "runtime_validation_status",
    )


def test_run_summary_reconciles_qc_sources() -> None:
    unknown_metric = run_summary_with_complete_artifact()
    unknown_metric["qc_metrics"] = [
        {
            "metric_id": "unknown_source",
            "name": "Unknown source metric",
            "value": 1,
            "unit": "rows",
            "status": "pass",
            "source_artifact_id": "missing.artifact",
        }
    ]
    assert_schema_valid("run-summary", unknown_metric)
    assert_contract_failure("run-summary", unknown_metric, "unknown artifact")

    invented_metric = run_summary_with_complete_artifact()
    source_artifact_id = invented_metric["artifacts"][0]["artifact_id"]
    invented_metric["qc_metrics"] = [
        {
            "metric_id": "invented_metric",
            "name": "Invented metric",
            "value": 999999,
            "unit": "rows",
            "status": "pass",
            "source_artifact_id": source_artifact_id,
        }
    ]
    assert_schema_valid("run-summary", invented_metric)
    assert_contract_failure(
        "run-summary",
        invented_metric,
        "does not exactly match",
    )


def test_report_receipt_enforces_renderer_safety_outputs_and_banners() -> None:
    receipt = read_json(FIXTURES["report-receipt"])

    wrong_jinja = copy.deepcopy(receipt)
    wrong_jinja["renderer"]["version"] = "3.1.5"
    assert_schema_invalid("report-receipt", wrong_jinja, "3.1.6")

    networked = copy.deepcopy(receipt)
    networked["external_network_assets_used"] = True
    assert_schema_invalid("report-receipt", networked, "false")

    bad_banner = copy.deepcopy(receipt)
    bad_banner["state_banner"] = "Looks good."
    assert_schema_invalid("report-receipt", bad_banner, "COMPUTATIONAL RESULTS")

    missing_scientific = copy.deepcopy(receipt)
    missing_scientific["outputs"] = [
        output
        for output in missing_scientific["outputs"]
        if output["kind"] != "scientific_html"
    ]
    assert_schema_invalid("report-receipt", missing_scientific, "too short")

    for kind in ("scientific_html", "evidence_html"):
        unsafe_html = copy.deepcopy(receipt)
        output = next(item for item in unsafe_html["outputs"] if item["kind"] == kind)
        output["self_contained"] = False
        assert_schema_invalid("report-receipt", unsafe_html, "true")

    wrong_section = copy.deepcopy(receipt)
    wrong_section["truncations"][0]["report_section"] = "evidence-section"
    assert_schema_invalid(
        "report-receipt",
        wrong_section,
        "computational-results-section",
    )


def test_report_receipt_rejects_duplicate_outputs_and_bad_truncation() -> None:
    receipt = read_json(FIXTURES["report-receipt"])

    duplicate = copy.deepcopy(receipt)
    duplicate_output = copy.deepcopy(duplicate["outputs"][0])
    duplicate_output["output_id"] = "second-html"
    duplicate["outputs"].append(duplicate_output)
    assert_contract_failure("report-receipt", duplicate, "duplicate kinds")

    alias = copy.deepcopy(receipt)
    alias["outputs"][0]["output_id"] = "run-report-html"
    assert_schema_valid("report-receipt", alias)
    assert_contract_failure("report-receipt", alias, "output IDs must be exactly")

    wrong_kind = copy.deepcopy(receipt)
    wrong_kind["outputs"][0]["kind"], wrong_kind["outputs"][1]["kind"] = (
        wrong_kind["outputs"][1]["kind"],
        wrong_kind["outputs"][0]["kind"],
    )
    assert_schema_valid("report-receipt", wrong_kind)
    assert_contract_failure("report-receipt", wrong_kind, "must use kind")

    reordered = copy.deepcopy(receipt)
    reordered["outputs"][0], reordered["outputs"][1] = (
        reordered["outputs"][1],
        reordered["outputs"][0],
    )
    assert_schema_valid("report-receipt", reordered)
    assert_contract_failure("report-receipt", reordered, "must be ordered")

    bad_truncation = copy.deepcopy(receipt)
    bad_truncation["truncations"][0]["displayed_row_count"] = 100
    assert_contract_failure(
        "report-receipt",
        bad_truncation,
        "must display fewer",
    )


def test_report_receipt_rejects_cross_run_paths() -> None:
    receipt = read_json(FIXTURES["report-receipt"])
    receipt["outputs"][0]["path"] = (
        "results/reports/another_run/another_run.scientific_report.html"
    )

    assert_schema_valid("report-receipt", receipt)
    assert_contract_failure("report-receipt", receipt, "basename")

    wrong_directory = read_json(FIXTURES["report-receipt"])
    for output in wrong_directory["outputs"]:
        output["path"] = output["path"].replace(
            "/run_fixture/",
            "/different_directory/",
        )
    wrong_directory["input_run_summary"]["path"] = wrong_directory["input_run_summary"][
        "path"
    ].replace(
        "/run_fixture/",
        "/different_directory/",
    )
    assert_schema_valid("report-receipt", wrong_directory)
    assert_contract_failure("report-receipt", wrong_directory, "directory name")


def write_inventory(
    path: Path,
    header: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=header,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def inventory_rows() -> tuple[list[str], list[dict[str, str]]]:
    with INVENTORY.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        assert reader.fieldnames is not None
        return list(reader.fieldnames), list(reader)


def test_contract_paths_honor_an_explicit_source_root(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)

    explicit_path = contracts.resolve_contract_path(
        "alias/source.tsv",
        source_root=tmp_path,
    )
    assert explicit_path == (actual / "source.tsv").resolve()
    assert explicit_path != contracts.resolve_contract_path("alias/source.tsv")

    header, rows = inventory_rows()
    alias_rows = copy.deepcopy(rows[:2])
    alias_rows[0]["source_path"] = "actual/source.tsv"
    alias_rows[1]["source_path"] = "alias/source.tsv"
    inventory = tmp_path / "inventory.tsv"
    write_inventory(inventory, header, alias_rows)
    with pytest.raises(
        contracts.ContractValidationError,
        match="source_path resolves to the same physical path",
    ):
        contracts.validate_inventory(inventory, source_root=tmp_path)

    artifact_record = read_json(FIXTURES["artifact-record"])
    artifact_record.update(
        {
            "availability_status": "missing",
            "completion_status": "incomplete",
            "state_reason": "Synthetic incomplete artifact.",
            "attempt_provenance_status": "unavailable",
            "attempts": [],
            "selected_attempt_id": None,
            "source": None,
        }
    )
    artifact_record["expectation"]["source_path"] = "actual/source.tsv"
    artifact_record["members"] = [
        {
            "member_id": "contradictory_source_alias",
            "role": "supplemental",
            "path": "alias/source.tsv",
            "sha256": "f" * 64,
            "size_bytes": 10,
            "row_count": 1,
            "media_type": "text/tab-separated-values",
        }
    ]
    assert_schema_valid("artifact-record", artifact_record)
    with pytest.raises(
        contracts.ContractValidationError,
        match="cannot claim the absent expected source",
    ):
        contracts.validate_artifact_semantics(
            artifact_record,
            source_root=tmp_path,
        )

    run_summary = read_json(FIXTURES["run-summary"])
    run_summary["artifacts"] = [artifact_record]
    with pytest.raises(
        contracts.ContractValidationError,
        match="cannot claim the absent expected source",
    ):
        contracts.validate_run_summary_semantics(
            run_summary,
            source_root=tmp_path,
        )


def test_run_summary_semantics_threads_the_explicit_source_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Propagate one explicit root through every run-summary artifact path seam."""
    summary = read_json(FIXTURES["run-summary"])
    artifact = read_json(FIXTURES["artifact-record"])
    artifact["members"] = [
        {
            "member_id": "supplemental",
            "role": "supplemental",
            "path": "supplemental/member.tsv",
            "sha256": "d" * 64,
            "size_bytes": 1,
            "row_count": 1,
            "media_type": "text/tab-separated-values",
        },
    ]
    summary["artifacts"] = [artifact]
    summary["attempts"] = copy.deepcopy(artifact["attempts"])
    summary["expected_scopes"][0].update(
        {
            "scope": copy.deepcopy(artifact["scope"]),
            "artifact_ids": [artifact["artifact_id"]],
            "aggregate_state": "complete",
        }
    )
    summary["computational_rollup"].update(
        {
            "complete_artifact_count": 1,
            "missing_artifact_count": 0,
        },
    )

    semantic_roots: list[Path] = []
    resolved_values: list[str] = []

    def record_artifact_semantics(
        _document: dict[str, Any],
        *,
        source_root: Path,
    ) -> None:
        semantic_roots.append(source_root)

    def record_contract_path(value: str, *, source_root: Path) -> Path:
        resolved_values.append(value)
        assert source_root == tmp_path
        return (source_root / value).resolve()

    monkeypatch.setattr(
        run_summary_validation,
        "validate_artifact_semantics",
        record_artifact_semantics,
    )
    monkeypatch.setattr(
        run_summary_validation,
        "resolve_contract_path",
        record_contract_path,
    )

    contracts.validate_run_summary_semantics(summary, source_root=tmp_path)

    expected_path = artifact["expectation"]["source_path"]
    assert semantic_roots == [tmp_path]
    assert resolved_values == [
        expected_path,
        artifact["source"]["path"],
        "supplemental/member.tsv",
    ]


def test_inventory_is_explicit_ordered_unique_and_covers_steps_00a_through_10() -> None:
    rows = contracts.validate_inventory(INVENTORY)

    assert Counter(row["step_id"] for row in rows) == {
        "00a": 16,
        "00b": 2,
        "00c": 4,
        "01": 6,
        "02": 3,
        "02b": 3,
        "03": 2,
        "04": 4,
        "05": 3,
        "06": 6,
        "07": 8,
        "08": 4,
        "09": 7,
        "10": 6,
    }
    assert all(row["required"] == "true" for row in rows)
    assert all(not any(token in row["source_path"] for token in "*?[]") for row in rows)
    assert (
        len({row["artifact_id"] for row in rows}) == EXPECTED_INVENTORY_ARTIFACT_COUNT
    )
    assert (
        len({row["source_path"] for row in rows}) == EXPECTED_INVENTORY_ARTIFACT_COUNT
    )


@pytest.mark.parametrize(
    ("mutation", "token"),
    [
        ("glob", "glob syntax"),
        ("template", "not templated"),
        ("boolean", "exactly 'true' or 'false'"),
        ("duplicate_artifact", "duplicate artifact_id"),
        ("duplicate_source", "duplicate source_path"),
    ],
)
def test_inventory_rejects_implicit_or_ambiguous_rows(
    tmp_path: Path,
    mutation: str,
    token: str,
) -> None:
    header, rows = inventory_rows()
    if mutation == "glob":
        rows[0]["source_path"] = "results/star/*/Log.final.out"
    elif mutation == "template":
        rows[0]["source_path"] = "results/star/${SAMPLE}/Log.final.out"
    elif mutation == "boolean":
        rows[0]["required"] = "True"
    elif mutation == "duplicate_artifact":
        rows[1]["artifact_id"] = rows[0]["artifact_id"]
    elif mutation == "duplicate_source":
        rows[1]["source_path"] = rows[0]["source_path"]

    inventory = tmp_path / "inventory.tsv"
    write_inventory(inventory, header, rows)
    with pytest.raises(contracts.ContractValidationError, match=token):
        contracts.validate_inventory(inventory)


def test_inventory_allows_multiple_physical_artifacts_per_scope(
    tmp_path: Path,
) -> None:
    header, rows = inventory_rows()
    rows = rows[:2]
    rows[1]["step_id"] = rows[0]["step_id"]
    rows[1]["scope_type"] = rows[0]["scope_type"]
    rows[1]["scope_id"] = rows[0]["scope_id"]
    inventory = tmp_path / "inventory.tsv"
    write_inventory(inventory, header, rows)

    assert len(contracts.validate_inventory(inventory)) == len(rows)


def test_inventory_rejects_canonical_aliases_and_interleaved_scopes(
    tmp_path: Path,
) -> None:
    header, rows = inventory_rows()

    alias_rows = copy.deepcopy(rows[:2])
    alias_rows[1]["source_path"] = alias_rows[0]["source_path"].replace(
        "tests/",
        "tests//",
        1,
    )
    alias_inventory = tmp_path / "alias.tsv"
    write_inventory(alias_inventory, header, alias_rows)
    with pytest.raises(
        contracts.ContractValidationError,
        match="redundant path separators",
    ):
        contracts.validate_inventory(alias_inventory)

    interleaved = [
        copy.deepcopy(rows[0]),
        copy.deepcopy(rows[22]),
        copy.deepcopy(rows[1]),
    ]
    interleaved_inventory = tmp_path / "interleaved.tsv"
    write_inventory(interleaved_inventory, header, interleaved)
    with pytest.raises(contracts.ContractValidationError, match="contiguous"):
        contracts.validate_inventory(interleaved_inventory)


def inventory_row_for_artifact(
    artifact: dict[str, Any],
) -> dict[str, str]:
    return {
        "artifact_id": artifact["artifact_id"],
        "step_id": artifact["scope"]["step_id"],
        "scope_type": artifact["scope"]["scope_type"],
        "scope_id": artifact["scope"]["scope_id"],
        "adapter": artifact["adapter"],
        "source_path": artifact["expectation"]["source_path"],
        "required": str(artifact["expectation"]["required"]).lower(),
    }


@pytest.mark.parametrize(
    "field",
    [
        "step_id",
        "scope_type",
        "scope_id",
        "adapter",
        "source_path",
        "required",
    ],
)
def test_artifact_record_reconciles_every_inventory_field(
    tmp_path: Path,
    field: str,
) -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    row = inventory_row_for_artifact(artifact)
    contracts.reconcile_artifact_inventory_row(artifact, row)

    changed = row.copy()
    changed[field] = {
        "step_id": "08",
        "scope_type": "cohort",
        "scope_id": "different_scope",
        "adapter": "different_adapter",
        "source_path": "results/different.tsv",
        "required": "false",
    }[field]
    with pytest.raises(
        contracts.ContractValidationError,
        match="explicit inventory row",
    ):
        contracts.reconcile_artifact_inventory_row(artifact, changed)

    inventory = tmp_path / "inventory.tsv"
    write_inventory(inventory, list(contracts.INVENTORY_HEADER), [row])
    document = tmp_path / "artifact.json"
    write_json(document, artifact)
    result = run_cli(
        "--schema",
        "artifact-record",
        "--document",
        str(document),
        "--inventory",
        str(inventory),
    )
    assert result.returncode == 0, result.stderr
    assert "Document/inventory reconciliation passed" in result.stdout


def test_run_summary_reconciles_inventory_hash_order_and_scope(
    tmp_path: Path,
) -> None:
    summary = read_json(FIXTURES["run-summary"])
    row = inventory_row_for_artifact(summary["artifacts"][0])
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    inventory = actual / "inventory.tsv"
    write_inventory(inventory, list(contracts.INVENTORY_HEADER), [row])
    summary["inventory"].update(
        {
            "path": "alias/inventory.tsv",
            "sha256": contracts.sha256_file(inventory),
            "size_bytes": inventory.stat().st_size,
            "row_count": 1,
        }
    )

    contracts.reconcile_document_inventory(
        "run-summary",
        summary,
        [row],
        inventory,
        source_root=tmp_path,
    )

    wrong_hash = copy.deepcopy(summary)
    wrong_hash["inventory"]["sha256"] = "f" * 64
    with pytest.raises(contracts.ContractValidationError, match="hash"):
        contracts.reconcile_document_inventory(
            "run-summary",
            wrong_hash,
            [row],
            inventory,
            source_root=tmp_path,
        )


def test_inventory_header_order_and_unrelated_files_are_fail_closed(
    tmp_path: Path,
) -> None:
    header, rows = inventory_rows()
    swapped = header.copy()
    swapped[0], swapped[1] = swapped[1], swapped[0]
    wrong_header = tmp_path / "wrong_header.tsv"
    write_inventory(wrong_header, swapped, rows)
    with pytest.raises(contracts.ContractValidationError, match="header"):
        contracts.validate_inventory(wrong_header)

    unrelated = tmp_path / "unrelated.pipeline_output.tsv"
    unrelated.write_text("must\tnot\nbe\tread\n", encoding="utf-8")
    assert (
        len(contracts.validate_inventory(INVENTORY))
        == EXPECTED_INVENTORY_ARTIFACT_COUNT
    )


def test_duplicate_json_keys_are_rejected_before_schema_validation(
    tmp_path: Path,
) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"schema_name":"norad.artifact_record","schema_name":"duplicate"}\n',
        encoding="utf-8",
    )

    result = run_cli(
        "--schema",
        "artifact-record",
        "--document",
        str(duplicate),
    )

    assert result.returncode != 0
    assert "Duplicate JSON object key" in result.stderr


def test_nonstandard_json_numbers_are_rejected(tmp_path: Path) -> None:
    artifact = read_json(FIXTURES["artifact-record"])
    payload = json.dumps(artifact).replace(
        '"parameters": {',
        '"parameters": {"nonstandard": NaN,',
        1,
    )
    document = tmp_path / "nan.json"
    document.write_text(payload, encoding="utf-8")

    result = run_cli(
        "--schema",
        "artifact-record",
        "--document",
        str(document),
    )

    assert result.returncode != 0
    assert "Non-standard JSON numeric constant" in result.stderr
