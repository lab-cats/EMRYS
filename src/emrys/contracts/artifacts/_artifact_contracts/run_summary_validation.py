"""Run-summary status reduction and semantic validation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .artifact import validate_artifact_semantics
from .definitions import (
    REPO_ROOT,
    ContractValidationError,
)
from .identity import (
    require_unique_key,
    resolve_contract_path,
    validate_attempt_graph,
    validate_document_paths,
    validate_run_contract,
)
from .run_summary_status import (
    AGGREGATE_ARTIFACT_STATES,
    RUN_SUMMARY_STATUS_FIELDS,
    aggregate_artifact_state,
    aggregate_equal_or_mixed,
    artifact_rollup_state,
    artifact_status_dimensions,
    scope_key,
)


def _validate_scope_statuses(
    record: dict[str, Any],
    artifacts: list[dict[str, Any]],
    prefix: str,
) -> None:
    for status_field in RUN_SUMMARY_STATUS_FIELDS:
        expected_status = aggregate_equal_or_mixed(
            artifact_status_dimensions(artifact)[status_field] for artifact in artifacts
        )
        if record[status_field] != expected_status:
            raise ContractValidationError(
                f"{prefix} {status_field} is "
                f"{record[status_field]!r}, expected {expected_status!r}"
            )


def _validate_module_summary(document: dict[str, Any]) -> None:
    if document.get("schema_version") != "3.0.0":
        return

    from emrys.contracts.orchestration import api as orchestration_contracts

    policy_binding = document["analysis_policy"]
    policy = policy_binding["record"]
    policy_sha256 = orchestration_contracts.canonical_sha256(policy)
    if (
        policy_sha256 != policy_binding["sha256"]
        or policy_sha256 != document["run_contract"]["primary_analysis_policy_sha256"]
        or policy_binding["size_bytes"]
        != len(orchestration_contracts.canonical_json_bytes(policy))
    ):
        raise ContractValidationError(
            "modular run summary does not bind its exact analysis policy"
        )
    if policy["analysis_id"] != document["run_contract"]["primary_analysis_id"]:
        raise ContractValidationError(
            "modular run summary analysis policy identifies another analysis"
        )
    analysis_id = policy["analysis_id"]
    admitted_adapters = [
        artifact["adapter"]
        for artifact in document["artifacts"]
        if artifact["scope"]["scope_type"] == "analysis"
        and artifact["scope"]["scope_id"] == analysis_id
    ]
    if len(admitted_adapters) != len(set(admitted_adapters)):
        raise ContractValidationError(
            "modular run summary repeats an admitted analysis adapter"
        )


def validate_run_summary_semantics(
    document: dict[str, Any],
    *,
    source_root: Path = REPO_ROOT,
) -> None:
    validate_run_contract(document["run_contract"], "run summary")
    validate_document_paths(document)
    _validate_module_summary(document)

    attempts = validate_attempt_graph(
        document["attempts"],
        label="run summary",
        require_single_chain=False,
    )
    superseded = document["superseded_attempt_ids"]
    if unknown_superseded := sorted(set(superseded) - set(attempts)):
        raise ContractValidationError(
            "run summary superseded_attempt_ids contain unknown attempts: "
            + ", ".join(unknown_superseded)
        )
    actual_superseded = {
        attempt["supersedes_attempt_id"]
        for attempt in document["attempts"]
        if attempt["supersedes_attempt_id"] is not None
    }
    if set(superseded) != actual_superseded:
        raise ContractValidationError(
            "run summary superseded_attempt_ids must exactly name attempts "
            "superseded by another recorded attempt"
        )

    artifacts = document["artifacts"]
    artifact_index = require_unique_key(artifacts, "artifact_id", "run artifacts")
    artifact_attempts: dict[str, dict[str, Any]] = {}
    expected_source_artifacts: dict[Path, dict[str, Any]] = {}
    physical_path_records: dict[Path, tuple[Any, ...]] = {}
    for artifact in artifacts:
        validate_artifact_semantics(artifact, source_root=source_root)
        if artifact["run_id"] != document["run_id"]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} has a different run_id"
            )
        if artifact["run_contract"] != document["run_contract"]:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} has a different "
                "immutable run contract"
            )
        for attempt in artifact["attempts"]:
            attempt_id = attempt["attempt_id"]
            if (
                attempt_id in artifact_attempts
                and artifact_attempts[attempt_id] != attempt
            ):
                raise ContractValidationError(
                    f"artifact attempt {attempt_id!r} has conflicting "
                    "definitions across artifact records"
                )
            artifact_attempts[attempt_id] = attempt
            if attempt_id not in attempts or attempts[attempt_id] != attempt:
                raise ContractValidationError(
                    f"artifact attempt {attempt_id!r} is not represented "
                    "identically in the run attempt history"
                )
        if artifact["selected_attempt_id"] in superseded:
            raise ContractValidationError(
                f"artifact {artifact['artifact_id']!r} selects a superseded run attempt"
            )
        expected_path = resolve_contract_path(
            artifact["expectation"]["source_path"],
            source_root=source_root,
        )
        if expected_path in expected_source_artifacts:
            raise ContractValidationError(
                f"run artifacts contain duplicate expected source path "
                f"{expected_path!r}"
            )
        expected_source_artifacts[expected_path] = artifact
        physical_records = (
            [artifact["source"]] if artifact["source"] is not None else []
        ) + artifact["members"]
        for record in physical_records:
            fingerprint = (
                record["sha256"],
                record.get("size_bytes"),
                record.get("row_count"),
                record.get("media_type"),
            )
            physical_path = resolve_contract_path(
                record["path"],
                source_root=source_root,
            )
            prior = physical_path_records.get(physical_path)
            if prior is not None and prior != fingerprint:
                raise ContractValidationError(
                    f"run artifacts disagree on physical path {str(physical_path)!r}"
                )
            physical_path_records[physical_path] = fingerprint

    for expected_path, expected_artifact in expected_source_artifacts.items():
        if expected_path not in physical_path_records:
            continue
        source = expected_artifact["source"]
        if source is None:
            raise ContractValidationError(
                f"run member records claim missing expected source "
                f"{str(expected_path)!r}"
            )
        expected_fingerprint = (
            source["sha256"],
            source.get("size_bytes"),
            source.get("row_count"),
            source.get("media_type"),
        )
        if physical_path_records[expected_path] != expected_fingerprint:
            raise ContractValidationError(
                f"run member/source metadata disagree for expected path "
                f"{str(expected_path)!r}"
            )

    scope_keys: set[tuple[str, str, str]] = set()
    ordered_expected_artifact_ids: list[str] = []
    for scope_record in document["expected_scopes"]:
        scope = scope_record["scope"]
        scope_key_ = scope_key(scope)
        if scope_key_ in scope_keys:
            raise ContractValidationError(
                f"run summary contains duplicate expected scope {scope_key_}"
            )
        scope_keys.add(scope_key_)
        scope_artifacts: list[dict[str, Any]] = []
        for artifact_id in scope_record["artifact_ids"]:
            if artifact_id not in artifact_index:
                raise ContractValidationError(
                    f"expected scope {scope_key_} references unknown artifact "
                    f"{artifact_id!r}"
                )
            artifact = artifact_index[artifact_id]
            artifact_scope = artifact["scope"]
            if scope_key(artifact_scope) != scope_key_:
                raise ContractValidationError(
                    f"expected scope {scope_key_} does not match artifact "
                    f"{artifact_id!r}"
                )
            scope_artifacts.append(artifact)
        expected_aggregate = aggregate_artifact_state(scope_artifacts)
        if scope_record["aggregate_state"] != expected_aggregate:
            raise ContractValidationError(
                f"expected scope {scope_key_} aggregate_state is "
                f"{scope_record['aggregate_state']!r}, expected "
                f"{expected_aggregate!r}"
            )
        _validate_scope_statuses(
            scope_record, scope_artifacts, f"expected scope {scope_key_}"
        )
        ordered_expected_artifact_ids.extend(scope_record["artifact_ids"])

    if len(ordered_expected_artifact_ids) != len(set(ordered_expected_artifact_ids)):
        raise ContractValidationError(
            "an artifact_id appears in more than one expected scope"
        )
    if ordered_expected_artifact_ids != list(artifact_index):
        raise ContractValidationError(
            "artifacts must appear exactly once in expected-scope/inventory order"
        )
    inventory_row_count = document["inventory"]["row_count"]
    if inventory_row_count is not None and inventory_row_count != len(artifacts):
        raise ContractValidationError(
            "inventory row_count does not match the expected artifact count"
        )

    rollup = document["computational_rollup"]
    if rollup["expected_artifact_count"] != len(artifacts):
        raise ContractValidationError(
            "computational_rollup expected_artifact_count does not match "
            "the artifact array"
        )
    observed_counts = Counter(artifact_rollup_state(artifact) for artifact in artifacts)
    for state in AGGREGATE_ARTIFACT_STATES + ("complete",):
        field = f"{state}_artifact_count"
        if rollup[field] != observed_counts[state]:
            raise ContractValidationError(
                f"computational_rollup {field} is {rollup[field]}, expected {observed_counts[state]}"
            )
    _validate_scope_statuses(rollup, artifacts, "computational_rollup")

    qc_metrics = require_unique_key(
        document["qc_metrics"],
        "metric_id",
        "QC metrics",
    )
    for metric in qc_metrics.values():
        source_artifact_id = metric["source_artifact_id"]
        if source_artifact_id is None:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} requires an explicit "
                "source_artifact_id"
            )
        if source_artifact_id not in artifact_index:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} references unknown "
                f"artifact {source_artifact_id!r}"
            )
        source_metrics = {
            source_metric["metric_id"]: source_metric
            for source_metric in artifact_index[source_artifact_id]["metrics"]
        }
        if source_metrics.get(metric["metric_id"]) != metric:
            raise ContractValidationError(
                f"QC metric {metric['metric_id']!r} does not exactly match "
                f"the metric recorded by artifact {source_artifact_id!r}"
            )
    require_unique_key(
        document["limitations"],
        "limitation_id",
        "run summary limitations",
    )
