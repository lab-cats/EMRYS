"""Validate the neutral Step 08 scientific-evidence table contract."""

from __future__ import annotations

import csv
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

if (src_root := str(Path(__file__).resolve().parents[3])) not in sys.path:
    sys.path.insert(0, src_root)

from norad.libraries import validation as report
from norad.libraries.alignments import orientation as alignment_orientation


class ContractError(RuntimeError):
    """Raised when an explicit scientific-review contract is invalid."""


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NA_VALUE = "NA"
ORIENTATIONS = alignment_orientation.ORIENTATIONS
STEP08_METADATA_HEADER = (
    "partition_id",
    "candidate_id",
    "orientation",
    "chromosome",
    "position",
    "alt_index",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "annotation_strand",
    "gene_ids",
    "transcript_ids",
    "is_cds",
    "is_five_prime_utr",
    "is_three_prime_utr",
    "is_exon",
    "is_intron",
    "qual",
    "filter",
    "info_alt_depth",
    "orientation_policy",
)

STEP08_INPUTS_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "step07_receipt_path",
    "step07_receipt_sha256",
    "vcf_path",
    "vcf_sha256",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "sample_count",
    "declared_vcf_record_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "orientation_policy",
)

STEP08_SUMMARY_HEADER = (
    "cohort_id",
    "partition_count",
    "step07_receipt_count",
    "input_vcf_count",
    "sample_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "orientation_policy",
)

SAMPLE_MANIFEST_REQUIRED = (
    "sample_id",
    "r1_fastq",
    "r2_fastq",
    "strandedness",
    "condition",
    "replicate",
)
SAMPLE_MANIFEST_ALLOWED = SAMPLE_MANIFEST_REQUIRED + ("notes",)
PARTITION_MANIFEST_HEADER = (
    "partition_id",
    "selector_type",
    "selector_value",
)


@dataclass
class Table:
    header: tuple[str, ...]
    rows: list[dict[str, str]]
    path: Path


def fail(message: str) -> None:
    raise ContractError(message)


def validate_safe_id(label: str, value: str) -> None:
    if not SAFE_ID_RE.fullmatch(value):
        fail(f"{label} must match [A-Za-z0-9][A-Za-z0-9._-]*; got: {value}")


def validate_enum(label: str, value: str, allowed: Sequence[str]) -> None:
    if value not in allowed:
        fail(f"{label} must be one of {', '.join(allowed)}; got: {value}")


def parse_nonnegative_int(label: str, value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        fail(f"{label} must be a non-negative integer; got: {value}")
    return int(value)


def parse_number(
    label: str, value: str, *, allow_na: bool = False, nonnegative: bool = False
) -> float | None:
    if allow_na and value == NA_VALUE:
        return None
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} must be numeric; got: {value}")
    if not math.isfinite(parsed):
        fail(f"{label} must be finite; got: {value}")
    if nonnegative and parsed < 0:
        fail(f"{label} must be non-negative; got: {value}")
    return parsed


def values_close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=1.5e-8, abs_tol=1.5e-8)


def sha256_file(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        fail(f"Could not hash {path}: {exc}")


def require_file(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        fail(f"{label} does not exist or is not a regular file: {path}")
    if path.stat().st_size == 0:
        fail(f"{label} is empty: {path}")
    return path.resolve()


def read_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str] | None = None,
) -> Table:
    path = require_file(label, value)
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")
    if not raw_rows:
        fail(f"{label} is empty: {path}")
    header = tuple(raw_rows[0])
    if any(not column for column in header):
        fail(f"{label} contains an empty header field: {path}")
    if len(header) != len(set(header)):
        fail(f"{label} contains duplicate header fields: {path}")
    if expected_header is not None and header != tuple(expected_header):
        fail(
            f"{label} header is invalid: {path}\n"
            f"Expected: {' | '.join(expected_header)}\n"
            f"Observed: {' | '.join(header)}"
        )
    rows: list[dict[str, str]] = []
    for index, values in enumerate(raw_rows[1:], start=2):
        if len(values) != len(header):
            fail(
                f"{label} row {index} has {len(values)} fields; "
                f"expected {len(header)}: {path}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return Table(header=header, rows=rows, path=path)


def ensure_unique(rows: Sequence[Mapping[str, str]], column: str, label: str) -> None:
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        value = row[column]
        if not value:
            fail(f"{label} row {row_number} has an empty {column}.")
        if value in seen:
            fail(f"{label} contains duplicate {column}: {value}")
        seen.add(value)


def require_text(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    if not value or value.strip() != value:
        fail(f"{label} must be non-empty and have no surrounding whitespace.")


def validate_hash(label: str, value: str) -> None:
    if not SHA256_RE.fullmatch(value):
        fail(f"{label} must be a lowercase SHA-256 value; got: {value}")


def validate_sample_manifest(
    value: str | Path,
) -> tuple[Table, list[str], list[dict[str, str]]]:
    table = read_tsv("Sample manifest", value)
    if table.header not in (SAMPLE_MANIFEST_REQUIRED, SAMPLE_MANIFEST_ALLOWED):
        fail(
            "Sample manifest must have the exact Step 09 schema, with optional "
            "notes as the final column."
        )
    if not table.rows:
        fail("Sample manifest contains no sample rows.")
    ensure_unique(table.rows, "sample_id", "Sample manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in SAMPLE_MANIFEST_REQUIRED:
            require_text(f"Sample manifest row {row_number} {column}", row[column])
        validate_safe_id("sample_id", row["sample_id"])
        validate_safe_id("replicate", row["replicate"])
        if row["strandedness"] not in (
            "forward",
            "reverse",
            "unstranded",
            "unknown",
        ):
            fail(
                "Sample manifest row "
                f"{row_number} has invalid strandedness: {row['strandedness']}"
            )
    return table, [row["sample_id"] for row in table.rows], table.rows


def validate_partition_manifest(value: str | Path) -> Table:
    table = read_tsv("Partition manifest", value, PARTITION_MANIFEST_HEADER)
    if not table.rows:
        fail("Partition manifest contains no partition rows.")
    ensure_unique(table.rows, "partition_id", "Partition manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in PARTITION_MANIFEST_HEADER:
            require_text(f"Partition manifest row {row_number} {column}", row[column])
        validate_safe_id("partition_id", row["partition_id"])
        validate_enum(
            f"Partition manifest row {row_number} selector_type",
            row["selector_type"],
            ("region", "regions_file"),
        )
    return table


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
                "observed_vcf_record_count",
                "observed_alt_allele_count",
                "supported_snv_count",
                "skipped_symbolic_count",
                "skipped_non_snv_count",
                "published_candidate_count",
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
    expected_header = (
        STEP08_METADATA_HEADER
        + tuple(f"DP__{sample}" for sample in sample_ids)
        + tuple(f"AD__{sample}" for sample in sample_ids)
        + tuple(f"AF__{sample}" for sample in sample_ids)
    )
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
    aggregate_columns = (
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
    )
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
