"""Read-only semantic validation of complete reporting transactions.

The lifecycle calls this direct owner after Snakemake exits and again during
inspection. A receipt pathname or hash is never sufficient: current
transactions re-admit the producer checkout, while historical reads
admit the current reader and verify recorded producer identities. Every path
validates its bound inputs and outputs and reconstructs the deterministic
projection where applicable.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import re
import stat
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration import application_model
from emrys.contracts.orchestration.artifact_inventory import report_output_root
from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    SourceCheckoutError,
    admit_artifact_source_root,
    admit_source_checkout,
    attest_source_checkout,
    matching_clean_checkout_head_commit,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
)

TransactionKind = Literal["artifact_index", "run_summary", "html_report"]


class ReportingTransactionError(RuntimeError):
    """A reporting receipt does not prove its complete bound transaction."""


@dataclass(frozen=True, slots=True)
class ValidatedTransaction:
    """The receipt identity returned only after full semantic validation."""

    receipt_path: Path
    receipt_sha256: str
    verified_report_locations: tuple[tuple[str, Path], ...] = ()
    _recheck: Callable[[], None] | None = field(default=None, repr=False, compare=False)


def _no_transaction_fault(_paths: tuple[Path, ...]) -> None:
    return None


@dataclass(frozen=True, slots=True)
class ReceiptValidationOps:
    """Explicit source observation and race seam for focused validation tests."""

    before_final_snapshot: Callable[[tuple[Path, ...]], None] = _no_transaction_fault
    matching_clean_checkout_head_commit: Callable[..., str | None] = (
        matching_clean_checkout_head_commit
    )


DEFAULT_RECEIPT_VALIDATION_OPS = ReceiptValidationOps()


def _predecessor_receipt_ops(ops: ReceiptValidationOps) -> ReceiptValidationOps:
    """Preserve source identity without applying an outer transaction fault."""

    return ReceiptValidationOps(
        matching_clean_checkout_head_commit=(ops.matching_clean_checkout_head_commit),
    )


@dataclass(frozen=True, slots=True)
class _ReceiptSnapshot:
    path: Path
    payload: bytes
    device: int
    inode: int
    mode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _BoundFileSnapshot:
    path: Path
    state: Literal["regular", "missing"]
    device: int | None
    inode: int | None
    mode: int | None
    size_bytes: int | None
    mtime_ns: int | None
    ctime_ns: int | None
    sha256: str | None


@dataclass(frozen=True, slots=True)
class _BoundDirectorySnapshot:
    path: Path
    device: int
    inode: int
    mode: int
    mtime_ns: int
    ctime_ns: int
    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _BoundRosterSnapshot:
    files: tuple[_BoundFileSnapshot, ...]
    directories: tuple[_BoundDirectorySnapshot, ...]


def _snapshot_receipt(path: Path) -> _ReceiptSnapshot:
    if not path.is_absolute():
        raise ReportingTransactionError(f"Reporting receipt must be absolute: {path}")
    try:
        if path.resolve(strict=True) != path:
            raise ReportingTransactionError(
                f"Reporting receipt must be canonical and nonsymlink: {path}"
            )
        payload, before = read_bytes_with_identity(
            path,
            "Reporting receipt",
            nonempty=False,
        )
    except (OSError, ValidationError) as exc:
        raise ReportingTransactionError(
            f"Could not admit reporting receipt {path}: {exc}"
        ) from exc
    return _ReceiptSnapshot(
        path=path,
        payload=payload,
        device=before.st_dev,
        inode=before.st_ino,
        mode=before.st_mode,
        size_bytes=before.st_size,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _bound_file_snapshot(snapshot: _ReceiptSnapshot) -> _BoundFileSnapshot:
    return _BoundFileSnapshot(
        path=snapshot.path,
        state="regular",
        device=snapshot.device,
        inode=snapshot.inode,
        mode=snapshot.mode,
        size_bytes=snapshot.size_bytes,
        mtime_ns=snapshot.mtime_ns,
        ctime_ns=snapshot.ctime_ns,
        sha256=snapshot.sha256,
    )


def _nearest_existing_ancestor(path: Path) -> Path | None:
    """Return the directory whose membership proves ``path`` is absent."""

    try:
        os.lstat(path)
    except FileNotFoundError:
        candidate = path.parent
    except OSError as exc:
        raise ReportingTransactionError(
            f"Could not inspect bound transaction path {path}: {exc}"
        ) from exc
    else:
        return None

    while True:
        try:
            observed = os.lstat(candidate)
        except FileNotFoundError:
            parent = candidate.parent
            if parent == candidate:
                raise ReportingTransactionError(
                    f"Bound transaction path has no existing ancestor: {path}"
                )
            candidate = parent
            continue
        except OSError as exc:
            raise ReportingTransactionError(
                f"Could not inspect bound transaction ancestor {candidate}: {exc}"
            ) from exc
        if not stat.S_ISDIR(observed.st_mode):
            raise ReportingTransactionError(
                "Bound transaction absence traverses a non-directory or symlink: "
                f"{candidate}"
            )
        try:
            if candidate.resolve(strict=True) != candidate:
                raise ReportingTransactionError(
                    f"Bound transaction absence traverses a symlink: {candidate}"
                )
        except OSError as exc:
            raise ReportingTransactionError(
                f"Could not resolve bound transaction ancestor {candidate}: {exc}"
            ) from exc
        return candidate


def _snapshot_bound_file(
    path: Path,
    *,
    hash_content: bool = True,
) -> _BoundFileSnapshot:
    if not path.is_absolute():
        raise ReportingTransactionError(
            f"Bound transaction path must be absolute: {path}"
        )
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportingTransactionError(
            "This platform lacks required O_NOFOLLOW transaction admission"
        )
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        return _BoundFileSnapshot(
            path, "missing", None, None, None, None, None, None, None
        )
    except OSError as exc:
        raise ReportingTransactionError(
            f"Could not admit bound transaction file {path}: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReportingTransactionError(
                f"Bound transaction path is not a regular file: {path}"
            )
        digest = hashlib.sha256() if hash_content else None
        if digest is not None:
            while block := os.read(descriptor, 1024 * 1024):
                digest.update(block)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        lexical_parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise ReportingTransactionError(
            f"Bound transaction parent changed while admitted: {path.parent}"
        ) from exc
    if lexical_parent != path.parent:
        raise ReportingTransactionError(
            f"Bound transaction path traverses a symlink: {path}"
        )
    try:
        current = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ReportingTransactionError(
            f"Bound transaction file changed while admitted: {path}"
        ) from exc
    if _stat_identity(before) != _stat_identity(after) or _stat_identity(after) != (
        _stat_identity(current)
    ):
        raise ReportingTransactionError(
            f"Bound transaction file changed while admitted: {path}"
        )
    return _BoundFileSnapshot(
        path=path,
        state="regular",
        device=before.st_dev,
        inode=before.st_ino,
        mode=before.st_mode,
        size_bytes=before.st_size,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
        sha256=None if digest is None else digest.hexdigest(),
    )


def _snapshot_bound_directory(path: Path) -> _BoundDirectorySnapshot:
    if not path.is_absolute():
        raise ReportingTransactionError(f"Bound directory must be absolute: {path}")
    try:
        entries, before = directory_entries_with_identity(
            path,
            "Bound transaction directory",
        )
    except ValidationError as exc:
        raise ReportingTransactionError(
            f"Could not admit bound transaction directory {path}: {exc}"
        ) from exc
    return _BoundDirectorySnapshot(
        path=path,
        device=before.st_dev,
        inode=before.st_ino,
        mode=before.st_mode,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
        entries=entries,
    )


def _snapshot_bound_roster(
    files: Iterable[Path],
    directories: Iterable[Path] = (),
    *,
    identity_only_files: Iterable[Path] = (),
) -> _BoundRosterSnapshot:
    file_paths = tuple(sorted(set(files), key=os.fspath))
    identity_only_paths = set(identity_only_files)
    absence_anchors_before = {
        path: anchor
        for path in file_paths
        if (anchor := _nearest_existing_ancestor(path)) is not None
    }
    directory_paths = tuple(
        sorted(
            {*directories, *absence_anchors_before.values()},
            key=os.fspath,
        )
    )
    directories_before = tuple(
        _snapshot_bound_directory(path) for path in directory_paths
    )
    snapshots = tuple(
        _snapshot_bound_file(
            path,
            hash_content=path not in identity_only_paths,
        )
        for path in file_paths
    )
    absence_anchors_after = {
        snapshot.path: anchor
        for snapshot in snapshots
        if snapshot.state == "missing"
        if (anchor := _nearest_existing_ancestor(snapshot.path)) is not None
    }
    if absence_anchors_after != absence_anchors_before:
        raise ReportingTransactionError(
            "Bound transaction absence membership changed during admission"
        )
    directories_after = tuple(
        _snapshot_bound_directory(path) for path in directory_paths
    )
    if directories_after != directories_before:
        raise ReportingTransactionError(
            "Bound transaction directory membership changed during admission"
        )
    return _BoundRosterSnapshot(files=snapshots, directories=directories_before)


def _receipt_is_in_roster(
    receipt: _ReceiptSnapshot,
    roster: _BoundRosterSnapshot,
) -> bool:
    expected = next((item for item in roster.files if item.path == receipt.path), None)
    return expected == _bound_file_snapshot(receipt)


def _admit_authorities(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
) -> tuple[SourceCheckout, ArtifactSourceRoot]:
    return (
        admit_source_checkout(
            root=source_checkout,
            package_root=Path(__file__).resolve().parents[1],
        ),
        admit_artifact_source_root(root=artifact_source_root),
    )


def _validated_result(
    receipt: _ReceiptSnapshot,
    roster: _BoundRosterSnapshot,
    ops: ReceiptValidationOps,
    reject_control_residue: Callable[[], None],
    *,
    identity_only_paths: Iterable[Path] = (),
    reusable_expandable_directories: Iterable[Path] = (),
    verified_report_locations: tuple[tuple[str, Path], ...] = (),
) -> ValidatedTransaction:
    if not _receipt_is_in_roster(receipt, roster):
        raise ReportingTransactionError(
            f"Reporting receipt changed before roster admission: {receipt.path}"
        )
    paths = tuple(item.path for item in roster.files)
    ops.before_final_snapshot(paths)
    identity_only = frozenset(identity_only_paths)
    expandable = frozenset(reusable_expandable_directories)

    def recheck() -> None:
        reject_control_residue()
        _recheck_bound_roster(
            roster,
            identity_only_paths=identity_only,
            expandable_directory_paths=expandable,
        )

    recheck()
    return ValidatedTransaction(
        receipt_path=receipt.path,
        receipt_sha256=receipt.sha256,
        verified_report_locations=verified_report_locations,
        _recheck=recheck,
    )


def _recheck_bound_roster(
    roster: _BoundRosterSnapshot,
    *,
    identity_only_paths: Iterable[Path] = (),
    expandable_directory_paths: Iterable[Path] = (),
) -> None:
    """Require an admitted transaction roster to retain the same identities."""

    identity_only = set(identity_only_paths)
    observed = _snapshot_bound_roster(
        (item.path for item in roster.files),
        (item.path for item in roster.directories),
        identity_only_files=identity_only,
    )
    files_match = len(observed.files) == len(roster.files) and all(
        (
            before.path,
            before.state,
            before.device,
            before.inode,
            before.mode,
            before.size_bytes,
            before.mtime_ns,
            before.ctime_ns,
        )
        == (
            after.path,
            after.state,
            after.device,
            after.inode,
            after.mode,
            after.size_bytes,
            after.mtime_ns,
            after.ctime_ns,
        )
        and (before.path in identity_only or before.sha256 == after.sha256)
        for before, after in zip(roster.files, observed.files, strict=True)
    )
    expandable = set(expandable_directory_paths)
    directories_match = len(observed.directories) == len(roster.directories) and all(
        before == after
        if before.path not in expandable
        else (before.path, before.device, before.inode, before.mode)
        == (after.path, after.device, after.inode, after.mode)
        for before, after in zip(
            roster.directories, observed.directories, strict=True
        )
    )
    if not files_match or not directories_match:
        raise ReportingTransactionError(
            "Reporting transaction roster changed during semantic validation"
        )


def recheck_run_summary_inputs(context: Any) -> None:
    """Revalidate all bound run-summary input snapshots."""

    from emrys.reporting._run_summary.inputs import (
        _verify_file_snapshot,
    )
    from emrys.reporting._run_summary.transaction import (
        _assert_output_directory_identity,
    )

    _assert_output_directory_identity(context.paths)
    for snapshot in context.input_snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)


def _contract_path(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path(os.path.abspath(root / path))


def _artifact_record_bound_paths(
    records: Iterable[Mapping[str, Any]],
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    include_implementation_evidence: bool = True,
) -> set[Path]:
    paths: set[Path] = set()
    for record in records:
        expectation = record.get("expectation")
        if isinstance(expectation, Mapping):
            source_path = expectation.get("source_path")
            if isinstance(source_path, str) and source_path:
                paths.add(_contract_path(source_path, artifact_source_root))
        if not include_implementation_evidence:
            continue
        implementation = record.get("implementation")
        if not isinstance(implementation, Mapping):
            continue
        evidence = implementation.get("evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, Mapping):
                continue
            evidence_path = item.get("path")
            if isinstance(evidence_path, str) and evidence_path:
                paths.add(_contract_path(evidence_path, source_checkout))
    return paths


_CONTROL_TOKEN = r"[1-9][0-9]*-[0-9a-f]{32}"


def _reject_reporting_control_residue(
    *,
    kind: TransactionKind,
    output_dir: Path,
    run_id: str,
    output_names: Iterable[str] = (),
) -> None:
    """Reject owner-known lock, staging, backup, and recovery names."""

    entries = _snapshot_bound_directory(output_dir).entries
    escaped_run_id = re.escape(run_id)
    if kind == "artifact_index":
        exact = {f".{run_id}.artifact-index.lock"}
        patterns = (
            re.compile(
                rf"\.artifact-index\.{_CONTROL_TOKEN}\."
                r"(?:tmp\.records|tmp\.tsv|previous\.records|previous\.tsv|"
                r"RECOVERY\.txt)"
            ),
            re.compile(
                rf"\.artifact-receipt\.{_CONTROL_TOKEN}\."
                r"(?:tmp|previous)\.tsv"
            ),
        )
    elif kind == "run_summary":
        exact = {f".{run_id}.run-summary.lock"}
        patterns = (
            re.compile(
                rf"\.{escaped_run_id}\.run-summary\.{_CONTROL_TOKEN}\."
                r"RECOVERY\.txt"
            ),
            *(
                re.compile(
                    rf"\.{re.escape(name)}\.{_CONTROL_TOKEN}\."
                    r"(?:tmp|previous)"
                )
                for name in output_names
            ),
        )
    else:
        exact = {f".{run_id}.report.lock"}
        patterns = (
            re.compile(rf"\.run-report\.{_CONTROL_TOKEN}\.tmp"),
            re.compile(rf"\.{escaped_run_id}\.report\.{_CONTROL_TOKEN}\.RECOVERY\.txt"),
            *(
                re.compile(rf"\.{re.escape(name)}\.{_CONTROL_TOKEN}\.previous")
                for name in output_names
            ),
        )
    residue = sorted(
        name
        for name in entries
        if name in exact or any(pattern.fullmatch(name) for pattern in patterns)
    )
    if residue:
        raise ReportingTransactionError(
            f"{kind} transaction retains owner control residue: " + ", ".join(residue)
        )


def _artifact_context_roster(context: Any) -> _BoundRosterSnapshot:
    record_paths = {
        context.records_dir / f"{record['artifact_id']}.json"
        for record in context.records
    }
    files = {
        context.run_contract_path,
        context.inventory_path,
        context.artifacts_path,
        context.receipt_path,
        *record_paths,
        *(inspection.resolved_path for inspection in context.inspections),
        *_artifact_record_bound_paths(
            context.records,
            source_checkout=context.source_checkout.root,
            artifact_source_root=context.artifact_source_root.root,
        ),
    }
    return _snapshot_bound_roster(
        files,
        (context.output_dir, context.records_dir),
    )


def _summary_context_roster(
    context: Any,
    *,
    include_implementation_evidence: bool = True,
) -> _BoundRosterSnapshot:
    files = {
        *(snapshot.path for snapshot in context.input_snapshots),
        context.paths.summary_json,
        context.paths.summary_tsv,
        context.paths.qc_summary,
        context.paths.receipt,
        *_artifact_record_bound_paths(
            context.artifacts,
            source_checkout=context.source_checkout.root,
            artifact_source_root=context.artifact_source_root.root,
            include_implementation_evidence=include_implementation_evidence,
        ),
    }
    return _snapshot_bound_roster(
        files,
        (context.paths.output_dir, context.records_dir),
    )


def _report_roster(
    summary: Mapping[str, Any],
    *,
    run_summary_path: Path,
    output_dir: Path,
    output_paths: Iterable[Path],
    report_receipt: Path,
    source_checkout: Path,
    artifact_source_root: Path,
    input_paths: Iterable[Path] = (),
    include_implementation_evidence: bool = True,
    expected_run_contract: Path | None = None,
    expected_inventory: Path | None = None,
) -> _BoundRosterSnapshot:
    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index.models import ARTIFACT_RECEIPT_HEADER

    run_id = str(summary["run_id"])
    summary_dir = run_summary_path.parent
    artifact_receipt = summary_dir / f"{run_id}.artifact_receipt.tsv"
    if Path(str(summary["artifact_receipt"]["path"])) != artifact_receipt:
        raise ReportingTransactionError(
            "Run summary binds a noncanonical artifact receipt path"
        )
    receipt_row = artifact_api.read_exact_tsv(
        artifact_receipt,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    artifact_index = summary_dir / f"{run_id}.artifacts.tsv"
    records_dir = summary_dir / "records"
    record_paths = {
        records_dir / f"{record['artifact_id']}.json" for record in summary["artifacts"]
    }
    run_contract = expected_run_contract or Path(receipt_row["run_contract_path"])
    inventory = expected_inventory or Path(receipt_row["inventory_path"])
    analysis_policy = summary.get("analysis_policy")
    files = {
        *input_paths,
        run_summary_path,
        *(() if analysis_policy is None else (Path(analysis_policy["path"]),)),
        *output_paths,
        report_receipt,
        summary_dir / f"{run_id}.run_summary.tsv",
        summary_dir / f"{run_id}.qc_summary.tsv",
        summary_dir / f"{run_id}.run_summary_receipt.tsv",
        artifact_receipt,
        run_contract,
        inventory,
        artifact_index,
        *record_paths,
        *_artifact_record_bound_paths(
            summary["artifacts"],
            source_checkout=source_checkout,
            artifact_source_root=artifact_source_root,
            include_implementation_evidence=include_implementation_evidence,
        ),
    }
    return _snapshot_bound_roster(
        files,
        (output_dir, records_dir, summary_dir),
    )


def _validate_historical_artifact_index_transaction(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    run_id: str,
    run_contract: Path,
    inventory: Path,
    output_root: Path,
    receipt_ops: ReceiptValidationOps = DEFAULT_RECEIPT_VALIDATION_OPS,
) -> ValidatedTransaction:
    """Validate an immutable artifact ledger without today's producer registry."""

    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import records as artifact_records
    from emrys.reporting._artifact_index.models import (
        ARTIFACT_INDEX_HEADER,
        ARTIFACT_RECEIPT_HEADER,
    )
    from emrys.reporting._artifact_index.validation import (
        validate_published_transaction,
    )

    output_dir = output_root / run_id
    records_dir = output_dir / "records"
    artifacts_path = output_dir / f"{run_id}.artifacts.tsv"
    receipt_path = output_dir / f"{run_id}.artifact_receipt.tsv"
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="artifact_index",
        output_dir=output_dir,
        run_id=run_id,
    )
    reject_control_residue()
    receipt_snapshot = _snapshot_receipt(receipt_path)
    _checkout, source_root = _admit_authorities(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )
    run_contract_snapshot = _snapshot_receipt(run_contract)
    inventory_snapshot = _snapshot_receipt(inventory)
    artifacts_snapshot = _snapshot_receipt(artifacts_path)
    receipt_row = artifact_records.read_exact_tsv_bytes(
        receipt_snapshot.payload,
        receipt_path,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    for field, expected in (
        ("run_contract_path", run_contract),
        ("inventory_path", inventory),
        ("artifacts_index_path", artifacts_path),
    ):
        if Path(receipt_row[field]) != expected:
            raise ReportingTransactionError(
                f"Historical artifact receipt binds a noncanonical {field}"
            )

    admitted_run_contract = artifact_contracts.load_json_object_bytes(
        run_contract_snapshot.payload,
        f"historical run contract {run_contract}",
    )
    run_contract_document, run_contract_sha256 = artifact_api.load_run_contract(
        run_contract
    )
    if (
        run_contract_document != admitted_run_contract
        or run_contract_sha256 != run_contract_snapshot.sha256
    ):
        raise ReportingTransactionError(
            "Historical run contract changed during ledger admission"
        )
    admitted_inventory_rows = artifact_records.read_exact_tsv_bytes(
        inventory_snapshot.payload,
        inventory,
        artifact_contracts.INVENTORY_HEADER,
    )
    inventory_rows = artifact_contracts.validate_inventory(
        inventory,
        source_root=source_root.root,
    )
    if inventory_rows != admitted_inventory_rows:
        raise ReportingTransactionError(
            "Historical inventory changed during ledger admission"
        )
    run_contract_document = admitted_run_contract
    inventory_rows = admitted_inventory_rows
    record_paths = {
        records_dir / f"{row['artifact_id']}.json" for row in inventory_rows
    }
    record_snapshots = tuple(
        _snapshot_receipt(path) for path in sorted(record_paths, key=os.fspath)
    )
    records = tuple(
        artifact_contracts.load_json_object_bytes(
            snapshot.payload,
            f"artifact record {snapshot.path.stem} {snapshot.path}",
        )
        for snapshot in record_snapshots
    )
    native_roster = _snapshot_bound_roster(
        {
            _contract_path(row["source_path"], source_root.root)
            for row in inventory_rows
        },
        (output_dir, records_dir),
    )
    files_by_path = {snapshot.path: snapshot for snapshot in native_roster.files}
    for snapshot in (
        receipt_snapshot,
        run_contract_snapshot,
        inventory_snapshot,
        artifacts_snapshot,
        *record_snapshots,
    ):
        bound = _bound_file_snapshot(snapshot)
        previous = files_by_path.setdefault(bound.path, bound)
        if previous != bound:
            raise ReportingTransactionError(
                f"Historical ledger path has conflicting identities: {bound.path}"
            )
    roster = _BoundRosterSnapshot(
        files=tuple(
            sorted(files_by_path.values(), key=lambda item: os.fspath(item.path))
        ),
        directories=native_roster.directories,
    )
    admitted_bytes = {
        snapshot.path: snapshot.payload
        for snapshot in (receipt_snapshot, artifacts_snapshot, *record_snapshots)
    }
    validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract_document,
        run_contract_path=run_contract,
        run_contract_file_sha256=run_contract_sha256,
        inventory_path=inventory,
        inventory_sha256=inventory_snapshot.sha256,
        inventory_rows=inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        require_current_source_locations=True,
        source_root=source_root.root,
        admitted_bytes=admitted_bytes,
    )
    snapshots = {snapshot.path: snapshot for snapshot in roster.files}
    recorded_commit = receipt_row["git_commit"]
    for record in records:
        provenance = record["provenance"]
        implementation = record["implementation"]
        if (
            provenance["producer"] != receipt_row["producer"]
            or provenance["producer_version"] != receipt_row["producer_version"]
            or provenance["git_commit"] != recorded_commit
            or implementation["git_commit"] != recorded_commit
        ):
            raise ReportingTransactionError(
                "Historical artifact record differs from its recorded producer identity: "
                f"{record['artifact_id']}"
            )
        source = record.get("source")
        source_path = _contract_path(
            record["expectation"]["source_path"],
            source_root.root,
        )
        snapshot = snapshots[source_path]
        if source is None:
            if snapshot.state != "missing":
                raise ReportingTransactionError(
                    "Historical artifact source appeared after publication: "
                    f"{record['artifact_id']}"
                )
        elif (
            snapshot.state != "regular"
            or snapshot.sha256 != source["sha256"]
            or snapshot.size_bytes != source["size_bytes"]
        ):
            raise ReportingTransactionError(
                "Historical artifact source differs from its recorded identity: "
                f"{record['artifact_id']}"
            )
    return _validated_result(
        receipt_snapshot,
        roster,
        receipt_ops,
        reject_control_residue,
        reusable_expandable_directories=(output_dir,),
    )


def validate_artifact_index_transaction(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    run_id: str,
    run_contract: Path,
    inventory: Path,
    output_root: Path,
    analysis_policy: Path | None = None,
    profile: Mapping[str, Any] | None = None,
    receipt_ops: ReceiptValidationOps = DEFAULT_RECEIPT_VALIDATION_OPS,
) -> ValidatedTransaction:
    """Revalidate one artifact index plus current native artifact sources."""

    output_dir = output_root / run_id
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="artifact_index",
        output_dir=output_dir,
        run_id=run_id,
    )
    reject_control_residue()
    receipt_snapshot = _snapshot_receipt(output_dir / f"{run_id}.artifact_receipt.tsv")

    from emrys.reporting._artifact_index import context as artifact_context
    from emrys.reporting._artifact_index import records as artifact_records
    from emrys.reporting._artifact_index.validation import (  # noqa: PLC0415
        validate_published_transaction,
    )

    checkout, source_root = _admit_authorities(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )
    arguments = argparse.Namespace(
        run_id=run_id,
        run_contract=run_contract,
        analysis_policy=analysis_policy,
        profile=profile,
        inventory=inventory,
        output_root=output_root,
        execute=False,
    )
    context = artifact_context.prepare_context(
        arguments,
        source_checkout=checkout,
        artifact_source_root=source_root,
        identity_ops=artifact_context.ArtifactIdentityOps(
            matching_clean_checkout_head_commit=(
                receipt_ops.matching_clean_checkout_head_commit
            ),
        ),
    )
    if context.previous_receipt is None:
        raise ReportingTransactionError(
            f"Artifact-index transaction is absent: {context.receipt_path}"
        )
    admitted_receipt = artifact_records.tsv_bytes(
        artifact_context.ARTIFACT_RECEIPT_HEADER,
        [context.previous_receipt],
    )
    if admitted_receipt != receipt_snapshot.payload:
        raise ReportingTransactionError(
            "Artifact-index semantic validation admitted a different receipt"
        )
    roster = _artifact_context_roster(context)
    validate_published_transaction(
        run_id=context.run_id,
        run_contract=context.run_contract,
        run_contract_path=context.run_contract_path,
        run_contract_file_sha256=context.run_contract_file_sha256,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_rows=context.inventory_rows,
        records_dir=context.records_dir,
        artifacts_path=context.artifacts_path,
        receipt_path=context.receipt_path,
        require_current_source_locations=True,
        source_root=context.artifact_source_root.root,
    )

    reconstructed: list[dict[str, Any]] = []
    reconstructed_bytes: list[bytes] = []
    for regenerated in context.records:
        current = copy.deepcopy(regenerated)
        path = context.records_dir / f"{current['artifact_id']}.json"
        existing = artifact_contracts.load_json_object(
            path,
            f"published artifact record {current['artifact_id']}",
        )
        # created_at identifies the original index projection, not native
        # scientific content. Reusing it makes every other regenerated field
        # and byte deterministic for an exact comparison.
        current["provenance"]["created_at"] = existing["provenance"]["created_at"]
        if current != existing:
            raise ReportingTransactionError(
                "Published artifact record differs from current declared source: "
                f"{current['artifact_id']}"
            )
        payload = artifact_context.canonical_json_bytes(current)
        if path.read_bytes() != payload:
            raise ReportingTransactionError(
                f"Published artifact record is not canonical: {path}"
            )
        reconstructed.append(current)
        reconstructed_bytes.append(payload)
    expected_rows = artifact_records.build_index_rows(
        records=reconstructed,
        record_bytes=reconstructed_bytes,
        records_dir=context.records_dir,
    )
    expected_index = artifact_records.tsv_bytes(
        artifact_context.ARTIFACT_INDEX_HEADER,
        expected_rows,
    )
    if context.artifacts_path.read_bytes() != expected_index:
        raise ReportingTransactionError(
            "Published artifact index differs from current reconstructed records"
        )
    artifact_context.recheck_inputs(context)
    if context.receipt_path != receipt_snapshot.path:
        raise ReportingTransactionError(
            "Artifact-index context selected a different receipt path"
        )
    return _validated_result(
        receipt_snapshot,
        roster,
        receipt_ops,
        reject_control_residue,
        reusable_expandable_directories=(context.output_dir,),
    )


def validate_run_summary_transaction(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    run_id: str,
    artifact_receipt: Path,
    output_root: Path,
    receipt_ops: ReceiptValidationOps = DEFAULT_RECEIPT_VALIDATION_OPS,
    recorded_producer_commit: str | None = None,
    expected_run_contract: Path | None = None,
    expected_inventory: Path | None = None,
    analysis_policy: Path | None = None,
    profile: Mapping[str, Any] | None = None,
    validate_upstream: bool = True,
) -> ValidatedTransaction:
    """Revalidate one run summary and its bound transaction inputs.

    A historical report reader may supply the producer identity already bound
    by the admitted run-summary ledger. Current callers derive that identity
    from the executing checkout as before.
    """

    historical_read = any(
        value is not None
        for value in (
            recorded_producer_commit,
            expected_run_contract,
            expected_inventory,
        )
    )
    if historical_read and (
        expected_run_contract is None or expected_inventory is None
    ):
        raise ReportingTransactionError(
            "Historical run-summary admission requires fixed contract inputs"
        )
    output_dir = output_root / run_id
    output_names = (
        f"{run_id}.run_summary.json",
        f"{run_id}.run_summary.tsv",
        f"{run_id}.qc_summary.tsv",
        f"{run_id}.run_summary_receipt.tsv",
    )
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="run_summary",
        output_dir=output_dir,
        run_id=run_id,
        output_names=output_names,
    )
    reject_control_residue()
    receipt_snapshot = _snapshot_receipt(
        output_dir / f"{run_id}.run_summary_receipt.tsv"
    )

    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import records as artifact_records
    from emrys.reporting._run_summary import builder as summary_builder
    from emrys.reporting._run_summary.models import RUN_SUMMARY_RECEIPT_HEADER

    if historical_read and recorded_producer_commit is None:
        transaction = artifact_records.read_exact_tsv_bytes(
            receipt_snapshot.payload,
            receipt_snapshot.path,
            RUN_SUMMARY_RECEIPT_HEADER,
            exact_rows=1,
        )[0]
        recorded_producer_commit = str(transaction["git_commit"])

    checkout, source_root = _admit_authorities(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )
    arguments = argparse.Namespace(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        run_id=run_id,
        artifact_receipt=artifact_receipt,
        analysis_policy=analysis_policy,
        output_root=output_root,
        expected_run_contract_path=expected_run_contract,
        expected_inventory_path=expected_inventory,
        execute=False,
    )
    build_deps = summary_builder.DEFAULT_RUN_SUMMARY_BUILD_DEPS
    if recorded_producer_commit is not None:
        build_deps = summary_builder.RunSummaryBuildDeps(
            matching_checkout_head_commit=(lambda **_kwargs: recorded_producer_commit),
        )
    context = summary_builder.prepare_context(
        arguments,
        source_checkout=checkout,
        artifact_source_root=source_root,
        deps=build_deps,
    )
    if context.previous_receipt is None:
        raise ReportingTransactionError(
            f"Run-summary transaction is absent: {context.paths.receipt}"
        )
    admitted_receipt = artifact_api.tsv_bytes(
        RUN_SUMMARY_RECEIPT_HEADER,
        [context.previous_receipt],
    )
    if admitted_receipt != receipt_snapshot.payload:
        raise ReportingTransactionError(
            "Run-summary semantic validation admitted a different receipt"
        )
    roster = _summary_context_roster(
        context,
        include_implementation_evidence=not historical_read,
    )
    if validate_upstream:
        artifact_validator = (
            _validate_historical_artifact_index_transaction
            if historical_read
            else validate_artifact_index_transaction
        )
        artifact_options: dict[str, Any] = {
            "source_checkout": source_checkout,
            "artifact_source_root": source_root.root,
            "run_id": run_id,
            "run_contract": context.run_contract_path,
            "inventory": context.inventory_path,
            "output_root": output_root,
            "receipt_ops": _predecessor_receipt_ops(receipt_ops),
        }
        if not historical_read:
            artifact_options["profile"] = profile
            if context.analysis_policy_path is not None:
                artifact_options["analysis_policy"] = context.analysis_policy_path
        artifact_validator(
            **artifact_options,
        )
    recheck_run_summary_inputs(context)
    for path, expected, label in (
        (context.paths.summary_json, context.summary_json_bytes, "JSON"),
        (context.paths.summary_tsv, context.summary_tsv_bytes, "TSV"),
        (context.paths.qc_summary, context.qc_summary_bytes, "QC TSV"),
    ):
        if path.read_bytes() != expected:
            raise ReportingTransactionError(
                f"Published run-summary {label} differs from current projection: {path}"
            )
    if context.paths.receipt != receipt_snapshot.path:
        raise ReportingTransactionError(
            "Run-summary context selected a different receipt path"
        )
    return _validated_result(
        receipt_snapshot,
        roster,
        receipt_ops,
        reject_control_residue,
    )


def validate_report_transaction(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    run_summary: Path,
    output_root: Path,
    receipt_ops: ReceiptValidationOps = DEFAULT_RECEIPT_VALIDATION_OPS,
    analysis_policy: Path | None = None,
    profile: Mapping[str, Any] | None = None,
    validate_upstream: bool = True,
) -> ValidatedTransaction:
    """Revalidate both HTML views, TSV, receipt, and bound inputs."""

    from emrys.reporting import report
    from emrys.reporting._run_report import context as report_context
    from emrys.reporting._run_report import receipt, validation

    summary = artifact_contracts.load_json_object(run_summary, "run summary")
    run_id = str(summary.get("run_id", ""))
    if analysis_policy is None and summary.get("analysis_policy") is not None:
        analysis_policy = Path(str(summary["analysis_policy"]["path"]))
        if not analysis_policy.is_absolute():
            analysis_policy = artifact_source_root / analysis_policy
    output_dir = output_root / run_id
    output_names = (
        f"{run_id}.scientific_report.html",
        f"{run_id}.evidence_report.html",
        f"{run_id}.run_summary.tsv",
        f"{run_id}.report_outputs.tsv",
    )
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="html_report",
        output_dir=output_dir,
        run_id=run_id,
        output_names=output_names,
    )
    reject_control_residue()
    receipt_snapshot = _snapshot_receipt(output_dir / f"{run_id}.report_outputs.tsv")
    try:
        context = report.prepare_report(
            argparse.Namespace(
                source_checkout=source_checkout,
                artifact_source_root=artifact_source_root,
                run_summary=run_summary,
                analysis_policy=analysis_policy,
                output_root=output_root,
                execute=False,
            )
        )
    except report.ReportRenderError as exc:
        raise ReportingTransactionError(
            f"Report transaction failed semantic validation: {exc}"
        ) from exc
    if not context.previous_snapshots:
        raise ReportingTransactionError(
            f"Report transaction is absent: {context.output_receipt}"
        )
    roster = _report_roster(
        context.summary,
        run_summary_path=context.run_summary_path,
        output_dir=context.output_dir,
        output_paths=(
            context.output_scientific_html,
            context.output_evidence_html,
            context.output_summary_tsv,
        ),
        report_receipt=context.output_receipt,
        source_checkout=context.source_checkout.root,
        artifact_source_root=context.artifact_source_root.root,
        input_paths=(snapshot.path for snapshot in context.input_snapshots),
    )
    if validate_upstream:
        artifact_receipt = Path(str(context.summary["artifact_receipt"]["path"]))
        validate_run_summary_transaction(
            source_checkout=source_checkout,
            artifact_source_root=artifact_source_root,
            run_id=run_id,
            artifact_receipt=artifact_receipt,
            output_root=artifact_receipt.parent.parent,
            analysis_policy=analysis_policy,
            profile=profile,
            receipt_ops=_predecessor_receipt_ops(receipt_ops),
        )
    admitted_snapshot = context.previous_snapshots.get(context.output_receipt)
    if admitted_snapshot is None or (
        admitted_snapshot.path != receipt_snapshot.path
        or admitted_snapshot.sha256 != receipt_snapshot.sha256
        or admitted_snapshot.device != receipt_snapshot.device
        or admitted_snapshot.inode != receipt_snapshot.inode
        or admitted_snapshot.size_bytes != receipt_snapshot.size_bytes
        or admitted_snapshot.mtime_ns != receipt_snapshot.mtime_ns
        or admitted_snapshot.ctime_ns != receipt_snapshot.ctime_ns
    ):
        raise ReportingTransactionError(
            "Report semantic validation admitted a different receipt"
        )
    if context.output_scientific_html.read_bytes() != context.scientific_html_bytes:
        raise ReportingTransactionError(
            "Published scientific HTML differs from the current deterministic "
            "projection"
        )
    if context.output_evidence_html.read_bytes() != context.evidence_html_bytes:
        raise ReportingTransactionError(
            "Published evidence HTML differs from the current deterministic projection"
        )
    expected_summary = receipt.summary_tsv_bytes(context)
    if context.output_summary_tsv.read_bytes() != expected_summary:
        raise ReportingTransactionError(
            "Published report summary TSV differs from the current projection"
        )
    document = receipt.read_receipt_tsv(context.output_receipt)
    expected_document = receipt.receipt_document(
        context,
        (
            (
                "scientific-report-html",
                "scientific_html",
                context.output_scientific_html,
                context.output_scientific_html,
            ),
            (
                "evidence-report-html",
                "evidence_html",
                context.output_evidence_html,
                context.output_evidence_html,
            ),
            (
                "run-summary-tsv",
                "run_summary_tsv",
                context.output_summary_tsv,
                context.output_summary_tsv,
            ),
        ),
    )
    if document != expected_document:
        raise ReportingTransactionError(
            "Published report receipt differs from the current projection"
        )
    verified_report_locations = tuple(
        (str(output["output_id"]), Path(str(output["path"])))
        for output in document["outputs"]
        if output["output_id"] in {"scientific-report-html", "evidence-report-html"}
    )
    if tuple(output_id for output_id, _path in verified_report_locations) != (
        "scientific-report-html",
        "evidence-report-html",
    ):
        raise ReportingTransactionError(
            "Published report receipt does not identify both verified HTML outputs"
        )
    validation.validate_rendered_html(
        context.output_scientific_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity=report_context.expected_html_identity(
            context,
            "scientific",
        ),
    )
    validation.validate_rendered_html(
        context.output_evidence_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity=report_context.expected_html_identity(context, "evidence"),
    )
    receipt.validate_summary_tsv(context.output_summary_tsv, context)
    if context.output_receipt != receipt_snapshot.path:
        raise ReportingTransactionError(
            "Report context selected a different receipt path"
        )
    return _validated_result(
        receipt_snapshot,
        roster,
        receipt_ops,
        reject_control_residue,
        identity_only_paths=(
            snapshot.path
            for snapshot, _label, rehash_content in context.input_rechecks
            if not rehash_content
        ),
        verified_report_locations=verified_report_locations,
    )


def _validate_historical_report_transaction(
    *,
    source_checkout: Path,
    artifact_source_root: Path,
    run_id: str,
    run_summary: Path,
    output_root: Path,
    expected_source_commit: str,
    expected_run_contract: Path,
    expected_inventory: Path,
    analysis_policy: Path | None = None,
    receipt_ops: ReceiptValidationOps = DEFAULT_RECEIPT_VALIDATION_OPS,
    validate_upstream: bool = True,
) -> ValidatedTransaction:
    """Admit a ledger-bound legacy report without re-rendering it as current."""

    from emrys.reporting import ReportProviderError
    from emrys.reporting._run_report.inputs import _load_run_summary
    from emrys.reporting._run_report import receipt
    from emrys.reporting._run_report.models import (
        HISTORICAL_REPORT_RECEIPT_SCHEMA_VERSION,
        HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION,
        PRODUCER,
        REPORT_RECEIPT_SCHEMA_VERSION,
        RUN_SUMMARY_SCHEMA_VERSION,
    )

    if not artifact_contracts.SAFE_ID_RE.fullmatch(run_id):
        raise ReportingTransactionError("Historical report Run ID is invalid")
    expected_summary_name = f"{run_id}.run_summary.json"
    if run_summary.name != expected_summary_name or run_summary.parent.name != run_id:
        raise ReportingTransactionError(
            "Historical report requires the fixed Run-summary path"
        )
    summary_snapshot = _snapshot_receipt(run_summary)
    summary = artifact_contracts.load_json_object_bytes(
        summary_snapshot.payload,
        "run summary",
    )
    if str(summary.get("run_id", "")) != run_id:
        raise ReportingTransactionError(
            "Historical report Run summary binds another Run"
        )
    if analysis_policy is None and summary.get("analysis_policy") is not None:
        analysis_policy = Path(str(summary["analysis_policy"]["path"]))
        if not analysis_policy.is_absolute():
            analysis_policy = artifact_source_root / analysis_policy
    output_dir = output_root / run_id
    output_names = (
        f"{run_id}.scientific_report.html",
        f"{run_id}.evidence_report.html",
        f"{run_id}.run_summary.tsv",
        f"{run_id}.report_outputs.tsv",
    )
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="html_report",
        output_dir=output_dir,
        run_id=run_id,
        output_names=output_names,
    )
    reject_control_residue()
    receipt_path = output_dir / output_names[-1]
    receipt_snapshot = _snapshot_receipt(receipt_path)
    try:
        summary = _load_run_summary(
            run_summary,
            source_root=artifact_source_root,
        )
        document = receipt.read_receipt_tsv(receipt_path)
    except ReportProviderError as exc:
        raise ReportingTransactionError(
            f"Historical report receipt failed validation: {exc}"
        ) from exc
    if _snapshot_receipt(run_summary) != summary_snapshot:
        raise ReportingTransactionError(
            "Historical report Run summary changed during admission"
        )
    if (
        summary["schema_version"],
        document["schema_version"],
    ) not in {
        (
            HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION,
            HISTORICAL_REPORT_RECEIPT_SCHEMA_VERSION,
        ),
        (RUN_SUMMARY_SCHEMA_VERSION, REPORT_RECEIPT_SCHEMA_VERSION),
    }:
        raise ReportingTransactionError(
            "Historical report receipt and Run-summary versions do not match"
        )
    if document["run_id"] != run_id:
        raise ReportingTransactionError("Historical report receipt binds another Run")
    if (
        document["provenance"]["producer"] != PRODUCER
        or document["provenance"]["git_commit"] != expected_source_commit
    ):
        raise ReportingTransactionError(
            "Historical report receipt does not bind its recorded producer identity"
        )
    summary_binding = document["input_run_summary"]
    if Path(summary_binding["path"]) != run_summary:
        raise ReportingTransactionError(
            "Historical report receipt binds another run summary"
        )
    expected_outputs = {
        "scientific-report-html": output_dir / output_names[0],
        "evidence-report-html": output_dir / output_names[1],
        "run-summary-tsv": output_dir / output_names[2],
    }
    if any(
        Path(output["path"]) != expected_outputs[output["output_id"]]
        for output in document["outputs"]
    ):
        raise ReportingTransactionError(
            "Historical report receipt binds a noncanonical output path"
        )
    roster = _report_roster(
        summary,
        run_summary_path=run_summary,
        output_dir=output_dir,
        output_paths=expected_outputs.values(),
        report_receipt=receipt_path,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        include_implementation_evidence=False,
        expected_run_contract=expected_run_contract,
        expected_inventory=expected_inventory,
    )
    snapshots = {snapshot.path: snapshot for snapshot in roster.files}
    bound_summary = snapshots[run_summary]
    if (
        bound_summary.state != "regular"
        or bound_summary.sha256 != summary_binding["sha256"]
    ):
        raise ReportingTransactionError(
            "Historical report receipt run-summary identity differs"
        )
    for output in document["outputs"]:
        snapshot = snapshots[Path(output["path"])]
        if (
            snapshot.state != "regular"
            or snapshot.sha256 != output["sha256"]
            or snapshot.size_bytes != output["size_bytes"]
        ):
            raise ReportingTransactionError(
                f"Historical report output differs: {output['path']}"
            )
    if validate_upstream:
        artifact_receipt = Path(str(summary["artifact_receipt"]["path"]))
        validate_run_summary_transaction(
            source_checkout=source_checkout,
            artifact_source_root=artifact_source_root,
            run_id=run_id,
            artifact_receipt=artifact_receipt,
            output_root=artifact_receipt.parent.parent,
            recorded_producer_commit=str(summary["provenance"]["git_commit"]),
            expected_run_contract=expected_run_contract,
            expected_inventory=expected_inventory,
            analysis_policy=analysis_policy,
            receipt_ops=_predecessor_receipt_ops(receipt_ops),
        )
    locations = tuple(
        (str(output["output_id"]), Path(str(output["path"])))
        for output in document["outputs"][:2]
    )
    return _validated_result(
        receipt_snapshot,
        roster,
        receipt_ops,
        reject_control_residue,
        verified_report_locations=locations,
    )


def validate_receipt(
    kind: str,
    receipt_path: Path,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempt: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    historical_read: bool = False,
    validated_predecessor: ValidatedTransaction | None = None,
) -> ValidatedTransaction:
    """Validate the exact fixed-profile receipt selected by lifecycle state.

    ``historical_read`` is restricted to transactions selected by an exact
    legacy profile. It verifies each recorded producer identity without
    claiming that the current reader checkout produced the preserved bytes.
    """

    if kind not in {"artifact_index", "run_summary", "html_report"}:
        raise ReportingTransactionError(f"Unknown reporting transaction kind: {kind}")
    try:
        orchestration_contracts.validate_record("profile", profile)
        authority = application_model.read_application_record(
            orchestration_contracts.canonical_json_bytes(execution),
            legacy_profile=profile,
        )
        successor = isinstance(authority, application_model.RunBinding)
        if not successor and not isinstance(
            authority, application_model.LegacyExecution
        ):
            raise ReportingTransactionError("Reporting authority is not a Run binding")
        orchestration_contracts.validate_record("workflow-attempt", attempt)
    except Exception as exc:
        raise ReportingTransactionError(
            f"Could not admit {kind} orchestration identity: {exc}"
        ) from exc
    run_id = str(execution["run_id"])
    execution_sha256 = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(execution)
    ).hexdigest()
    profile_sha256 = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(profile)
    ).hexdigest()
    for field, expected_value in (
        ("run_id", run_id),
        ("execution_contract_sha256", execution_sha256),
        ("profile_sha256", profile_sha256),
    ):
        if attempt[field] != expected_value:
            raise ReportingTransactionError(
                f"Workflow attempt does not bind reporting {field}"
            )
    artifact_root = run_root / "products" / "artifact-summary"
    html_report_root = report_output_root(run_root, profile)
    receipts = {
        "artifact_index": artifact_root / run_id / f"{run_id}.artifact_receipt.tsv",
        "run_summary": artifact_root / run_id / f"{run_id}.run_summary_receipt.tsv",
        "html_report": html_report_root / run_id / f"{run_id}.report_outputs.tsv",
    }
    expected = receipts[kind]
    if receipt_path != expected:
        raise ReportingTransactionError(
            f"{kind} receipt path is not the fixed transaction path: {receipt_path}"
        )
    historical_transaction = (
        historical_read and html_report_root == run_root / "products" / "report"
    )
    if historical_read and not historical_transaction:
        raise ReportingTransactionError(
            "Historical transaction admission requires the bound legacy profile"
        )
    predecessor_kind = {
        "run_summary": "artifact_index",
        "html_report": "run_summary",
    }.get(kind)
    reuse_predecessor = (
        predecessor_kind is not None and validated_predecessor is not None
    )
    if reuse_predecessor:
        assert validated_predecessor is not None
        predecessor_receipt = _snapshot_receipt(receipts[predecessor_kind])
        if (
            validated_predecessor.receipt_path != predecessor_receipt.path
            or validated_predecessor.receipt_sha256 != predecessor_receipt.sha256
        ):
            raise ReportingTransactionError(
                "Previously validated reporting predecessor no longer matches"
            )
        if validated_predecessor._recheck is None:
            reuse_predecessor = False
        else:
            validated_predecessor._recheck()
    declared_checkout = attempt["source_checkout"]
    source_checkout = Path(str(declared_checkout["path"]))
    package_root = Path(__file__).resolve().parents[1]
    source_attestation = None
    if not historical_transaction:
        try:
            source_attestation = attest_source_checkout(
                root=source_checkout,
                package_root=package_root,
                expected_commit=str(declared_checkout["commit"]),
            )
        except SourceCheckoutError as exc:
            raise ReportingTransactionError(
                f"Could not attest {kind} source checkout to its workflow attempt: {exc}"
            ) from exc
    contract_root = run_root / "contract"
    run_contract = contract_root / "reporting_run_contract.json"
    inventory = contract_root / "artifact_inventory.tsv"
    analysis_policy = None
    if successor:
        run_contract = run_root / config["reporting_run_contract_path"]["path"]
        inventory = run_root / config["artifact_inventory_path"]["path"]
    if successor and not historical_transaction:
        analysis_policy = run_root / config["primary_analysis_policy_path"]["path"]
    artifact_receipt = artifact_root / run_id / f"{run_id}.artifact_receipt.tsv"
    try:
        if kind == "artifact_index":
            if historical_transaction:
                artifact_validator = _validate_historical_artifact_index_transaction
            else:
                artifact_validator = validate_artifact_index_transaction
            artifact_options = {
                "source_checkout": source_checkout,
                "artifact_source_root": run_root,
                "run_id": run_id,
                "run_contract": run_contract,
                "inventory": inventory,
                "output_root": artifact_root,
            }
            if successor and not historical_transaction:
                artifact_options.update(
                    analysis_policy=analysis_policy,
                    profile=profile,
                )
            result = artifact_validator(
                **artifact_options,
            )
        elif kind == "run_summary":
            result = validate_run_summary_transaction(
                source_checkout=source_checkout,
                artifact_source_root=run_root,
                run_id=run_id,
                artifact_receipt=artifact_receipt,
                output_root=artifact_root,
                expected_run_contract=(
                    run_contract if historical_transaction else None
                ),
                expected_inventory=(inventory if historical_transaction else None),
                analysis_policy=analysis_policy,
                profile=profile,
                validate_upstream=not reuse_predecessor,
            )
        elif historical_transaction:
            result = _validate_historical_report_transaction(
                source_checkout=source_checkout,
                artifact_source_root=run_root,
                run_id=run_id,
                run_summary=artifact_root / run_id / f"{run_id}.run_summary.json",
                output_root=html_report_root,
                expected_source_commit=str(declared_checkout["commit"]),
                expected_run_contract=run_contract,
                expected_inventory=inventory,
                analysis_policy=analysis_policy,
                validate_upstream=not reuse_predecessor,
            )
        else:
            result = validate_report_transaction(
                source_checkout=source_checkout,
                artifact_source_root=run_root,
                run_summary=artifact_root / run_id / f"{run_id}.run_summary.json",
                output_root=html_report_root,
                analysis_policy=analysis_policy,
                profile=profile,
                validate_upstream=not reuse_predecessor,
            )
    except ReportingTransactionError:
        raise
    except Exception as exc:
        raise ReportingTransactionError(
            f"Could not validate {kind} reporting transaction: {exc}"
        ) from exc
    if not historical_transaction:
        try:
            confirmed_source = attest_source_checkout(
                root=source_checkout,
                package_root=package_root,
                expected_commit=str(declared_checkout["commit"]),
            )
        except SourceCheckoutError as exc:
            raise ReportingTransactionError(
                f"Could not reattest {kind} source checkout: {exc}"
            ) from exc
        if confirmed_source != source_attestation:
            raise ReportingTransactionError(
                f"{kind} source checkout identity changed during validation"
            )
    return result


__all__ = (
    "ReportingTransactionError",
    "ReceiptValidationOps",
    "ValidatedTransaction",
    "recheck_run_summary_inputs",
    "validate_artifact_index_transaction",
    "validate_receipt",
    "validate_report_transaction",
    "validate_run_summary_transaction",
)
