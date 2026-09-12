"""Receipt-backed Step 10 scientific-context admission for static reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from types import MappingProxyType

from emrys.contracts.scientific_evidence import scientific_context as owner_context

from emrys.reporting import (
    AnalysisReportArtifactV1,
    ReportInputSnapshot as FileSnapshot,
    admit_report_input as _snapshot_regular,
    fail_report_provider as _fail,
    recheck_report_input as _assert_snapshot,
)

from .computational import (
    ComputationalResults,
    ComputationalTable,
    _inspect_validation,
    _source_table,
)


@dataclass(frozen=True)
class ScientificContextResults:
    analysis_id: str
    validation: ComputationalTable
    candidate_context: ComputationalTable
    motif_hits: ComputationalTable
    sequence_logo: ComputationalTable
    motif_statistics: ComputationalTable
    receipt: ComputationalTable
    bound_inputs: tuple[FileSnapshot, ...]
    reference_fasta_path: Path

    @property
    def tables(self) -> tuple[ComputationalTable, ...]:
        return (
            self.validation,
            self.candidate_context,
            self.motif_hits,
            self.sequence_logo,
            self.motif_statistics,
            self.receipt,
        )

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return (
            *(table.snapshot for table in self.tables),
            *self.bound_inputs,
        )


_VALIDATION_ADAPTER = "step10_validation_report_v1"
_ROLE_SPECS = (
    (
        "candidate_context",
        "step10_candidate_context_v1",
        owner_context.CANDIDATE_CONTEXT_HEADER,
        0,
    ),
    (
        "motif_hits",
        "step10_motif_hits_v1",
        owner_context.MOTIF_HITS_HEADER,
        0,
    ),
    (
        "sequence_logo",
        "step10_sequence_logo_v1",
        owner_context.SEQUENCE_LOGO_HEADER,
        len(owner_context.CONTEXT_POPULATIONS)
        * (2 * owner_context.LOGO_RADIUS + 1)
        * 4,
    ),
    (
        "motif_statistics",
        "step10_motif_statistics_v1",
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


def _select_artifacts(
    artifacts: Mapping[str, AnalysisReportArtifactV1],
) -> tuple[dict[str, AnalysisReportArtifactV1] | None, str | None]:
    expected = (
        *((spec[0], spec[1]) for spec in _ROLE_SPECS),
        ("receipt", _RECEIPT_ADAPTER),
        ("validation", _VALIDATION_ADAPTER),
    )
    selected = {
        role: artifacts[adapter] for role, adapter in expected if adapter in artifacts
    }
    if not selected:
        return (
            None,
            "This run predates the Step 10 scientific-context transaction; "
            "the sequence-context and motif-enrichment figures are unavailable. "
            "Selected-candidate editing-rate and location evidence remains "
            "reportable from Step 09, with sequence and registered-motif context "
            "marked not admitted.",
        )
    missing = [adapter for _role, adapter in expected if adapter not in artifacts]
    if missing:
        return (
            None,
            "The complete primary-analysis Step 10 transaction is unavailable, "
            "so the Step 10 sequence-context and motif-enrichment figures were not "
            "inferred. Selected-candidate editing-rate and location evidence can "
            "remain reportable from Step 09, with sequence and registered-motif "
            "context marked not admitted: " + ", ".join(missing) + ".",
        )
    return selected, None


def _receipt_table(
    record: AnalysisReportArtifactV1,
    *,
    transaction: owner_context.ScientificContextTransaction,
) -> ComputationalTable:
    snapshot = record.snapshot
    header = tuple(transaction.receipt.header)
    if (
        snapshot.path != transaction.receipt.path
        or snapshot.sha256 != transaction.receipt_sha256
        or record.row_count != 1
    ):
        _fail("Primary Step 10 receipt record differs from its canonical transaction")
    return ComputationalTable(
        artifact_id=record.artifact_id,
        row_count=1,
        header=header,
        display_rows=tuple(MappingProxyType(row) for row in transaction.receipt.rows),
        snapshot=snapshot,
    )


def _bound_inputs(
    receipt_row: Mapping[str, str],
    computational_results: ComputationalResults | None,
) -> tuple[FileSnapshot, ...]:
    reusable = (
        {
            "step09_all_sites": computational_results.all_sites.snapshot,
            "step09_significant_sites": computational_results.significant_sites.snapshot,
            "step09_summary": computational_results.summary.snapshot,
        }
        if computational_results is not None
        else {}
    )
    sources: list[FileSnapshot] = []
    for role in _BOUND_INPUT_ROLES:
        path = Path(receipt_row[f"{role}_path"])
        prior = reusable.get(role)
        snapshot = (
            prior
            if prior is not None
            and prior.path == path
            and prior.sha256 == receipt_row[f"{role}_sha256"]
            else _snapshot_regular(path, f"scientific-context bound input {role!r}")
        )
        if snapshot.sha256 != receipt_row[f"{role}_sha256"]:
            _fail(f"Scientific-context bound input {role!r} changed after admission")
        sources.append(snapshot)
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
            Path(receipt_row[f"{role}_path"]) != table.snapshot.path
            or receipt_row[f"{role}_sha256"] != table.snapshot.sha256
        ):
            _fail(
                f"Step 10 receipt-bound {role} differs from the admitted Step 09 "
                "report source"
            )


def admit_scientific_context_results(
    summary: Mapping[str, Any],
    artifacts: Mapping[str, AnalysisReportArtifactV1],
    *,
    computational_results: ComputationalResults | None,
) -> tuple[ScientificContextResults | None, str | None]:
    """Admit one complete Step 10 transaction or disclose bounded absence."""

    records, unavailable_reason = _select_artifacts(artifacts)
    if records is None:
        return None, unavailable_reason
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    validation = _inspect_validation(
        records["validation"],
        analysis_id=analysis_id,
        step_id="10",
        check_ids=("scientific_context_transaction",),
    )
    receipt_record = records["receipt"]
    for record in records.values():
        _assert_snapshot(
            record.snapshot, f"scientific-context result {record.artifact_id!r}"
        )
    transaction = receipt_record.projection
    if transaction is None:
        _fail("Primary Step 10 requires its admitted scientific transaction")
    receipt = _receipt_table(
        receipt_record,
        transaction=transaction,
    )
    receipt_row = transaction.receipt.rows[0]
    if receipt_row["analysis_id"] != analysis_id:
        _fail("Primary Step 10 receipt has the wrong analysis_id")
    _reconcile_step09_inputs(receipt_row, computational_results)
    tables = {}
    for role, _adapter, header, display_limit in _ROLE_SPECS:
        record = records[role]
        canonical = getattr(transaction.outputs, role)
        if (record.snapshot.path, record.snapshot.sha256, record.row_count) != (
            canonical.path,
            canonical.sha256,
            canonical.row_count,
        ):
            _fail(f"Primary Step 10 {role} differs from its canonical transaction")
        tables[role] = _source_table(
            record,
            expected_header=header,
            display_limit=display_limit,
        )
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
            reference_fasta_path=Path(receipt_row["reference_fasta_path"]),
        ),
        None,
    )
