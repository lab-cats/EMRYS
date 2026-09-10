"""Artifact records, deterministic indexes, identities, and receipts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from emrys import analyses
from emrys.contracts.artifacts import api as contracts
from emrys.contracts.orchestration.artifact_inventory import processing_tasks
from emrys.libraries.validation.tsv import tsv_bytes as render_tsv_bytes

from .core import safe_tsv
from .models import (
    ArtifactIndexError,
    Inspection,
)


def producer_evidence(
    git_commit: str,
    *,
    analysis_module: analyses.LoadedAnalysisModuleV1,
    source_root: Path = contracts.PACKAGE_ROOT,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for task in processing_tasks(source_root):
        step_id = str(task["step_id"])
        relative_path = str(task["producer_path"])
        path = source_root / relative_path
        if not path.is_file():
            raise ArtifactIndexError(
                f"Registered producer path is missing: {relative_path}"
            )
        result[step_id] = {
            "status": "implemented",
            "git_commit": git_commit,
            "evidence": [
                {
                    "evidence_id": f"implementation_{step_id}",
                    "role": "implementation",
                    "path": relative_path,
                    "sha256": contracts.sha256_file(path),
                }
            ],
        }
    module_evidence = [
        {
            "evidence_id": "implementation_module",
            "role": "implementation",
            "path": (
                f"{analysis_module.provider.distribution_name}@"
                f"{analysis_module.provider.distribution_version}/"
                f"{analysis_module.provider.entry_point_value}"
            ),
            "sha256": analysis_module.provider.package.sha256,
        }
    ]
    installed_builtin = source_root / "analyses/paired_cmh_candidate_ranking"
    for step_id in dict.fromkeys(
        task.step_id for task in analysis_module.descriptor.tasks
    ):
        module_git_commit = (
            git_commit
            if analysis_module.descriptor.module_id
            == analyses.BUILTIN_PAIRED_CMH_MODULE_ID
            and analysis_module.provider.package.root == installed_builtin
            else None
        )
        result[step_id] = {
            "status": "implemented",
            "git_commit": module_git_commit,
            "evidence": module_evidence,
        }
    return result


def build_artifact_record(
    *,
    inspection: Inspection,
    implementation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_id": inspection.row["artifact_id"],
        "scope": {
            "step_id": inspection.row["step_id"],
            "scope_type": inspection.row["scope_type"],
            "scope_id": inspection.row["scope_id"],
        },
        "adapter": inspection.row["adapter"],
        "expectation": {
            "required": inspection.row["required"] == "true",
            "source_path": inspection.row["source_path"],
        },
        "availability_status": inspection.availability_status,
        "completion_status": inspection.completion_status,
        "state_reason": inspection.state_reason,
        "attempt_provenance_status": inspection.attempt_provenance_status,
        "attempts": [],
        "selected_attempt_id": None,
        "implementation": implementation,
        "local_testing": {"status": "not_run", "evidence": []},
        "runtime_validation": {
            "status": "not_run",
            "detail": None,
            "evidence": [],
        },
        "cluster_validation": {
            "dry_run_status": "not_run",
            "proof_status": "not_run",
            "evidence": [],
        },
        "source": inspection.source,
        "members": [],
        "tools": [],
        "parameters": inspection.parameters,
        "metrics": inspection.metrics,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
    }


def validate_record_in_memory(
    record: dict[str, Any],
    inventory_row: dict[str, str],
    validator: Draft202012Validator,
    *,
    source_root: Path,
) -> None:
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed schema:\n{detail}"
        )
    try:
        contracts.validate_artifact_semantics(record, source_root=source_root)
        contracts.reconcile_artifact_inventory_row(record, inventory_row)
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed semantic "
            f"validation: {exc}"
        ) from exc


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    return render_tsv_bytes(
        header,
        ({field: safe_tsv(row[field]) for field in header} for row in rows),
    )
