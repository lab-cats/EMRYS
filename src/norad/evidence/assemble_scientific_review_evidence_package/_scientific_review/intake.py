"""Review models, explicit input helpers, plan, and evidence manifest validation."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from norad.libraries.alignments import orientation as alignment_orientation

from .contracts import (
    COMPUTATIONAL_VALIDATION_HEADER,
    EVIDENCE_MANIFEST_HEADER,
    NA_VALUE,
    Table,
    read_tsv,
    review_package,
    sha256_file,
    step08,
)


@dataclass
class Artifact:
    label: str
    path: Path
    sha256: str
    row_count: str


@dataclass
class ReviewContext:
    review_id: str
    plan: dict[str, str]
    evidence_rows: list[dict[str, str]]
    category_rows: dict[str, list[dict[str, str]]]
    evidence_index_rows: list[dict[str, str]]
    artifacts: dict[str, Artifact]
    input_hashes: dict[Path, str]
    sample_ids: list[str]
    sample_rows: list[dict[str, str]]
    partition_rows: list[dict[str, str]]
    step08_input_rows: list[dict[str, str]]
    step08_site_rows: list[dict[str, str]]
    step09_all_rows: list[dict[str, str]]
    step09_significant_rows: list[dict[str, str]]
    step09_summary: dict[str, str]
    output_paths: dict[str, Path]


def validate_iso_date(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")
    if parsed.isoformat() != value:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")


def complement_base(value: str) -> str:
    complements = {"A": "T", "C": "G", "G": "C", "T": "A"}
    if value not in complements:
        step08.fail(f"Expected a canonical DNA base; got: {value}")
    return complements[value]


def split_ids(label: str, value: str) -> list[str]:
    if value == NA_VALUE:
        return []
    parts = value.split(",")
    if any(not part or part.strip() != part for part in parts):
        step08.fail(f"{label} must be comma-separated safe IDs or NA; got: {value}")
    for part in parts:
        step08.validate_safe_id(label, part)
    if len(parts) != len(set(parts)):
        step08.fail(f"{label} contains duplicate IDs: {value}")
    return parts


def require_directory(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_dir():
        step08.fail(f"{label} does not exist or is not a directory: {path}")
    return path.resolve()


def write_tsv(
    path: Path, header: Sequence[str], rows: Iterable[Mapping[str, str]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def artifact_from_table(label: str, table: Table) -> Artifact:
    return Artifact(
        label=label,
        path=table.path,
        sha256=sha256_file(table.path),
        row_count=str(len(table.rows)),
    )


def artifact_from_binary(label: str, path: Path) -> Artifact:
    return Artifact(
        label=label,
        path=path,
        sha256=sha256_file(path),
        row_count=NA_VALUE,
    )


def resolve_declared_path(value: str, source_file: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = source_file.parent / path
    return path.resolve()


def register_artifact(
    artifacts: dict[str, Artifact],
    input_hashes: dict[Path, str],
    key: str,
    artifact: Artifact,
) -> None:
    if key in artifacts:
        step08.fail(f"Internal artifact key was registered twice: {key}")
    artifacts[key] = artifact
    input_hashes[artifact.path] = artifact.sha256


def step09_paths(analysis_dir: Path, analysis_id: str) -> dict[str, Path]:
    return {
        "step09_all_sites": analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        "step09_significant_sites": (
            analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        "step09_summary": analysis_dir / f"{analysis_id}.cmh_summary.tsv",
        "step09_mutation_spectrum": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.tsv"
        ),
        "step09_mutation_spectrum_pdf": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.pdf"
        ),
        "step09_depth_delta_pdf": (analysis_dir / f"{analysis_id}.depth_delta.pdf"),
    }


def validate_review_plan(
    value: str | Path, review_id: str
) -> tuple[Table, dict[str, str], set[str]]:
    table = read_tsv("Scientific review plan", value, review_package.REVIEW_PLAN_HEADER)
    if len(table.rows) != 1:
        step08.fail("Scientific review plan must contain exactly one data row.")
    plan = table.rows[0]
    if plan["review_id"] != review_id:
        step08.fail("Scientific review plan review_id differs from --review-id.")
    step08.validate_safe_id("review_id", plan["review_id"])
    step08.validate_safe_id("primary_analysis_id", plan["primary_analysis_id"])
    requested_status = plan["overall_science_status"]
    if requested_status == review_package.RESERVED_SCIENCE_STATUS:
        step08.fail(
            "biological_interpretation_ready is reserved and cannot be "
            "produced by Step 09c."
        )
    step08.validate_enum(
        "overall_science_status", requested_status, review_package.SCIENCE_STATUSES
    )
    step08.validate_enum(
        "implementation_status",
        plan["implementation_status"],
        review_package.IMPLEMENTATION_STATUSES,
    )
    step08.validate_enum(
        "local_test_status",
        plan["local_test_status"],
        review_package.LOCAL_TEST_STATUSES,
    )
    step08.validate_enum(
        "runtime_validation_status",
        plan["runtime_validation_status"],
        review_package.RUNTIME_VALIDATION_STATUSES,
    )
    step08.validate_enum(
        "cluster_dry_run_status",
        plan["cluster_dry_run_status"],
        review_package.CLUSTER_DRY_RUN_STATUSES,
    )
    step08.validate_enum(
        "cluster_proof_status",
        plan["cluster_proof_status"],
        review_package.CLUSTER_PROOF_STATUSES,
    )
    step08.validate_enum(
        "orientation_status",
        plan["orientation_status"],
        review_package.ORIENTATION_STATUSES,
    )
    validate_iso_date("plan_date", plan["plan_date"])
    validate_iso_date(
        "review_completed_date",
        plan["review_completed_date"],
        allow_na=True,
    )
    for column in (
        "plan_version",
        "git_commit",
        "orientation_policy",
        "orientation_policy_version",
        "locus_selection_policy_version",
        "candidate_selection_policy_version",
        "sensitivity_policy_version",
        "background_policy_version",
        "annotation_policy_version",
        "adjudication_policy_version",
    ):
        step08.validate_safe_id(
            f"Scientific review plan {column}",
            plan[column],
        )
    for column in (
        "reviewer",
        "decision_owner",
        "locus_selection_rule",
        "candidate_selection_rule",
        "sensitivity_rule",
        "leave_one_pair_out_rule",
        "software_versions",
        "notes",
    ):
        step08.require_text(f"Scientific review plan {column}", plan[column])
    for column in (
        "locus_target_count",
        "top_up_count",
        "top_down_count",
        "discordant_count",
        "near_threshold_count",
    ):
        step08.parse_nonnegative_int(f"Scientific review plan {column}", plan[column])
    required_orientations = split_ids(
        "required_orientations", plan["required_orientations"]
    )
    if required_orientations != list(alignment_orientation.ORIENTATIONS):
        step08.fail(
            "required_orientations must be exactly "
            f"{','.join(alignment_orientation.ORIENTATIONS)} in that order."
        )
    required_strands = plan["required_annotation_strands"].split(",")
    if required_strands != ["+", "-"]:
        step08.fail("required_annotation_strands must be exactly +,-.")
    step08.require_text("required_annotation_cases", plan["required_annotation_cases"])
    superseded = split_ids("superseded_analysis_ids", plan["superseded_analysis_ids"])
    sensitivity = split_ids(
        "sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]
    )
    if plan["primary_analysis_id"] in superseded + sensitivity:
        step08.fail(
            "The primary analysis cannot also be superseded or a sensitivity run."
        )
    overlap = sorted(set(superseded) & set(sensitivity))
    if overlap:
        step08.fail(
            "Superseded and sensitivity analysis IDs must be disjoint; "
            f"overlap: {','.join(overlap)}."
        )
    allowed_analyses = {
        plan["primary_analysis_id"],
        *superseded,
        *sensitivity,
    }
    if plan["cluster_proof_status"] == "proven" and (
        plan["runtime_validation_status"] != "passed"
        or plan["cluster_dry_run_status"] != "passed"
    ):
        step08.fail(
            "cluster_proof_status=proven requires runtime and cluster "
            "dry-run status passed."
        )
    if requested_status == "science_review_complete_exploratory":
        if plan["review_completed_date"] == NA_VALUE:
            step08.fail(
                "An exploratory-complete science review requires review_completed_date."
            )
    elif plan["review_completed_date"] != NA_VALUE:
        step08.fail(
            "evidence_incomplete must use review_completed_date=NA so that "
            "review completion is not overstated."
        )
    return table, plan, allowed_analyses


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
    superseded_analyses = set(
        split_ids(
            "superseded_analysis_ids",
            plan["superseded_analysis_ids"],
        )
    )
    sensitivity_analyses = set(
        split_ids(
            "sensitivity_analysis_ids",
            plan["sensitivity_analysis_ids"],
        )
    )
    allowed_analyses = {
        primary_analysis_id,
        *superseded_analyses,
        *sensitivity_analyses,
    }
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
                COMPUTATIONAL_VALIDATION_HEADER
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


def validate_supporting_ids(label: str, value: str, evidence_ids: set[str]) -> None:
    for evidence_id in split_ids(label, value):
        if evidence_id not in evidence_ids:
            step08.fail(f"{label} references unknown evidence_id {evidence_id}.")


def category_is_complete(
    evidence_rows: Sequence[Mapping[str, str]], category: str
) -> bool:
    return (
        review_package.aggregate_evidence_status(evidence_rows, category) == "complete"
    )


def validate_candidate_reference(
    label: str, candidate_id: str, candidates: Mapping[str, Mapping[str, str]]
) -> Mapping[str, str]:
    result = candidates.get(candidate_id)
    if result is None:
        step08.fail(f"{label} references unknown candidate_id {candidate_id}.")
    return result
