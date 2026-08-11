"""Scientific evidence-manifest validation and normalization."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from norad.contracts.scientific_evidence import (
    computational_validation,
    review_package,
    step08,
)
from norad.contracts.scientific_evidence.step08 import (
    NA_VALUE,
    Table,
    read_tsv,
    sha256_file,
)

from .contracts import (
    EVIDENCE_MANIFEST_HEADER,
)
from .intake import resolve_declared_path, split_ids, validate_iso_date


def validate_evidence_manifest(
    value: str | Path,
    review_id: str,
    plan: Mapping[str, str],
    input_hashes: dict[Path, str],
) -> tuple[
    Table,
    list[dict[str, str]],
    dict[str, list[dict[str, str]]],
    list[dict[str, str]],
]:
    manifest = read_tsv("Scientific evidence manifest", value, EVIDENCE_MANIFEST_HEADER)
    step08.ensure_unique(manifest.rows, "evidence_id", "Scientific evidence manifest")
    for category in review_package.CATEGORY_ORDER:
        if not any(row["evidence_category"] == category for row in manifest.rows):
            step08.fail(
                "Scientific evidence manifest must explicitly represent "
                f"category {category}."
            )
    primary_analysis_id = plan["primary_analysis_id"]
    sensitivity_analyses = set(
        split_ids(
            "sensitivity_analysis_ids",
            plan["sensitivity_analysis_ids"],
        )
    )
    source_paths: set[Path] = set()
    payload_by_category = {
        category: [] for category in review_package.ALLOWED_EVIDENCE_CATEGORIES
    }
    evidence_index_rows: list[dict[str, str]] = []
    evidence_order = {
        category: index
        for index, category in enumerate(review_package.ALLOWED_EVIDENCE_CATEGORIES)
    }
    normalized_manifest_rows: list[dict[str, str]] = []
    for row_number, original in enumerate(manifest.rows, start=2):
        row = dict(original)
        step08.validate_safe_id("evidence_id", row["evidence_id"])
        step08.validate_enum(
            f"Evidence manifest row {row_number} category",
            row["evidence_category"],
            review_package.ALLOWED_EVIDENCE_CATEGORIES,
        )
        step08.validate_enum(
            f"Evidence manifest row {row_number} status",
            row["evidence_status"],
            review_package.EVIDENCE_STATUSES,
        )
        category_allowed_analyses = (
            {primary_analysis_id, *sensitivity_analyses}
            if row["evidence_category"] in ("sensitivity_matrix", "leave_one_pair_out")
            else {primary_analysis_id}
        )
        if row["analysis_id"] not in category_allowed_analyses:
            step08.fail(
                f"Evidence manifest row {row_number} category "
                f"{row['evidence_category']} cannot use analysis_id "
                f"{row['analysis_id']}."
            )
        for column in ("reviewer", "owner"):
            step08.require_text(
                f"Evidence manifest row {row_number} {column}", row[column]
            )
        step08.validate_safe_id(
            f"Evidence manifest row {row_number} policy_version",
            row["policy_version"],
        )
        validate_iso_date(
            f"Evidence manifest row {row_number} evidence_date",
            row["evidence_date"],
            allow_na=True,
        )
        status = row["evidence_status"]
        if status in ("missing", "not_applicable"):
            if any(
                row[column] != NA_VALUE
                for column in (
                    "source_path",
                    "source_sha256",
                    "source_row_count",
                )
            ):
                step08.fail(
                    f"Evidence {row['evidence_id']} with status {status} "
                    "must use NA for source path, hash, and row count."
                )
            if status == "not_applicable":
                step08.require_text(
                    f"Evidence {row['evidence_id']} not_applicable_reason",
                    row["not_applicable_reason"],
                )
            elif row["not_applicable_reason"] != NA_VALUE:
                step08.fail("Missing evidence must use not_applicable_reason=NA.")
            observed_path = NA_VALUE
            observed_hash = NA_VALUE
            observed_count = NA_VALUE
        else:
            if row["evidence_date"] == NA_VALUE:
                step08.fail(
                    f"Evidence {row['evidence_id']} with status {status} "
                    "must record evidence_date."
                )
            if row["not_applicable_reason"] != NA_VALUE:
                step08.fail(
                    "Complete or incomplete evidence must use not_applicable_reason=NA."
                )
            source_path = resolve_declared_path(row["source_path"], manifest.path)
            source_path = step08.require_file(
                f"Evidence source {row['evidence_id']}", source_path
            )
            if source_path in source_paths:
                step08.fail(
                    "Scientific evidence manifest declares the same source "
                    f"path more than once: {source_path}"
                )
            source_paths.add(source_path)
            step08.validate_hash(
                f"Evidence {row['evidence_id']} source_sha256",
                row["source_sha256"],
            )
            observed_hash = sha256_file(source_path)
            if observed_hash != row["source_sha256"]:
                step08.fail(f"Evidence source hash differs for {row['evidence_id']}.")
            expected_header = (
                computational_validation.HEADER
                if row["evidence_category"] == "computational_validation"
                else review_package.CATEGORY_HEADERS[row["evidence_category"]]
            )
            source_table = read_tsv(
                f"Evidence source {row['evidence_id']}",
                source_path,
                expected_header,
            )
            declared_count = step08.parse_nonnegative_int(
                f"Evidence {row['evidence_id']} source_row_count",
                row["source_row_count"],
            )
            if declared_count != len(source_table.rows):
                step08.fail(
                    f"Evidence source row count differs for {row['evidence_id']}."
                )
            for source_row_number, payload in enumerate(source_table.rows, start=2):
                if payload["review_id"] != review_id:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong review_id."
                    )
                if payload["evidence_id"] != row["evidence_id"]:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong evidence_id."
                    )
                if row["evidence_category"] in (
                    "sensitivity_matrix",
                    "leave_one_pair_out",
                ):
                    if payload["analysis_id"] not in {
                        primary_analysis_id,
                        *sensitivity_analyses,
                    }:
                        step08.fail(
                            f"Evidence {row['evidence_id']} payload "
                            "references an analysis_id outside the primary "
                            "and declared sensitivity analyses."
                        )
                elif payload["analysis_id"] != row["analysis_id"]:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload references "
                        "an analysis_id different from its manifest row."
                    )
            if row["evidence_category"] in payload_by_category:
                payload_by_category[row["evidence_category"]].extend(source_table.rows)
            input_hashes[source_path] = observed_hash
            observed_path = str(source_path)
            observed_count = str(len(source_table.rows))
        normalized_manifest_rows.append(row)
        evidence_index_rows.append(
            {
                "review_id": review_id,
                "evidence_id": row["evidence_id"],
                "evidence_category": row["evidence_category"],
                "analysis_id": row["analysis_id"],
                "source_path": observed_path,
                "declared_sha256": row["source_sha256"],
                "observed_sha256": observed_hash,
                "declared_row_count": row["source_row_count"],
                "observed_row_count": observed_count,
                "evidence_status": status,
                "not_applicable_reason": row["not_applicable_reason"],
                "reviewer": row["reviewer"],
                "owner": row["owner"],
                "evidence_date": row["evidence_date"],
                "policy_version": row["policy_version"],
            }
        )
    sort_key = lambda item: (
        evidence_order[item["evidence_category"]],
        item["evidence_id"],
    )
    normalized_manifest_rows.sort(key=sort_key)
    evidence_index_rows.sort(key=sort_key)
    return (
        manifest,
        normalized_manifest_rows,
        payload_by_category,
        evidence_index_rows,
    )
