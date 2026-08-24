"""Schema-level contracts for immutable reporting ledger records."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
ATTEMPT_ID = "workflow-20260812T120000Z-" + "a" * 32


def _reference(path: str, digest: str = ZERO_HASH) -> dict[str, str]:
    return {"path": path, "sha256": digest}


def _records() -> dict[str, dict[str, Any]]:
    identity = {
        "run_id": f"run-{ZERO_HASH}",
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "origin_workflow_attempt_id": ATTEMPT_ID,
        "kind": "artifact_index",
    }
    start = {
        "schema_version": "emrys.reporting-start.v1",
        **identity,
        "workflow_attempt": _reference(f"attempts/{ATTEMPT_ID}/attempt.json"),
        "workflow_config": _reference("contract/workflow-config.json"),
        "run_lock": _reference(f"attempts/{ATTEMPT_ID}/released-run-lock.json"),
        "created_at": "2026-08-12T12:00:00Z",
    }
    verified = {
        "schema_version": "emrys.verified-reporting.v1",
        **identity,
        "reporting_start": _reference("state/reporting/artifact_index/start.json"),
        "semantic_receipt": _reference(
            f"products/artifact-summary/run-{ZERO_HASH}/"
            f"run-{ZERO_HASH}.artifact_receipt.tsv"
        ),
        "created_at": "2026-08-12T12:01:00Z",
    }
    return {"reporting-start": start, "verified-reporting": verified}


def test_reporting_ledger_schemas_are_registered_and_closed() -> None:
    schemas, _registry = orchestration_contracts.load_schema_registry()
    assert "reporting-start" in schemas
    assert "verified-reporting" in schemas
    for name, record in _records().items():
        orchestration_contracts.validate_record(name, record)
        mutated = copy.deepcopy(record)
        mutated["unbound"] = True
        with pytest.raises(
            orchestration_contracts.ContractValidationError,
            match="Additional properties",
        ):
            orchestration_contracts.validate_record(name, mutated)


@pytest.mark.parametrize("name", ("reporting-start", "verified-reporting"))
def test_reporting_ledger_kind_is_closed(name: str) -> None:
    record = _records()[name]
    record["kind"] = "pdf_report"
    with pytest.raises(
        orchestration_contracts.ContractValidationError,
        match="artifact_index",
    ):
        orchestration_contracts.validate_record(name, record)
