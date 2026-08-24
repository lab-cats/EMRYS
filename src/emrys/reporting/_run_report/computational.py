"""Exact Step 09 computational-result admission for static reports."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from emrys.contracts.scientific_evidence import step08, step09
from emrys.libraries import validation as owner_validation

from .inputs import (
    _assert_snapshot,
    _fail,
    _resolve_contract_file,
    _snapshot_regular,
)
from .models import (
    COMPUTATIONAL_ALL_SITES_DISPLAY_LIMIT,
    COMPUTATIONAL_SIGNIFICANT_DISPLAY_LIMIT,
    ComputationalSampleManifest,
    ComputationalResults,
    ComputationalTable,
    ReportRenderError,
    SamplePair,
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
    (
        "mutation_spectrum",
        "computational_mutation_spectrum",
        "step09_mutation_spectrum_tsv_v1",
        "mutation_spectrum",
        "Step 09 canonical mutation spectrum",
        len(step09.CANONICAL_MUTATIONS),
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
            "The exact primary-analysis Step 09 result trio, mutation spectrum, "
            "and owner-validation artifact are not complete, so no computational "
            "candidate rows were opened or displayed: " + "; ".join(unavailable) + "."
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


def _admit_source_identity(
    record: Mapping[str, Any],
    *,
    source_root: Path,
) -> tuple[Path, Any]:
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
    return path, snapshot


def _source_table(
    record: Mapping[str, Any],
    *,
    source_root: Path,
    display_limit: int,
    expected_header: Sequence[str] | None = None,
    admitted_source: tuple[Path, Any] | None = None,
) -> tuple[Path, Any, tuple[str, ...], list[tuple[str, ...]], int]:
    path, snapshot = admitted_source or _admit_source_identity(
        record, source_root=source_root
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
    _assert_snapshot(snapshot, f"computational result {record['artifact_id']!r}")
    return path, snapshot, header, displayed, observed_row_count


def _projection_table(
    record: Mapping[str, Any],
    *,
    role: str,
    table_id: str,
    title: str,
    source_root: Path,
    display_limit: int,
    admitted_source: tuple[Path, Any],
    canonical_path: Path,
    canonical_header: Sequence[str],
    canonical_row_count: int,
) -> ComputationalTable:
    path, snapshot, header, displayed, observed_row_count = _source_table(
        record,
        source_root=source_root,
        display_limit=display_limit,
        expected_header=canonical_header,
        admitted_source=admitted_source,
    )
    source = record["source"]
    assert isinstance(source, Mapping)
    if canonical_path != path:
        _fail(
            f"Canonical Step 09 projection selected a different source for "
            f"{record['artifact_id']!r}"
        )
    if observed_row_count != canonical_row_count:
        _fail(
            f"Computational result {record['artifact_id']!r} row count differs "
            "from the canonical Step 09 projection"
        )
    if observed_row_count != source["row_count"]:
        _fail(
            f"Computational result {record['artifact_id']!r} row-count mismatch: "
            f"observed {observed_row_count}; expected {source['row_count']}"
        )
    return ComputationalTable(
        role=role,
        table_id=table_id,
        artifact_id=record["artifact_id"],
        title=title,
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=observed_row_count,
        display_row_limit=display_limit,
        header=header,
        display_rows=tuple(displayed),
        snapshot=snapshot,
    )


def _admit_sample_manifest(
    summary: Mapping[str, Any],
    summary_table: ComputationalTable,
    sample_ids: Sequence[str],
    *,
    source_root: Path,
) -> ComputationalSampleManifest:
    summary_row = dict(
        zip(summary_table.header, summary_table.display_rows[0], strict=True)
    )
    recorded_hash = summary_row["sample_manifest_sha256"]
    try:
        step08.validate_hash("Step 09 sample manifest SHA-256", recorded_hash)
    except step08.ContractError as exc:
        _fail(str(exc))
    run_contract_hash = summary["run_contract"]["sample_manifest_sha256"]
    if recorded_hash != run_contract_hash:
        _fail("Step 09 sample manifest SHA-256 differs from the immutable run contract")
    path = _resolve_contract_file(
        summary_row["sample_manifest_path"],
        "Step 09 sample manifest",
        source_root=source_root,
    )
    snapshot = _snapshot_regular(path, "Step 09 sample manifest")
    if snapshot.sha256 != recorded_hash:
        _fail(
            "Step 09 sample manifest SHA-256 mismatch: observed "
            f"{snapshot.sha256}; expected {recorded_hash}"
        )
    try:
        data = path.read_bytes()
    except OSError as exc:
        _fail(f"Could not read Step 09 sample manifest: {exc}")
    if (
        len(data) != snapshot.size_bytes
        or hashlib.sha256(data).hexdigest() != snapshot.sha256
    ):
        _fail("Step 09 sample manifest changed while its bytes were admitted")
    try:
        _table, manifest_sample_ids, sample_rows = (
            step08.validate_sample_manifest_bytes(data, path)
        )
    except (step08.ContractError, UnicodeError, csv.Error) as exc:
        _fail(f"Step 09 sample manifest failed validation: {exc}")
    if tuple(manifest_sample_ids) != tuple(sample_ids):
        _fail(
            "Step 09 sample manifest order differs from the admitted result-table "
            "sample blocks"
        )
    control = summary_row["control_condition"]
    treatment = summary_row["treatment_condition"]
    try:
        replicate_ids, pairs = step09.paired_samples(
            sample_rows,
            control,
            treatment,
        )
    except step09.ContractError as exc:
        _fail(f"Step 09 sample manifest pairing failed validation: {exc}")
    if len(replicate_ids) != int(summary_row["replicate_count"]):
        _fail(
            "Step 09 sample manifest replicate count differs from the admitted summary"
        )
    _assert_snapshot(snapshot, "Step 09 sample manifest")
    return ComputationalSampleManifest(
        role="sample_manifest",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        sample_ids=tuple(manifest_sample_ids),
        control_condition=control,
        treatment_condition=treatment,
        pairs=tuple(
            SamplePair(
                replicate=replicate,
                control_sample_id=pairs[replicate][0],
                treatment_sample_id=pairs[replicate][1],
            )
            for replicate in replicate_ids
        ),
        snapshot=snapshot,
    )


def admit_computational_results(
    summary: Mapping[str, Any],
    *,
    source_root: Path,
) -> tuple[ComputationalResults | None, str | None]:
    """Admit the exact primary Step 09 report sources or disclose unavailability."""

    records, unavailable_reason = _select_records(summary)
    if unavailable_reason is not None:
        return None, unavailable_reason
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    validation = _inspect_validation(
        records["validation"],
        source_root=source_root,
        analysis_id=analysis_id,
    )
    admitted = {
        role: _admit_source_identity(records[role], source_root=source_root)
        for role in (
            "all_sites",
            "significant_sites",
            "summary",
            "mutation_spectrum",
        )
    }
    try:
        all_projection, significant_projection, summary_projection, sample_ids = (
            step09.validate_step09_projection(
                admitted["all_sites"][0],
                admitted["significant_sites"][0],
                admitted["summary"][0],
                analysis_id,
                mutation_spectrum=admitted["mutation_spectrum"][0],
            )
        )
    except (step09.ContractError, OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Primary Step 09 projection failed validation: {exc}")

    projections = {
        "all_sites": (
            all_projection.path,
            all_projection.header,
            all_projection.row_count,
        ),
        "significant_sites": (
            significant_projection.path,
            significant_projection.header,
            significant_projection.row_count,
        ),
        "summary": (
            summary_projection.path,
            summary_projection.header,
            len(summary_projection.rows),
        ),
        "mutation_spectrum": (
            admitted["mutation_spectrum"][0],
            step09.STEP09_MUTATION_HEADER,
            len(step09.CANONICAL_MUTATIONS),
        ),
    }
    tables: dict[str, ComputationalTable] = {}
    for role, table_id, _adapter, _suffix, title, display_limit in _ROLE_SPECS:
        canonical_path, canonical_header, canonical_row_count = projections[role]
        tables[role] = _projection_table(
            records[role],
            role=role,
            table_id=table_id,
            title=title,
            source_root=source_root,
            display_limit=display_limit,
            admitted_source=admitted[role],
            canonical_path=canonical_path,
            canonical_header=canonical_header,
            canonical_row_count=canonical_row_count,
        )
    for role, table in tables.items():
        _assert_snapshot(
            table.snapshot,
            f"computational result {records[role]['artifact_id']!r}",
        )
    sample_manifest = _admit_sample_manifest(
        summary,
        tables["summary"],
        sample_ids,
        source_root=source_root,
    )
    return (
        ComputationalResults(
            analysis_id=analysis_id,
            sample_ids=tuple(sample_ids),
            validation=validation,
            all_sites=tables["all_sites"],
            significant_sites=tables["significant_sites"],
            summary=tables["summary"],
            mutation_spectrum=tables["mutation_spectrum"],
            sample_manifest=sample_manifest,
        ),
        None,
    )
