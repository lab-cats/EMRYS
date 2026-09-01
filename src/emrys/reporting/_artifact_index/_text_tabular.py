"""TSV parsing, sample-block headers, parameters, and native run anchors."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .models import (
    ANCHOR_HASH_FIELDS,
    SHA256_RE,
    AdapterSpec,
    ArtifactIndexError,
)


def inspect_tsv(
    path: Path,
    spec: AdapterSpec,
) -> tuple[int, dict[str, str] | None, dict[str, Any], dict[str, Any]]:
    captured_rows: list[dict[str, str]] = []
    anchor_values: dict[str, set[str]] = defaultdict(set)
    value_counts: dict[str, Counter[str]] = defaultdict(Counter)
    capture_rows = (
        spec.kind == "validation_report"
        or spec.exact_data_rows is not None
        or spec.adapter_id
        in {
            "step07_mpileup_receipt_v1",
            "step08_inputs_v1",
        }
    )
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
                    raise ArtifactIndexError(f"TSV row {row_number} is blank")
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
                    "cohort_id",
                    "orientation_policy",
                ):
                    if field_name in row:
                        anchor_values[field_name].add(row[field_name])
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
            key: sorted(values) for key, values in sorted(anchor_values.items())
        },
    }
    if spec.kind == "sample_blocks_tsv":
        remainder = header[len(spec.expected_header or ()) :]
        sample_count = len(remainder) // 3
        native["samples"] = [
            value.removeprefix("DP__") for value in remainder[:sample_count]
        ]
        native["sample_count"] = sample_count
    if capture_rows:
        native["rows"] = captured_rows
    if value_counts:
        native["value_counts"] = {
            field_name: dict(sorted(counts.items()))
            for field_name, counts in sorted(value_counts.items())
        }
    return count, first_row, parameters, native


def validate_sample_block_header(
    header: Sequence[str],
    fixed_prefix: Sequence[str],
) -> None:
    if tuple(header[: len(fixed_prefix)]) != tuple(fixed_prefix):
        raise ArtifactIndexError("Sample-block TSV fixed metadata header is invalid")
    remainder = tuple(header[len(fixed_prefix) :])
    if not remainder:
        raise ArtifactIndexError("Sample-block TSV must declare at least one sample")
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
        "primary_analysis_id",
        "orientation_policy",
        "transaction_state",
    )
    return {field: row[field] for field in fields if field in row}


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
    if "analysis_id" in row and inventory_row.get("scope_type") == "analysis":  # noqa: SIM102
        if row["analysis_id"] != inventory_row["scope_id"]:
            raise ArtifactIndexError(
                "Native analysis_id does not match the explicit inventory scope"
            )
