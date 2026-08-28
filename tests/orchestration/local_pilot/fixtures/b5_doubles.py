"""Test-only replacement of B5 science commands with deterministic owner doubles."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.local_pilot import materialization
from emrys.orchestration.local_pilot.materialization import AttemptPlan, PlannedFile
from tests.orchestration.local_pilot.fixtures import workflow


def with_owner_doubles(
    plan: AttemptPlan,
    *,
    fail_machine_key: str | None = None,
) -> AttemptPlan:
    """Return the same exact output plan with no-science test commands."""

    source = materialization._construction_source(plan.run)
    reporting = build_reporting_bundle(
        source,
        plan.run.normalized.profile,
        plan.run.normalized.analysis_revision,
    )
    rows = tuple(dict(row) for row in reporting.artifact_inventory_rows)
    raw_payloads = workflow.artifact_payloads(
        rows,
        source,
        artifact_source_root=plan.run_root,
    )
    payloads: dict[Path, bytes] = {}
    for raw, data in raw_payloads.items():
        path = Path(raw)
        payloads[path if path.is_absolute() else plan.run_root / path] = data

    replacement_files: list[PlannedFile] = []
    manifest_files: list[PlannedFile] = []
    dispatch_sha: dict[Path, str] = {}
    dispatch_paths = {item.path for item in plan.new_dispatch_files}
    for item in plan.attempt_files:
        if item.path not in dispatch_paths:
            replacement_files.append(item)
            continue
        record = json.loads(item.data)
        manifest = item.path.with_suffix(".payload.json")
        manifest_record = {
            "producer": [
                {
                    "path": output["path"],
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
        manifest_data = orchestration_contracts.canonical_json_bytes(manifest_record)
        manifest_files.append(PlannedFile(manifest, manifest_data))
        record["producer_argv"] = list(
            controlled_python_argv(
                sys.executable,
                str(workflow.OWNER_ARTIFACT_DOUBLE),
                "producer",
                "--manifest",
                str(manifest),
            )
        )
        if record["machine_key"] == fail_machine_key:
            record["producer_argv"] = list(
                controlled_python_argv(
                    sys.executable,
                    "-c",
                    "raise SystemExit(17)",
                )
            )
        record["validator_argv"] = list(
            controlled_python_argv(
                sys.executable,
                str(workflow.OWNER_ARTIFACT_DOUBLE),
                "validator",
                "--manifest",
                str(manifest),
            )
        )
        record["inputs"].append(
            {"role": "test_payload_manifest", "path": str(manifest)}
        )
        data = orchestration_contracts.canonical_json_bytes(record)
        replacement_files.append(PlannedFile(item.path, data))
        dispatch_sha[item.path] = hashlib.sha256(data).hexdigest()

    config_index = next(
        index
        for index, item in enumerate(replacement_files)
        if "/contract/workflow-configs/" in str(item.path)
    )
    config_file = replacement_files[config_index]
    config = json.loads(config_file.data)
    for by_scope in config["dispatch_paths"].values():
        for reference in by_scope.values():
            path = Path(reference["path"])
            if path in dispatch_sha:
                reference["sha256"] = dispatch_sha[path]
    config_data = orchestration_contracts.canonical_json_bytes(config)
    replacement_files[config_index] = PlannedFile(config_file.path, config_data)
    attempt = dict(plan.attempt_record)
    attempt["execution_mode"] = "test-double"
    attempt["workflow_config"] = {
        **attempt["workflow_config"],
        "sha256": hashlib.sha256(config_data).hexdigest(),
    }
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    return replace(
        plan,
        attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
        attempt_files=tuple((*replacement_files, *manifest_files)),
    )


__all__ = ("with_owner_doubles",)
