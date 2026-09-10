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
from emrys.contracts.orchestration import artifact_inventory
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
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
    source: Mapping[str, Any],
    profile: Mapping[str, Any],
    analysis: AnalysisRevision,
    processing_source_root: Path | None = None,
    processing_artifact_paths: Mapping[tuple[str, str, str], Path] | None = None,
) -> ReportingBundle:
    """Build exact reporting inputs for one admitted immutable Run."""

    orchestration_contracts.validate_record("profile", profile)
    if (
        analysis_revision_from_execution_fields(source).canonical_bytes
        != analysis.canonical_bytes
    ):
        raise orchestration_contracts.ContractValidationError(
            "Reporting source differs from the admitted Analysis"
        )
    reference_contract = dict(source["reference"])
    primary_analysis_policy = dict(source["analysis"]["policy"])
    reference_bytes = orchestration_contracts.canonical_json_bytes(reference_contract)
    policy_bytes = orchestration_contracts.canonical_json_bytes(primary_analysis_policy)
    primary_analysis_id = analysis.scope_id("analysis")
    components = {
        "sample_manifest_sha256": str(source["samples"]["manifest"]["sha256"]),
        "reference_contract_sha256": _sha256_bytes(reference_bytes),
        "partition_manifest_sha256": str(source["partitions"]["manifest"]["sha256"]),
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
    rows = artifact_inventory.project_rows(
        source,
        profile,
        analysis,
        processing_source_root,
        processing_artifact_paths,
    )
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


__all__ = (
    "CONTRACT_PATHS",
    "ReportingBundle",
    "build_reporting_bundle",
)
