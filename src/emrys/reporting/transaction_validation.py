"""Read-only semantic validation of complete reporting transactions.

The lifecycle calls this direct owner after Snakemake exits and again during
inspection. A receipt pathname or hash is never sufficient: current
transactions re-admit the current installed producer. Every path
validates its bound inputs and outputs and reconstructs the deterministic
projection where applicable.
"""

from __future__ import annotations

import argparse
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
    InstalledPackage,
    admit_artifact_source_root,
    admit_installed_package,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
)

TransactionKind = Literal["run_summary", "html_report"]


class ReportingTransactionError(RuntimeError):
    """A reporting receipt does not prove its complete bound transaction."""


@dataclass(frozen=True, slots=True)
class ValidatedTransaction:
    """The receipt identity returned only after full semantic validation."""

    receipt_path: Path
    receipt_sha256: str
    verified_report_locations: tuple[tuple[str, Path], ...] = ()
    _recheck: Callable[[], None] | None = field(default=None, repr=False, compare=False)


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
    package_root: Path,
    artifact_source_root: Path,
) -> tuple[InstalledPackage, ArtifactSourceRoot]:
    return (
        admit_installed_package(
            root=package_root,
        ),
        admit_artifact_source_root(root=artifact_source_root),
    )


def _validated_result(
    receipt: _ReceiptSnapshot,
    roster: _BoundRosterSnapshot,
    reject_control_residue: Callable[[], None],
    *,
    identity_only_paths: Iterable[Path] = (),
    verified_report_locations: tuple[tuple[str, Path], ...] = (),
) -> ValidatedTransaction:
    if not _receipt_is_in_roster(receipt, roster):
        raise ReportingTransactionError(
            f"Reporting receipt changed before roster admission: {receipt.path}"
        )
    identity_only = frozenset(identity_only_paths)
    reject_control_residue()
    _recheck_bound_roster(roster, identity_only_paths=identity_only)

    def recheck() -> None:
        reject_control_residue()
        _recheck_bound_roster(
            roster,
            identity_only_paths=identity_only,
        )

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
    directories_match = observed.directories == roster.directories
    if not files_match or not directories_match:
        raise ReportingTransactionError(
            "Reporting transaction roster changed during semantic validation"
        )


def _contract_path(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path(os.path.abspath(root / path))


def _artifact_record_bound_paths(
    records: Iterable[Mapping[str, Any]],
    *,
    package_root: Path,
    artifact_source_root: Path,
) -> set[Path]:
    paths: set[Path] = set()
    for record in records:
        expectation = record.get("expectation")
        if isinstance(expectation, Mapping):
            source_path = expectation.get("source_path")
            if isinstance(source_path, str) and source_path:
                paths.add(_contract_path(source_path, artifact_source_root))
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
                paths.add(_contract_path(evidence_path, package_root))
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
    if kind == "run_summary":
        exact = {f".{run_id}.artifact-index.lock"}
        patterns = (
            re.compile(
                rf"\.artifact-index\.{_CONTROL_TOKEN}\.(?:tmp\.records|RECOVERY\.txt)"
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


def validate_report_transaction(
    *,
    package_root: Path,
    artifact_source_root: Path,
    run_summary: Path,
    output_root: Path,
    analysis_policy: Path | None = None,
    profile: Mapping[str, Any] | None = None,
    validate_upstream: bool = True,
) -> ValidatedTransaction:
    """Revalidate both HTML views, TSV, receipt, and bound inputs."""

    from emrys.reporting._run_report import context as report_context
    from emrys.reporting._run_report import receipt, validation

    summary = artifact_contracts.load_json_object(run_summary, "run summary")
    run_id = str(summary.get("run_id", ""))
    if analysis_policy is None and summary.get("analysis_policy") is not None:
        analysis_policy = Path(str(summary["analysis_policy"]["path"]))
        if not analysis_policy.is_absolute():
            analysis_policy = artifact_source_root / analysis_policy
    output_dir = output_root / run_id
    output_names = tuple(
        f"{run_id}.{suffix}" for _id, _kind, suffix in artifact_contracts.REPORT_OUTPUTS
    ) + (f"{run_id}.report_outputs.tsv",)
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
        context = report_context.prepare_context(
            argparse.Namespace(
                package_root=package_root,
                artifact_source_root=artifact_source_root,
                run_summary=run_summary,
                analysis_policy=analysis_policy,
                output_root=output_root,
                execute=False,
            )
        )
    except report_context.ReportRenderError as exc:
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
        output_paths=context.stable_paths[:3],
        report_receipt=context.output_receipt,
        package_root=context.installed_package.root,
        artifact_source_root=context.artifact_source_root.root,
        input_paths=(snapshot.path for snapshot in context.input_snapshots),
    )
    if validate_upstream:
        validate_run_summary_transaction(
            package_root=package_root,
            artifact_source_root=artifact_source_root,
            run_id=run_id,
            run_contract=Path(context.summary["run_contract_file"]["path"]),
            inventory=Path(context.summary["inventory"]["path"]),
            output_root=run_summary.parent.parent,
            analysis_policy=analysis_policy,
            profile=profile,
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
        tuple(
            (output_id, kind, path, path)
            for (output_id, kind, _suffix), path in zip(
                artifact_contracts.REPORT_OUTPUTS, context.stable_paths[:3], strict=True
            )
        ),
    )
    if document != expected_document:
        raise ReportingTransactionError(
            "Published report receipt differs from the current projection"
        )
    html_ids = tuple(
        output_id for output_id, _kind, _suffix in artifact_contracts.REPORT_OUTPUTS[:2]
    )
    verified_report_locations = tuple(
        (str(output["output_id"]), Path(str(output["path"])))
        for output in document["outputs"]
        if output["output_id"] in html_ids
    )
    if tuple(output_id for output_id, _path in verified_report_locations) != html_ids:
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
        reject_control_residue,
        identity_only_paths=(
            snapshot.path
            for snapshot, _label, rehash_content in context.input_rechecks
            if not rehash_content
        ),
        verified_report_locations=verified_report_locations,
    )


def _report_roster(
    summary: Mapping[str, Any],
    *,
    run_summary_path: Path,
    output_dir: Path,
    output_paths: Iterable[Path],
    report_receipt: Path,
    package_root: Path,
    artifact_source_root: Path,
    input_paths: Iterable[Path] = (),
) -> _BoundRosterSnapshot:
    run_id = str(summary["run_id"])
    summary_dir = run_summary_path.parent
    return _snapshot_bound_roster(
        {
            *input_paths,
            run_summary_path,
            *output_paths,
            report_receipt,
            Path(summary["analysis_policy"]["path"]),
            Path(summary["run_contract_file"]["path"]),
            Path(summary["inventory"]["path"]),
            summary_dir / f"{run_id}.run_summary.tsv",
            summary_dir / f"{run_id}.qc_summary.tsv",
            *_artifact_record_bound_paths(
                summary["artifacts"],
                package_root=package_root,
                artifact_source_root=artifact_source_root,
            ),
        },
        (output_dir, summary_dir),
    )


def validate_run_summary_transaction(
    *,
    package_root: Path,
    artifact_source_root: Path,
    run_id: str,
    run_contract: Path,
    inventory: Path,
    output_root: Path,
    analysis_policy: Path | None = None,
    profile: Mapping[str, Any] | None = None,
) -> ValidatedTransaction:
    """Re-admit the current result manifest, native sources and table projections."""
    from emrys.reporting._artifact_index import context as artifact_context
    from emrys.reporting._artifact_index.core import canonical_json_bytes
    from emrys.reporting._run_summary.validation import _validate_document

    output_dir = output_root / run_id
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="run_summary",
        output_dir=output_dir,
        run_id=run_id,
    )
    reject_control_residue()
    snapshot = _snapshot_receipt(output_dir / f"{run_id}.run_summary.json")
    document = artifact_contracts.load_json_object_bytes(
        snapshot.payload, "Run result manifest"
    )
    installed_package, source_root = _admit_authorities(
        package_root=package_root, artifact_source_root=artifact_source_root
    )
    evidence = artifact_context.prepare_evidence_context(
        argparse.Namespace(
            run_id=run_id,
            run_contract=run_contract,
            inventory=inventory,
            analysis_policy=analysis_policy,
            profile=profile,
            output_root=output_root,
            execute=False,
        ),
        installed_package=installed_package,
        artifact_source_root=source_root,
    )
    context = evidence.index
    _validate_document(
        document, context.inventory_rows, inventory, source_root=artifact_source_root
    )
    files = {
        *evidence.summary_paths.ordered_outputs,
        run_contract,
        inventory,
        Path(document["analysis_policy"]["path"]),
        *_artifact_record_bound_paths(
            context.records,
            package_root=package_root,
            artifact_source_root=artifact_source_root,
        ),
    }
    roster = _snapshot_bound_roster(files, (output_dir,))
    expected = evidence.summary_document
    # Only the original publication clock and attempt ID survive regeneration.
    expected["generated_at"] = document["generated_at"]
    expected["provenance"]["created_at"] = document["generated_at"]
    expected["publication"] = document["publication"]
    if snapshot.payload != canonical_json_bytes(expected):
        raise ReportingTransactionError(
            "Published Run result manifest differs from current sources, immutable inputs or canonical projection"
        )
    for path, payload in (
        (evidence.summary_paths.summary_tsv, evidence.summary_tsv_bytes),
        (evidence.summary_paths.qc_summary, evidence.qc_summary_bytes),
    ):
        if path.read_bytes() != payload:
            raise ReportingTransactionError(
                f"Published Run result table differs from its manifest: {path}"
            )
    artifact_context.recheck_inputs(context)
    artifact_context.recheck_source_identity(context)
    return _validated_result(snapshot, roster, reject_control_residue)


def validate_receipt(
    kind: str,
    receipt_path: Path,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempt: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    validated_predecessor: ValidatedTransaction | None = None,
) -> ValidatedTransaction:
    """Validate the current Run result or its HTML projection transaction."""
    if kind not in {"run_summary", "html_report"}:
        raise ReportingTransactionError(f"Unknown reporting transaction kind: {kind}")
    try:
        orchestration_contracts.validate_record("profile", profile)
        authority = application_model.read_application_record(
            orchestration_contracts.canonical_json_bytes(execution)
        )
        if not isinstance(authority, application_model.RunBinding):
            raise ReportingTransactionError(
                "Reporting authority is not a current Run binding"
            )
        orchestration_contracts.validate_record("workflow-attempt", attempt)
    except Exception as exc:
        raise ReportingTransactionError(
            f"Could not admit {kind} orchestration identity: {exc}"
        ) from exc
    run_id = str(execution["run_id"])
    for field, expected in (
        ("run_id", run_id),
        (
            "execution_contract_sha256",
            hashlib.sha256(
                orchestration_contracts.canonical_json_bytes(execution)
            ).hexdigest(),
        ),
        (
            "profile_sha256",
            hashlib.sha256(
                orchestration_contracts.canonical_json_bytes(profile)
            ).hexdigest(),
        ),
    ):
        if attempt[field] != expected:
            raise ReportingTransactionError(
                f"Workflow attempt does not bind reporting {field}"
            )
    artifact_root = run_root / "products" / "artifact-summary"
    html_root = report_output_root(run_root, profile)
    manifest = artifact_root / run_id / f"{run_id}.run_summary.json"
    expected = (
        manifest
        if kind == "run_summary"
        else html_root / run_id / f"{run_id}.report_outputs.tsv"
    )
    if receipt_path != expected:
        raise ReportingTransactionError(
            f"{kind} receipt path is not the fixed transaction path: {receipt_path}"
        )
    reuse = False
    if kind == "html_report" and validated_predecessor is not None:
        predecessor = _snapshot_receipt(manifest)
        if (
            validated_predecessor.receipt_path != manifest
            or validated_predecessor.receipt_sha256 != predecessor.sha256
        ):
            raise ReportingTransactionError(
                "Previously validated reporting predecessor no longer matches"
            )
        if validated_predecessor._recheck is not None:
            validated_predecessor._recheck()
            reuse = True
    declared = attempt["installed_package"]
    package_root = Path(str(declared["path"]))

    def attest():
        observed = admit_installed_package(root=package_root)
        if observed.record != declared:
            raise ReportingTransactionError(
                "Installed reporting package differs from the Attempt"
            )
        return observed.record

    try:
        source = attest()
        common = dict(
            package_root=package_root,
            artifact_source_root=run_root,
            analysis_policy=run_root / config["primary_analysis_policy_path"]["path"],
            profile=profile,
        )
        if kind == "run_summary":
            result = validate_run_summary_transaction(
                **common,
                run_id=run_id,
                run_contract=run_root / config["reporting_run_contract_path"]["path"],
                inventory=run_root / config["artifact_inventory_path"]["path"],
                output_root=artifact_root,
            )
        else:
            result = validate_report_transaction(
                **common,
                run_summary=manifest,
                output_root=html_root,
                validate_upstream=not reuse,
            )
        if attest() != source:
            raise ReportingTransactionError(
                f"{kind} installed package identity changed during validation"
            )
    except ReportingTransactionError:
        raise
    except Exception as exc:
        raise ReportingTransactionError(
            f"Could not validate {kind} reporting transaction: {exc}"
        ) from exc
    return result


__all__ = (
    "ReportingTransactionError",
    "ValidatedTransaction",
    "validate_receipt",
    "validate_report_transaction",
    "validate_run_summary_transaction",
)
