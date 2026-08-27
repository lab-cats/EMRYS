"""Deterministically project one execution identity into reporting v1 inputs."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration import artifact_inventory
from emrys.contracts.orchestration.application_model import (
    EXECUTION_PROJECTION_SCHEMA_VERSION,
    analysis_revision_from_execution_fields,
)

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
    primary_analysis_id = str(execution["analysis"]["primary_analysis_id"])
    if execution.get("schema_version") == EXECUTION_PROJECTION_SCHEMA_VERSION:
        primary_analysis_id = analysis_revision_from_execution_fields(
            execution
        ).scope_id("analysis")
    components = {
        "sample_manifest_sha256": str(execution["samples"]["manifest"]["sha256"]),
        "reference_contract_sha256": _sha256_bytes(reference_bytes),
        "partition_manifest_sha256": str(execution["partitions"]["manifest"]["sha256"]),
        "primary_analysis_id": primary_analysis_id,
        "primary_analysis_policy_sha256": _sha256_bytes(policy_bytes),
    }
    reporting_run_contract = {
        "run_contract_sha256": _run_contract_sha256(components),
        **components,
    }
    artifact_contracts.validate_run_contract(
        reporting_run_contract, "projected reporting"
    )
    rows = artifact_inventory.project_rows(execution, profile)
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
