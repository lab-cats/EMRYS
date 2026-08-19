"""Validate the neutral Step 09 scientific-evidence output contract."""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from norad.contracts.scientific_evidence.step08 import (
    ContractError,
    NA_VALUE,
    STEP08_METADATA_HEADER,
    Table,
    ensure_unique,
    fail,
    parse_nonnegative_int,
    parse_number,
    read_tsv,
    require_file,
    sample_block_header,
    validate_enum,
    validate_hash,
    validate_safe_id,
    validate_step08_carried_location,
    values_close,
)
from norad.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY,
)
from norad.libraries.alignments.orientation import (
    validate_legacy_orientation_policy as IS_LEGACY_ORIENTATION_POLICY,
)

__all__ = (
    "ContractError",
    "Table",
    "NA_VALUE",
    "STEP09_RESULT_HEADER",
    "STEP09_SUMMARY_HEADER",
    "STEP09_MUTATION_HEADER",
    "CANONICAL_MUTATIONS",
    "STEP09_TEST_STATUSES",
    "STEP09_CALL_STATUSES",
    "STEP09_BACKGROUND_STATUSES",
    "STEP09_STATUS_COUNT_FIELDS",
    "count_status",
    "paired_samples",
    "resolve_recorded_path",
    "validate_step09_projection",
    "validate_step09_results",
    "validate_step09_summary",
    "validate_step09_result_semantics",
    "validate_significant_subset",
    "validate_mutation_spectrum",
    "validate_pdf",
)


STEP09_RESULT_HEADER = (
    "analysis_id",
    *STEP08_METADATA_HEADER,
    "control_condition",
    "treatment_condition",
    "target_rna_change",
    "replicate_count",
    "test_status",
    "call_status",
    "background_condition",
    "background_status",
    "min_analysis_dp",
    "mean_analysis_dp",
    "mean_control_af",
    "mean_treatment_af",
    "treatment_control_difference",
    "max_background_af",
    "cmh_statistic",
    "cmh_degrees_freedom",
    "cmh_p_value",
    "cmh_fdr_bh",
    "common_odds_ratio",
)

STEP09_SUMMARY_HEADER = (
    "analysis_id",
    "cohort_id",
    "control_condition",
    "treatment_condition",
    "background_condition",
    "target_rna_change",
    "replicate_count",
    "sample_count",
    "candidate_count",
    "target_candidate_count",
    "successfully_tested_count",
    "not_target_change_count",
    "missing_counts_count",
    "low_coverage_count",
    "degenerate_table_count",
    "below_mean_dp_count",
    "background_not_passed_count",
    "fdr_not_met_count",
    "effect_not_met_count",
    "significant_up_count",
    "significant_down_count",
    "sample_manifest_path",
    "sample_manifest_sha256",
    "partition_manifest_path",
    "partition_manifest_sha256",
    "step08_sites_path",
    "step08_sites_sha256",
    "step08_inputs_path",
    "step08_inputs_sha256",
    "min_sample_dp",
    "mean_dp_threshold",
    "fdr_threshold",
    "common_or_threshold",
    "absolute_difference_threshold",
    "background_max_fraction",
    "multiple_testing_method",
    "cmh_alternative",
    "continuity_correction",
    "orientation_policy",
)

STEP09_MUTATION_HEADER = (
    "analysis_id",
    "rna_ref",
    "rna_alt",
    "mutation_type",
    "candidate_count",
    "candidate_fraction",
    "successfully_tested_count",
    "significant_up_count",
    "significant_down_count",
)

CANONICAL_MUTATIONS = (
    "A>C",
    "A>G",
    "A>T",
    "C>A",
    "C>G",
    "C>T",
    "G>A",
    "G>C",
    "G>T",
    "T>A",
    "T>C",
    "T>G",
)

STEP09_TEST_STATUSES = (
    "tested",
    "not_target_change",
    "missing_counts",
    "low_coverage",
    "degenerate_table",
)
STEP09_CALL_STATUSES = (
    "not_tested",
    "below_mean_dp",
    "background_not_passed",
    "fdr_not_met",
    "effect_not_met",
    "significant_up",
    "significant_down",
)
STEP09_BACKGROUND_STATUSES = (
    "disabled",
    "pass",
    "missing_counts",
    "low_coverage",
    "fail_fraction",
)

STEP09_STATUS_COUNT_FIELDS = (
    ("successfully_tested_count", "test_status", "tested"),
    ("not_target_change_count", "test_status", "not_target_change"),
    ("missing_counts_count", "test_status", "missing_counts"),
    ("low_coverage_count", "test_status", "low_coverage"),
    ("degenerate_table_count", "test_status", "degenerate_table"),
    ("below_mean_dp_count", "call_status", "below_mean_dp"),
    ("background_not_passed_count", "call_status", "background_not_passed"),
    ("fdr_not_met_count", "call_status", "fdr_not_met"),
    ("effect_not_met_count", "call_status", "effect_not_met"),
    ("significant_up_count", "call_status", "significant_up"),
    ("significant_down_count", "call_status", "significant_down"),
)

_PROJECTION_CONTEXT_FIELDS = (
    "control_condition",
    "treatment_condition",
    "target_rna_change",
    "replicate_count",
    "background_condition",
    "orientation_policy",
)

_PROJECTION_STATISTICAL_FIELDS = (
    "cmh_statistic",
    "cmh_degrees_freedom",
    "cmh_p_value",
    "cmh_fdr_bh",
    "common_odds_ratio",
)

_MUTATION_COUNT_FIELDS = (
    "candidate_count",
    "successfully_tested_count",
    "significant_up_count",
    "significant_down_count",
)
_SIGNIFICANT_CALLS = frozenset(("significant_up", "significant_down"))
_SIGNIFICANT_SUBSET_ERROR = (
    "Step 09 significant-sites table is not the exact ordered significant subset "
    "of all-sites."
)
_SIGNIFICANT_STATUS_ERROR = (
    "Step 09 significant-sites contains a non-significant call status."
)


@dataclass(frozen=True, slots=True)
class _ProjectionTable:
    path: Path
    header: tuple[str, ...]
    row_count: int


def parse_nonnegative_or_infinite(label: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} must be numeric; got: {value}")
    if math.isnan(parsed) or parsed < 0:
        fail(f"{label} must be non-negative and not NaN; got: {value}")
    return parsed


def resolve_recorded_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def validate_pdf(label: str, path: Path) -> None:
    path = require_file(label, path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"Could not read {label}: {exc}")
    if not data.startswith(b"%PDF-"):
        fail(f"{label} lacks a %PDF- signature: {path}")
    if b"%%EOF" not in data[-2048:]:
        fail(f"{label} lacks a trailing %%EOF marker: {path}")


def count_status(rows: Sequence[Mapping[str, str]], column: str, value: str) -> int:
    return sum(row[column] == value for row in rows)


def paired_samples(
    sample_rows: Sequence[Mapping[str, str]],
    control: str,
    treatment: str,
) -> tuple[list[str], dict[str, tuple[str, str]]]:
    if control == treatment:
        fail("Step 09 control and treatment conditions must differ.")
    analysis_rows = [
        row for row in sample_rows if row["condition"] in (control, treatment)
    ]
    replicates: list[str] = []
    for row in analysis_rows:
        if row["replicate"] not in replicates:
            replicates.append(row["replicate"])
    pairs: dict[str, tuple[str, str]] = {}
    for replicate in replicates:
        controls = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == control and row["replicate"] == replicate
        ]
        treatments = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == treatment and row["replicate"] == replicate
        ]
        if len(controls) != 1 or len(treatments) != 1:
            fail(
                "Sample manifest must define exactly one control and one "
                f"treatment for replicate {replicate}."
            )
        pairs[replicate] = (controls[0], treatments[0])
    control_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == control
    }
    treatment_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == treatment
    }
    if control_replicates != treatment_replicates or len(replicates) < 2:
        fail(
            "Sample manifest must define identical control/treatment replicate "
            "sets with at least two strata."
        )
    return replicates, pairs


def _projection_sample_ids(
    header: Sequence[str],
    label: str,
) -> tuple[str, ...]:
    prefix = STEP09_RESULT_HEADER
    if tuple(header[: len(prefix)]) != prefix:
        fail(f"{label} has an invalid fixed Step 09 header.")
    remainder = tuple(header[len(prefix) :])
    if not remainder or len(remainder) % 3:
        fail(f"{label} must have equal non-empty DP__, AD__, and AF__ blocks.")
    count = len(remainder) // 3
    dp = remainder[:count]
    ad = remainder[count : count * 2]
    af = remainder[count * 2 :]
    sample_ids = tuple(value.removeprefix("DP__") for value in dp)
    if any(
        not value.startswith("DP__") or not sample_id
        for value, sample_id in zip(dp, sample_ids, strict=True)
    ) or len(sample_ids) != len(set(sample_ids)):
        fail(f"{label} has an invalid DP__ sample block.")
    if ad != tuple(f"AD__{sample_id}" for sample_id in sample_ids):
        fail(f"{label} has an invalid AD__ sample block.")
    if af != tuple(f"AF__{sample_id}" for sample_id in sample_ids):
        fail(f"{label} has an invalid AF__ sample block.")
    return sample_ids


def _validate_projection_result_identity(
    table: Table,
    label: str,
    analysis_id: str,
    sample_ids: Sequence[str],
) -> None:
    expected_header = sample_block_header(STEP09_RESULT_HEADER, sample_ids)
    if table.header != expected_header:
        fail(f"{label} header is invalid: {table.path}")
    ensure_unique(table.rows, "candidate_id", label)
    for row_number, row in enumerate(table.rows, start=2):
        _validate_projection_result_row_identity(
            row,
            label,
            row_number,
            analysis_id,
        )


def _validate_projection_result_row_identity(
    row: Mapping[str, str],
    label: str,
    row_number: int,
    analysis_id: str,
) -> None:
    if all(value == "" for value in row.values()):
        fail(f"{label} row {row_number} is blank.")
    if row["analysis_id"] != analysis_id:
        fail(f"{label} row {row_number} has the wrong analysis_id.")
    validate_step08_carried_location(row, f"{label} row {row_number}")
    validate_enum(
        f"{label} row {row_number} test_status",
        row["test_status"],
        STEP09_TEST_STATUSES,
    )
    validate_enum(
        f"{label} row {row_number} call_status",
        row["call_status"],
        STEP09_CALL_STATUSES,
    )
    parse_nonnegative_int(
        f"{label} row {row_number} replicate_count",
        row["replicate_count"],
    )


def _projection_number(
    label: str,
    value: str,
    *,
    allow_na: bool = False,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    parsed = parse_number(label, value, allow_na=allow_na)
    if parsed is None:
        return None
    if minimum is not None and parsed < minimum:
        fail(f"{label} must be at least {minimum}; got: {value}")
    if maximum is not None and parsed > maximum:
        fail(f"{label} must be at most {maximum}; got: {value}")
    return parsed


def _validate_projection_sample_values(
    row: Mapping[str, str],
    sample_ids: Sequence[str],
    label: str,
) -> None:
    for sample_id in sample_ids:
        sample_label = f"{label} sample {sample_id}"
        dp_text = row[f"DP__{sample_id}"]
        ad_text = row[f"AD__{sample_id}"]
        af_text = row[f"AF__{sample_id}"]
        if (dp_text == NA_VALUE) != (ad_text == NA_VALUE):
            fail(f"{sample_label} has one-sided DP/AD missingness.")
        if dp_text == NA_VALUE:
            if af_text != NA_VALUE:
                fail(f"{sample_label} has AF without DP/AD.")
            continue
        dp = parse_nonnegative_int(f"{sample_label} DP", dp_text)
        ad = parse_nonnegative_int(f"{sample_label} AD", ad_text)
        if ad > dp:
            fail(f"{sample_label} has AD greater than DP.")
        if dp == 0:
            if ad != 0 or af_text != NA_VALUE:
                fail(f"{sample_label} has invalid zero-depth DP/AD/AF values.")
            continue
        af = _projection_number(
            f"{sample_label} AF",
            af_text,
            minimum=0,
            maximum=1,
        )
        if not values_close(af, ad / dp):
            fail(f"{sample_label} AF does not reconcile with AD/DP.")


def _validate_projection_result_row_values(
    row: Mapping[str, str],
    sample_ids: Sequence[str],
    label: str,
    row_number: int,
) -> None:
    row_label = f"{label} row {row_number}"
    _validate_projection_sample_values(row, sample_ids, row_label)
    parse_nonnegative_int(f"{row_label} position", row["position"])
    if parse_nonnegative_int(f"{row_label} alt_index", row["alt_index"]) < 1:
        fail(f"{row_label} alt_index must be at least 1.")
    degrees = None
    for field, minimum, maximum in (
        ("min_analysis_dp", 0, None),
        ("mean_analysis_dp", 0, None),
        ("mean_control_af", 0, 1),
        ("mean_treatment_af", 0, 1),
        ("treatment_control_difference", -1, 1),
        ("max_background_af", 0, 1),
        ("cmh_statistic", 0, None),
        ("cmh_degrees_freedom", 0, None),
        ("cmh_p_value", 0, 1),
        ("cmh_fdr_bh", 0, 1),
    ):
        parsed = _projection_number(
            f"{row_label} {field}",
            row[field],
            allow_na=True,
            minimum=minimum,
            maximum=maximum,
        )
        if field == "cmh_degrees_freedom":
            degrees = parsed
    if row["common_odds_ratio"] != NA_VALUE:
        parse_nonnegative_or_infinite(
            f"{row_label} common_odds_ratio",
            row["common_odds_ratio"],
        )
    if row["test_status"] == "tested":
        if row["call_status"] == "not_tested" or any(
            row[field] == NA_VALUE for field in _PROJECTION_STATISTICAL_FIELDS
        ):
            fail(f"{row_label} tested row lacks complete CMH statistics.")
        if degrees != 1:
            fail(f"{row_label} tested row must use one CMH degree of freedom.")
    elif row["call_status"] != "not_tested" or any(
        row[field] != NA_VALUE for field in _PROJECTION_STATISTICAL_FIELDS
    ):
        fail(f"{row_label} untested row contains a computational call.")


def _validate_projection_thresholds(
    summary: Mapping[str, str],
) -> tuple[int, float, float, float, float, float]:
    min_sample_dp = parse_nonnegative_int(
        "Step 09 min_sample_dp", summary["min_sample_dp"]
    )
    mean_dp_threshold = _projection_number(
        "Step 09 mean_dp_threshold",
        summary["mean_dp_threshold"],
        minimum=0,
    )
    fdr_threshold = _projection_number(
        "Step 09 fdr_threshold",
        summary["fdr_threshold"],
        minimum=0,
        maximum=1,
    )
    odds_threshold = _projection_number(
        "Step 09 common_or_threshold",
        summary["common_or_threshold"],
        minimum=0,
    )
    difference_threshold = _projection_number(
        "Step 09 absolute_difference_threshold",
        summary["absolute_difference_threshold"],
        minimum=0,
        maximum=1,
    )
    background_threshold = _projection_number(
        "Step 09 background_max_fraction",
        summary["background_max_fraction"],
        minimum=0,
        maximum=1,
    )
    if (
        min_sample_dp < 1
        or mean_dp_threshold is None
        or fdr_threshold is None
        or not 0 < fdr_threshold <= 1
        or odds_threshold is None
        or odds_threshold <= 1
        or difference_threshold is None
        or background_threshold is None
        or not 0 < background_threshold < 1
    ):
        fail("Step 09 summary thresholds are outside the supported contract.")
    return (
        min_sample_dp,
        mean_dp_threshold,
        fdr_threshold,
        odds_threshold,
        difference_threshold,
        background_threshold,
    )


def _read_projection_summary(
    value: str | Path,
    analysis_id: str,
) -> Table:
    table = read_tsv("Step 09 summary", value, STEP09_SUMMARY_HEADER)
    if len(table.rows) != 1:
        fail("Step 09 summary must contain exactly one data row.")
    row = table.rows[0]
    if row["analysis_id"] != analysis_id:
        fail("Step 09 summary analysis_id differs from its directory.")
    return table


def _validate_projection_summary_fields(row: Mapping[str, str]) -> None:
    for field in (
        "replicate_count",
        "sample_count",
        "candidate_count",
        "target_candidate_count",
        *(field for field, _column, _status in STEP09_STATUS_COUNT_FIELDS),
    ):
        parse_nonnegative_int(f"Step 09 summary {field}", row[field])
    _validate_projection_thresholds(row)
    _validate_projection_method(row)


def _validate_projection_method(row: Mapping[str, str]) -> None:
    if (
        row["multiple_testing_method"] != "BH"
        or row["cmh_alternative"] != "two.sided"
        or row["continuity_correction"] != "TRUE"
    ):
        fail("Step 09 summary does not declare the approved CMH contract.")
    if not re.fullmatch(r"[ACGT]>[ACGT]", row["target_rna_change"]):
        fail("Step 09 summary target_rna_change must be a canonical SNV.")


@contextmanager
def _stream_projection_tsv(
    label: str,
    value: str | Path,
) -> Iterator[tuple[Path, tuple[str, ...], Iterator[tuple[int, dict[str, str]]]]]:
    path = require_file(label, value)
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                header = tuple(next(reader))
            except StopIteration:
                fail(f"{label} is empty: {path}")
            if any(not column for column in header):
                fail(f"{label} contains an empty header field: {path}")
            if len(header) != len(set(header)):
                fail(f"{label} contains duplicate header fields: {path}")

            def rows() -> Iterator[tuple[int, dict[str, str]]]:
                for row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        fail(
                            f"{label} row {row_number} has {len(values)} fields; "
                            f"expected {len(header)}: {path}"
                        )
                    yield row_number, dict(zip(header, values, strict=True))

            yield path, header, rows()
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")


def _new_mutation_counts() -> dict[str, dict[str, int]]:
    return {
        mutation: {field: 0 for field in _MUTATION_COUNT_FIELDS}
        for mutation in CANONICAL_MUTATIONS
    }


def _accumulate_mutation_counts(
    row: Mapping[str, str],
    mutation_counts: dict[str, dict[str, int]],
) -> None:
    counts = mutation_counts.get(f"{row['rna_ref']}>{row['rna_alt']}")
    if counts is None:
        return
    counts["candidate_count"] += 1
    if row["test_status"] == "tested":
        counts["successfully_tested_count"] += 1
    if row["call_status"] == "significant_up":
        counts["significant_up_count"] += 1
    if row["call_status"] == "significant_down":
        counts["significant_down_count"] += 1


def _reconcile_projection_counts(
    summary: Mapping[str, str],
    sample_ids: Sequence[str],
    all_row_count: int,
    significant_row_count: int,
    status_counts: Mapping[str, int],
    target_count: int,
) -> None:
    if (
        int(summary["significant_up_count"]) + int(summary["significant_down_count"])
        != significant_row_count
    ):
        fail("Step 09 summary significant counts disagree with significant-sites rows.")
    expected_counts = {
        "sample_count": len(sample_ids),
        "candidate_count": all_row_count,
        "target_candidate_count": target_count,
        **status_counts,
    }
    for field, expected in expected_counts.items():
        if int(summary[field]) != expected:
            owner = {
                "sample_count": "result columns",
                "candidate_count": "all-sites rows",
            }.get(field, "all-sites")
            fail(f"Step 09 summary {field} disagrees with {owner}.")


def validate_step09_projection(
    all_sites: str | Path,
    significant_sites: str | Path,
    summary: str | Path,
    analysis_id: str,
    *,
    mutation_spectrum: str | Path | None = None,
) -> tuple[_ProjectionTable, _ProjectionTable, Table, tuple[str, ...]]:
    """Admit the intrinsic Step 09 result trio used by read-only projections.

    This deliberately excludes upstream Step 08 identity, paired-sample CMH
    semantics, global BH reconciliation, and publication state. Mutation-spectrum
    reconciliation is included when its optional path is supplied.
    """

    summary_table = _read_projection_summary(summary, analysis_id)
    summary_row = summary_table.rows[0]
    _validate_projection_summary_fields(summary_row)

    all_candidate_ids: set[str] = set()
    status_counts = {
        summary_field: 0
        for summary_field, _column, _status in STEP09_STATUS_COUNT_FIELDS
    }
    mutation_counts = _new_mutation_counts()
    all_row_count = 0
    significant_row_count = 0
    target_count = 0

    with (
        _stream_projection_tsv("Step 09 all-sites", all_sites) as (
            all_path,
            all_header,
            all_rows,
        ),
        _stream_projection_tsv("Step 09 significant-sites", significant_sites) as (
            significant_path,
            significant_header,
            significant_rows,
        ),
    ):
        all_sample_ids = _projection_sample_ids(all_header, "Step 09 all-sites")
        significant_sample_ids = _projection_sample_ids(
            significant_header,
            "Step 09 significant-sites",
        )
        if all_sample_ids != significant_sample_ids:
            fail("Step 09 result-table sample blocks disagree.")

        for all_row_number, all_row in all_rows:
            candidate_id = all_row["candidate_id"]
            if not candidate_id:
                fail(
                    f"Step 09 all-sites row {all_row_number} has an empty candidate_id."
                )
            if candidate_id in all_candidate_ids:
                fail(
                    f"Step 09 all-sites contains duplicate candidate_id: {candidate_id}"
                )
            all_candidate_ids.add(candidate_id)
            _validate_projection_result_row_identity(
                all_row,
                "Step 09 all-sites",
                all_row_number,
                analysis_id,
            )
            _validate_projection_result_row_values(
                all_row,
                all_sample_ids,
                "Step 09 all-sites",
                all_row_number,
            )
            all_row_count += 1
            for summary_field, column, status in STEP09_STATUS_COUNT_FIELDS:
                if all_row[column] == status:
                    status_counts[summary_field] += 1
            for field in _PROJECTION_CONTEXT_FIELDS:
                if all_row[field] != summary_row[field]:
                    fail(f"Step 09 all-sites {field} disagrees with the summary.")
            if (
                f"{all_row['rna_ref']}>{all_row['rna_alt']}"
                == summary_row["target_rna_change"]
            ):
                target_count += 1
            _accumulate_mutation_counts(all_row, mutation_counts)

            if all_row["call_status"] not in _SIGNIFICANT_CALLS:
                continue
            try:
                _, significant_row = next(significant_rows)
            except StopIteration:
                fail(_SIGNIFICANT_SUBSET_ERROR)
            if significant_row["call_status"] not in _SIGNIFICANT_CALLS:
                fail(_SIGNIFICANT_STATUS_ERROR)
            if significant_row != all_row:
                fail(_SIGNIFICANT_SUBSET_ERROR)
            significant_row_count += 1

        try:
            _, extra_significant = next(significant_rows)
        except StopIteration:
            extra_significant = None
        if extra_significant is not None:
            if extra_significant["call_status"] not in _SIGNIFICANT_CALLS:
                fail(_SIGNIFICANT_STATUS_ERROR)
            fail(_SIGNIFICANT_SUBSET_ERROR)

    _reconcile_projection_counts(
        summary_row,
        all_sample_ids,
        all_row_count,
        significant_row_count,
        status_counts,
        target_count,
    )
    if mutation_spectrum is not None:
        _validate_mutation_spectrum_counts(
            mutation_spectrum,
            analysis_id,
            mutation_counts,
            {
                "candidate_count": all_row_count,
                "successfully_tested_count": status_counts["successfully_tested_count"],
                "significant_up_count": status_counts["significant_up_count"],
                "significant_down_count": status_counts["significant_down_count"],
            },
        )
    return (
        _ProjectionTable(all_path, all_header, all_row_count),
        _ProjectionTable(
            significant_path,
            significant_header,
            significant_row_count,
        ),
        summary_table,
        all_sample_ids,
    )


def validate_step09_results(
    label: str,
    value: str | Path,
    sample_ids: Sequence[str],
    analysis_id: str,
    step08_sites: Sequence[Mapping[str, str]],
) -> Table:
    expected_header = sample_block_header(STEP09_RESULT_HEADER, sample_ids)
    table = read_tsv(label, value, expected_header)
    _validate_projection_result_identity(
        table,
        label,
        analysis_id,
        sample_ids,
    )
    sites_by_id = {row["candidate_id"]: row for row in step08_sites}
    metadata_columns = STEP08_METADATA_HEADER
    sample_columns = sample_block_header((), sample_ids)
    for row_number, row in enumerate(table.rows, start=2):
        site = sites_by_id.get(row["candidate_id"])
        if site is None:
            fail(f"{label} references an unknown Step 08 candidate.")
        for column in metadata_columns + sample_columns:
            if row[column] != site[column]:
                fail(
                    f"{label} row {row_number} {column} differs from "
                    "the Step 08 candidate."
                )
    return table


def validate_step09_summary(
    value: str | Path,
    analysis_id: str,
    cohort_id: str,
    sample_ids: Sequence[str],
    sample_rows: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    sample_manifest: Path,
    partition_manifest: Path,
    step08_sites: Path,
    step08_inputs: Path,
    sample_hash: str,
    partition_hash: str,
    sites_hash: str,
    inputs_hash: str,
    step08_orientation_policy: str,
) -> Table:
    validate_safe_id("analysis_id", analysis_id)
    validate_safe_id("cohort_id", cohort_id)
    table = _read_projection_summary(value, analysis_id)
    row = table.rows[0]
    if row["cohort_id"] != cohort_id:
        fail("Step 09 summary cohort_id differs from the Step 08 receipt.")
    validate_safe_id("control_condition", row["control_condition"])
    validate_safe_id("treatment_condition", row["treatment_condition"])
    if row["background_condition"] != NA_VALUE:
        validate_safe_id("background_condition", row["background_condition"])
    _validate_projection_method(row)
    expected_paths = {
        "sample_manifest_path": sample_manifest,
        "partition_manifest_path": partition_manifest,
        "step08_sites_path": step08_sites,
        "step08_inputs_path": step08_inputs,
    }
    for column, expected in expected_paths.items():
        if resolve_recorded_path(row[column]) != expected:
            fail(f"Step 09 summary {column} differs from the explicit input.")
    expected_hashes = {
        "sample_manifest_sha256": sample_hash,
        "partition_manifest_sha256": partition_hash,
        "step08_sites_sha256": sites_hash,
        "step08_inputs_sha256": inputs_hash,
    }
    for column, expected in expected_hashes.items():
        validate_hash(f"Step 09 summary {column}", row[column])
        if row[column] != expected:
            fail(f"Step 09 summary {column} is stale.")
    if parse_nonnegative_int(
        "Step 09 summary sample_count", row["sample_count"]
    ) != len(sample_ids):
        fail("Step 09 summary sample_count differs from the sample manifest.")
    if parse_nonnegative_int(
        "Step 09 summary candidate_count", row["candidate_count"]
    ) != len(all_rows):
        fail("Step 09 summary candidate_count differs from all-sites.")
    target_change = row["target_rna_change"]
    if not re.fullmatch(r"[ACGT]>[ACGT]", target_change):
        fail("Step 09 summary target_rna_change must be a canonical SNV.")
    target_ref, target_alt = target_change.split(">")
    expected_target_count = sum(
        result["rna_ref"] == target_ref and result["rna_alt"] == target_alt
        for result in all_rows
    )
    if (
        parse_nonnegative_int(
            "Step 09 summary target_candidate_count",
            row["target_candidate_count"],
        )
        != expected_target_count
    ):
        fail("Step 09 summary target candidate count does not reconcile.")
    for summary_column, result_column, status in STEP09_STATUS_COUNT_FIELDS:
        expected = count_status(all_rows, result_column, status)
        if (
            parse_nonnegative_int(
                f"Step 09 summary {summary_column}", row[summary_column]
            )
            != expected
        ):
            fail(f"Step 09 summary {summary_column} does not reconcile.")
    replicates, _ = paired_samples(
        sample_rows, row["control_condition"], row["treatment_condition"]
    )
    if parse_nonnegative_int(
        "Step 09 summary replicate_count", row["replicate_count"]
    ) != len(replicates):
        fail("Step 09 summary replicate_count differs from the sample manifest.")
    if (
        not IS_LEGACY_ORIENTATION_POLICY(step08_orientation_policy)[0]
        or not IS_LEGACY_ORIENTATION_POLICY(row["orientation_policy"])[0]
        or row["orientation_policy"] != step08_orientation_policy
    ):
        fail(
            "Step 09 summary and Step 08 must use "
            f"orientation_policy={LEGACY_PROVISIONAL_ORIENTATION_POLICY}."
        )
    if any(
        result["orientation_policy"] != row["orientation_policy"] for result in all_rows
    ):
        fail("Step 09 results contain an inconsistent orientation policy.")
    background = row["background_condition"]
    if background != NA_VALUE:
        if background in (row["control_condition"], row["treatment_condition"]):
            fail("Step 09 background condition must be independent.")
        if not any(sample["condition"] == background for sample in sample_rows):
            fail("Step 09 background condition is absent from the manifest.")
    expected_result_context = {
        "control_condition": row["control_condition"],
        "treatment_condition": row["treatment_condition"],
        "target_rna_change": row["target_rna_change"],
        "replicate_count": row["replicate_count"],
        "background_condition": row["background_condition"],
        "orientation_policy": row["orientation_policy"],
    }
    for result in all_rows:
        for column, expected in expected_result_context.items():
            if result[column] != expected:
                fail(
                    f"Step 09 all-sites {column} differs from the summary "
                    f"for candidate {result['candidate_id']}."
                )
    return table


def _validate_mutation_spectrum_counts(
    value: str | Path,
    analysis_id: str,
    mutation_counts: Mapping[str, Mapping[str, int]],
    aggregate_expected: Mapping[str, int],
) -> Table:
    table = read_tsv("Step 09 mutation spectrum", value, STEP09_MUTATION_HEADER)
    if [row["mutation_type"] for row in table.rows] != list(CANONICAL_MUTATIONS):
        fail("Step 09 mutation spectrum must contain the canonical 12 SNVs.")
    total = aggregate_expected["candidate_count"]
    aggregate_observed = {field: 0 for field in _MUTATION_COUNT_FIELDS}
    for row in table.rows:
        mutation_type = row["mutation_type"]
        ref, alt = mutation_type.split(">")
        if (
            row["analysis_id"] != analysis_id
            or row["rna_ref"] != ref
            or row["rna_alt"] != alt
        ):
            fail("Step 09 mutation spectrum identity columns do not reconcile.")
        expected_counts = mutation_counts[mutation_type]
        for column in _MUTATION_COUNT_FIELDS:
            observed = parse_nonnegative_int(
                f"Step 09 mutation spectrum {column}", row[column]
            )
            aggregate_observed[column] += observed
            if observed != expected_counts[column]:
                fail(f"Step 09 mutation spectrum {column} does not reconcile.")
        fraction = parse_number(
            "Step 09 mutation spectrum candidate_fraction",
            row["candidate_fraction"],
            nonnegative=True,
        )
        expected_fraction = (
            0.0 if total == 0 else expected_counts["candidate_count"] / total
        )
        if (
            fraction is None
            or fraction > 1
            or not values_close(fraction, expected_fraction)
        ):
            fail("Step 09 mutation spectrum candidate_fraction is invalid.")
    for column, expected in aggregate_expected.items():
        if aggregate_observed[column] != expected:
            fail(f"Step 09 mutation spectrum aggregate {column} does not reconcile.")
    return table


def validate_mutation_spectrum(
    value: str | Path,
    analysis_id: str,
    all_rows: Sequence[Mapping[str, str]],
) -> Table:
    mutation_counts = _new_mutation_counts()
    aggregate_expected = {field: 0 for field in _MUTATION_COUNT_FIELDS}
    for row in all_rows:
        aggregate_expected["candidate_count"] += 1
        if row["test_status"] == "tested":
            aggregate_expected["successfully_tested_count"] += 1
        if row["call_status"] == "significant_up":
            aggregate_expected["significant_up_count"] += 1
        if row["call_status"] == "significant_down":
            aggregate_expected["significant_down_count"] += 1
        _accumulate_mutation_counts(row, mutation_counts)
    return _validate_mutation_spectrum_counts(
        value,
        analysis_id,
        mutation_counts,
        aggregate_expected,
    )


def validate_step09_result_semantics(
    rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, str],
    sample_rows: Sequence[Mapping[str, str]],
) -> None:
    target_ref, target_alt = summary["target_rna_change"].split(">")
    (
        min_sample_dp,
        mean_dp_threshold,
        fdr_threshold,
        odds_threshold,
        difference_threshold,
        background_threshold,
    ) = _validate_projection_thresholds(summary)
    _, pairs = paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    analysis_samples = [sample_id for pair in pairs.values() for sample_id in pair]
    control_samples = [pair[0] for pair in pairs.values()]
    treatment_samples = [pair[1] for pair in pairs.values()]
    background_samples = [
        row["sample_id"]
        for row in sample_rows
        if row["condition"] == summary["background_condition"]
    ]
    tested_statistics: list[tuple[str, float, float]] = []
    for row in rows:
        is_target = row["rna_ref"] == target_ref and row["rna_alt"] == target_alt
        if is_target == (row["test_status"] == "not_target_change"):
            fail(
                "Step 09 test_status does not match the declared target "
                f"change for candidate {row['candidate_id']}."
            )
        validate_enum(
            "Step 09 background_status",
            row["background_status"],
            STEP09_BACKGROUND_STATUSES,
        )
        if summary["background_condition"] == NA_VALUE:
            if (
                row["background_status"] != "disabled"
                or row["max_background_af"] != NA_VALUE
            ):
                fail("Step 09 background-disabled result contains a background claim.")
        else:
            background_dp = [row[f"DP__{sample}"] for sample in background_samples]
            background_ad = [row[f"AD__{sample}"] for sample in background_samples]
            background_missing = any(
                value == NA_VALUE for value in background_dp + background_ad
            )
            background_low = not background_missing and any(
                int(value) < min_sample_dp for value in background_dp
            )
            background_positive = not background_missing and all(
                int(value) > 0 for value in background_dp
            )
            background_af = (
                [
                    int(ad) / int(dp)
                    for dp, ad in zip(background_dp, background_ad, strict=True)
                ]
                if background_positive
                else []
            )
            if background_missing:
                expected_background_status = "missing_counts"
                expected_background_max = None
            elif background_low:
                expected_background_status = "low_coverage"
                expected_background_max = max(background_af) if background_af else None
            elif not background_af:
                fail(
                    "Step 09 enabled background has zero depth at or above "
                    "the minimum depth threshold."
                )
            else:
                expected_background_max = max(background_af)
                expected_background_status = (
                    "pass"
                    if all(value < background_threshold for value in background_af)
                    else "fail_fraction"
                )
            observed_background_max = parse_number(
                "Step 09 max_background_af",
                row["max_background_af"],
                allow_na=True,
                nonnegative=True,
            )
            if row[
                "background_status"
            ] != expected_background_status or not values_close(
                observed_background_max, expected_background_max
            ):
                fail(
                    "Step 09 enabled-background status or maximum AF does "
                    f"not reconcile for candidate {row['candidate_id']}."
                )
        sample_dp = [row[f"DP__{sample}"] for sample in analysis_samples]
        sample_ad = [row[f"AD__{sample}"] for sample in analysis_samples]
        missing_counts = any(value == NA_VALUE for value in sample_dp + sample_ad)
        low_coverage = not missing_counts and any(
            int(value) < min_sample_dp for value in sample_dp
        )
        if missing_counts:
            for column in (
                "min_analysis_dp",
                "mean_analysis_dp",
                "mean_control_af",
                "mean_treatment_af",
                "treatment_control_difference",
            ):
                if row[column] != NA_VALUE:
                    fail(
                        f"Step 09 {column} must be NA when analysis counts "
                        f"are missing for candidate {row['candidate_id']}."
                    )
        else:
            dp_values = [int(value) for value in sample_dp]
            observed_min_dp = parse_number(
                "Step 09 min_analysis_dp",
                row["min_analysis_dp"],
                nonnegative=True,
            )
            observed_mean_dp = parse_number(
                "Step 09 mean_analysis_dp",
                row["mean_analysis_dp"],
                nonnegative=True,
            )
            if not values_close(
                observed_min_dp, float(min(dp_values))
            ) or not values_close(
                observed_mean_dp,
                sum(dp_values) / len(dp_values),
            ):
                fail(
                    "Step 09 depth metrics do not reconcile with immutable "
                    f"sample counts for candidate {row['candidate_id']}."
                )
            if all(value > 0 for value in dp_values):
                control_af_values = [
                    int(row[f"AD__{sample}"]) / int(row[f"DP__{sample}"])
                    for sample in control_samples
                ]
                treatment_af_values = [
                    int(row[f"AD__{sample}"]) / int(row[f"DP__{sample}"])
                    for sample in treatment_samples
                ]
                expected_control_af = sum(control_af_values) / len(control_af_values)
                expected_treatment_af = sum(treatment_af_values) / len(
                    treatment_af_values
                )
                expected_delta = expected_treatment_af - expected_control_af
                observed_control_af = parse_number(
                    "Step 09 mean_control_af",
                    row["mean_control_af"],
                    nonnegative=True,
                )
                observed_treatment_af = parse_number(
                    "Step 09 mean_treatment_af",
                    row["mean_treatment_af"],
                    nonnegative=True,
                )
                observed_delta = parse_number(
                    "Step 09 treatment_control_difference",
                    row["treatment_control_difference"],
                )
                if (
                    not values_close(observed_control_af, expected_control_af)
                    or not values_close(observed_treatment_af, expected_treatment_af)
                    or not values_close(observed_delta, expected_delta)
                ):
                    fail(
                        "Step 09 AF/delta metrics do not reconcile with "
                        "immutable sample counts for candidate "
                        f"{row['candidate_id']}."
                    )
            else:
                for column in (
                    "mean_control_af",
                    "mean_treatment_af",
                    "treatment_control_difference",
                ):
                    if row[column] != NA_VALUE:
                        fail(
                            f"Step 09 {column} must be NA with zero analysis "
                            f"depth for candidate {row['candidate_id']}."
                        )
        if is_target:
            if missing_counts:
                expected_pretest_statuses = {"missing_counts"}
            elif low_coverage:
                expected_pretest_statuses = {"low_coverage"}
            else:
                expected_pretest_statuses = {"degenerate_table", "tested"}
            if row["test_status"] not in expected_pretest_statuses:
                fail(
                    "Step 09 test_status conflicts with observed target "
                    "candidate count availability/coverage."
                )
        if row["test_status"] != "tested":
            if row["call_status"] != "not_tested":
                fail("An untested Step 09 candidate must use call_status=not_tested.")
            for column in (
                "cmh_statistic",
                "cmh_degrees_freedom",
                "cmh_p_value",
                "cmh_fdr_bh",
                "common_odds_ratio",
            ):
                if row[column] != NA_VALUE:
                    fail(
                        f"Untested Step 09 candidate {row['candidate_id']} "
                        f"must use {column}=NA."
                    )
            continue
        if row["call_status"] == "not_tested":
            fail("A tested Step 09 candidate cannot use call_status=not_tested.")
        statistic = parse_number(
            "Step 09 cmh_statistic", row["cmh_statistic"], nonnegative=True
        )
        degrees = parse_number(
            "Step 09 cmh_degrees_freedom",
            row["cmh_degrees_freedom"],
            nonnegative=True,
        )
        p_value = parse_number(
            "Step 09 cmh_p_value", row["cmh_p_value"], nonnegative=True
        )
        fdr = parse_number("Step 09 cmh_fdr_bh", row["cmh_fdr_bh"], nonnegative=True)
        odds = parse_nonnegative_or_infinite(
            "Step 09 common_odds_ratio", row["common_odds_ratio"]
        )
        mean_dp = parse_number(
            "Step 09 mean_analysis_dp",
            row["mean_analysis_dp"],
            nonnegative=True,
        )
        control_af = parse_number(
            "Step 09 mean_control_af",
            row["mean_control_af"],
            nonnegative=True,
        )
        treatment_af = parse_number(
            "Step 09 mean_treatment_af",
            row["mean_treatment_af"],
            nonnegative=True,
        )
        delta = parse_number(
            "Step 09 treatment_control_difference",
            row["treatment_control_difference"],
        )
        if (
            statistic is None
            or degrees != 1
            or p_value is None
            or p_value > 1
            or fdr is None
            or fdr > 1
            or mean_dp is None
            or control_af is None
            or control_af > 1
            or treatment_af is None
            or treatment_af > 1
            or delta is None
            or not values_close(delta, treatment_af - control_af)
        ):
            fail("Step 09 tested-candidate statistics are malformed.")
        tested_statistics.append((row["candidate_id"], p_value, fdr))
        if mean_dp <= mean_dp_threshold:
            expected_call = "below_mean_dp"
        elif row["background_status"] not in ("disabled", "pass"):
            expected_call = "background_not_passed"
        elif fdr >= fdr_threshold:
            expected_call = "fdr_not_met"
        elif odds > odds_threshold and delta > difference_threshold:
            expected_call = "significant_up"
        elif odds < (1 / odds_threshold) and delta < -difference_threshold:
            expected_call = "significant_down"
        else:
            expected_call = "effect_not_met"
        if row["call_status"] != expected_call:
            fail(
                "Step 09 call_status conflicts with the declared strict "
                f"thresholds for candidate {row['candidate_id']}."
            )
    if tested_statistics:
        p_values = [value[1] for value in tested_statistics]
        count = len(p_values)
        descending = sorted(
            range(count), key=lambda index: p_values[index], reverse=True
        )
        adjusted = [0.0] * count
        running = 1.0
        for rank, index in zip(range(count, 0, -1), descending, strict=True):
            running = min(running, count * p_values[index] / rank)
            adjusted[index] = min(1.0, running)
        for (candidate_id, p_value, observed), expected in zip(
            tested_statistics, adjusted, strict=True
        ):
            if observed < p_value or not values_close(observed, expected):
                fail(
                    "Step 09 cmh_fdr_bh does not match global BH adjustment "
                    f"for candidate {candidate_id}."
                )


def validate_significant_subset(
    all_rows: Sequence[Mapping[str, str]],
    significant_rows: Sequence[Mapping[str, str]],
) -> None:
    expected = [
        row
        for row in all_rows
        if row["call_status"] in ("significant_up", "significant_down")
    ]
    if list(significant_rows) != expected:
        fail(
            "Step 09 significant-sites table is not the exact ordered "
            "significant subset of all-sites."
        )
