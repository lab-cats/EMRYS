"""Exact Step 09 computational-result admission for static reports."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.contracts.scientific_evidence import step08, step09
from norad.libraries import validation as owner_validation

from .inputs import (
    _assert_snapshot,
    _fail,
    _resolve_contract_file,
    _snapshot_regular,
)
from .models import (
    COMPUTATIONAL_ALL_SITES_DISPLAY_LIMIT,
    COMPUTATIONAL_SIGNIFICANT_DISPLAY_LIMIT,
    ComputationalResults,
    ComputationalTable,
    ReportRenderError,
)


@dataclass(frozen=True)
class _ResultInspection:
    table: ComputationalTable
    sample_ids: tuple[str, ...]
    status_counts: Mapping[str, Counter[str]]
    context_values: Mapping[str, frozenset[str]]
    target_change_counts: Mapping[str, int]


_RESULT_CONTEXT_FIELDS = (
    "control_condition",
    "treatment_condition",
    "target_rna_change",
    "replicate_count",
    "background_condition",
    "orientation_policy",
)
_VALIDATION_ADAPTER = "step09_validation_report_v1"
_VALIDATION_CHECK_IDS = (
    "output_transaction",
    "upstream_identity_and_candidate_order",
    "status_semantics",
    "significant_subset",
    "summary_count_reconciliation",
    "mutation_spectrum_reconciliation",
    "pdf_structure",
)
_ROLE_SPECS = (
    (
        "all_sites",
        "computational_all_sites",
        "step09_cmh_all_sites_v1",
        "cmh_all_sites",
        "Step 09 all CMH-ranked candidates",
        COMPUTATIONAL_ALL_SITES_DISPLAY_LIMIT,
    ),
    (
        "significant_sites",
        "computational_significant_sites",
        "step09_cmh_significant_sites_v1",
        "cmh_significant_sites",
        "Step 09 threshold-passing CMH-ranked candidates",
        COMPUTATIONAL_SIGNIFICANT_DISPLAY_LIMIT,
    ),
    (
        "summary",
        "computational_summary",
        "step09_cmh_summary_v1",
        "cmh_summary",
        "Step 09 computational-analysis summary",
        1,
    ),
)


def _record_identity(
    record: Mapping[str, Any],
    *,
    analysis_id: str,
    adapter: str,
) -> None:
    if record["adapter"] != adapter:
        _fail(
            f"Primary Step 09 artifact {record['artifact_id']!r} uses the wrong "
            f"adapter: {record['adapter']!r}"
        )
    expected_scope = {
        "step_id": "09",
        "scope_type": "analysis",
        "scope_id": analysis_id,
    }
    if record["scope"] != expected_scope:
        _fail(
            f"Primary Step 09 artifact {record['artifact_id']!r} uses the wrong "
            f"scope: {record['scope']!r}"
        )
    if record["expectation"]["required"] is not True:
        _fail(f"Primary Step 09 artifact {record['artifact_id']!r} must be required")
    recorded_analysis_id = record["parameters"].get("analysis_id")
    source_is_complete = (
        record["availability_status"] == "present"
        and record["completion_status"] == "complete"
        and record["source"] is not None
    )
    if recorded_analysis_id not in {None, analysis_id} or (
        source_is_complete and recorded_analysis_id != analysis_id
    ):
        _fail(
            f"Primary Step 09 artifact {record['artifact_id']!r} has a mismatched "
            "analysis_id parameter"
        )


def _select_records(
    summary: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], str | None]:
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    selected: dict[str, Mapping[str, Any]] = {}
    unavailable: list[str] = []
    for role, _table_id, adapter, _artifact_suffix, _title, _limit in _ROLE_SPECS:
        identity_matches = [
            artifact
            for artifact in summary["artifacts"]
            if artifact["adapter"] == adapter
            and artifact["scope"]
            == {
                "step_id": "09",
                "scope_type": "analysis",
                "scope_id": analysis_id,
            }
        ]
        if len(identity_matches) != 1:
            _fail(
                "Run summary must declare exactly one primary Step 09 artifact "
                f"using adapter {adapter!r}; observed {len(identity_matches)}"
            )
        record = identity_matches[0]
        _record_identity(
            record,
            analysis_id=analysis_id,
            adapter=adapter,
        )
        selected[role] = record
        if not (
            record["availability_status"] == "present"
            and record["completion_status"] == "complete"
            and record["source"] is not None
        ):
            unavailable.append(
                f"{record['artifact_id']} "
                f"({record['availability_status']}/{record['completion_status']})"
            )
    validation_matches = [
        artifact
        for artifact in summary["artifacts"]
        if artifact["adapter"] == _VALIDATION_ADAPTER
        and artifact["scope"]
        == {
            "step_id": "09",
            "scope_type": "analysis",
            "scope_id": analysis_id,
        }
    ]
    if len(validation_matches) != 1:
        _fail(
            "Run summary must declare exactly one primary Step 09 owner-validation "
            f"artifact; observed {len(validation_matches)}"
        )
    validation_record = validation_matches[0]
    if validation_record["expectation"]["required"] is not True:
        _fail("Primary Step 09 owner-validation artifact must be required")
    selected["validation"] = validation_record
    if not (
        validation_record["availability_status"] == "present"
        and validation_record["completion_status"] == "complete"
        and validation_record["source"] is not None
    ):
        unavailable.append(
            f"{validation_record['artifact_id']} "
            f"({validation_record['availability_status']}/"
            f"{validation_record['completion_status']})"
        )
    reason = None
    if unavailable:
        reason = (
            "The exact primary-analysis Step 09 result trio and owner-validation "
            "artifact are not complete, so no computational candidate rows were "
            "opened or displayed: " + "; ".join(unavailable) + "."
        )
    return selected, reason


def _inspect_validation(
    record: Mapping[str, Any],
    *,
    source_root: Path,
    analysis_id: str,
) -> ComputationalTable:
    path, snapshot, header, rows, observed_row_count = _source_table(
        record,
        source_root=source_root,
        display_limit=len(_VALIDATION_CHECK_IDS),
        expected_header=owner_validation.HEADER,
    )
    source = record["source"]
    assert isinstance(source, Mapping)
    if (
        source["row_count"] != len(_VALIDATION_CHECK_IDS)
        or observed_row_count != len(_VALIDATION_CHECK_IDS)
        or len(rows) != len(_VALIDATION_CHECK_IDS)
    ):
        _fail(
            "Primary Step 09 owner-validation report must contain exactly "
            f"{len(_VALIDATION_CHECK_IDS)} check rows"
        )
    for row_number, (values, expected_check_id) in enumerate(
        zip(rows, _VALIDATION_CHECK_IDS, strict=True),
        start=2,
    ):
        row = dict(zip(header, values, strict=True))
        if row["step_id"] != "09" or row["scope_id"] != analysis_id:
            _fail(
                "Primary Step 09 owner-validation report row "
                f"{row_number} has the wrong step/scope"
            )
        if row["check_id"] != expected_check_id:
            _fail(
                "Primary Step 09 owner-validation report has the wrong ordered "
                f"check roster at row {row_number}"
            )
        if row["status"] != "pass":
            _fail(
                "Primary Step 09 owner-validation report is not all-pass: "
                f"{expected_check_id}={row['status'] or '<empty>'}"
            )
    _assert_snapshot(snapshot, f"computational validation {record['artifact_id']!r}")
    return ComputationalTable(
        role="validation",
        table_id="computational_validation",
        artifact_id=record["artifact_id"],
        title="Step 09 owner-validation report",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=len(rows),
        display_row_limit=len(_VALIDATION_CHECK_IDS),
        header=header,
        display_rows=tuple(rows),
        snapshot=snapshot,
    )


def _source_table(
    record: Mapping[str, Any],
    *,
    source_root: Path,
    display_limit: int,
    expected_header: Sequence[str] | None = None,
) -> tuple[Path, Any, tuple[str, ...], list[tuple[str, ...]], int]:
    source = record["source"]
    if not isinstance(source, Mapping):
        _fail(f"Computational result {record['artifact_id']!r} has no source record")
    if source["media_type"] != "text/tab-separated-values":
        _fail(f"Computational result {record['artifact_id']!r} must be a TSV source")
    if source["path"] != record["expectation"]["source_path"]:
        _fail(
            f"Computational result {record['artifact_id']!r} source path differs "
            "from its expectation"
        )
    path = _resolve_contract_file(
        source["path"],
        f"computational result {record['artifact_id']!r}",
        source_root=source_root,
    )
    snapshot = _snapshot_regular(
        path,
        f"computational result {record['artifact_id']!r}",
    )
    if snapshot.sha256 != source["sha256"]:
        _fail(
            f"Computational result {record['artifact_id']!r} SHA-256 mismatch: "
            f"observed {snapshot.sha256}; expected {source['sha256']}"
        )
    if snapshot.size_bytes != source["size_bytes"]:
        _fail(
            f"Computational result {record['artifact_id']!r} size mismatch: "
            f"observed {snapshot.size_bytes}; expected {source['size_bytes']}"
        )

    header: tuple[str, ...] | None = None
    displayed: list[tuple[str, ...]] = []
    observed_row_count = 0
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                header = tuple(next(reader))
            except StopIteration:
                _fail(f"Computational result {record['artifact_id']!r} is empty")
            if not header or any(not column for column in header):
                _fail(
                    f"Computational result {record['artifact_id']!r} has a blank "
                    "header column"
                )
            if len(header) != len(set(header)):
                _fail(
                    f"Computational result {record['artifact_id']!r} has duplicate "
                    "header columns"
                )
            if expected_header is not None and header != tuple(expected_header):
                _fail(
                    f"Computational result {record['artifact_id']!r} has the wrong "
                    "header"
                )
            for row_number, row in enumerate(reader, start=2):
                if not row or all(value == "" for value in row):
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} is blank"
                    )
                if len(row) != len(header):
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} has {len(row)} fields; expected {len(header)}"
                    )
                if len(displayed) < display_limit:
                    displayed.append(tuple(row))
                observed_row_count += 1
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not parse computational result {record['artifact_id']!r}: {exc}")
    assert header is not None
    return path, snapshot, header, displayed, observed_row_count


def _sample_ids(header: Sequence[str], artifact_id: str) -> tuple[str, ...]:
    prefix = step09.STEP09_RESULT_HEADER
    if tuple(header[: len(prefix)]) != tuple(prefix):
        _fail(
            f"Computational result {artifact_id!r} has an invalid fixed Step 09 header"
        )
    remainder = tuple(header[len(prefix) :])
    if not remainder or len(remainder) % 3:
        _fail(
            f"Computational result {artifact_id!r} must have equal non-empty "
            "DP__, AD__, and AF__ sample blocks"
        )
    count = len(remainder) // 3
    dp = remainder[:count]
    ad = remainder[count : count * 2]
    af = remainder[count * 2 :]
    samples = tuple(value.removeprefix("DP__") for value in dp)
    if any(
        not value.startswith("DP__") or not sample
        for value, sample in zip(dp, samples, strict=True)
    ) or len(samples) != len(set(samples)):
        _fail(f"Computational result {artifact_id!r} has an invalid DP__ sample block")
    if ad != tuple(f"AD__{sample}" for sample in samples):
        _fail(f"Computational result {artifact_id!r} has an invalid AD__ sample block")
    if af != tuple(f"AF__{sample}" for sample in samples):
        _fail(f"Computational result {artifact_id!r} has an invalid AF__ sample block")
    return samples


def _nonnegative_integer(label: str, value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        _fail(f"{label} must be a non-negative integer; got {value!r}")
    return int(value)


def _number(
    label: str,
    value: str,
    *,
    allow_na: bool = False,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    if allow_na and value == step08.NA_VALUE:
        return None
    try:
        parsed = float(value)
    except ValueError:
        _fail(f"{label} must be numeric; got {value!r}")
    if not math.isfinite(parsed):
        _fail(f"{label} must be finite; got {value!r}")
    if minimum is not None and parsed < minimum:
        _fail(f"{label} must be at least {minimum}; got {value!r}")
    if maximum is not None and parsed > maximum:
        _fail(f"{label} must be at most {maximum}; got {value!r}")
    return parsed


def _nonnegative_or_infinite(label: str, value: str) -> None:
    if value == step08.NA_VALUE:
        return
    try:
        parsed = float(value)
    except ValueError:
        _fail(f"{label} must be numeric; got {value!r}")
    if math.isnan(parsed) or parsed < 0:
        _fail(f"{label} must be non-negative and not NaN; got {value!r}")


def _sample_values(
    row: Mapping[str, str],
    *,
    sample_ids: Sequence[str],
    artifact_id: str,
    row_number: int,
) -> None:
    for sample_id in sample_ids:
        label = (
            f"Computational result {artifact_id!r} row {row_number} sample {sample_id}"
        )
        dp_text = row[f"DP__{sample_id}"]
        ad_text = row[f"AD__{sample_id}"]
        af_text = row[f"AF__{sample_id}"]
        if (dp_text == step08.NA_VALUE) != (ad_text == step08.NA_VALUE):
            _fail(f"{label} has one-sided DP/AD missingness")
        if dp_text == step08.NA_VALUE:
            if af_text != step08.NA_VALUE:
                _fail(f"{label} has AF without DP/AD")
            continue
        dp = _nonnegative_integer(f"{label} DP", dp_text)
        ad = _nonnegative_integer(f"{label} AD", ad_text)
        if ad > dp:
            _fail(f"{label} has AD greater than DP")
        if dp == 0:
            if ad != 0 or af_text != step08.NA_VALUE:
                _fail(f"{label} has invalid zero-depth DP/AD/AF values")
            continue
        try:
            af = float(af_text)
        except ValueError:
            _fail(f"{label} AF must be numeric when DP is positive")
        if not 0 <= af <= 1 or not step08.values_close(af, ad / dp):
            _fail(f"{label} AF does not reconcile with AD/DP")


def _inspect_result(
    record: Mapping[str, Any],
    *,
    role: str,
    table_id: str,
    title: str,
    source_root: Path,
    display_limit: int,
    analysis_id: str,
) -> _ResultInspection:
    path, snapshot, header, displayed, first_row_count = _source_table(
        record,
        source_root=source_root,
        display_limit=display_limit,
    )
    sample_ids = _sample_ids(header, record["artifact_id"])
    row_count = 0
    candidate_ids: set[str] = set()
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    contexts: dict[str, set[str]] = defaultdict(set)
    target_changes: Counter[str] = Counter()
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            if tuple(reader.fieldnames or ()) != header:
                _fail(
                    f"Computational result {record['artifact_id']!r} header changed "
                    "between reads"
                )
            for row_number, row in enumerate(reader, start=2):
                row_count += 1
                if row["analysis_id"] != analysis_id:
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} has the wrong analysis_id"
                    )
                candidate_id = row["candidate_id"]
                if not candidate_id:
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} has a blank candidate_id"
                    )
                if candidate_id in candidate_ids:
                    _fail(
                        f"Computational result {record['artifact_id']!r} has duplicate "
                        f"candidate_id {candidate_id!r}"
                    )
                candidate_ids.add(candidate_id)
                if row["test_status"] not in step09.STEP09_TEST_STATUSES:
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} has unknown test_status {row['test_status']!r}"
                    )
                if row["call_status"] not in step09.STEP09_CALL_STATUSES:
                    _fail(
                        f"Computational result {record['artifact_id']!r} row "
                        f"{row_number} has unknown call_status {row['call_status']!r}"
                    )
                _nonnegative_integer(
                    f"Computational result {record['artifact_id']!r} row "
                    f"{row_number} replicate_count",
                    row["replicate_count"],
                )
                _sample_values(
                    row,
                    sample_ids=sample_ids,
                    artifact_id=record["artifact_id"],
                    row_number=row_number,
                )
                prefix = (
                    f"Computational result {record['artifact_id']!r} row {row_number}"
                )
                _nonnegative_integer(f"{prefix} position", row["position"])
                if _nonnegative_integer(f"{prefix} alt_index", row["alt_index"]) < 1:
                    _fail(f"{prefix} alt_index must be at least 1")
                for field in ("min_analysis_dp", "mean_analysis_dp"):
                    _number(
                        f"{prefix} {field}",
                        row[field],
                        allow_na=True,
                        minimum=0,
                    )
                for field in (
                    "mean_control_af",
                    "mean_treatment_af",
                    "max_background_af",
                    "cmh_p_value",
                    "cmh_fdr_bh",
                ):
                    _number(
                        f"{prefix} {field}",
                        row[field],
                        allow_na=True,
                        minimum=0,
                        maximum=1,
                    )
                _number(
                    f"{prefix} treatment_control_difference",
                    row["treatment_control_difference"],
                    allow_na=True,
                    minimum=-1,
                    maximum=1,
                )
                for field in ("cmh_statistic", "cmh_degrees_freedom"):
                    _number(
                        f"{prefix} {field}",
                        row[field],
                        allow_na=True,
                        minimum=0,
                    )
                _nonnegative_or_infinite(
                    f"{prefix} common_odds_ratio",
                    row["common_odds_ratio"],
                )
                statistical_fields = (
                    "cmh_statistic",
                    "cmh_degrees_freedom",
                    "cmh_p_value",
                    "cmh_fdr_bh",
                    "common_odds_ratio",
                )
                if row["test_status"] == "tested":
                    if row["call_status"] == "not_tested" or any(
                        row[field] == step08.NA_VALUE for field in statistical_fields
                    ):
                        _fail(f"{prefix} tested row lacks complete CMH statistics")
                    if float(row["cmh_degrees_freedom"]) != 1:
                        _fail(f"{prefix} tested row must use one CMH degree of freedom")
                elif row["call_status"] != "not_tested" or any(
                    row[field] != step08.NA_VALUE for field in statistical_fields
                ):
                    _fail(f"{prefix} untested row contains a computational call")
                counts["test_status"][row["test_status"]] += 1
                counts["call_status"][row["call_status"]] += 1
                target_changes[f"{row['rna_ref']}>{row['rna_alt']}"] += 1
                for field in _RESULT_CONTEXT_FIELDS:
                    contexts[field].add(row[field])
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error, KeyError) as exc:
        _fail(
            f"Could not validate computational result {record['artifact_id']!r}: {exc}"
        )
    source = record["source"]
    assert isinstance(source, Mapping)
    if row_count != first_row_count or row_count != source["row_count"]:
        _fail(
            f"Computational result {record['artifact_id']!r} row-count mismatch: "
            f"observed {row_count}; expected {source['row_count']}"
        )
    _assert_snapshot(snapshot, f"computational result {record['artifact_id']!r}")
    return _ResultInspection(
        table=ComputationalTable(
            role=role,
            table_id=table_id,
            artifact_id=record["artifact_id"],
            title=title,
            path=path,
            sha256=snapshot.sha256,
            size_bytes=snapshot.size_bytes,
            row_count=row_count,
            display_row_limit=display_limit,
            header=header,
            display_rows=tuple(displayed),
            snapshot=snapshot,
        ),
        sample_ids=sample_ids,
        status_counts={key: Counter(value) for key, value in counts.items()},
        context_values={key: frozenset(value) for key, value in contexts.items()},
        target_change_counts=dict(target_changes),
    )


def _inspect_summary(
    record: Mapping[str, Any],
    *,
    source_root: Path,
    analysis_id: str,
) -> ComputationalTable:
    path, snapshot, header, displayed, observed_row_count = _source_table(
        record,
        source_root=source_root,
        display_limit=1,
        expected_header=step09.STEP09_SUMMARY_HEADER,
    )
    source = record["source"]
    assert isinstance(source, Mapping)
    if source["row_count"] != 1 or observed_row_count != 1 or len(displayed) != 1:
        _fail("Primary Step 09 computational summary must contain exactly one row")
    row = dict(zip(header, displayed[0], strict=True))
    if row["analysis_id"] != analysis_id:
        _fail("Primary Step 09 computational summary has the wrong analysis_id")
    for field in (
        "replicate_count",
        "sample_count",
        "candidate_count",
        "target_candidate_count",
        *(field for field, _column, _status in step09.STEP09_STATUS_COUNT_FIELDS),
    ):
        _nonnegative_integer(f"Step 09 summary {field}", row[field])
    min_sample_dp = _nonnegative_integer(
        "Step 09 summary min_sample_dp", row["min_sample_dp"]
    )
    mean_dp = _number(
        "Step 09 summary mean_dp_threshold",
        row["mean_dp_threshold"],
        minimum=0,
    )
    fdr = _number(
        "Step 09 summary fdr_threshold",
        row["fdr_threshold"],
        minimum=0,
        maximum=1,
    )
    odds = _number(
        "Step 09 summary common_or_threshold",
        row["common_or_threshold"],
        minimum=0,
    )
    difference = _number(
        "Step 09 summary absolute_difference_threshold",
        row["absolute_difference_threshold"],
        minimum=0,
        maximum=1,
    )
    background = _number(
        "Step 09 summary background_max_fraction",
        row["background_max_fraction"],
        minimum=0,
        maximum=1,
    )
    if (
        min_sample_dp < 1
        or mean_dp is None
        or fdr is None
        or not 0 < fdr <= 1
        or odds is None
        or odds <= 1
        or difference is None
        or background is None
        or not 0 < background < 1
    ):
        _fail("Primary Step 09 summary thresholds are outside the supported contract")
    if (
        row["multiple_testing_method"] != "BH"
        or row["cmh_alternative"] != "two.sided"
        or row["continuity_correction"] != "TRUE"
    ):
        _fail("Primary Step 09 summary does not declare the supported CMH contract")
    if not re.fullmatch(r"[ACGT]>[ACGT]", row["target_rna_change"]):
        _fail("Primary Step 09 summary target_rna_change is not a canonical SNV")
    _assert_snapshot(snapshot, f"computational result {record['artifact_id']!r}")
    return ComputationalTable(
        role="summary",
        table_id="computational_summary",
        artifact_id=record["artifact_id"],
        title="Step 09 computational-analysis summary",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=1,
        display_row_limit=1,
        header=header,
        display_rows=tuple(displayed),
        snapshot=snapshot,
    )


def _exact_significant_subset(
    all_sites: ComputationalTable,
    significant_sites: ComputationalTable,
) -> None:
    try:
        with all_sites.path.open(encoding="utf-8", newline="") as all_stream:
            with significant_sites.path.open(
                encoding="utf-8", newline=""
            ) as significant_stream:
                all_reader = csv.reader(all_stream, delimiter="\t", strict=True)
                significant_reader = csv.reader(
                    significant_stream,
                    delimiter="\t",
                    strict=True,
                )
                all_header = tuple(next(all_reader))
                significant_header = tuple(next(significant_reader))
                if all_header != significant_header:
                    _fail("Step 09 all-sites and significant-sites headers disagree")
                call_index = all_header.index("call_status")
                current = next(significant_reader, None)
                for row in all_reader:
                    if row[call_index] not in {"significant_up", "significant_down"}:
                        continue
                    if current != row:
                        _fail(
                            "Step 09 significant-sites is not the exact ordered "
                            "significant subset of all-sites"
                        )
                    current = next(significant_reader, None)
                if current is not None:
                    _fail("Step 09 significant-sites contains an extra row")
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error, StopIteration, ValueError) as exc:
        _fail(f"Could not compare Step 09 result tables: {exc}")


def _reconcile(
    all_sites: _ResultInspection,
    significant_sites: _ResultInspection,
    summary_table: ComputationalTable,
) -> None:
    if all_sites.sample_ids != significant_sites.sample_ids:
        _fail("Step 09 result-table sample blocks disagree")
    summary = dict(
        zip(summary_table.header, summary_table.display_rows[0], strict=True)
    )
    if _nonnegative_integer(
        "Step 09 summary sample_count", summary["sample_count"]
    ) != len(all_sites.sample_ids):
        _fail("Step 09 summary sample_count disagrees with result columns")
    if (
        _nonnegative_integer(
            "Step 09 summary candidate_count", summary["candidate_count"]
        )
        != all_sites.table.row_count
    ):
        _fail("Step 09 summary candidate_count disagrees with all-sites rows")
    significant_count = _nonnegative_integer(
        "Step 09 summary significant_up_count", summary["significant_up_count"]
    ) + _nonnegative_integer(
        "Step 09 summary significant_down_count", summary["significant_down_count"]
    )
    if significant_count != significant_sites.table.row_count:
        _fail("Step 09 summary significant counts disagree with significant-sites rows")
    for summary_field, column, status in step09.STEP09_STATUS_COUNT_FIELDS:
        expected = all_sites.status_counts.get(column, {}).get(status, 0)
        if (
            _nonnegative_integer(
                f"Step 09 summary {summary_field}", summary[summary_field]
            )
            != expected
        ):
            _fail(f"Step 09 summary {summary_field} disagrees with all-sites")
    target_count = all_sites.target_change_counts.get(summary["target_rna_change"], 0)
    if (
        _nonnegative_integer(
            "Step 09 summary target_candidate_count",
            summary["target_candidate_count"],
        )
        != target_count
    ):
        _fail("Step 09 summary target_candidate_count disagrees with all-sites")
    unexpected_significant = set(
        significant_sites.status_counts.get("call_status", {})
    ) - {"significant_up", "significant_down"}
    if unexpected_significant:
        _fail("Step 09 significant-sites contains a non-significant call status")
    for field in _RESULT_CONTEXT_FIELDS:
        values = all_sites.context_values.get(field, frozenset())
        if values and values != {summary[field]}:
            _fail(f"Step 09 all-sites {field} disagrees with the summary")
    _exact_significant_subset(all_sites.table, significant_sites.table)
    for table in (all_sites.table, significant_sites.table, summary_table):
        _assert_snapshot(table.snapshot, f"computational result {table.artifact_id!r}")


def admit_computational_results(
    summary: Mapping[str, Any],
    *,
    source_root: Path,
) -> tuple[ComputationalResults | None, str | None]:
    """Admit the exact complete primary Step 09 trio, or disclose unavailability."""

    records, unavailable_reason = _select_records(summary)
    if unavailable_reason is not None:
        return None, unavailable_reason
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    validation = _inspect_validation(
        records["validation"],
        source_root=source_root,
        analysis_id=analysis_id,
    )
    all_spec = _ROLE_SPECS[0]
    significant_spec = _ROLE_SPECS[1]
    all_sites = _inspect_result(
        records["all_sites"],
        role=all_spec[0],
        table_id=all_spec[1],
        title=all_spec[4],
        source_root=source_root,
        display_limit=all_spec[5],
        analysis_id=analysis_id,
    )
    significant_sites = _inspect_result(
        records["significant_sites"],
        role=significant_spec[0],
        table_id=significant_spec[1],
        title=significant_spec[4],
        source_root=source_root,
        display_limit=significant_spec[5],
        analysis_id=analysis_id,
    )
    summary_table = _inspect_summary(
        records["summary"],
        source_root=source_root,
        analysis_id=analysis_id,
    )
    _reconcile(all_sites, significant_sites, summary_table)
    return (
        ComputationalResults(
            analysis_id=analysis_id,
            sample_ids=all_sites.sample_ids,
            validation=validation,
            all_sites=all_sites.table,
            significant_sites=significant_sites.table,
            summary=summary_table,
        ),
        None,
    )
