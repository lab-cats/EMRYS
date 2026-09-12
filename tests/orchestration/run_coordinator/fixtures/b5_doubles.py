"""Test-only replacement of B5 science commands with deterministic owner doubles."""

from __future__ import annotations

import base64
import csv
import io
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.contracts.scientific_evidence import step08
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.run_coordinator.materialization import AttemptPlan
from tests.orchestration.run_coordinator.fixtures import workflow


def with_owner_doubles(plan: AttemptPlan) -> AttemptPlan:
    """Replace only owner command effects in an otherwise unchanged plan."""

    source = {**plan.run.analysis.workflow_inputs, "run_id": plan.run.run_id}
    selected_path = (
        plan.run_root
        / "contract"
        / "workflow-inputs"
        / plan.workflow_attempt_id
        / "samples.tsv"
    )
    selected = next(
        (item for item in plan.attempt_files if item.path == selected_path),
        None,
    )
    if selected is not None:
        _, _, selected_rows = step08.validate_sample_manifest_bytes(
            selected.data,
            selected.path,
        )
        rows_by_id = {str(row["sample_id"]): row for row in source["samples"]["rows"]}
        source["samples"] = {
            **source["samples"],
            "rows": [rows_by_id[str(row["sample_id"])] for row in selected_rows],
            "manifest": {
                "path": str(selected.path),
                "size_bytes": len(selected.data),
                "sha256": hashlib.sha256(selected.data).hexdigest(),
            },
        }
    reporting = build_reporting_bundle(
        source,
        plan.run.analysis.profile,
        plan.run.analysis.revision,
    )
    rows = tuple(
        csv.DictReader(
            io.StringIO(reporting.artifact_inventory_bytes.decode()), delimiter="\t"
        )
    )
    raw_payloads = workflow.artifact_payloads(
        rows,
        source,
        artifact_source_root=plan.run_root,
    )
    payloads: dict[Path, bytes] = {}
    for raw, data in raw_payloads.items():
        path = Path(raw)
        payloads[path if path.is_absolute() else plan.run_root / path] = data

    attempt = json.loads(plan.attempt_record_bytes)
    records = (
        record
        for by_scope in attempt["tasks"].values()
        for record in by_scope.values()
        if "workflow_attempt_record" not in record
    )
    for record in records:
        payload_record = {
            "producer": [
                {
                    "path": output["working_path"],
                    "data_base64": base64.b64encode(
                        payloads[Path(output["path"])]
                    ).decode(),
                }
                for output in record["outputs"]
            ],
            "validation": {
                "path": record["validation_report_path"],
                "data_base64": base64.b64encode(
                    payloads[Path(record["validation_report_path"])]
                ).decode(),
            },
        }
        payload_data = orchestration_contracts.canonical_json_bytes(payload_record)
        payload_argument = workflow._inline_payload_argument(payload_data)
        record["producer_argv"] = list(
            controlled_python_argv(
                sys.executable,
                str(workflow.TASK_DOUBLE),
                "payload",
                "producer",
                "--payload-base64",
                payload_argument,
            )
        )
        record["validator_argv"] = list(
            controlled_python_argv(
                sys.executable,
                str(workflow.TASK_DOUBLE),
                "payload",
                "validator",
                "--payload-base64",
                payload_argument,
            )
        )
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    return replace(
        plan,
        attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
    )
