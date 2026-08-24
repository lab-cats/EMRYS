"""Deterministically project one execution identity into reporting v1 inputs."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts

CONTRACT_PATHS = {
    "reference_contract": "contract/reference_contract.json",
    "primary_analysis_policy": "contract/primary_analysis_policy.json",
    "reporting_run_contract": "contract/reporting_run_contract.json",
    "artifact_inventory": "contract/artifact_inventory.tsv",
}


@dataclass(frozen=True, slots=True)
class ReportingBundle:
    """Exact deterministic documents required by the reporting owners."""

    reference_contract: dict[str, Any]
    primary_analysis_policy: dict[str, Any]
    reporting_run_contract: dict[str, Any]
    artifact_inventory_rows: tuple[dict[str, str], ...]
    reference_contract_bytes: bytes
    primary_analysis_policy_bytes: bytes
    reporting_run_contract_bytes: bytes
    artifact_inventory_bytes: bytes

    @property
    def projection_references(self) -> dict[str, dict[str, str]]:
        """Return deterministic contract-relative paths and content identities."""

        documents = {
            "reference_contract": self.reference_contract_bytes,
            "primary_analysis_policy": self.primary_analysis_policy_bytes,
            "reporting_run_contract": self.reporting_run_contract_bytes,
            "artifact_inventory": self.artifact_inventory_bytes,
        }
        return {
            name: {
                "path": CONTRACT_PATHS[name],
                "sha256": _sha256_bytes(data),
            }
            for name, data in documents.items()
        }


def _sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _run_contract_sha256(components: Mapping[str, str]) -> str:
    return orchestration_contracts.canonical_sha256(dict(components))


def _template_contexts(
    selector: str,
    execution: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    reference_id = str(execution["reference"]["reference_id"])
    reference_fasta_path = str(execution["reference"]["fasta"]["path"])
    reference_path = Path(reference_fasta_path)
    reference_dict_path = str(reference_path.with_name(f"{reference_path.stem}.dict"))
    cohort_id = str(execution["analysis"]["cohort_id"])
    analysis_id = str(execution["analysis"]["primary_analysis_id"])
    shared = {
        "run_id": str(execution["run_id"]),
        "reference_id": reference_id,
        "reference_fasta_path": reference_fasta_path,
        "reference_dict_path": reference_dict_path,
        "cohort_id": cohort_id,
        "analysis_id": analysis_id,
    }
    if selector == "reference":
        return ({**shared, "scope_id": reference_id},)
    if selector == "samples":
        return tuple(
            {
                **shared,
                "sample_id": str(row["sample_id"]),
                "scope_id": str(row["sample_id"]),
            }
            for row in execution["samples"]["rows"]
        )
    if selector == "partitions":
        return tuple(
            {
                **shared,
                "partition_id": str(row["partition_id"]),
                "scope_id": f"{cohort_id}__{row['partition_id']}",
            }
            for row in execution["partitions"]["rows"]
        )
    if selector == "cohort":
        return ({**shared, "scope_id": cohort_id},)
    if selector == "analysis":
        return ({**shared, "scope_id": analysis_id},)
    raise orchestration_contracts.ContractValidationError(
        f"Unsupported profile scope_selector: {selector}"
    )


def _expand_template(value: str, context: Mapping[str, str], label: str) -> str:
    try:
        expanded = value.format_map(dict(context))
    except (KeyError, ValueError) as exc:
        raise orchestration_contracts.ContractValidationError(
            f"Could not expand {label} {value!r}: {exc}"
        ) from exc
    if "{" in expanded or "}" in expanded:
        raise orchestration_contracts.ContractValidationError(
            f"Unresolved template syntax remains in {label}: {expanded}"
        )
    return expanded


def _validate_artifact_inventory_rows(rows: Sequence[Mapping[str, str]]) -> None:
    """Apply the artifact inventory's pure row semantics before serialization."""

    if not rows:
        raise orchestration_contracts.ContractValidationError(
            "Profile projects no artifact inventory rows"
        )
    seen_values = {"artifact_id": set(), "source_path": set()}
    closed_scopes: set[tuple[str, str, str]] = set()
    active_scope: tuple[str, str, str] | None = None
    for row in rows:
        for field in artifact_contracts.INVENTORY_HEADER[:-2]:
            if not artifact_contracts.SAFE_ID_RE.fullmatch(row[field]):
                raise orchestration_contracts.ContractValidationError(
                    f"Projected inventory {field} is not a safe ID: {row[field]}"
                )
        artifact_contracts.validate_resolved_path(
            row["source_path"], "Projected inventory source_path"
        )
        for field, seen in seen_values.items():
            value = row[field]
            if value in seen:
                raise orchestration_contracts.ContractValidationError(
                    f"Projected artifact inventory contains duplicate {field} values"
                )
            seen.add(value)
        scope = artifact_contracts.scope_key(dict(row))
        if active_scope is None:
            active_scope = scope
        elif scope != active_scope:
            closed_scopes.add(active_scope)
            if scope in closed_scopes:
                raise orchestration_contracts.ContractValidationError(
                    "Projected artifact inventory reopens logical scope: "
                    + "/".join(scope)
                )
            active_scope = scope


def _artifact_inventory_rows(
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    expected_scope = {
        "reference": "reference",
        "samples": "sample",
        "partitions": "cohort_partition",
        "cohort": "cohort",
        "analysis": "analysis",
    }
    templates_by_selector: dict[str, list[Mapping[str, Any]]] = {}
    selector_order: list[str] = []
    for template in profile["artifact_templates"]:
        selector = str(template["scope_selector"])
        if selector not in templates_by_selector:
            templates_by_selector[selector] = []
            selector_order.append(selector)
        templates_by_selector[selector].append(template)

    for selector in selector_order:
        for context in _template_contexts(selector, execution):
            for template in templates_by_selector[selector]:
                scope_type = str(template["scope_type"])
                if expected_scope[selector] != scope_type:
                    raise orchestration_contracts.ContractValidationError(
                        "Artifact template scope_selector/scope_type mismatch: "
                        f"{selector}/{scope_type}"
                    )
                artifact_id = _expand_template(
                    str(template["artifact_id_template"]),
                    context,
                    "artifact_id_template",
                )
                source_path = _expand_template(
                    str(template["source_path_template"]),
                    context,
                    "source_path_template",
                )
                row = {
                    "artifact_id": artifact_id,
                    "step_id": str(template["step_id"]),
                    "scope_type": scope_type,
                    "scope_id": context["scope_id"],
                    "adapter": str(template["adapter"]),
                    "source_path": source_path,
                    "required": "true" if template["required"] else "false",
                }
                rows.append(row)

    _validate_artifact_inventory_rows(rows)
    return tuple(rows)


def _inventory_bytes(rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=artifact_contracts.INVENTORY_HEADER,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build_reporting_bundle(
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> ReportingBundle:
    """Build exact reporting inputs before the execution contract is finalized."""

    orchestration_contracts.validate_record("profile", profile)
    reference_contract = dict(execution["reference"])
    primary_analysis_policy = dict(execution["analysis"]["policy"])
    reference_bytes = orchestration_contracts.canonical_json_bytes(reference_contract)
    policy_bytes = orchestration_contracts.canonical_json_bytes(primary_analysis_policy)
    components = {
        "sample_manifest_sha256": str(execution["samples"]["manifest"]["sha256"]),
        "reference_contract_sha256": _sha256_bytes(reference_bytes),
        "partition_manifest_sha256": str(execution["partitions"]["manifest"]["sha256"]),
        "primary_analysis_id": str(execution["analysis"]["primary_analysis_id"]),
        "primary_analysis_policy_sha256": _sha256_bytes(policy_bytes),
    }
    reporting_run_contract = {
        "run_contract_sha256": _run_contract_sha256(components),
        **components,
    }
    artifact_contracts.validate_run_contract(
        reporting_run_contract, "projected reporting"
    )
    rows = _artifact_inventory_rows(execution, profile)
    return ReportingBundle(
        reference_contract=reference_contract,
        primary_analysis_policy=primary_analysis_policy,
        reporting_run_contract=reporting_run_contract,
        artifact_inventory_rows=rows,
        reference_contract_bytes=reference_bytes,
        primary_analysis_policy_bytes=policy_bytes,
        reporting_run_contract_bytes=(
            orchestration_contracts.canonical_json_bytes(reporting_run_contract)
        ),
        artifact_inventory_bytes=_inventory_bytes(rows),
    )


def project_reporting(
    execution_contract: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> ReportingBundle:
    """Rebuild and verify the reporting projection of a complete execution."""

    orchestration_contracts.validate_record(
        "execution", execution_contract, profile=profile
    )
    return build_reporting_bundle(execution_contract, profile)


def validate_reporting_projection(
    execution_contract: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> None:
    """Require the complete deterministic projection without recursion."""

    expected_profile_identity = {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
    }
    observed_profile_identity = {
        "profile_id": execution_contract["profile"]["profile_id"],
        "profile_version": execution_contract["profile"]["profile_version"],
    }
    if observed_profile_identity != expected_profile_identity:
        raise orchestration_contracts.ContractValidationError(
            "Execution profile identity does not match the supplied profile"
        )
    expected_profile_sha = orchestration_contracts.canonical_sha256(profile)
    if execution_contract["profile"]["profile_sha256"] != expected_profile_sha:
        raise orchestration_contracts.ContractValidationError(
            "Execution profile digest does not match the supplied profile"
        )
    bundle = build_reporting_bundle(execution_contract, profile)
    if execution_contract["reporting_projection"] != bundle.projection_references:
        raise orchestration_contracts.ContractValidationError(
            "Execution reporting_projection does not match deterministic documents"
        )


__all__ = (
    "CONTRACT_PATHS",
    "ReportingBundle",
    "build_reporting_bundle",
    "project_reporting",
    "validate_reporting_projection",
)
