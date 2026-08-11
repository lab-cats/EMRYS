"""Output-table validation for the neutral Step 08 contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.contracts.scientific_evidence._step08_definitions import (
    NA_VALUE,
    STEP08_AGGREGATE_COUNT_FIELDS,
    STEP08_INPUTS_HEADER,
    STEP08_METADATA_HEADER,
    STEP08_PARTITION_COUNT_FIELDS,
    STEP08_SUMMARY_HEADER,
    Table,
)
from norad.contracts.scientific_evidence._step08_support import (
    ensure_unique,
    fail,
    parse_nonnegative_int,
    parse_number,
    read_tsv,
    require_text,
    sample_block_header,
    validate_enum,
    validate_hash,
    validate_safe_id,
    values_close,
)
from norad.libraries.alignments import orientation as alignment_orientation


def validate_step08_inputs(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    sample_hash: str,
    partition_hash: str,
) -> Table:
    table = read_tsv("Step 08 input receipt", value, STEP08_INPUTS_HEADER)
    expected = [
        (partition, orientation)
        for partition in partitions
        for orientation in alignment_orientation.ORIENTATIONS
    ]
    if len(table.rows) != len(expected):
        fail(
            "Step 08 input receipt is not the complete declared partition "
            "x orientation set."
        )
    cohort_ids: set[str] = set()
    annotation_paths: set[str] = set()
    annotation_hashes: set[str] = set()
    for index, (row, (partition, orientation)) in enumerate(
        zip(table.rows, expected, strict=True), start=2
    ):
        if (
            row["partition_id"] != partition["partition_id"]
            or row["selector_type"] != partition["selector_type"]
            or row["selector_value"] != partition["selector_value"]
            or row["orientation"] != orientation
        ):
            fail(
                "Step 08 input receipt is not ordered as the declared "
                "partition x {FWD_like, REV_like} universe."
            )
        cohort_ids.add(row["cohort_id"])
        annotation_paths.add(row["annotation_gtf"])
        annotation_hashes.add(row["annotation_gtf_sha256"])
        require_text(f"Step 08 input receipt row {index} cohort_id", row["cohort_id"])
        validate_safe_id("cohort_id", row["cohort_id"])
        for path_column in ("step07_receipt_path", "vcf_path", "annotation_gtf"):
            require_text(
                f"Step 08 input receipt row {index} {path_column}",
                row[path_column],
            )
        for hash_column in (
            "step07_receipt_sha256",
            "vcf_sha256",
            "sample_manifest_sha256",
            "partition_manifest_sha256",
            "annotation_gtf_sha256",
        ):
            validate_hash(
                f"Step 08 input receipt row {index} {hash_column}",
                row[hash_column],
            )
        if row["sample_manifest_sha256"] != sample_hash:
            fail("Step 08 input receipt sample manifest hash is stale.")
        if row["partition_manifest_sha256"] != partition_hash:
            fail("Step 08 input receipt partition manifest hash is stale.")
        counts = {
            column: parse_nonnegative_int(
                f"Step 08 input receipt row {index} {column}", row[column]
            )
            for column in (
                "sample_count",
                "declared_vcf_record_count",
                *STEP08_PARTITION_COUNT_FIELDS,
            )
        }
        if counts["sample_count"] != len(sample_ids):
            fail("Step 08 input receipt sample_count differs from the manifest.")
        if counts["declared_vcf_record_count"] != counts["observed_vcf_record_count"]:
            fail("Step 08 declared and observed VCF record counts differ.")
        if counts["observed_alt_allele_count"] != (
            counts["supported_snv_count"]
            + counts["skipped_symbolic_count"]
            + counts["skipped_non_snv_count"]
        ):
            fail("Step 08 alternate-allele counts do not reconcile.")
        if counts["published_candidate_count"] != counts["supported_snv_count"]:
            fail("Step 08 published and supported SNV counts do not reconcile.")
        require_text(
            f"Step 08 input receipt row {index} orientation_policy",
            row["orientation_policy"],
        )
    if len(cohort_ids) != 1:
        fail("Step 08 input receipt contains multiple cohort IDs.")
    if len(annotation_paths) != 1 or len(annotation_hashes) != 1:
        fail("Step 08 input receipt contains inconsistent annotation provenance.")
    if len({row["orientation_policy"] for row in table.rows}) != 1:
        fail("Step 08 input receipt contains multiple orientation policies.")
    return table


def validate_step08_sites(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
) -> Table:
    expected_header = sample_block_header(STEP08_METADATA_HEADER, sample_ids)
    table = read_tsv("Step 08 sites table", value, expected_header)
    ensure_unique(table.rows, "candidate_id", "Step 08 sites table")
    partition_ids = {row["partition_id"] for row in partitions}
    policies = {row["orientation_policy"] for row in step08_inputs}
    published_by_scope = {
        (row["partition_id"], row["orientation"]): parse_nonnegative_int(
            "Step 08 published_candidate_count",
            row["published_candidate_count"],
        )
        for row in step08_inputs
    }
    observed_by_scope = {key: 0 for key in published_by_scope}
    for row_number, row in enumerate(table.rows, start=2):
        require_text(
            f"Step 08 sites row {row_number} candidate_id",
            row["candidate_id"],
        )
        if row["partition_id"] not in partition_ids:
            fail(f"Step 08 sites row {row_number} references an unknown partition.")
        validate_enum(
            f"Step 08 sites row {row_number} orientation",
            row["orientation"],
            alignment_orientation.ORIENTATIONS,
        )
        scope = (row["partition_id"], row["orientation"])
        observed_by_scope[scope] += 1
        if row["orientation_policy"] not in policies:
            fail("Step 08 sites table orientation policy differs from its receipt.")
        parse_nonnegative_int(
            f"Step 08 sites row {row_number} position", row["position"]
        )
        alt_index = parse_nonnegative_int(
            f"Step 08 sites row {row_number} alt_index", row["alt_index"]
        )
        if alt_index < 1:
            fail("Step 08 alt_index must be at least 1.")
        for sample in sample_ids:
            dp_value = row[f"DP__{sample}"]
            ad_value = row[f"AD__{sample}"]
            dp = (
                None
                if dp_value == NA_VALUE
                else parse_nonnegative_int(
                    f"Step 08 sites row {row_number} DP__{sample}",
                    dp_value,
                )
            )
            ad = (
                None
                if ad_value == NA_VALUE
                else parse_nonnegative_int(
                    f"Step 08 sites row {row_number} AD__{sample}",
                    ad_value,
                )
            )
            af = parse_number(
                f"Step 08 sites row {row_number} AF__{sample}",
                row[f"AF__{sample}"],
                allow_na=True,
                nonnegative=True,
            )
            if (dp is None) != (ad is None):
                fail(
                    f"Step 08 sites row {row_number} has one-sided DP/AD "
                    f"missingness for sample {sample}."
                )
            if dp is None:
                if af is not None:
                    fail(
                        f"Step 08 sites row {row_number} has AF without "
                        f"DP/AD for sample {sample}."
                    )
                continue
            assert ad is not None
            if ad > dp or (af is not None and af > 1):
                fail(
                    f"Step 08 sites row {row_number} has inconsistent counts "
                    f"for sample {sample}."
                )
            if dp == 0:
                if ad != 0 or af is not None:
                    fail(
                        f"Step 08 sites row {row_number} has invalid zero-depth "
                        f"counts for sample {sample}."
                    )
                continue
            if af is None or not values_close(af, ad / dp):
                fail(
                    f"Step 08 sites row {row_number} AF__{sample} does not equal AD/DP."
                )
    if observed_by_scope != published_by_scope:
        fail("Step 08 sites counts do not reconcile by partition and orientation.")
    return table


def validate_step08_summary(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
    step08_sites: Sequence[Mapping[str, str]],
    sample_hash: str,
    partition_hash: str,
) -> Table:
    table = read_tsv("Step 08 summary", value, STEP08_SUMMARY_HEADER)
    if len(table.rows) != 1:
        fail("Step 08 summary must contain exactly one data row.")
    row = table.rows[0]
    if row["sample_manifest_sha256"] != sample_hash:
        fail("Step 08 summary sample manifest hash is stale.")
    if row["partition_manifest_sha256"] != partition_hash:
        fail("Step 08 summary partition manifest hash is stale.")
    expected_counts = {
        "partition_count": len(partitions),
        "step07_receipt_count": len(partitions),
        "input_vcf_count": len(step08_inputs),
        "sample_count": len(sample_ids),
        "published_candidate_count": len(step08_sites),
    }
    aggregate_columns = STEP08_AGGREGATE_COUNT_FIELDS
    for column in aggregate_columns:
        expected_counts[column] = sum(
            parse_nonnegative_int(f"Step 08 input receipt {column}", input_row[column])
            for input_row in step08_inputs
        )
    for column, expected in expected_counts.items():
        if parse_nonnegative_int(f"Step 08 summary {column}", row[column]) != expected:
            fail(f"Step 08 summary {column} does not reconcile.")
    first = step08_inputs[0]
    for column in (
        "cohort_id",
        "annotation_gtf",
        "annotation_gtf_sha256",
        "orientation_policy",
    ):
        if row[column] != first[column]:
            fail(f"Step 08 summary {column} differs from the input receipt.")
    return table
