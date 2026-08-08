"""Explicit native reconciliation for Steps 00c, 06, 07, and 08."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.libraries.alignments import orientation as alignment_orientation

from .contracts import step08
from .core import declared_contract_path, issue
from .models import STEP06_COUNTS_HEADER, ArtifactIndexError, Inspection


def infer_orient_from_path(path: Path) -> str:
    orientation = alignment_orientation.infer_orientation_from_path(path)
    if orientation is None:
        raise ArtifactIndexError(
            f"Unable to infer mechanical orientation from filename: {path}"
        )
    return orientation


def native_int(row: Mapping[str, str], field_name: str) -> int:
    value = row.get(field_name, "")
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ArtifactIndexError(
            f"Native field {field_name} is not a non-negative integer: {value!r}"
        )
    return int(value)


def mark_native_transaction_failed(
    members: Sequence[Inspection],
    marker_adapter: str,
    message: str,
) -> None:
    marker = next(
        (
            member
            for member in members
            if member.row["adapter"] == marker_adapter
            and member.completion_status == "complete"
        ),
        None,
    )
    if marker is None:
        marker = next(
            (member for member in members if member.completion_status == "complete"),
            None,
        )
    if marker is None:
        return
    marker.completion_status = "failed"
    marker.state_reason = "Native logical transaction is inconsistent."
    marker.errors.append(
        issue(
            "native_transaction_inconsistent",
            message,
            marker.row["artifact_id"],
        )
    )


def require_referenced_source(
    *,
    row: Mapping[str, str],
    path_field: str,
    hash_field: str,
    row_count_field: str | None,
    source_lookup: Mapping[Path, Inspection],
) -> Inspection:
    path_value = row.get(path_field, "")
    if not path_value:
        raise ArtifactIndexError(f"Native reference field {path_field} is empty")
    target = source_lookup.get(declared_contract_path(path_value))
    if target is None:
        raise ArtifactIndexError(
            f"Native reference {path_field} is not declared by the inventory: "
            f"{path_value}"
        )
    if target.completion_status != "complete" or target.snapshot is None:
        raise ArtifactIndexError(
            f"Native reference {path_field} is not complete: {path_value}"
        )
    if row.get(hash_field, "") != target.snapshot.sha256:
        raise ArtifactIndexError(
            f"Native reference hash {hash_field} disagrees with {path_field}"
        )
    if row_count_field is not None:
        expected_count = target.source["row_count"] if target.source else None
        observed_count = row.get(row_count_field, "")
        if expected_count is None:
            if observed_count != step08.NA_VALUE:
                raise ArtifactIndexError(
                    f"Native binary reference {row_count_field} must be "
                    f"{step08.NA_VALUE}"
                )
        elif native_int(row, row_count_field) != expected_count:
            raise ArtifactIndexError(
                f"Native reference row count {row_count_field} disagrees "
                f"with {path_field}"
            )
    return target


def reconcile_step00c(members: Sequence[Inspection]) -> None:
    contig_sets = [
        member.native.get("contigs")
        for member in members
        if member.row["adapter"]
        in {
            "step00c_reference_fasta_v1",
            "step00c_reference_fai_v1",
            "step00c_reference_dict_v1",
        }
    ]
    if len(contig_sets) != 3 or any(value is None for value in contig_sets):
        raise ArtifactIndexError(
            "Step 00c FASTA/FAI/DICT contig projections are incomplete"
        )
    if not all(value == contig_sets[0] for value in contig_sets[1:]):
        raise ArtifactIndexError(
            "Step 00c FASTA/FAI/DICT contig names or lengths disagree"
        )


def reconcile_step06(members: Sequence[Inspection]) -> None:
    counts = next(
        member
        for member in members
        if member.row["adapter"] == "step06_orientation_counts_v1"
    )
    row = counts.first_row or {}
    values = {
        field_name: native_int(row, field_name)
        for field_name in STEP06_COUNTS_HEADER[1:-1]
    }
    if row.get("sample_id") != counts.row["scope_id"]:
        raise ArtifactIndexError(
            "Step 06 count sample_id disagrees with inventory scope"
        )
    for orientation in alignment_orientation.ORIENTATIONS:
        if not alignment_orientation.mechanical_like_count_detail(values, orientation)[
            0
        ]:
            raise ArtifactIndexError(
                f"Step 06 {orientation} count arithmetic is invalid"
            )
    if values["assigned_records"] != (
        values["fwd_like_records"] + values["rev_like_records"]
    ):
        raise ArtifactIndexError("Step 06 assigned count arithmetic is invalid")
    if values["input_records"] != (
        values["assigned_records"] + values["unassigned_records"]
    ):
        raise ArtifactIndexError("Step 06 input count arithmetic is invalid")
    try:
        assigned_fraction = float(row.get("assigned_fraction", ""))
    except ValueError as exc:
        raise ArtifactIndexError("Step 06 assigned_fraction is not numeric") from exc
    if not 0.0 <= assigned_fraction <= 1.0:
        raise ArtifactIndexError("Step 06 assigned_fraction is outside [0, 1]")
    expected_fraction = (
        values["assigned_records"] / values["input_records"]
        if values["input_records"]
        else 0.0
    )
    # The Step 06 producer writes this value with printf "%.6f".
    if abs(assigned_fraction - expected_fraction) > 5.000001e-7:
        raise ArtifactIndexError(
            "Step 06 assigned_fraction disagrees with count arithmetic"
        )


def reconcile_step07(members: Sequence[Inspection]) -> None:
    vcfs = [
        member for member in members if member.row["adapter"] == "step07_mpileup_vcf_v1"
    ]
    receipt = next(
        member
        for member in members
        if member.row["adapter"] == "step07_mpileup_receipt_v1"
    )
    receipt_rows = receipt.native.get("rows", [])
    if len(vcfs) != 2 or len(receipt_rows) != 2:
        raise ArtifactIndexError(
            "Step 07 transaction must contain two VCFs and two receipt rows"
        )
    sample_orders = [vcf.native.get("samples") for vcf in vcfs]
    if (
        any(not samples for samples in sample_orders)
        or sample_orders[0] != sample_orders[1]
    ):
        raise ArtifactIndexError(
            "Step 07 VCF sample columns disagree across orientations"
        )
    required_format_ids = {"DP", "AD", "ADF", "ADR", "SP"}
    required_info_ids = {"AD", "ADF", "ADR"}
    for vcf in vcfs:
        missing_format = required_format_ids - set(vcf.native.get("format_ids", []))
        missing_info = required_info_ids - set(vcf.native.get("info_ids", []))
        if missing_format or missing_info:
            raise ArtifactIndexError(
                "Step 07 VCF lacks required header definitions; missing "
                f"FORMAT={sorted(missing_format)}, INFO={sorted(missing_info)}"
            )
    cohort_ids = {row["cohort_id"] for row in receipt_rows}
    partition_ids = {row["partition_id"] for row in receipt_rows}
    if len(cohort_ids) != 1 or len(partition_ids) != 1:
        raise ArtifactIndexError(
            "Step 07 receipt rows disagree on cohort or partition identity"
        )
    cohort_id = next(iter(cohort_ids))
    partition_id = next(iter(partition_ids))
    receipt_by_path: dict[Path, Mapping[str, str]] = {}
    for row in receipt_rows:
        path = declared_contract_path(row["vcf_path"])
        if path in receipt_by_path:
            raise ArtifactIndexError("Step 07 receipt repeats a VCF path")
        receipt_by_path[path] = row
    observed_orientations: set[str] = set()
    for vcf in vcfs:
        row = receipt_by_path.get(vcf.resolved_path)
        if row is None:
            raise ArtifactIndexError(
                "Step 07 receipt does not declare every inventory VCF path"
            )
        orientation = infer_orient_from_path(vcf.resolved_path)
        observed_orientations.add(orientation)
        if (
            row["cohort_id"] != cohort_id
            or row["partition_id"] != partition_id
            or row["orientation"] != orientation
        ):
            raise ArtifactIndexError(
                "Step 07 receipt cohort, partition, or orientation disagrees "
                "with the inventory VCF"
            )
        if native_int(row, "sample_count") != len(sample_orders[0]):
            raise ArtifactIndexError(
                "Step 07 receipt sample_count disagrees with VCF columns"
            )
        if native_int(row, "vcf_record_count") != (
            vcf.source["row_count"] if vcf.source else None
        ):
            raise ArtifactIndexError(
                "Step 07 receipt record count disagrees with its VCF"
            )
    if observed_orientations != alignment_orientation.REQUIRED_ORIENTATIONS:
        raise ArtifactIndexError("Step 07 transaction lacks one neutral orientation")


def reconcile_step08(
    members: Sequence[Inspection],
    source_lookup: Mapping[Path, Inspection],
) -> None:
    sites = next(
        member for member in members if member.row["adapter"] == "step08_sites_v1"
    )
    inputs = next(
        member for member in members if member.row["adapter"] == "step08_inputs_v1"
    )
    summary = next(
        member for member in members if member.row["adapter"] == "step08_summary_v1"
    )
    input_rows = inputs.native.get("rows", [])
    summary_row = summary.first_row or {}
    samples = sites.native.get("samples", [])
    if not input_rows or not samples:
        raise ArtifactIndexError(
            "Step 08 inputs and sample-block sites must be non-empty"
        )
    partitions: dict[str, set[str]] = defaultdict(set)
    sum_fields = (
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
        "published_candidate_count",
    )
    observed_sums = Counter()
    receipt_paths: set[Path] = set()
    input_keys: set[tuple[str, str]] = set()
    input_vcf_paths: set[Path] = set()
    for row in input_rows:
        if row["cohort_id"] != sites.row["scope_id"]:
            raise ArtifactIndexError(
                "Step 08 input cohort disagrees with inventory scope"
            )
        input_key = (row["partition_id"], row["orientation"])
        if input_key in input_keys:
            raise ArtifactIndexError(
                "Step 08 inputs repeat a partition/orientation key"
            )
        input_keys.add(input_key)
        partitions[row["partition_id"]].add(row["orientation"])
        if native_int(row, "sample_count") != len(samples):
            raise ArtifactIndexError(
                "Step 08 input sample_count disagrees with sites columns"
            )
        if native_int(row, "declared_vcf_record_count") != native_int(
            row, "observed_vcf_record_count"
        ):
            raise ArtifactIndexError(
                "Step 08 declared and observed VCF counts disagree"
            )
        if native_int(row, "observed_alt_allele_count") != (
            native_int(row, "supported_snv_count")
            + native_int(row, "skipped_symbolic_count")
            + native_int(row, "skipped_non_snv_count")
        ):
            raise ArtifactIndexError("Step 08 alternate-allele counts do not reconcile")
        if native_int(row, "published_candidate_count") != native_int(
            row, "supported_snv_count"
        ):
            raise ArtifactIndexError(
                "Step 08 supported and published candidate counts disagree"
            )
        vcf = require_referenced_source(
            row=row,
            path_field="vcf_path",
            hash_field="vcf_sha256",
            row_count_field=None,
            source_lookup=source_lookup,
        )
        expected_orientation = infer_orient_from_path(vcf.resolved_path)
        if (
            row["orientation"] != expected_orientation
            or vcf.native.get("samples") != samples
        ):
            raise ArtifactIndexError(
                "Step 08 input partition, orientation, or sample order "
                "disagrees with its Step 07 VCF"
            )
        if vcf.resolved_path in input_vcf_paths:
            raise ArtifactIndexError("Step 08 inputs repeat a VCF path")
        input_vcf_paths.add(vcf.resolved_path)
        if native_int(row, "observed_vcf_record_count") != (
            vcf.source["row_count"] if vcf.source else None
        ):
            raise ArtifactIndexError(
                "Step 08 input observed count disagrees with source VCF"
            )
        receipt = require_referenced_source(
            row=row,
            path_field="step07_receipt_path",
            hash_field="step07_receipt_sha256",
            row_count_field=None,
            source_lookup=source_lookup,
        )
        if receipt.row["scope_id"] != vcf.row["scope_id"]:
            raise ArtifactIndexError(
                "Step 08 input receipt belongs to the wrong Step 07 scope"
            )
        receipt_rows = receipt.native.get("rows", [])
        matching_receipt_rows = [
            receipt_row
            for receipt_row in receipt_rows
            if declared_contract_path(receipt_row["vcf_path"]) == vcf.resolved_path
        ]
        if len(matching_receipt_rows) != 1:
            raise ArtifactIndexError(
                "Step 08 input VCF lacks one matching Step 07 receipt row"
            )
        receipt_row = matching_receipt_rows[0]
        for field_name in (
            "cohort_id",
            "partition_id",
            "selector_type",
            "selector_value",
            "orientation",
        ):
            if row[field_name] != receipt_row[field_name]:
                raise ArtifactIndexError(
                    f"Step 08 input {field_name} disagrees with Step 07 receipt"
                )
        if native_int(row, "declared_vcf_record_count") != native_int(
            receipt_row, "vcf_record_count"
        ):
            raise ArtifactIndexError(
                "Step 08 declared VCF count disagrees with Step 07 receipt"
            )
        receipt_paths.add(receipt.resolved_path)
        for field_name in sum_fields:
            observed_sums[field_name] += native_int(row, field_name)
    if any(
        orientations != alignment_orientation.REQUIRED_ORIENTATIONS
        for orientations in partitions.values()
    ) or len(input_rows) != 2 * len(partitions):
        raise ArtifactIndexError(
            "Step 08 inputs do not contain both orientations per partition"
        )
    expected_scalars = {
        "partition_count": len(partitions),
        "step07_receipt_count": len(receipt_paths),
        "input_vcf_count": len(input_rows),
        "sample_count": len(samples),
        "published_candidate_count": (
            sites.source["row_count"] if sites.source else None
        ),
    }
    for field_name, expected in expected_scalars.items():
        if native_int(summary_row, field_name) != expected:
            raise ArtifactIndexError(f"Step 08 summary {field_name} is inconsistent")
    for field_name in sum_fields:
        if native_int(summary_row, field_name) != observed_sums[field_name]:
            raise ArtifactIndexError(
                f"Step 08 summary {field_name} does not reconcile inputs"
            )
    for field_name in (
        "annotation_gtf",
        "annotation_gtf_sha256",
        "orientation_policy",
    ):
        values = {row[field_name] for row in input_rows}
        if values != {summary_row[field_name]}:
            raise ArtifactIndexError(
                f"Step 08 {field_name} differs across inputs and summary"
            )
