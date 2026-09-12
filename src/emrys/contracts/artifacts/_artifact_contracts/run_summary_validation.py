"""Run-summary status reduction and semantic validation."""

from __future__ import annotations

from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Any

from .artifact import validate_artifact_semantics
from .definitions import (
    PACKAGE_ROOT,
    ContractValidationError,
)
from .identity import (
    require_unique_key,
    resolve_contract_path,
    scope_key,
    validate_document_paths,
    validate_run_contract,
)
from .run_summary_status import (
    AGGREGATE_ARTIFACT_STATES,
    aggregate_artifact_state,
    artifact_rollup_state,
)


def validate_run_summary_semantics(
    document: dict[str, Any],
    *,
    source_root: Path = PACKAGE_ROOT,
) -> None:
    validate_run_contract(document["run_contract"], "run summary")
    validate_document_paths(document)
    if (
        document["analysis_policy"]["sha256"]
        != document["run_contract"]["primary_analysis_policy_sha256"]
    ):
        raise ContractValidationError(
            "modular run summary analysis policy differs from its run contract"
        )

    table_paths = tuple(Path(table["path"]) for table in document["tables"])
    if (
        len(table_paths) != 2
        or not table_paths[0].is_absolute()
        or table_paths[0].parent.name != document["run_id"]
        or table_paths
        != tuple(
            table_paths[0].parent / f"{document['run_id']}.{suffix}"
            for suffix in ("run_summary.tsv", "qc_summary.tsv")
        )
    ):
        raise ContractValidationError(
            "Run result tables must use their fixed paths and order"
        )

    publication = document["publication"]
    if (
        publication["finished_at"] != document["generated_at"]
        or document["generated_at"] != document["provenance"]["created_at"]
        or datetime.fromisoformat(publication["started_at"].replace("Z", "+00:00"))
        > datetime.fromisoformat(publication["finished_at"].replace("Z", "+00:00"))
    ):
        raise ContractValidationError("Run result publication timestamps disagree")

    artifacts = document["artifacts"]
    artifact_index = require_unique_key(artifacts, "artifact_id", "run artifacts")
    expected_source_paths: set[Path] = set()
    for artifact in artifacts:
        validate_artifact_semantics(artifact)
        expected_path = resolve_contract_path(
            artifact["expectation"]["source_path"],
            source_root=source_root,
        )
        if expected_path in expected_source_paths:
            raise ContractValidationError(
                f"run artifacts contain duplicate expected source path "
                f"{expected_path!r}"
            )
        expected_source_paths.add(expected_path)

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
