"""Run-summary status reduction and semantic validation."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from .artifact import validate_artifact_semantics
from .definitions import (
    SCIENCE_UPSTREAM_ROLE_CONTRACTS,
    ContractValidationError,
)
from .identity import (
    require_unique_key,
    resolve_contract_path,
    validate_attempt_graph,
    validate_document_paths,
    validate_resolved_path,
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
from .scientific_review import validate_scientific_review_semantics


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


def validate_run_summary_semantics(document: dict[str, Any]) -> None:
    validate_run_contract(document["run_contract"], "run summary")
    validate_document_paths(document)

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
        validate_artifact_semantics(artifact)
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
        expected_path = resolve_contract_path(artifact["expectation"]["source_path"])
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
            physical_path = resolve_contract_path(record["path"])
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

    review = document["scientific_review"]
    if review["overall_status"] != document["science_status"]:
        raise ContractValidationError(
            "run summary science_status does not match scientific_review"
        )
    if (record := review["record"]) is not None:
        validate_scientific_review_semantics(record)
        if record["run_id"] != document["run_id"]:
            raise ContractValidationError(
                "scientific review record has a different run_id"
            )
        if record["run_contract"] != document["run_contract"]:
            raise ContractValidationError(
                "scientific review record has a different immutable run contract"
            )
        if record["scientific_state"]["overall_status"] != document["science_status"]:
            raise ContractValidationError(
                "scientific review record has a different overall science status"
            )
        if (
            review["source"]["path"] != record["review_summary"]["path"]
            or review["source"]["sha256"] != record["review_summary"]["sha256"]
        ):
            raise ContractValidationError(
                "scientific review source path/hash does not match the "
                "embedded review record"
            )
        matching_review_artifacts = [
            artifact
            for artifact in artifacts
            if scope_key(artifact["scope"])
            == (
                "09c",
                "scientific_review",
                record["review_id"],
            )
            and artifact["completion_status"] == "complete"
            and artifact["source"] is not None
            and resolve_contract_path(artifact["source"]["path"])
            == resolve_contract_path(record["review_summary"]["path"])
            and artifact["source"]["sha256"] == record["review_summary"]["sha256"]
        ]
        if len(matching_review_artifacts) != 1:
            raise ContractValidationError(
                "embedded scientific review must match exactly one complete "
                "scientific-review artifact source"
            )
        for input_artifact in record["input_artifacts"]:
            role_contract = SCIENCE_UPSTREAM_ROLE_CONTRACTS.get(input_artifact["role"])
            if role_contract is None:
                continue
            artifact_id = input_artifact["artifact_id"]
            if artifact_id not in artifact_index:
                raise ContractValidationError(
                    f"scientific review input role "
                    f"{input_artifact['role']!r} references artifact "
                    f"{artifact_id!r} absent from the run summary"
                )
            upstream = artifact_index[artifact_id]
            source = upstream["source"]
            expected_step, expected_scope_type, expected_adapter, _ = role_contract
            if (
                upstream["completion_status"] != "complete"
                or source is None
                or upstream["scope"]["step_id"] != expected_step
                or upstream["scope"]["scope_type"] != expected_scope_type
                or upstream["adapter"] != expected_adapter
                or source["path"] != input_artifact["path"]
                or source["sha256"] != input_artifact["sha256"]
                or source.get("row_count") != input_artifact["row_count"]
            ):
                raise ContractValidationError(
                    f"scientific review input role "
                    f"{input_artifact['role']!r} does not match one complete "
                    "run artifact source"
                )

    report_tables = require_unique_key(
        document["approved_report_tables"],
        "table_id",
        "approved report tables",
    )
    for table in report_tables.values():
        artifact_id = table["artifact_id"]
        if artifact_id not in artifact_index:
            raise ContractValidationError(
                f"report table {table['table_id']!r} references unknown "
                f"artifact {artifact_id!r}"
            )
        artifact = artifact_index[artifact_id]
        if artifact["completion_status"] != "complete":
            raise ContractValidationError(
                f"report table {table['table_id']!r} references a non-complete artifact"
            )
        report_sources = {
            (member["path"], member["sha256"]): member for member in artifact["members"]
        }
        source = artifact["source"]
        if source is not None:
            report_sources[(source["path"], source["sha256"])] = source
        source_record = report_sources.get((table["path"], table["sha256"]))
        if source_record is None:
            raise ContractValidationError(
                f"report table {table['table_id']!r} path/hash does not match "
                "its artifact source or members"
            )
        if source_record.get("row_count") != table["row_count"]:
            raise ContractValidationError(
                f"report table {table['table_id']!r} row_count does not match "
                "its source artifact"
            )
        if source_record.get("media_type") != "text/tab-separated-values":
            raise ContractValidationError(
                f"report table {table['table_id']!r} must reference a TSV artifact"
            )

    if "report_table_approvals" in document["parameters"]:
        approval_source = document["parameters"]["report_table_approvals"]
        if approval_source is None:
            if report_tables:
                raise ContractValidationError(
                    "approved report tables require explicit approval-manifest "
                    "provenance"
                )
        else:
            expected_fields = {
                "path",
                "sha256",
                "size_bytes",
                "row_count",
                "media_type",
            }
            if (
                not isinstance(approval_source, dict)
                or set(approval_source) != expected_fields
            ):
                raise ContractValidationError(
                    "report-table approval provenance has an invalid shape"
                )
            if not isinstance(approval_source["path"], str):
                raise ContractValidationError(
                    "report-table approval provenance path is invalid"
                )
            validate_resolved_path(
                approval_source["path"],
                "report-table approval provenance path",
            )
            if not isinstance(approval_source["sha256"], str) or not re.fullmatch(
                r"[0-9a-f]{64}",
                approval_source["sha256"],
            ):
                raise ContractValidationError(
                    "report-table approval provenance SHA-256 is invalid"
                )
            if (
                not isinstance(approval_source["size_bytes"], int)
                or isinstance(approval_source["size_bytes"], bool)
                or approval_source["size_bytes"] < 0
                or not isinstance(approval_source["row_count"], int)
                or isinstance(approval_source["row_count"], bool)
                or approval_source["row_count"] < 1
                or approval_source["row_count"] != len(report_tables)
                or approval_source["media_type"] != "text/tab-separated-values"
            ):
                raise ContractValidationError(
                    "report-table approval provenance does not reconcile with "
                    "the approved records"
                )

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
