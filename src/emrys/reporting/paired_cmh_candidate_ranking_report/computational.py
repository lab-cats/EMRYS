"""Exact Step 09 computational-result admission for static reports."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from types import MappingProxyType

from emrys.contracts.scientific_evidence import step08, step09
from emrys.libraries import validation as owner_validation

from emrys.reporting import (
    AnalysisReportArtifactV1,
    ReportInputSnapshot as FileSnapshot,
    admit_report_input as _snapshot_regular,
    fail_report_provider as _fail,
    recheck_report_input as _assert_snapshot,
    resolve_report_input as _resolve_contract_file,
)


@dataclass(frozen=True)
class ComputationalTable:
    artifact_id: str
    row_count: int
    header: tuple[str, ...]
    display_rows: tuple[Mapping[str, str], ...]
    snapshot: FileSnapshot

    def iter_rows(self) -> Iterator[dict[str, str]]:
        """Stream named rows; callers recheck snapshots around their projection."""
        label = f"computational result {self.artifact_id!r}"
        observed_count = 0
        try:
            with self.snapshot.path.open(encoding="utf-8", newline="") as stream:
                reader = csv.reader(stream, delimiter="\t", strict=True)
                if tuple(next(reader, ())) != self.header:
                    _fail(f"{label} has the wrong header")
                for row_number, values in enumerate(reader, start=2):
                    if not values or all(value == "" for value in values):
                        _fail(f"{label} row {row_number} is blank")
                    if len(values) != len(self.header):
                        _fail(f"{label} row {row_number} has the wrong field count")
                    observed_count += 1
                    yield dict(zip(self.header, values, strict=True))
        except (OSError, UnicodeError, csv.Error) as exc:
            _fail(f"Could not parse {label}: {exc}")
        if observed_count != self.row_count:
            _fail(
                f"{label} row-count mismatch: observed {observed_count}; "
                f"expected {self.row_count}"
            )


@dataclass(frozen=True)
class SamplePair:
    replicate: str
    control_sample_id: str
    treatment_sample_id: str


@dataclass(frozen=True)
class ComputationalSampleManifest:
    sample_ids: tuple[str, ...]
    control_condition: str
    treatment_condition: str
    pairs: tuple[SamplePair, ...]
    snapshot: FileSnapshot


@dataclass(frozen=True)
class ComputationalResults:
    analysis_id: str
    sample_ids: tuple[str, ...]
    validation: ComputationalTable
    all_sites: ComputationalTable
    significant_sites: ComputationalTable
    summary: ComputationalTable
    mutation_spectrum: ComputationalTable
    sample_manifest: ComputationalSampleManifest

    @property
    def tables(self) -> tuple[ComputationalTable, ...]:
        return (
            self.validation,
            self.all_sites,
            self.significant_sites,
            self.summary,
            self.mutation_spectrum,
        )

    @property
    def input_snapshots(self) -> tuple[FileSnapshot, ...]:
        return (
            *(table.snapshot for table in self.tables),
            self.sample_manifest.snapshot,
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
    ("all_sites", "step09_cmh_all_sites_v1"),
    ("significant_sites", "step09_cmh_significant_sites_v1"),
    ("summary", "step09_cmh_summary_v1"),
    ("mutation_spectrum", "step09_mutation_spectrum_tsv_v1"),
)


def _select_artifacts(
    artifacts: Mapping[str, AnalysisReportArtifactV1],
) -> tuple[dict[str, AnalysisReportArtifactV1], str | None]:
    selected = {
        role: artifacts[adapter]
        for role, adapter in _ROLE_SPECS
        if adapter in artifacts
    }
    if _VALIDATION_ADAPTER in artifacts:
        selected["validation"] = artifacts[_VALIDATION_ADAPTER]
    missing = [
        adapter
        for adapter in (
            *(spec[1] for spec in _ROLE_SPECS),
            _VALIDATION_ADAPTER,
        )
        if adapter not in artifacts
    ]
    reason = (
        "The exact primary-analysis Step 09 result trio, mutation spectrum, "
        "and owner-validation artifact are not complete, so no computational "
        "candidate rows were opened or displayed: " + ", ".join(missing) + "."
        if missing
        else None
    )
    return selected, reason


def _inspect_validation(
    record: AnalysisReportArtifactV1,
    *,
    analysis_id: str,
) -> ComputationalTable:
    table = _source_table(
        record,
        display_limit=len(_VALIDATION_CHECK_IDS),
        expected_header=owner_validation.HEADER,
    )
    if record.row_count != len(_VALIDATION_CHECK_IDS) or len(table.display_rows) != len(
        _VALIDATION_CHECK_IDS
    ):
        _fail(
            "Primary Step 09 owner-validation report must contain exactly "
            f"{len(_VALIDATION_CHECK_IDS)} check rows"
        )
    for row_number, (row, expected_check_id) in enumerate(
        zip(table.display_rows, _VALIDATION_CHECK_IDS, strict=True),
        start=2,
    ):
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
    return table


def _admit_source_identity(
    record: AnalysisReportArtifactV1,
) -> FileSnapshot:
    if record.media_type != "text/tab-separated-values":
        _fail(f"Computational result {record.artifact_id!r} must be a TSV source")
    path = record.path
    snapshot = _snapshot_regular(
        path,
        f"computational result {record.artifact_id!r}",
    )
    if snapshot.sha256 != record.sha256:
        _fail(
            f"Computational result {record.artifact_id!r} SHA-256 mismatch: "
            f"observed {snapshot.sha256}; expected {record.sha256}"
        )
    if snapshot.size_bytes != record.size_bytes:
        _fail(
            f"Computational result {record.artifact_id!r} size mismatch: "
            f"observed {snapshot.size_bytes}; expected {record.size_bytes}"
        )
    return snapshot


def _source_table(
    record: AnalysisReportArtifactV1,
    *,
    display_limit: int,
    expected_header: Sequence[str],
    snapshot: FileSnapshot | None = None,
) -> ComputationalTable:
    table = ComputationalTable(
        artifact_id=record.artifact_id,
        row_count=record.row_count,
        header=tuple(expected_header),
        display_rows=(),
        snapshot=snapshot or _admit_source_identity(record),
    )
    displayed = tuple(
        MappingProxyType(row)
        for index, row in enumerate(table.iter_rows())
        if index < display_limit
    )
    _assert_snapshot(table.snapshot, f"computational result {record.artifact_id!r}")
    return replace(table, display_rows=displayed)


def _admit_sample_manifest(
    summary: Mapping[str, Any],
    summary_table: ComputationalTable,
    sample_ids: Sequence[str],
    *,
    source_root: Path,
) -> ComputationalSampleManifest:
    summary_row = summary_table.display_rows[0]
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
    artifacts: Mapping[str, AnalysisReportArtifactV1],
    *,
    source_root: Path,
) -> tuple[ComputationalResults | None, str | None]:
    """Admit the exact primary Step 09 report sources or disclose unavailability."""

    records, unavailable_reason = _select_artifacts(artifacts)
    if unavailable_reason is not None:
        return None, unavailable_reason
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    validation = _inspect_validation(
        records["validation"],
        analysis_id=analysis_id,
    )
    admitted = {
        role: _admit_source_identity(records[role])
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
                admitted["all_sites"].path,
                admitted["significant_sites"].path,
                admitted["summary"].path,
                analysis_id,
                mutation_spectrum=admitted["mutation_spectrum"].path,
            )
        )
    except (step09.ContractError, OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Primary Step 09 projection failed validation: {exc}")

    tables = {}
    for role, canonical, rows in (
        ("all_sites", all_projection, ()),
        ("significant_sites", significant_projection, ()),
        ("summary", summary_projection, tuple(summary_projection.rows)),
    ):
        record = records[role]
        row_count = len(rows) if role == "summary" else canonical.row_count
        if canonical.path != admitted[role].path:
            _fail(
                f"Canonical Step 09 projection selected a different source for {record.artifact_id!r}"
            )
        if row_count != record.row_count:
            _fail(
                f"Computational result {record.artifact_id!r} row-count mismatch: "
                f"observed {row_count}; expected {record.row_count}"
            )
        tables[role] = ComputationalTable(
            artifact_id=record.artifact_id,
            row_count=row_count,
            header=tuple(canonical.header),
            display_rows=tuple(MappingProxyType(row) for row in rows),
            snapshot=admitted[role],
        )
    tables["mutation_spectrum"] = _source_table(
        records["mutation_spectrum"],
        display_limit=len(step09.CANONICAL_MUTATIONS),
        expected_header=step09.STEP09_MUTATION_HEADER,
        snapshot=admitted["mutation_spectrum"],
    )
    for role, table in tables.items():
        _assert_snapshot(
            table.snapshot,
            f"computational result {records[role].artifact_id!r}",
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
