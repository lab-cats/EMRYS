"""Strict text and tabular artifact readers."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    ANCHOR_HASH_FIELDS,
    SHA256_RE,
    STEP09C_CATEGORY_ADAPTERS,
    AdapterSpec,
    ArtifactIndexError,
)

def iter_text_lines(path: Path) -> Iterable[tuple[int, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if "\x00" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a NUL byte"
                    )
                if "\r" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a carriage return"
                    )
                line = (
                    raw_line[:-1]
                    if raw_line.endswith("\n")
                    else raw_line
                )
                yield line_number, line
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(f"Could not read UTF-8 text: {exc}") from exc


def inspect_nonempty_text(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    has_content = False
    for _line_number, line in iter_text_lines(path):
        count += 1
        has_content = has_content or bool(line.strip())
    if not has_content:
        raise ArtifactIndexError("Text file is empty")
    return count, {}


def inspect_tsv(
    path: Path,
    spec: AdapterSpec,
) -> tuple[int, dict[str, str] | None, dict[str, Any], dict[str, Any]]:
    captured_rows: list[dict[str, str]] = []
    anchor_values: dict[str, set[str]] = defaultdict(set)
    value_counts: dict[str, Counter[str]] = defaultdict(Counter)
    capture_rows = (
        spec.exact_data_rows is not None
        or spec.adapter_id in set(STEP09C_CATEGORY_ADAPTERS.values())
        or spec.adapter_id
        in {
        "step07_mpileup_receipt_v1",
        "step08_inputs_v1",
        "step09_mutation_spectrum_tsv_v1",
        "step09c_evidence_index_v1",
        }
    )
    mutation_pair_counts: dict[str, Counter[str]] = defaultdict(Counter)
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t")
            try:
                header = tuple(next(reader))
            except StopIteration as exc:
                raise ArtifactIndexError("TSV is empty") from exc
            if not header or any(not value for value in header):
                raise ArtifactIndexError("TSV header contains an empty field")
            if len(header) != len(set(header)):
                raise ArtifactIndexError("TSV header contains duplicate fields")
            if spec.kind == "sample_blocks_tsv":
                validate_sample_block_header(header, spec.expected_header or ())
            elif spec.expected_header is not None and header != spec.expected_header:
                raise ArtifactIndexError(
                    "TSV header mismatch; expected "
                    + " | ".join(spec.expected_header)
                    + "; observed "
                    + " | ".join(header)
                )
            count = 0
            first_row: dict[str, str] | None = None
            for row_number, values in enumerate(reader, start=2):
                if not values or all(value == "" for value in values):
                    raise ArtifactIndexError(
                        f"TSV row {row_number} is blank"
                    )
                if len(values) != len(header):
                    raise ArtifactIndexError(
                        f"TSV row {row_number} has {len(values)} fields; "
                        f"expected {len(header)}"
                    )
                row = dict(zip(header, values, strict=True))
                validate_native_run_anchors(row, {})
                for field_name in (
                    "sample_manifest_sha256",
                    "partition_manifest_sha256",
                    "analysis_id",
                    "primary_analysis_id",
                    "review_id",
                    "cohort_id",
                    "orientation_policy",
                ):
                    if field_name in row:
                        anchor_values[field_name].add(row[field_name])
                if spec.adapter_id in {
                    "step09_cmh_all_sites_v1",
                    "step09_cmh_significant_sites_v1",
                }:
                    for field_name in (
                        "test_status",
                        "call_status",
                        "rna_ref",
                        "rna_alt",
                    ):
                        value_counts[field_name][row[field_name]] += 1
                    mutation_type = f"{row['rna_ref']}>{row['rna_alt']}"
                    mutation_pair_counts[mutation_type]["candidate_count"] += 1
                    if row["test_status"] == "tested":
                        mutation_pair_counts[mutation_type][
                            "successfully_tested_count"
                        ] += 1
                    if row["call_status"] == "significant_up":
                        mutation_pair_counts[mutation_type][
                            "significant_up_count"
                        ] += 1
                    if row["call_status"] == "significant_down":
                        mutation_pair_counts[mutation_type][
                            "significant_down_count"
                        ] += 1
                if spec.kind == "validation_report":
                    value_counts["status"][row["status"]] += 1
                if capture_rows:
                    captured_rows.append(row)
                if first_row is None:
                    first_row = row
                count += 1
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ArtifactIndexError(f"Could not parse TSV: {exc}") from exc
    if spec.exact_data_rows is not None and count != spec.exact_data_rows:
        raise ArtifactIndexError(
            f"TSV must contain exactly {spec.exact_data_rows} data rows; "
            f"observed {count}"
        )
    if not spec.allow_header_only and count == 0:
        raise ArtifactIndexError("TSV must contain at least one data row")
    parameters = extract_parameters(first_row)
    native: dict[str, Any] = {
        "header": list(header),
        "anchor_values": {
            key: sorted(values)
            for key, values in sorted(anchor_values.items())
        },
    }
    if spec.kind == "sample_blocks_tsv":
        remainder = header[len(spec.expected_header or ()) :]
        sample_count = len(remainder) // 3
        native["samples"] = [
            value.removeprefix("DP__")
            for value in remainder[:sample_count]
        ]
        native["sample_count"] = sample_count
    if capture_rows:
        native["rows"] = captured_rows
    if value_counts:
        native["value_counts"] = {
            field_name: dict(sorted(counts.items()))
            for field_name, counts in sorted(value_counts.items())
        }
    if mutation_pair_counts:
        native["mutation_pair_counts"] = {
            mutation_type: dict(sorted(counts.items()))
            for mutation_type, counts in sorted(mutation_pair_counts.items())
        }
    return count, first_row, parameters, native


def validate_sample_block_header(
    header: Sequence[str],
    fixed_prefix: Sequence[str],
) -> None:
    if tuple(header[: len(fixed_prefix)]) != tuple(fixed_prefix):
        raise ArtifactIndexError(
            "Sample-block TSV fixed metadata header is invalid"
        )
    remainder = tuple(header[len(fixed_prefix) :])
    if not remainder:
        raise ArtifactIndexError(
            "Sample-block TSV must declare at least one sample"
        )
    if len(remainder) % 3 != 0:
        raise ArtifactIndexError(
            "Sample-block TSV must have equal DP__, AD__, and AF__ blocks"
        )
    sample_count = len(remainder) // 3
    dp = remainder[:sample_count]
    ad = remainder[sample_count : sample_count * 2]
    af = remainder[sample_count * 2 :]
    samples = tuple(value.removeprefix("DP__") for value in dp)
    if any(
        not value.startswith("DP__") or not sample
        for value, sample in zip(dp, samples, strict=True)
    ):
        raise ArtifactIndexError("Sample-block TSV has an invalid DP__ block")
    if len(samples) != len(set(samples)):
        raise ArtifactIndexError("Sample-block TSV has duplicate samples")
    if ad != tuple(f"AD__{sample}" for sample in samples):
        raise ArtifactIndexError("Sample-block TSV AD__ order is invalid")
    if af != tuple(f"AF__{sample}" for sample in samples):
        raise ArtifactIndexError("Sample-block TSV AF__ order is invalid")


def extract_parameters(row: Mapping[str, str] | None) -> dict[str, Any]:
    if row is None:
        return {}
    fields = (
        "sample_id",
        "cohort_id",
        "partition_id",
        "selector_type",
        "selector_value",
        "orientation",
        "analysis_id",
        "review_id",
        "primary_analysis_id",
        "orientation_policy",
        "overall_science_status",
        "orientation_status",
        "transaction_state",
    )
    return {field: row[field] for field in fields if field in row}


def inspect_vcf(path: Path) -> tuple[int, dict[str, Any]]:
    fields: list[str] | None = None
    samples: list[str] = []
    format_ids: set[str] = set()
    info_ids: set[str] = set()
    count = 0
    observed_lines = 0
    for line_number, line in iter_text_lines(path):
        observed_lines += 1
        if line_number == 1 and not line.startswith("##fileformat=VCF"):
            raise ArtifactIndexError(
                "VCF is missing the leading ##fileformat declaration"
            )
        format_match = re.match(r"^##FORMAT=<ID=([^,>]+)", line)
        if format_match:
            format_ids.add(format_match.group(1))
            continue
        info_match = re.match(r"^##INFO=<ID=([^,>]+)", line)
        if info_match:
            info_ids.add(info_match.group(1))
            continue
        if line.startswith("##"):
            continue
        if line.startswith("#CHROM\t"):
            if fields is not None:
                raise ArtifactIndexError(
                    "VCF must contain exactly one #CHROM header"
                )
            fields = line.split("\t")
            if fields[:9] != [
                "#CHROM",
                "POS",
                "ID",
                "REF",
                "ALT",
                "QUAL",
                "FILTER",
                "INFO",
                "FORMAT",
            ]:
                raise ArtifactIndexError("VCF fixed columns are invalid")
            samples = fields[9:]
            if not samples or any(not sample for sample in samples):
                raise ArtifactIndexError("VCF must declare at least one sample")
            if len(samples) != len(set(samples)):
                raise ArtifactIndexError("VCF sample columns are not unique")
            continue
        if line.startswith("#"):
            raise ArtifactIndexError(
                f"VCF line {line_number} has an unexpected header record"
            )
        if fields is None:
            raise ArtifactIndexError(
                f"VCF record line {line_number} precedes #CHROM"
            )
        values = line.split("\t")
        if len(values) != len(fields):
            raise ArtifactIndexError(
                f"VCF record line {line_number} has {len(values)} fields; "
                f"expected {len(fields)}"
            )
        try:
            if int(values[1]) <= 0:
                raise ValueError
        except ValueError as exc:
            raise ArtifactIndexError(
                f"VCF record line {line_number} has invalid POS"
            ) from exc
        count += 1
    if observed_lines == 0 or fields is None:
        raise ArtifactIndexError(
            "VCF must contain exactly one #CHROM header"
        )
    return count, {
        "sample_count": len(samples),
        "samples": samples,
        "format_ids": sorted(format_ids),
        "info_ids": sorted(info_ids),
    }


def inspect_fasta(path: Path) -> tuple[int, dict[str, Any]]:
    sequence_ids: set[str] = set()
    sequence_lengths: dict[str, int] = {}
    current: str | None = None
    total_bases = 0
    sequence_has_bases = False
    for line_number, line in iter_text_lines(path):
        if line.startswith(">"):
            if current is not None and not sequence_has_bases:
                raise ArtifactIndexError(
                    f"FASTA sequence {current!r} has no bases"
                )
            current = line[1:].split()[0] if line[1:].split() else ""
            if not current or current in sequence_ids:
                raise ArtifactIndexError(
                    f"FASTA line {line_number} has an empty or duplicate ID"
                )
            sequence_ids.add(current)
            sequence_lengths[current] = 0
            sequence_has_bases = False
            continue
        if current is None:
            raise ArtifactIndexError("FASTA sequence appears before a header")
        sequence = line.strip()
        if not sequence or not re.fullmatch(r"[A-Za-z*.-]+", sequence):
            raise ArtifactIndexError(
                f"FASTA line {line_number} contains invalid sequence text"
            )
        total_bases += len(sequence)
        sequence_lengths[current] += len(sequence)
        sequence_has_bases = True
    if current is None or not sequence_has_bases:
        raise ArtifactIndexError("FASTA has no complete sequence")
    return len(sequence_ids), {
        "total_bases": total_bases,
        "contigs": sequence_lengths,
    }


def inspect_fai(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) < 5 or not values[0] or values[0] in seen:
            raise ArtifactIndexError(f"FAI line {line_number} is invalid")
        try:
            length, offset, line_bases, line_width = map(int, values[1:5])
        except ValueError as exc:
            raise ArtifactIndexError(
                f"FAI line {line_number} has non-integer fields"
            ) from exc
        if length <= 0 or offset < 0 or line_bases <= 0 or line_width <= 0:
            raise ArtifactIndexError(
                f"FAI line {line_number} has invalid numeric fields"
            )
        seen.add(values[0])
        contigs[values[0]] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("FAI has no sequence records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_dict(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        if not line.startswith("@SQ\t"):
            continue
        fields = {
            token.split(":", 1)[0]: token.split(":", 1)[1]
            for token in line.split("\t")[1:]
            if ":" in token
        }
        name = fields.get("SN", "")
        try:
            length = int(fields.get("LN", ""))
        except ValueError as exc:
            raise ArtifactIndexError(
                f"Dictionary line {line_number} has an invalid LN"
            ) from exc
        if not name or name in seen or length <= 0:
            raise ArtifactIndexError(
                f"Dictionary line {line_number} has invalid SN/LN"
            )
        seen.add(name)
        contigs[name] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("Dictionary has no @SQ records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_bed12(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 12:
            raise ArtifactIndexError(
                f"BED line {line_number} does not have 12 fields"
            )
        try:
            start = int(values[1])
            end = int(values[2])
            block_count = int(values[9])
            sizes = [int(value) for value in values[10].rstrip(",").split(",")]
            starts = [int(value) for value in values[11].rstrip(",").split(",")]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"BED line {line_number} has invalid numeric fields"
            ) from exc
        if (
            not values[0]
            or not values[3]
            or start < 0
            or end <= start
            or values[5] not in {"+", "-"}
            or block_count <= 0
            or len(sizes) != block_count
            or len(starts) != block_count
            or any(size <= 0 for size in sizes)
            or any(offset < 0 for offset in starts)
        ):
            raise ArtifactIndexError(f"BED line {line_number} is invalid")
        count += 1
    if count == 0:
        raise ArtifactIndexError("BED12 file has no records")
    return count, {}


def inspect_star_sj(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 9:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} does not have 9 fields"
            )
        try:
            numbers = [int(value) for value in values[1:]]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} has non-integer fields"
            ) from exc
        if not values[0] or numbers[0] <= 0 or numbers[1] < numbers[0]:
            raise ArtifactIndexError(f"STAR SJ line {line_number} is invalid")
        count += 1
    return count, {}


def inspect_picard_metrics(path: Path) -> tuple[int, dict[str, Any]]:
    header: list[str] | None = None
    metric_row: dict[str, str] | None = None
    for _line_number, line in iter_text_lines(path):
        if line.startswith("LIBRARY\t"):
            header = line.split("\t")
            continue
        if header is not None and line and not line.startswith("#"):
            values = line.split("\t")
            if len(header) != len(values):
                raise ArtifactIndexError("Picard metrics row width is invalid")
            metric_row = dict(zip(header, values, strict=True))
            break
    if header is None or metric_row is None:
        raise ArtifactIndexError("Picard metrics table is missing")
    native: dict[str, Any] = {}
    for key, value in metric_row.items():
        if key == "LIBRARY" or value == "":
            continue
        try:
            native[key.lower()] = (
                float(value) if any(token in value for token in (".", "e", "E"))
                else int(value)
            )
        except ValueError:
            continue
    return 1, native

def validate_native_run_anchors(
    row: Mapping[str, str] | None,
    inventory_row: Mapping[str, str],
) -> None:
    # The explicit run contract is checked later because it belongs to the
    # build context. This function only validates lexical anchor fields.
    if row is None:
        return
    for field_name in ANCHOR_HASH_FIELDS:
        if field_name in row and not SHA256_RE.fullmatch(row[field_name]):
            raise ArtifactIndexError(
                f"Native field {field_name} is not a lowercase SHA-256"
            )
    if (
        "analysis_id" in row
        and inventory_row.get("scope_type") == "analysis"
    ):
        if row["analysis_id"] != inventory_row["scope_id"]:
            raise ArtifactIndexError(
                "Native analysis_id does not match the explicit inventory scope"
            )
    if (
        "review_id" in row
        and inventory_row.get("scope_type") == "scientific_review"
    ):
        if row["review_id"] != inventory_row["scope_id"]:
            raise ArtifactIndexError(
                "Native review_id does not match the explicit inventory scope"
            )
