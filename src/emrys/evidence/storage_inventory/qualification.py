"""Qualify workflow storage semantics across compute and head nodes."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import secrets
import socket
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "emrys.storage-qualification.v1"
EVIDENCE_DIRECTORY = ".emrys-storage-qualification"
CHECKS = (
    "hardlink_same_filesystem_identity",
    "advisory_flock_contention",
    "atomic_rename_visibility",
    "write_and_fsync",
    "head_compute_uid_access_consistency",
    "post_allocation_durability",
)
ROLES = ("workflow_workspace", "step00c_sidecar_parent")
PROBE_FILES = (
    "flock.lock",
    "fsync-source.bin",
    "hardlink.bin",
    "visible.bin",
)
_CROSS_NODE_STABLE_ROOT_FIELDS = (
    "path",
    "inode",
    "uid",
    "gid",
    "mount_point",
    "filesystem_type",
    "filesystem_source",
)
_LOCK_CHILD = """import fcntl
import os
import sys

descriptor = os.open(sys.argv[1], os.O_RDWR)
try:
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(0)
    raise SystemExit(3)
finally:
    os.close(descriptor)
"""


class StorageQualificationError(RuntimeError):
    """Storage qualification input or retained evidence is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class QualifiedStorage:
    """One admitted final site-qualification receipt."""

    receipt_path: Path
    receipt_sha256: str
    qualification_id: str


def fail(message: str) -> None:
    raise StorageQualificationError(message)


def _canonical_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        fail(f"{label} must be absolute: {path}")
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        fail(f"Could not inspect {label} {path}: {exc}")
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != path
    ):
        fail(f"{label} must be a canonical real directory: {path}")
    if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
        fail(f"{label} must be readable, writable, and searchable: {path}")
    return path


def _storage_roots(workspace: Path, reference_fasta: Path) -> tuple[Path, Path]:
    if not workspace.is_absolute():
        fail(f"Workspace must be absolute: {workspace}")
    workspace_parent = _canonical_directory(
        workspace.parent,
        "Workspace immediate parent",
    )
    if os.path.lexists(workspace):
        try:
            workspace_state = workspace.lstat()
            resolved_workspace = workspace.resolve(strict=True)
        except OSError as exc:
            fail(f"Could not inspect workspace {workspace}: {exc}")
        if (
            stat.S_ISLNK(workspace_state.st_mode)
            or not stat.S_ISDIR(workspace_state.st_mode)
            or resolved_workspace != workspace
        ):
            fail(f"Workspace must be absent or a canonical real directory: {workspace}")
        if workspace_state.st_dev != workspace_parent.stat().st_dev:
            fail("Existing workspace is a different filesystem from its qualified parent")
    if not reference_fasta.is_absolute():
        fail(f"Reference FASTA must be absolute: {reference_fasta}")
    try:
        fasta_state = reference_fasta.lstat()
        resolved_fasta = reference_fasta.resolve(strict=True)
    except OSError as exc:
        fail(f"Could not inspect reference FASTA {reference_fasta}: {exc}")
    if (
        stat.S_ISLNK(fasta_state.st_mode)
        or not stat.S_ISREG(fasta_state.st_mode)
        or resolved_fasta != reference_fasta
    ):
        fail(f"Reference FASTA must be a canonical regular file: {reference_fasta}")
    sidecar_parent = _canonical_directory(
        reference_fasta.parent,
        "Step 00c sidecar parent",
    )
    return workspace_parent, sidecar_parent


def _qualification_id(roots: tuple[Path, Path]) -> str:
    payload = "\0".join(str(path) for path in roots).encode()
    return hashlib.sha256(payload).hexdigest()


def _evidence_paths(
    roots: tuple[Path, Path],
) -> tuple[str, Path, Path, Path, Path]:
    qualification_id = _qualification_id(roots)
    evidence_root = roots[0] / EVIDENCE_DIRECTORY
    compute = evidence_root / f"{qualification_id}.compute.json"
    final = evidence_root / f"{qualification_id}.qualified.json"
    staged = evidence_root / f".{qualification_id}.qualified.tmp"
    return qualification_id, evidence_root, compute, final, staged


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_evidence_root(path: Path) -> None:
    try:
        path.mkdir(mode=0o700)
        _fsync_directory(path.parent)
    except FileExistsError:
        pass
    _canonical_directory(path, "Storage qualification evidence directory")


def _write_exclusive(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        fail(f"Could not create qualification evidence {path}: {exc}")
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                fail(f"Short write while publishing qualification evidence: {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _read_regular(path: Path, label: str) -> bytes:
    try:
        before = path.lstat()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        fail(f"Could not read {label} {path}: {exc}")
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as exc:
        fail(f"{label} disappeared while being read: {path}: {exc}")
    identity = lambda item: (item.st_dev, item.st_ino, item.st_mode, item.st_size)
    if (
        not stat.S_ISREG(before.st_mode)
        or identity(before) != identity(opened)
        or identity(opened) != identity(after)
    ):
        fail(f"{label} changed or is not a stable regular file: {path}")
    return b"".join(chunks)


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode()


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"{label} is not valid UTF-8 JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def _unescape_mount(value: str) -> str:
    return (
        value.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
    )


def _mount_identity(path: Path) -> dict[str, str]:
    selected: tuple[Path, str, str] | None = None
    try:
        lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        fail(f"Could not read Linux mount identity for {path}: {exc}")
    for line in lines:
        try:
            before, after = line.split(" - ", 1)
            fields = before.split()
            post = after.split()
            mount_point = Path(_unescape_mount(fields[4]))
            filesystem_type = post[0]
            filesystem_source = _unescape_mount(post[1])
        except (IndexError, ValueError):
            fail("Linux mountinfo contains an invalid row")
        if path == mount_point or mount_point in path.parents:
            if selected is None or len(mount_point.parts) > len(selected[0].parts):
                selected = (mount_point, filesystem_type, filesystem_source)
    if selected is None:
        fail(f"No Linux mount identity covers {path}")
    return {
        "mount_point": str(selected[0]),
        "filesystem_type": selected[1],
        "filesystem_source": selected[2],
    }


def _root_snapshot(path: Path) -> dict[str, Any]:
    state = path.stat()
    capacity = os.statvfs(path)
    return {
        "path": str(path),
        "device_id": state.st_dev,
        "inode": state.st_ino,
        "uid": state.st_uid,
        "gid": state.st_gid,
        "filesystem_total_bytes": capacity.f_blocks * capacity.f_frsize,
        "filesystem_free_bytes": capacity.f_bfree * capacity.f_frsize,
        "filesystem_available_bytes": capacity.f_bavail * capacity.f_frsize,
        **_mount_identity(path),
    }


def _stable_snapshot(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    # Linux st_dev is recorded for diagnostics and same-node hard-link checks,
    # but a shared mount may receive a different device number on another node.
    return all(
        expected.get(field) == observed.get(field)
        for field in _CROSS_NODE_STABLE_ROOT_FIELDS
    )


def _probe_root(
    role: str,
    root: Path,
    qualification_id: str,
) -> dict[str, Any]:
    probe = root / f".emrys-storage-probe-{qualification_id[:16]}-{role}"
    try:
        probe.mkdir(mode=0o700)
    except OSError as exc:
        fail(f"Could not create private {role} probe directory {probe}: {exc}")
    _fsync_directory(root)
    source = probe / "fsync-source.bin"
    hardlink = probe / "hardlink.bin"
    lock = probe / "flock.lock"
    staged = probe / "rename.tmp"
    visible = probe / "visible.bin"
    source_bytes = secrets.token_bytes(64)
    visible_bytes = hashlib.sha256(source_bytes + role.encode()).digest()
    _write_exclusive(source, source_bytes)
    try:
        os.link(source, hardlink, follow_symlinks=False)
    except OSError as exc:
        fail(f"Hard-link probe failed for {role}: {exc}")
    _fsync_directory(probe)
    source_state = source.stat()
    hardlink_state = hardlink.stat()
    if (
        source_state.st_dev != root.stat().st_dev
        or (source_state.st_dev, source_state.st_ino)
        != (hardlink_state.st_dev, hardlink_state.st_ino)
    ):
        fail(f"Hard-link identity did not reconcile for {role}")
    _write_exclusive(lock, b"")
    with lock.open("r+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        child = subprocess.run(
            [sys.executable, "-I", "-c", _LOCK_CHILD, str(lock)],
            text=True,
            capture_output=True,
            check=False,
            env={},
        )
        if child.returncode != 0:
            fail(
                f"Advisory flock contention failed for {role}: "
                f"child exit {child.returncode}: {child.stderr.strip()}"
            )
    _write_exclusive(staged, visible_bytes)
    try:
        os.replace(staged, visible)
    except OSError as exc:
        fail(f"Atomic rename failed for {role}: {exc}")
    _fsync_directory(probe)
    if staged.exists() or _read_regular(visible, f"{role} visible probe") != visible_bytes:
        fail(f"Atomic rename visibility failed for {role}")
    return {
        "role": role,
        "root": _root_snapshot(root),
        "probe_directory": str(probe),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "visible_sha256": hashlib.sha256(visible_bytes).hexdigest(),
        "checks": list(CHECKS[:4]),
    }


def _validate_compute(
    value: dict[str, Any],
    qualification_id: str,
    roots: tuple[Path, Path],
) -> None:
    if set(value) != {
        "schema",
        "status",
        "qualification_id",
        "compute",
        "roots",
        "checks",
    }:
        fail("Compute qualification receipt has invalid fields")
    if (
        value["schema"] != SCHEMA
        or value["status"] != "compute_passed"
        or value["qualification_id"] != qualification_id
        or value["checks"] != list(CHECKS[:4])
    ):
        fail("Compute qualification receipt has invalid identity or status")
    compute = value["compute"]
    if not isinstance(compute, dict) or set(compute) != {
        "gid",
        "host",
        "slurm_job_id",
        "uid",
    }:
        fail("Compute qualification receipt has invalid execution identity")
    rows = value["roots"]
    if not isinstance(rows, list) or len(rows) != len(ROLES):
        fail("Compute qualification receipt has invalid root roster")
    for role, root, row in zip(ROLES, roots, rows, strict=True):
        if not isinstance(row, dict) or row.get("role") != role:
            fail("Compute qualification receipt has invalid ordered roles")
        if row.get("root", {}).get("path") != str(root):
            fail("Compute qualification receipt names an unexpected root")
        expected_probe = root / (
            f".emrys-storage-probe-{qualification_id[:16]}-{role}"
        )
        if row.get("probe_directory") != str(expected_probe):
            fail("Compute qualification receipt names an unexpected probe directory")
        if row.get("checks") != list(CHECKS[:4]):
            fail("Compute qualification receipt has invalid check roster")
        for field in ("source_sha256", "visible_sha256"):
            observed = row.get(field)
            if not isinstance(observed, str) or len(observed) != 64:
                fail(f"Compute qualification receipt has invalid {field}")


def _run_compute(workspace: Path, reference_fasta: Path) -> Path:
    job_id = os.environ.get("SLURM_JOB_ID", "").strip()
    if not job_id:
        fail("Compute qualification must execute inside a Slurm allocation")
    roots = _storage_roots(workspace, reference_fasta)
    qualification_id, evidence_root, compute, final, staged = _evidence_paths(roots)
    _ensure_evidence_root(evidence_root)
    for path in (compute, final, staged):
        if os.path.lexists(path):
            fail(f"Qualification evidence already exists; preserve and inspect it: {path}")
    rows = [
        _probe_root(role, root, qualification_id)
        for role, root in zip(ROLES, roots, strict=True)
    ]
    receipt = {
        "schema": SCHEMA,
        "status": "compute_passed",
        "qualification_id": qualification_id,
        "compute": {
            "gid": os.getegid(),
            "host": socket.gethostname(),
            "slurm_job_id": job_id,
            "uid": os.geteuid(),
        },
        "roots": rows,
        "checks": list(CHECKS[:4]),
    }
    _write_exclusive(compute, _json_bytes(receipt))
    return compute


def _probe_roster(probe: Path) -> dict[str, Path]:
    try:
        state = probe.lstat()
        entries = {path.name: path for path in probe.iterdir()}
    except OSError as exc:
        fail(f"Could not re-admit retained probe directory {probe}: {exc}")
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
        fail(f"Retained probe is not a real directory: {probe}")
    if set(entries) != set(PROBE_FILES):
        fail(f"Retained probe has unexpected membership: {probe}")
    return entries


def _validate_retained_probe(row: dict[str, Any], root: Path) -> Path:
    expected = row["root"]
    observed = _root_snapshot(root)
    if not isinstance(expected, dict) or not _stable_snapshot(expected, observed):
        fail(f"Storage root identity changed after the allocation: {root}")
    probe = Path(row["probe_directory"])
    entries = _probe_roster(probe)
    source = _read_regular(entries["fsync-source.bin"], "Retained fsync source")
    hardlink = _read_regular(entries["hardlink.bin"], "Retained hard link")
    visible = _read_regular(entries["visible.bin"], "Retained renamed file")
    _read_regular(entries["flock.lock"], "Retained flock file")
    if source != hardlink:
        fail(f"Retained hard-link bytes differ: {probe}")
    source_state = entries["fsync-source.bin"].stat()
    link_state = entries["hardlink.bin"].stat()
    if (source_state.st_dev, source_state.st_ino) != (
        link_state.st_dev,
        link_state.st_ino,
    ):
        fail(f"Retained hard-link identity differs: {probe}")
    if hashlib.sha256(source).hexdigest() != row["source_sha256"]:
        fail(f"Retained source hash differs: {probe}")
    if hashlib.sha256(visible).hexdigest() != row["visible_sha256"]:
        fail(f"Retained visible-file hash differs: {probe}")
    head_probe = probe / "head-fsync.bin"
    _write_exclusive(head_probe, hashlib.sha256(source + visible).digest())
    _read_regular(head_probe, "Head-node fsync probe")
    head_probe.unlink()
    _fsync_directory(probe)
    return probe


def _cleanup_probe(probe: Path) -> None:
    entries = _probe_roster(probe)
    for name in PROBE_FILES:
        path = entries[name]
        state = path.lstat()
        if not stat.S_ISREG(state.st_mode):
            fail(f"Refusing to clean non-regular probe member: {path}")
        path.unlink()
    probe.rmdir()
    _fsync_directory(probe.parent)


def _run_finalize(workspace: Path, reference_fasta: Path) -> Path:
    if os.environ.get("SLURM_JOB_ID", "").strip():
        fail("Final qualification must execute after the allocation on the head node")
    roots = _storage_roots(workspace, reference_fasta)
    qualification_id, evidence_root, compute, final, staged = _evidence_paths(roots)
    _canonical_directory(evidence_root, "Storage qualification evidence directory")
    if os.path.lexists(final) or os.path.lexists(staged):
        fail("Final qualification evidence already exists; preserve and inspect it")
    compute_bytes = _read_regular(compute, "Compute qualification receipt")
    compute_value = _json_object(compute_bytes, "Compute qualification receipt")
    _validate_compute(compute_value, qualification_id, roots)
    observed_compute = compute_value["compute"]
    if (
        observed_compute["uid"] != os.geteuid()
        or observed_compute["gid"] != os.getegid()
    ):
        fail("Head and compute numeric UID/GID identities differ")
    probes = [
        _validate_retained_probe(row, root)
        for row, root in zip(compute_value["roots"], roots, strict=True)
    ]
    final_value = {
        "schema": SCHEMA,
        "status": "qualified",
        "qualification_id": qualification_id,
        "compute_receipt": {
            "path": str(compute),
            "sha256": hashlib.sha256(compute_bytes).hexdigest(),
        },
        "compute": observed_compute,
        "head": {
            "gid": os.getegid(),
            "host": socket.gethostname(),
            "uid": os.geteuid(),
        },
        "roots": [
            {"role": role, "root": _root_snapshot(root)}
            for role, root in zip(ROLES, roots, strict=True)
        ],
        "checks": list(CHECKS),
    }
    _write_exclusive(staged, _json_bytes(final_value))
    for probe in probes:
        _cleanup_probe(probe)
    try:
        os.link(staged, final, follow_symlinks=False)
    except OSError as exc:
        fail(f"Could not publish final qualification receipt without replacement: {exc}")
    _fsync_directory(evidence_root)
    staged.unlink()
    _fsync_directory(evidence_root)
    return final


def admit_final_qualification(
    workspace: Path,
    reference_fasta: Path,
) -> QualifiedStorage:
    """Read and validate the exact qualification required by the doctor."""
    roots = _storage_roots(workspace, reference_fasta)
    qualification_id, evidence_root, compute, final, staged = _evidence_paths(roots)
    _canonical_directory(evidence_root, "Storage qualification evidence directory")
    if os.path.lexists(staged):
        fail(f"Incomplete final qualification publication is present: {staged}")
    final_bytes = _read_regular(final, "Final storage qualification receipt")
    value = _json_object(final_bytes, "Final storage qualification receipt")
    if set(value) != {
        "schema",
        "status",
        "qualification_id",
        "compute_receipt",
        "compute",
        "head",
        "roots",
        "checks",
    }:
        fail("Final storage qualification receipt has invalid fields")
    if (
        value["schema"] != SCHEMA
        or value["status"] != "qualified"
        or value["qualification_id"] != qualification_id
        or value["checks"] != list(CHECKS)
    ):
        fail("Final storage qualification receipt has invalid identity or status")
    compute_bytes = _read_regular(compute, "Compute qualification receipt")
    compute_value = _json_object(compute_bytes, "Compute qualification receipt")
    _validate_compute(compute_value, qualification_id, roots)
    receipt_binding = value["compute_receipt"]
    if (
        not isinstance(receipt_binding, dict)
        or receipt_binding.get("path") != str(compute)
        or receipt_binding.get("sha256") != hashlib.sha256(compute_bytes).hexdigest()
        or value["compute"] != compute_value["compute"]
    ):
        fail("Final qualification does not bind the retained compute receipt")
    for context in ("compute", "head"):
        identity = value.get(context)
        if (
            not isinstance(identity, dict)
            or identity.get("uid") != os.geteuid()
            or identity.get("gid") != os.getegid()
        ):
            fail("Current numeric UID/GID differs from qualified head/compute identity")
    rows = value["roots"]
    if not isinstance(rows, list) or len(rows) != len(ROLES):
        fail("Final qualification has invalid root roster")
    for role, root, row in zip(ROLES, roots, rows, strict=True):
        if (
            not isinstance(row, dict)
            or row.get("role") != role
            or not isinstance(row.get("root"), dict)
            or not _stable_snapshot(row["root"], _root_snapshot(root))
        ):
            fail(f"Qualified storage identity no longer matches {role}")
    return QualifiedStorage(
        receipt_path=final,
        receipt_sha256=hashlib.sha256(final_bytes).hexdigest(),
        qualification_id=qualification_id,
    )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=("compute", "finalize"))
    parser.add_argument("--execute", action="store_true")


def qualify_from_args(arguments: argparse.Namespace) -> int:
    """Plan or execute one two-phase storage qualification."""
    try:
        roots = _storage_roots(arguments.workspace, arguments.reference_fasta)
        qualification_id, evidence_root, compute, final, _staged = _evidence_paths(
            roots
        )
        print(f"Qualification ID: {qualification_id}")
        print(f"Workflow workspace parent: {roots[0]}")
        print(f"Step 00c sidecar parent: {roots[1]}")
        print(f"Evidence directory: {evidence_root}")
        print(f"Compute receipt: {compute}")
        print(f"Final receipt: {final}")
        print(f"Phase: {arguments.phase}")
        if not arguments.execute:
            print("Dry-run complete; no directories or files were created.")
            return 0
        if arguments.phase == "compute":
            published = _run_compute(
                arguments.workspace,
                arguments.reference_fasta,
            )
            print(f"Published compute qualification receipt: {published}")
        else:
            published = _run_finalize(
                arguments.workspace,
                arguments.reference_fasta,
            )
            print(f"Published final storage qualification receipt: {published}")
        return 0
    except StorageQualificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = (
    "CHECKS",
    "QualifiedStorage",
    "StorageQualificationError",
    "admit_final_qualification",
    "configure_parser",
    "qualify_from_args",
)
