"""Read-only semantic validation of complete reporting transactions.

The lifecycle calls this direct owner after Snakemake exits and again during
inspection. A receipt pathname or hash is never sufficient: current
transactions bind retained producer provenance through their immutable ledger.
Every path validates its bound inputs and outputs; new publication also checks
the deterministic projection.
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
from typing import TYPE_CHECKING, Any, Literal

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import (
    PACKAGE_ROOT,
    admit_artifact_source_root,
    admit_installed_package,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
)

if TYPE_CHECKING:
    from emrys.reporting._artifact_index.models import EvidenceContext
    from emrys.reporting._run_report.models import ReportContext

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
    artifact_source_root: Path,
) -> set[Path]:
    return {
        _contract_path(record["expectation"]["source_path"], artifact_source_root)
        for record in records
        if record["expectation"].get("source_path")
    }


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
    prepared_context: ReportContext | None = None,
    expected_receipt_sha256: str | None = None,
) -> ValidatedTransaction:
    """Admit retained report bytes and data without invoking their renderer."""
    from emrys.reporting._run_report import context as report_context
    from emrys.reporting._run_report import receipt, validation
    from emrys.reporting._run_report.publication import _recheck_inputs

    summary = artifact_contracts.load_json_object(run_summary, "run summary")
    run_id = str(summary["run_id"])
    analysis_policy = analysis_policy or _contract_path(
        summary["analysis_policy"]["path"], artifact_source_root
    )
    output_dir = output_root / run_id
    output_paths = tuple(
        output_dir / f"{run_id}.{suffix}"
        for _id, _kind, suffix in artifact_contracts.REPORT_OUTPUTS
    )
    receipt_path = output_dir / f"{run_id}.report_outputs.tsv"
    reject_control_residue = partial(
        _reject_reporting_control_residue,
        kind="html_report",
        output_dir=output_dir,
        run_id=run_id,
        output_names=tuple(path.name for path in (*output_paths, receipt_path)),
    )
    reject_control_residue()
    snapshot = _snapshot_receipt(receipt_path)
    if prepared_context is None and expected_receipt_sha256 != snapshot.sha256:
        raise ReportingTransactionError(
            "Retained report receipt differs from its verified ledger"
        )
    try:
        document = receipt.read_receipt_tsv(receipt_path)
        report_context._existing_outputs(output_dir, (*output_paths, receipt_path))
        if prepared_context is not None:
            if (
                prepared_context.installed_package.root != package_root
                or prepared_context.artifact_source_root.root != artifact_source_root
                or prepared_context.run_summary_path != run_summary
                or prepared_context.analysis_policy_path != analysis_policy
                or prepared_context.output_dir != output_dir
            ):
                raise ReportingTransactionError(
                    "Prepared report context does not match this reporting transaction"
                )
            _recheck_inputs(prepared_context)
            validation.validate_projected_outputs(
                prepared_context,
                (*output_paths, receipt_path),
                receipt.output_bytes(prepared_context),
            )
        else:
            for view, path in zip(
                ("scientific", "evidence"), output_paths[:2], strict=True
            ):
                validation.validate_rendered_html(
                    path,
                    expected_banner=document["state_banner"],
                    expected_identity=validation.expected_html_identity(document, view),
                )
    except report_context.ReportRenderError as exc:
        raise ReportingTransactionError(str(exc)) from exc
    if validate_upstream:
        validate_run_summary_transaction(
            package_root=package_root,
            artifact_source_root=artifact_source_root,
            run_id=run_id,
            run_contract=Path(summary["run_contract_file"]["path"]),
            inventory=Path(summary["inventory"]["path"]),
            output_root=run_summary.parent.parent,
            analysis_policy=analysis_policy,
            profile=profile,
            expected_receipt_sha256=document["input_run_summary"]["sha256"],
        )
    inputs = (
        *document["inputs"],
        document["input_run_summary"],
        document["analysis_policy"],
    )
    if (
        document["run_id"] != run_id
        or document["input_run_summary"]["path"] != str(run_summary)
        or document["input_run_summary"]["schema_name"] != summary["schema_name"]
        or document["input_run_summary"]["schema_version"] != summary["schema_version"]
        or document["analysis_policy"]["path"] != str(analysis_policy)
        or document["analysis_policy"]["sha256"] != summary["analysis_policy"]["sha256"]
        or len({item["path"] for item in document["inputs"]}) != len(document["inputs"])
    ):
        raise ReportingTransactionError(
            "Report receipt does not bind its Run, summary and input roster"
        )
    roster = _snapshot_bound_roster(
        {
            *(Path(item["path"]) for item in inputs),
            *output_paths,
            receipt_path,
            Path(summary["run_contract_file"]["path"]),
            Path(summary["inventory"]["path"]),
            *(Path(item["path"]) for item in summary["scientific_origin"].values()),
            run_summary.with_name(f"{run_id}.run_summary.tsv"),
            run_summary.with_name(f"{run_id}.qc_summary.tsv"),
            *_artifact_record_bound_paths(
                summary["artifacts"], artifact_source_root=artifact_source_root
            ),
        },
        (output_dir, run_summary.parent),
    )
    observed = {item.path: item for item in roster.files}
    for item in (*inputs, *document["outputs"]):
        bound = observed[Path(item["path"])]
        if bound.sha256 != item["sha256"] or (
            "size_bytes" in item and bound.size_bytes != item["size_bytes"]
        ):
            raise ReportingTransactionError(
                f"Report file differs from its receipt: {bound.path}"
            )
    if prepared_context is not None:
        _recheck_inputs(prepared_context)
    return _validated_result(
        snapshot,
        roster,
        reject_control_residue,
        identity_only_paths=(
            Path(item["path"])
            for item in document["inputs"]
            if not item["rehash_content"]
        ),
        verified_report_locations=tuple(
            (output_id, path)
            for (output_id, _kind, _suffix), path in zip(
                artifact_contracts.REPORT_OUTPUTS[:2], output_paths[:2], strict=True
            )
        ),
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
    prepared_context: EvidenceContext | None = None,
    expected_receipt_sha256: str | None = None,
) -> ValidatedTransaction:
    """Validate scientific sources and retained tables without rebuilding reports."""
    from emrys.reporting._artifact_index import context as artifact_context
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
    if prepared_context is None and expected_receipt_sha256 != snapshot.sha256:
        raise ReportingTransactionError(
            "Retained manifest differs from its verified ledger"
        )
    document = artifact_contracts.load_json_object_bytes(
        snapshot.payload, "Run result manifest"
    )
    installed_package = admit_installed_package(root=package_root)
    source_root = admit_artifact_source_root(root=artifact_source_root)
    context = (
        prepared_context.index
        if prepared_context is not None
        else artifact_context.prepare_context(
            argparse.Namespace(
                run_id=run_id,
                run_contract=run_contract,
                inventory=inventory,
                analysis_policy=analysis_policy,
                profile=profile,
                output_root=output_root,
                execute=False,
                scientific_origin=document["scientific_origin"],
            ),
            installed_package=installed_package,
            artifact_source_root=source_root,
        )
    )
    if (
        context.installed_package.record != installed_package.record
        or context.artifact_source_root != source_root
        or context.run_id != run_id
        or context.profile_sha256 != orchestration_contracts.canonical_sha256(profile)
        or context.run_contract_path != run_contract
        or context.inventory_path != inventory
        or context.analysis_policy_path != analysis_policy
        or context.output_dir != output_dir
        or document["run_id"] != run_id
        or document["run_contract"] != context.run_contract
        or document["run_contract_file"]
        != {"path": str(run_contract), "sha256": context.run_contract_file_sha256}
        or document["analysis_policy"] != context.analysis_policy_binding
    ):
        raise ReportingTransactionError(
            "Run result manifest differs from its admitted inputs"
        )
    artifact_context.recheck_inputs(context)
    artifact_context.recheck_source_identity(context)
    _validate_document(
        document, context.inventory_rows, inventory, source_root=artifact_source_root
    )
    for recorded, observed in zip(document["artifacts"], context.records, strict=True):
        if any(
            recorded[field] != observed[field]
            for field in ("source", "availability_status", "completion_status")
        ):
            raise ReportingTransactionError(
                "Published Run result manifest differs from current scientific sources"
            )
    table_paths = tuple(Path(item["path"]) for item in document["tables"])
    if table_paths != tuple(
        output_dir / f"{run_id}.{suffix}"
        for suffix in ("run_summary.tsv", "qc_summary.tsv")
    ):
        raise ReportingTransactionError(
            "Run result tables are outside their publication directory"
        )
    if prepared_context is not None:
        if snapshot.payload != prepared_context.summary_json_bytes:
            raise ReportingTransactionError(
                "Published Run result manifest differs from its prepared projection"
            )
        for path, payload in zip(
            table_paths,
            (prepared_context.summary_tsv_bytes, prepared_context.qc_summary_bytes),
            strict=True,
        ):
            if path.read_bytes() != payload:
                raise ReportingTransactionError(
                    f"Published Run result table differs from its prepared projection: {path}"
                )
    roster = _snapshot_bound_roster(
        {
            snapshot.path,
            *table_paths,
            run_contract,
            inventory,
            *(Path(item["path"]) for item in document["scientific_origin"].values()),
            Path(document["analysis_policy"]["path"]),
            *_artifact_record_bound_paths(
                context.records, artifact_source_root=artifact_source_root
            ),
        },
        (output_dir,),
    )
    observed_files = {item.path: item for item in roster.files}
    for table in document["tables"]:
        observed = observed_files[Path(table["path"])]
        if (observed.sha256, observed.size_bytes) != (
            table["sha256"],
            table["size_bytes"],
        ):
            raise ReportingTransactionError(
                f"Published Run result table differs from its manifest: {observed.path}"
            )
    artifact_context.recheck_inputs(context)
    artifact_context.recheck_source_identity(context)
    return _validated_result(snapshot, roster, reject_control_residue)


def validate_receipt(
    kind: str,
    receipt_path: Path,
    identity: Any,
    *,
    validated_predecessor: ValidatedTransaction | None = None,
    prepared_context: EvidenceContext | ReportContext | None = None,
    expected_receipt_sha256: str | None = None,
) -> ValidatedTransaction:
    """Validate the current Run result or its HTML projection transaction."""
    if kind not in {"run_summary", "html_report"}:
        raise ReportingTransactionError(f"Unknown reporting transaction kind: {kind}")
    run_root = identity.root
    run_id = str(identity.execution["run_id"])
    config = identity.attempt["workflow"]
    artifact_root = run_root / "products" / "artifact-summary"
    html_root = run_root / "results" / "reports"
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
    package_root = PACKAGE_ROOT

    def attest():
        return admit_installed_package(root=package_root).record

    try:
        source = attest()
        snapshot = _snapshot_receipt(receipt_path)
        if (
            expected_receipt_sha256 is not None
            and snapshot.sha256 != expected_receipt_sha256
        ):
            raise ReportingTransactionError(
                "Reporting receipt differs from its verified ledger"
            )
        document = artifact_contracts.load_json_object(manifest, "Run result manifest")
        if document["scientific_origin"] != identity.scientific_origin:
            raise ReportingTransactionError(
                "Run result manifest does not bind its scientific origin"
            )
        common = dict(
            package_root=package_root,
            artifact_source_root=run_root,
            analysis_policy=run_root / config["primary_analysis_policy_path"]["path"],
            profile=identity.profile,
            prepared_context=prepared_context,
            expected_receipt_sha256=expected_receipt_sha256,
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
        if result.receipt_sha256 != snapshot.sha256:
            raise ReportingTransactionError(
                "Reporting receipt changed during validation"
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
