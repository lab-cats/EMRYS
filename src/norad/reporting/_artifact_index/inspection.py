"""Artifact inspection dispatch, metrics, and run-anchor checks."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts

from ._text_common import inspect_nonempty_text, iter_text_lines
from ._text_genomic import (
    inspect_bed12,
    inspect_dict,
    inspect_fai,
    inspect_fasta,
    inspect_picard_metrics,
    inspect_star_sj,
    inspect_vcf,
)
from ._text_tabular import (
    inspect_tsv,
    validate_native_run_anchors,
)
from .binary_readers import (
    inspect_bai_structure,
    inspect_bgzf_bam,
    inspect_pdf_structure,
)
from .core import declared_contract_path, issue, stat_source
from .models import ANCHOR_HASH_FIELDS, AdapterSpec, ArtifactIndexError, Inspection


def inspect_source(
    row: dict[str, str],
    spec: AdapterSpec,
    *,
    source_root: Path,
) -> Inspection:
    resolved = declared_contract_path(
        row["source_path"],
        source_root=source_root,
    )
    snapshot = stat_source(resolved)
    required = row["required"] == "true"
    artifact_id = row["artifact_id"]
    # All outcomes describe this same source identity; branches supply only state.
    build_inspection = partial(
        Inspection,
        row=row,
        spec=spec,
        resolved_path=resolved,
        attempt_provenance_status="unavailable",
        snapshot=snapshot,
    )
    if snapshot.status == "missing":
        if required:
            return build_inspection(
                availability_status="missing",
                completion_status="incomplete",
                state_reason="Required source is absent.",
                source=None,
                warnings=[
                    issue(
                        "required_source_missing",
                        f"Required source is absent: {row['source_path']}",
                        artifact_id,
                    )
                ],
            )
        return build_inspection(
            availability_status="missing",
            completion_status="not_attempted",
            state_reason="Optional source is absent.",
            attempt_provenance_status="not_attempted",
            source=None,
        )
    if snapshot.status == "externally_unavailable":
        return build_inspection(
            availability_status="externally_unavailable",
            completion_status="incomplete",
            state_reason="Declared source cannot be accessed.",
            source=None,
            warnings=[
                issue(
                    "source_externally_unavailable",
                    f"Declared source cannot be accessed "
                    f"({snapshot.file_type}): {row['source_path']}",
                    artifact_id,
                )
            ],
        )
    if snapshot.status == "unknown":
        return build_inspection(
            availability_status="unknown",
            completion_status="failed",
            state_reason="Declared source is not a readable regular file.",
            source=None,
            errors=[
                issue(
                    "source_state_unknown",
                    f"Declared source is not a readable regular file "
                    f"({snapshot.file_type}): {row['source_path']}",
                    artifact_id,
                )
            ],
        )

    source = {
        "path": row["source_path"],
        "sha256": snapshot.sha256,
        "size_bytes": snapshot.size_bytes,
        "row_count": None,
        "media_type": (
            "text/plain"
            if spec.kind == "star_index"
            and resolved.name not in {"Genome", "SA", "SAindex"}
            else spec.media_type
        ),
    }
    try:
        row_count, first_row, parameters, native_metrics = inspect_present(
            resolved, spec
        )
        source["row_count"] = row_count
        if spec.kind == "validation_report":
            validation_rows = native_metrics.get("rows", [])
            if any(
                item["step_id"] != spec.step_id
                or item["scope_id"] != row["scope_id"]
                or item["status"] not in {"pass", "fail"}
                or not contracts.SAFE_ID_RE.fullmatch(item["check_id"])
                for item in validation_rows
            ):
                raise ArtifactIndexError(
                    "Validation report step, scope, check ID, or status is invalid"
                )
            check_ids = [item["check_id"] for item in validation_rows]
            if len(check_ids) != len(set(check_ids)):
                raise ArtifactIndexError(
                    "Validation report contains duplicate check IDs"
                )
        validate_native_run_anchors(first_row, row)
        metrics = build_metrics(row, row_count, native_metrics)
        if spec.kind == "validation_report" and native_metrics.get(
            "value_counts", {}
        ).get("status", {}).get("fail", 0):
            return build_inspection(
                availability_status="present",
                completion_status="failed",
                state_reason="Validation report contains failed checks.",
                source=source,
                parameters=parameters,
                metrics=metrics,
                native=native_metrics,
                first_row=first_row,
                errors=[
                    issue(
                        "validation_checks_failed",
                        "One or more explicit validation checks failed.",
                        artifact_id,
                    )
                ],
            )
        return build_inspection(
            availability_status="present",
            completion_status="complete",
            state_reason=None,
            source=source,
            parameters=parameters,
            metrics=metrics,
            native=native_metrics,
            first_row=first_row,
        )
    except ArtifactIndexError as exc:
        return build_inspection(
            availability_status="present",
            completion_status="failed",
            state_reason="Present source failed its registered adapter.",
            source=source,
            errors=[
                issue(
                    "adapter_validation_failed",
                    f"{spec.adapter_id}: {exc}",
                    artifact_id,
                )
            ],
        )


def inspect_present(
    path: Path,
    spec: AdapterSpec,
) -> tuple[int | None, dict[str, str] | None, dict[str, Any], dict[str, Any]]:
    if spec.kind in {"tsv", "sample_blocks_tsv", "validation_report"}:
        return inspect_tsv(path, spec)
    if spec.kind == "vcf":
        row_count, native = inspect_vcf(path)
        return row_count, None, native, native
    if spec.kind == "fasta":
        row_count, native = inspect_fasta(path)
        return row_count, None, native, native
    if spec.kind == "fai":
        row_count, native = inspect_fai(path)
        return row_count, None, native, native
    if spec.kind == "dict":
        row_count, native = inspect_dict(path)
        return row_count, None, native, native
    if spec.kind == "bed12":
        row_count, native = inspect_bed12(path)
        return row_count, None, native, native
    if spec.kind == "star_sj":
        row_count, native = inspect_star_sj(path)
        return row_count, None, native, native
    if spec.kind == "picard_metrics":
        row_count, native = inspect_picard_metrics(path)
        return row_count, None, {}, native
    if spec.kind == "pdf":
        native = inspect_pdf_structure(path)
        return None, None, {}, native
    if spec.kind == "bam":
        native = inspect_bgzf_bam(path)
        return None, None, {}, native
    if spec.kind == "bai":
        native = inspect_bai_structure(path)
        return None, None, {}, native
    if spec.kind == "quickcheck":
        expected = "PASS: samtools quickcheck completed with no errors."
        observed = [line for _line_number, line in iter_text_lines(path) if line]
        if observed != [expected]:
            raise ArtifactIndexError("quickcheck output does not declare PASS")
        return 1, None, {}, {"quickcheck_pass": True}
    if spec.kind == "flagstat":
        count = 0
        native: dict[str, Any] = {}
        for line_number, line in iter_text_lines(path):
            count += 1
            match = re.match(r"^([0-9]+) \+ ([0-9]+) (.+)$", line)
            if match is None:
                raise ArtifactIndexError(f"flagstat line {line_number} is malformed")
            passed = int(match.group(1))
            failed = int(match.group(2))
            label = match.group(3)
            if label.startswith("in total "):
                native["total_reads"] = passed + failed
            elif label.startswith("mapped "):
                native["mapped_reads"] = passed + failed
        if "total_reads" not in native or "mapped_reads" not in native:
            raise ArtifactIndexError(
                "flagstat output must contain total and mapped rows"
            )
        return count, None, {}, native
    if spec.kind == "rseqc":
        count = 0
        native: dict[str, Any] = {}
        for _line_number, line in iter_text_lines(path):
            count += 1
            match = re.match(r"^Fraction of reads (.+): ([0-9]*\.?[0-9]+)$", line)
            if match is None:
                continue
            key = re.sub(
                r"[^A-Za-z0-9._-]",
                "_",
                match.group(1).strip().lower(),
            ).strip("_")
            native[f"fraction_{key}"] = float(match.group(2))
        if not native:
            raise ArtifactIndexError("RSeQC fraction output is missing")
        return count, None, {}, native
    if spec.kind == "star_log_final":
        count = 0
        native: dict[str, Any] = {}
        key_value_count = 0
        for _line_number, line in iter_text_lines(path):
            count += 1
            if "|" not in line:
                continue
            key_text, value_text = (value.strip() for value in line.split("|", 1))
            if not key_text or not value_text:
                continue
            key_value_count += 1
            metric_key = re.sub(
                r"[^A-Za-z0-9._-]",
                "_",
                key_text.strip().lower(),
            ).strip("_")
            numeric = value_text.removesuffix("%").replace(",", "")
            try:
                native[metric_key] = float(numeric)
            except ValueError:
                continue
        if key_value_count == 0:
            raise ArtifactIndexError("STAR final log has no key/value rows")
        return count, None, {}, native
    if spec.kind == "star_index":
        if path.stat().st_size == 0:
            raise ArtifactIndexError("STAR index member is empty")
        if path.name in {"Genome", "SA", "SAindex"}:
            return None, None, {}, {}
        count, _native = inspect_nonempty_text(path)
        native: dict[str, Any] = {}
        if path.name == "genomeParameters.txt":
            for _line_number, line in iter_text_lines(path):
                fields = line.split()
                if len(fields) >= 2 and fields[0] == "sjdbOverhang":
                    try:
                        native["sjdbOverhang"] = int(fields[1])
                    except ValueError as exc:
                        raise ArtifactIndexError(
                            "STAR genomeParameters sjdbOverhang is invalid"
                        ) from exc
                    break
            if "sjdbOverhang" not in native:
                raise ArtifactIndexError(
                    "STAR genomeParameters is missing sjdbOverhang"
                )
        return count, None, {}, native
    if spec.kind == "text":
        count, native = inspect_nonempty_text(path)
        return count, None, {}, native
    raise ArtifactIndexError(f"Adapter kind is not implemented: {spec.kind}")


def build_metrics(
    row: Mapping[str, str],
    row_count: int | None,
    native: Mapping[str, Any],
) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    if row_count is not None:
        metrics.append(
            {
                "metric_id": "source_row_count",
                "name": "Source row count",
                "value": row_count,
                "unit": "rows",
                "status": "not_assessed",
                "source_artifact_id": row["artifact_id"],
            }
        )
    for key in sorted(native):
        value = native[key]
        if value is None or isinstance(value, (dict, list, tuple)):
            continue
        metric_id = re.sub(r"[^A-Za-z0-9._-]", "_", key)
        if metric_id == "source_row_count":
            continue
        metrics.append(
            {
                "metric_id": metric_id,
                "name": key.replace("_", " ").title(),
                "value": value,
                "unit": None,
                "status": (
                    "pass"
                    if key.endswith("_pass") and value is True
                    else "not_assessed"
                ),
                "source_artifact_id": row["artifact_id"],
            }
        )
    return metrics


def apply_run_contract_checks(
    inspections: Sequence[Inspection],
    run_contract: Mapping[str, Any],
) -> None:
    for inspection in inspections:
        if inspection.completion_status != "complete":
            continue
        mismatches: list[str] = []
        anchor_values = inspection.native.get("anchor_values", {})
        for field_name in ANCHOR_HASH_FIELDS:
            values = anchor_values.get(field_name, [])
            if any(value != run_contract[field_name] for value in values):
                mismatches.append(field_name)
        if inspection.row["scope_type"] == "analysis":
            analysis_ids = anchor_values.get("analysis_id", [])
            if any(
                value != run_contract["primary_analysis_id"] for value in analysis_ids
            ):
                mismatches.append("primary_analysis_id")
        primary_analysis_ids = anchor_values.get("primary_analysis_id", [])
        if any(
            value != run_contract["primary_analysis_id"]
            for value in primary_analysis_ids
        ):
            mismatches.append("primary_analysis_id")
        review_ids = anchor_values.get("review_id", [])
        if inspection.row["scope_type"] == "scientific_review" and any(
            value != inspection.row["scope_id"] for value in review_ids
        ):
            mismatches.append("review_id")
        cohort_ids = anchor_values.get("cohort_id", [])
        if inspection.row["scope_type"] == "cohort" and any(
            value != inspection.row["scope_id"] for value in cohort_ids
        ):
            mismatches.append("cohort_id")
        if mismatches:
            inspection.completion_status = "failed"
            inspection.state_reason = (
                "Present source conflicts with the explicit run contract."
            )
            inspection.errors.append(
                issue(
                    "run_contract_mismatch",
                    "Native source conflicts with run contract fields: "
                    + ", ".join(sorted(set(mismatches))),
                    inspection.row["artifact_id"],
                )
            )
