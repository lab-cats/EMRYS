"""Receipt-backed Step 10 scientific-context admission for static reports."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from emrys.contracts.scientific_evidence import scientific_context as owner_context
from emrys.libraries import validation as owner_validation

from .computational import _admit_source_identity, _source_table
from .inputs import _fail, _resolve_contract_file, _snapshot_regular
from .models import (
    ComputationalResults,
    ComputationalTable,
    ScientificContextResults,
    ScientificContextSource,
)

_VALIDATION_ADAPTER = "step10_validation_report_v1"
_VALIDATION_CHECK_ID = "scientific_context_transaction"
_ROLE_SPECS = (
    (
        "candidate_context",
        "step10_candidate_context_v1",
        "scientific_context_candidate_context",
        "Step 10 candidate context",
        owner_context.CANDIDATE_CONTEXT_HEADER,
        0,
    ),
    (
        "motif_hits",
        "step10_motif_hits_v1",
        "scientific_context_motif_hits",
        "Step 10 exact registered-motif hits",
        owner_context.MOTIF_HITS_HEADER,
        0,
    ),
    (
        "sequence_logo",
        "step10_sequence_logo_v1",
        "scientific_context_sequence_logo",
        "Step 10 observed sequence-logo frequencies",
        owner_context.SEQUENCE_LOGO_HEADER,
        len(owner_context.CONTEXT_POPULATIONS)
        * (2 * owner_context.LOGO_RADIUS + 1)
        * 4,
    ),
    (
        "motif_statistics",
        "step10_motif_statistics_v1",
        "scientific_context_motif_statistics",
        "Step 10 registered-motif position and enrichment statistics",
        owner_context.MOTIF_STATISTICS_HEADER,
        1
        + len(owner_context.CONTEXT_POPULATIONS)
        * (2 * owner_context.CONTEXT_RADIUS // owner_context.MOTIF_DISTANCE_BIN_WIDTH),
    ),
)
_RECEIPT_ADAPTER = "step10_context_receipt_v1"
_ALL_ADAPTERS = frozenset(
    (*[spec[1] for spec in _ROLE_SPECS], _RECEIPT_ADAPTER, _VALIDATION_ADAPTER)
)
_BOUND_INPUT_ROLES = (
    "step09_all_sites",
    "step09_significant_sites",
    "step09_summary",
    "reference_fasta",
    "reference_fai",
    "motif_catalog",
)


def _is_complete(record: Mapping[str, Any]) -> bool:
    return (
        record["availability_status"] == "present"
        and record["completion_status"] == "complete"
        and record["source"] is not None
    )


def _validate_record_identity(
    record: Mapping[str, Any],
    *,
    analysis_id: str,
    adapter: str,
) -> None:
    if record["adapter"] != adapter:
        _fail(
            f"Primary Step 10 artifact {record['artifact_id']!r} uses the wrong "
            f"adapter: {record['adapter']!r}"
        )
    expected_scope = {
        "step_id": "10",
        "scope_type": "analysis",
        "scope_id": analysis_id,
    }
    if record["scope"] != expected_scope:
        _fail(
            f"Primary Step 10 artifact {record['artifact_id']!r} uses the wrong "
            f"scope: {record['scope']!r}"
        )
    if record["expectation"]["required"] is not True:
        _fail(f"Primary Step 10 artifact {record['artifact_id']!r} must be required")
    recorded_analysis_id = record["parameters"].get("analysis_id")
    if recorded_analysis_id not in {None, analysis_id}:
        _fail(
            f"Primary Step 10 artifact {record['artifact_id']!r} has a mismatched "
            "analysis_id parameter"
        )


def _select_records(
    summary: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]] | None, str | None]:
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    expected_scope = {
        "step_id": "10",
        "scope_type": "analysis",
        "scope_id": analysis_id,
    }
    primary_declarations = [
        artifact
        for artifact in summary["artifacts"]
        if artifact["adapter"] in _ALL_ADAPTERS
        and artifact["scope"]["scope_id"] == analysis_id
    ]
    if not primary_declarations:
        return (
            None,
            "This run predates the Step 10 scientific-context transaction; "
            "the sequence-context and motif-enrichment figures are unavailable. "
            "Selected-candidate editing-rate and location evidence remains "
            "reportable from Step 09, with sequence and registered-motif context "
            "marked not admitted.",
        )
    wrong_scopes = [
        artifact["artifact_id"]
        for artifact in primary_declarations
        if artifact["scope"] != expected_scope
    ]
    if wrong_scopes:
        _fail(
            "Primary Step 10 declarations use the wrong scope: "
            + ", ".join(wrong_scopes)
        )
    in_scope = primary_declarations

    selected: dict[str, Mapping[str, Any]] = {}
    missing_or_incomplete: list[str] = []
    for role, adapter in (
        *((spec[0], spec[1]) for spec in _ROLE_SPECS),
        ("receipt", _RECEIPT_ADAPTER),
        ("validation", _VALIDATION_ADAPTER),
    ):
        matches = [record for record in in_scope if record["adapter"] == adapter]
        if len(matches) > 1:
            _fail(
                "Run summary must not declare duplicate primary Step 10 artifacts "
                f"using adapter {adapter!r}; observed {len(matches)}"
            )
        if not matches:
            missing_or_incomplete.append(f"{adapter} (not declared)")
            continue
        record = matches[0]
        _validate_record_identity(record, analysis_id=analysis_id, adapter=adapter)
        selected[role] = record
        if not _is_complete(record):
            missing_or_incomplete.append(
                f"{record['artifact_id']} "
                f"({record['availability_status']}/{record['completion_status']})"
            )
    if missing_or_incomplete:
        return (
            None,
            "The complete primary-analysis Step 10 transaction is unavailable, "
            "so the Step 10 sequence-context and motif-enrichment figures were not "
            "inferred. Selected-candidate editing-rate and location evidence can "
            "remain reportable from Step 09, with sequence and registered-motif "
            "context marked not admitted: " + "; ".join(missing_or_incomplete) + ".",
        )
    return selected, None


def _validation_table(
    record: Mapping[str, Any],
    *,
    source_root: Path,
    analysis_id: str,
) -> ComputationalTable:
    path, snapshot, header, rows, observed_count = _source_table(
        record,
        source_root=source_root,
        display_limit=1,
        expected_header=owner_validation.HEADER,
    )
    source = record["source"]
    assert isinstance(source, Mapping)
    if source["row_count"] != 1 or observed_count != 1 or len(rows) != 1:
        _fail("Primary Step 10 owner-validation report must contain exactly one row")
    row = dict(zip(header, rows[0], strict=True))
    if row["step_id"] != "10" or row["scope_id"] != analysis_id:
        _fail("Primary Step 10 owner-validation row has the wrong step or scope")
    if row["check_id"] != _VALIDATION_CHECK_ID:
        _fail("Primary Step 10 owner-validation report has the wrong check roster")
    if row["status"] != "pass":
        _fail(
            "Primary Step 10 owner-validation report is not all-pass: "
            f"{_VALIDATION_CHECK_ID}={row['status'] or '<empty>'}"
        )
    return ComputationalTable(
        role="validation",
        table_id="scientific_context_validation",
        artifact_id=record["artifact_id"],
        title="Step 10 owner-validation report",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=1,
        display_row_limit=1,
        header=header,
        display_rows=tuple(rows),
        snapshot=snapshot,
    )


def _canonical_table(
    record: Mapping[str, Any],
    *,
    role: str,
    table_id: str,
    title: str,
    expected_header: tuple[str, ...],
    display_limit: int,
    canonical: owner_context.ContextTable,
    source_root: Path,
) -> ComputationalTable:
    if display_limit:
        path, snapshot, header, displayed, observed_count = _source_table(
            record,
            source_root=source_root,
            display_limit=display_limit,
            expected_header=expected_header,
        )
    else:
        path, snapshot = _admit_source_identity(record, source_root=source_root)
        header = expected_header
        displayed = []
        observed_count = canonical.row_count
    source = record["source"]
    assert isinstance(source, Mapping)
    if path != canonical.path or snapshot.sha256 != canonical.sha256:
        _fail(
            f"Primary Step 10 artifact {record['artifact_id']!r} differs from "
            "the canonical receipt transaction"
        )
    if observed_count != canonical.row_count or source["row_count"] != observed_count:
        _fail(
            f"Primary Step 10 artifact {record['artifact_id']!r} row count differs "
            "from the canonical receipt transaction"
        )
    return ComputationalTable(
        role=role,
        table_id=table_id,
        artifact_id=record["artifact_id"],
        title=title,
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=observed_count,
        display_row_limit=display_limit,
        header=header,
        display_rows=tuple(displayed),
        snapshot=snapshot,
    )


def _receipt_table(
    record: Mapping[str, Any],
    *,
    transaction: owner_context.ScientificContextTransaction,
    source_root: Path,
) -> ComputationalTable:
    path, snapshot = _admit_source_identity(record, source_root=source_root)
    header = tuple(transaction.receipt.header)
    rows = [tuple(transaction.receipt.rows[0][column] for column in header)]
    source = record["source"]
    assert isinstance(source, Mapping)
    if (
        path != transaction.receipt.path
        or snapshot.sha256 != transaction.receipt_sha256
        or source["row_count"] != 1
    ):
        _fail("Primary Step 10 receipt record differs from its canonical transaction")
    return ComputationalTable(
        role="receipt",
        table_id="scientific_context_receipt",
        artifact_id=record["artifact_id"],
        title="Step 10 receipt-last scientific-context transaction",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=1,
        display_row_limit=1,
        header=header,
        display_rows=tuple(rows),
        snapshot=snapshot,
    )


def _bound_inputs(
    receipt_row: Mapping[str, str],
    computational_results: ComputationalResults | None,
) -> tuple[ScientificContextSource, ...]:
    reusable = (
        {
            "step09_all_sites": computational_results.all_sites,
            "step09_significant_sites": computational_results.significant_sites,
            "step09_summary": computational_results.summary,
        }
        if computational_results is not None
        else {}
    )
    sources: list[ScientificContextSource] = []
    for role in _BOUND_INPUT_ROLES:
        path = Path(receipt_row[f"{role}_path"])
        prior = reusable.get(role)
        snapshot = (
            prior.snapshot
            if prior is not None
            and prior.path == path
            and prior.sha256 == receipt_row[f"{role}_sha256"]
            else _snapshot_regular(path, f"scientific-context bound input {role!r}")
        )
        if snapshot.sha256 != receipt_row[f"{role}_sha256"]:
            _fail(f"Scientific-context bound input {role!r} changed after admission")
        sources.append(
            ScientificContextSource(
                role=role,
                artifact_id="Step 10 receipt-bound input",
                path=path,
                sha256=snapshot.sha256,
                size_bytes=snapshot.size_bytes,
                row_count=(
                    prior.row_count
                    if prior is not None
                    else 1
                    if role == "motif_catalog"
                    else None
                ),
                snapshot=snapshot,
            )
        )
    return tuple(sources)


def _reconcile_step09_inputs(
    receipt_row: Mapping[str, str],
    results: ComputationalResults | None,
) -> None:
    if results is None:
        return
    for role, table in (
        ("step09_all_sites", results.all_sites),
        ("step09_significant_sites", results.significant_sites),
        ("step09_summary", results.summary),
    ):
        if (
            Path(receipt_row[f"{role}_path"]) != table.path
            or receipt_row[f"{role}_sha256"] != table.sha256
        ):
            _fail(
                f"Step 10 receipt-bound {role} differs from the admitted Step 09 "
                "report source"
            )


def admit_scientific_context_results(
    summary: Mapping[str, Any],
    *,
    source_root: Path,
    computational_results: ComputationalResults | None,
) -> tuple[ScientificContextResults | None, str | None]:
    """Admit one complete Step 10 transaction or disclose bounded absence."""

    records, unavailable_reason = _select_records(summary)
    if records is None:
        return None, unavailable_reason
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    validation = _validation_table(
        records["validation"], source_root=source_root, analysis_id=analysis_id
    )
    receipt_record = records["receipt"]
    source = receipt_record["source"]
    assert isinstance(source, Mapping)
    receipt_path = _resolve_contract_file(
        source["path"],
        f"scientific-context result {receipt_record['artifact_id']!r}",
        source_root=source_root,
    )
    try:
        transaction = owner_context.validate_scientific_context_transaction(
            receipt_path
        )
    except (owner_context.ContractError, OSError, UnicodeError) as exc:
        _fail(
            f"Primary Step 10 scientific-context transaction failed validation: {exc}"
        )
    receipt = _receipt_table(
        receipt_record,
        transaction=transaction,
        source_root=source_root,
    )
    receipt_row = transaction.receipt.rows[0]
    if receipt_row["analysis_id"] != analysis_id:
        _fail("Primary Step 10 receipt has the wrong analysis_id")
    _reconcile_step09_inputs(receipt_row, computational_results)
    canonical_outputs = transaction.outputs
    output_by_role = {
        "candidate_context": canonical_outputs.candidate_context,
        "motif_hits": canonical_outputs.motif_hits,
        "sequence_logo": canonical_outputs.sequence_logo,
        "motif_statistics": canonical_outputs.motif_statistics,
    }
    tables = {
        role: _canonical_table(
            records[role],
            role=role,
            table_id=table_id,
            title=title,
            expected_header=header,
            display_limit=display_limit,
            canonical=output_by_role[role],
            source_root=source_root,
        )
        for role, _adapter, table_id, title, header, display_limit in _ROLE_SPECS
    }
    bound_inputs = _bound_inputs(receipt_row, computational_results)
    return (
        ScientificContextResults(
            analysis_id=analysis_id,
            validation=validation,
            candidate_context=tables["candidate_context"],
            motif_hits=tables["motif_hits"],
            sequence_logo=tables["sequence_logo"],
            motif_statistics=tables["motif_statistics"],
            receipt=receipt,
            bound_inputs=bound_inputs,
            receipt_metadata=dict(receipt_row),
        ),
        None,
    )
