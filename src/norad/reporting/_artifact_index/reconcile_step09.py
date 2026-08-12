"""Explicit scientific reconciliation for Step 09 outputs."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.contracts.scientific_evidence import step08, step09

from .models import ArtifactIndexError, Inspection
from .reconcile_native import NativeSourceIndex, native_int, require_referenced_source


def validate_significant_exact_subset(
    all_sites_path: Path,
    significant_path: Path,
) -> None:
    try:
        all_stream = all_sites_path.open(encoding="utf-8", newline="")
        significant_stream = significant_path.open(encoding="utf-8", newline="")
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not open Step 09 result tables: {exc}"
        ) from exc
    try:
        with all_stream, significant_stream:
            all_reader = csv.DictReader(all_stream, delimiter="\t")
            significant_reader = csv.DictReader(
                significant_stream,
                delimiter="\t",
            )
            if tuple(all_reader.fieldnames or ()) != tuple(
                significant_reader.fieldnames or ()
            ):
                raise ArtifactIndexError(
                    "Step 09 significant and all-sites headers disagree"
                )
            current = next(significant_reader, None)
            for all_row in all_reader:
                if all_row["call_status"] not in {
                    "significant_up",
                    "significant_down",
                }:
                    continue
                if current != all_row:
                    raise ArtifactIndexError(
                        "Step 09 significant-sites table is not the exact "
                        "ordered significant subset of all-sites"
                    )
                current = next(significant_reader, None)
            if current is not None:
                raise ArtifactIndexError(
                    "Step 09 significant-sites table contains an extra row"
                )
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error, KeyError) as exc:
        raise ArtifactIndexError(
            f"Could not compare Step 09 result tables: {exc}"
        ) from exc


def validate_step09_statuses(
    all_value_counts: Mapping[str, Mapping[str, int]],
) -> None:
    allowed_test_statuses = set(step09.STEP09_TEST_STATUSES)
    allowed_call_statuses = set(step09.STEP09_CALL_STATUSES)
    unknown_test = set(all_value_counts.get("test_status", {})) - (
        allowed_test_statuses
    )
    unknown_call = set(all_value_counts.get("call_status", {})) - (
        allowed_call_statuses
    )
    if unknown_test or unknown_call:
        raise ArtifactIndexError(
            "Step 09 all-sites contains unknown statuses; "
            f"test_status={sorted(unknown_test)}, "
            f"call_status={sorted(unknown_call)}"
        )


def validate_step09_mutation_spectrum(
    mutation_rows: Sequence[Mapping[str, str]],
    all_sites: Inspection,
    analysis_id: str,
) -> None:
    if [row["mutation_type"] for row in mutation_rows] != list(
        step09.CANONICAL_MUTATIONS
    ):
        raise ArtifactIndexError(
            "Step 09 mutation spectrum must contain the canonical ordered "
            "12 directed substitutions"
        )
    pair_counts = all_sites.native.get("mutation_pair_counts", {})
    total = all_sites.source["row_count"] if all_sites.source else 0
    for row in mutation_rows:
        mutation_type = row["mutation_type"]
        reference, alternate = mutation_type.split(">")
        if (
            row["analysis_id"] != analysis_id
            or row["rna_ref"] != reference
            or row["rna_alt"] != alternate
        ):
            raise ArtifactIndexError(
                "Step 09 mutation spectrum identity columns do not reconcile"
            )
        expected_counts = pair_counts.get(mutation_type, {})
        for field_name in (
            "candidate_count",
            "successfully_tested_count",
            "significant_up_count",
            "significant_down_count",
        ):
            if native_int(row, field_name) != expected_counts.get(field_name, 0):
                raise ArtifactIndexError(
                    f"Step 09 mutation spectrum {field_name} does not "
                    f"reconcile for {mutation_type}"
                )
        try:
            observed_fraction = float(row["candidate_fraction"])
        except ValueError as exc:
            raise ArtifactIndexError(
                "Step 09 mutation spectrum candidate_fraction is not numeric"
            ) from exc
        expected_fraction = (
            0.0 if total == 0 else expected_counts.get("candidate_count", 0) / total
        )
        if not 0.0 <= observed_fraction <= 1.0 or not step08.values_close(
            observed_fraction, expected_fraction
        ):
            raise ArtifactIndexError(
                "Step 09 mutation spectrum candidate_fraction does not "
                f"reconcile for {mutation_type}"
            )


def reconcile_step09(
    members: Sequence[Inspection],
    sources: NativeSourceIndex,
) -> None:
    all_sites = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_all_sites_v1"
    )
    significant = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_significant_sites_v1"
    )
    summary = next(
        member for member in members if member.row["adapter"] == "step09_cmh_summary_v1"
    )
    mutation = next(
        member
        for member in members
        if member.row["adapter"] == "step09_mutation_spectrum_tsv_v1"
    )
    summary_row = summary.first_row or {}
    all_samples = all_sites.native.get("samples", [])
    if not all_samples or all_samples != significant.native.get("samples", []):
        raise ArtifactIndexError("Step 09 result sample blocks disagree")
    if native_int(summary_row, "sample_count") != len(all_samples):
        raise ArtifactIndexError(
            "Step 09 summary sample_count disagrees with result columns"
        )
    if native_int(summary_row, "candidate_count") != (
        all_sites.source["row_count"] if all_sites.source else None
    ):
        raise ArtifactIndexError(
            "Step 09 summary candidate_count disagrees with all-sites rows"
        )
    significant_count = significant.source["row_count"] if significant.source else None
    if significant_count != (
        native_int(summary_row, "significant_up_count")
        + native_int(summary_row, "significant_down_count")
    ):
        raise ArtifactIndexError(
            "Step 09 significant table count disagrees with summary"
        )
    validate_significant_exact_subset(
        all_sites.resolved_path,
        significant.resolved_path,
    )
    all_value_counts = all_sites.native.get("value_counts", {})
    significant_value_counts = significant.native.get("value_counts", {})
    validate_step09_statuses(all_value_counts)
    for summary_field, column, status in step09.STEP09_STATUS_COUNT_FIELDS:
        if native_int(summary_row, summary_field) != (
            all_value_counts.get(column, {}).get(status, 0)
        ):
            raise ArtifactIndexError(
                f"Step 09 summary {summary_field} disagrees with all-sites"
            )
    significant_statuses = significant_value_counts.get("call_status", {})
    if set(significant_statuses) - {"significant_up", "significant_down"}:
        raise ArtifactIndexError(
            "Step 09 significant table contains a non-significant call status"
        )
    for summary_field, status in (
        ("significant_up_count", "significant_up"),
        ("significant_down_count", "significant_down"),
    ):
        if significant_statuses.get(status, 0) != native_int(
            summary_row, summary_field
        ):
            raise ArtifactIndexError(
                f"Step 09 significant {status} rows disagree with summary"
            )
    mutation_rows = mutation.native.get("rows", [])
    validate_step09_mutation_spectrum(
        mutation_rows,
        all_sites,
        summary_row.get("analysis_id", ""),
    )
    for field_name, summary_field in (
        ("candidate_count", "candidate_count"),
        ("successfully_tested_count", "successfully_tested_count"),
        ("significant_up_count", "significant_up_count"),
        ("significant_down_count", "significant_down_count"),
    ):
        observed = sum(native_int(row, field_name) for row in mutation_rows)
        if observed != native_int(summary_row, summary_field):
            raise ArtifactIndexError(
                f"Step 09 mutation spectrum {field_name} does not reconcile"
            )
    for path_field, hash_field, adapter_id in (
        ("step08_sites_path", "step08_sites_sha256", "step08_sites_v1"),
        ("step08_inputs_path", "step08_inputs_sha256", "step08_inputs_v1"),
    ):
        target = require_referenced_source(
            row=summary_row,
            path_field=path_field,
            hash_field=hash_field,
            row_count_field=None,
            sources=sources,
        )
        if target.row["adapter"] != adapter_id:
            raise ArtifactIndexError(
                f"Step 09 {path_field} points to the wrong adapter"
            )
        if (
            adapter_id == "step08_sites_v1"
            and target.native.get("samples") != all_samples
        ):
            raise ArtifactIndexError(
                "Step 09 result sample order disagrees with Step 08 sites"
            )
