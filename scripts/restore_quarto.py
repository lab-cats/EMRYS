#!/usr/bin/env python3
"""Restore the one approved Quarto release into ignored local tool storage.

This command is the only report-layer operation allowed to download or install
Quarto.  It verifies the official archive checksum before safe extraction,
validates the executable version, and atomically publishes a versioned local
directory.  Report rendering never calls this command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable


QUARTO_VERSION = "1.9.38"
QUARTO_ARCHIVE_NAME = f"quarto-{QUARTO_VERSION}-macos.tar.gz"
QUARTO_URL = (
    "https://github.com/quarto-dev/quarto-cli/releases/download/"
    f"v{QUARTO_VERSION}/{QUARTO_ARCHIVE_NAME}"
)
QUARTO_SHA256 = (
    "47089a5020cfb41981ba0d4b46e110ed"
    "fa608722aea45ef248e14efba6d6b18a"
)
INSTALL_RECEIPT_NAME = ".norad-quarto-install.json"
INSTALL_RECEIPT_SCHEMA_VERSION = "1.0.0"
SAFE_TOOL_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"


class QuartoRestoreError(RuntimeError):
    """Raised when the pinned local Quarto restore cannot be completed safely."""


@dataclass(frozen=True)
class LockOwnership:
    path: Path
    token: str
    device: int
    inode: int


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            f"Restore checksum-pinned Quarto {QUARTO_VERSION} into "
            "repository-local ignored storage."
        )
    )
    parser.add_argument(
        "--install-root",
        required=True,
        type=Path,
        help=(
            "Parent directory for the versioned installation. The executable "
            f"will be <install-root>/{QUARTO_VERSION}/bin/quarto."
        ),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help=(
            "Optional already-downloaded official archive. It is still "
            "verified against the pinned SHA-256."
        ),
    )
    return parser.parse_args(argv)


def _fail(message: str) -> None:
    raise QuartoRestoreError(message)


def _explicit_path(path: Path, label: str) -> Path:
    value = str(path)
    if not value or value.strip() != value:
        _fail(f"{label} must be a non-empty path without surrounding whitespace")
    if "\x00" in value or "\n" in value or "\r" in value:
        _fail(f"{label} contains an invalid control character")
    if any(part in {".", ".."} for part in path.parts):
        _fail(f"{label} must not contain '.' or '..' components: {path}")
    if any(token in value for token in ("*", "?", "[", "]", "${", "{{", "}}")):
        _fail(f"{label} must be explicit and must not contain glob/template syntax")
    return path.absolute()


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        if not os.path.lexists(current):
            continue
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            _fail(f"Could not inspect {label} component {current}: {exc}")
        if stat.S_ISLNK(mode):
            _fail(f"{label} must not traverse a symbolic link: {current}")


def _require_regular_file(path: Path, label: str) -> os.stat_result:
    if not os.path.lexists(path):
        _fail(f"{label} does not exist: {path}")
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"Could not inspect {label} {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} must be a regular non-symlink file: {path}")
    return metadata


def _sha256_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    _require_regular_file(path, "Quarto archive")
    try:
        with path.open("rb") as stream:
            return _sha256_stream(stream)
    except OSError as exc:
        _fail(f"Could not hash Quarto archive {path}: {exc}")


def _tree_sha256(root: Path) -> str:
    """Hash the installed tree without following links or hashing its receipt."""

    if root.is_symlink() or not root.is_dir():
        _fail(f"Quarto tree must be a non-symlink directory: {root}")
    records: list[dict[str, object]] = []
    try:
        for current, directory_names, file_names in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current_path = Path(current)
            directory_names.sort()
            file_names.sort()
            traversable: list[str] = []
            for name in directory_names:
                path = current_path / name
                metadata = path.lstat()
                relative = path.relative_to(root).as_posix()
                if stat.S_ISLNK(metadata.st_mode):
                    records.append(
                        {
                            "mode": stat.S_IMODE(metadata.st_mode),
                            "path": relative,
                            "target": os.readlink(path),
                            "type": "symlink",
                        }
                    )
                elif stat.S_ISDIR(metadata.st_mode):
                    records.append(
                        {
                            "mode": stat.S_IMODE(metadata.st_mode),
                            "path": relative,
                            "type": "directory",
                        }
                    )
                    traversable.append(name)
                else:
                    _fail(
                        "Quarto tree contains an unsupported directory entry: "
                        f"{path}"
                    )
            directory_names[:] = traversable
            for name in file_names:
                path = current_path / name
                relative = path.relative_to(root).as_posix()
                if relative == INSTALL_RECEIPT_NAME:
                    continue
                metadata = path.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    records.append(
                        {
                            "mode": stat.S_IMODE(metadata.st_mode),
                            "path": relative,
                            "target": os.readlink(path),
                            "type": "symlink",
                        }
                    )
                elif stat.S_ISREG(metadata.st_mode):
                    with path.open("rb") as stream:
                        content_sha256 = _sha256_stream(stream)
                    records.append(
                        {
                            "mode": stat.S_IMODE(metadata.st_mode),
                            "path": relative,
                            "sha256": content_sha256,
                            "size_bytes": metadata.st_size,
                            "type": "file",
                        }
                    )
                else:
                    _fail(
                        "Quarto tree contains an unsupported filesystem entry: "
                        f"{path}"
                    )
    except QuartoRestoreError:
        raise
    except OSError as exc:
        _fail(f"Could not inspect installed Quarto tree {root}: {exc}")
    encoded = json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _install_receipt_bytes(
    *,
    archive_sha256: str,
    tree_sha256: str,
) -> bytes:
    document = {
        "archive_sha256": archive_sha256,
        "archive_url": QUARTO_URL,
        "producer": "restore_quarto",
        "quarto_version": QUARTO_VERSION,
        "schema_version": INSTALL_RECEIPT_SCHEMA_VERSION,
        "tree_sha256": tree_sha256,
    }
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _write_install_receipt(root: Path, archive_sha256: str) -> None:
    receipt = root / INSTALL_RECEIPT_NAME
    tree_sha256 = _tree_sha256(root)
    payload = _install_receipt_bytes(
        archive_sha256=archive_sha256,
        tree_sha256=tree_sha256,
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(receipt, flags, 0o644)
    except OSError as exc:
        _fail(f"Could not create Quarto install receipt {receipt}: {exc}")
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    except Exception:
        os.close(descriptor)
        try:
            receipt.unlink()
        except OSError:
            pass
        raise
    os.close(descriptor)
    _fsync_directory(root)


def _validate_install_receipt(target: Path, expected_sha256: str) -> None:
    receipt = target / INSTALL_RECEIPT_NAME
    _require_regular_file(receipt, "Quarto install receipt")
    try:
        payload = receipt.read_bytes()
        document = json.loads(payload)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"Could not read Quarto install receipt {receipt}: {exc}")
    if not isinstance(document, dict):
        _fail(f"Quarto install receipt must be a JSON object: {receipt}")
    tree_sha256 = _tree_sha256(target)
    expected = _install_receipt_bytes(
        archive_sha256=expected_sha256,
        tree_sha256=tree_sha256,
    )
    if payload != expected:
        _fail(
            "Quarto install receipt or installed tree does not match the "
            f"verified restore contract: {receipt}"
        )


def _member_path(member: tarfile.TarInfo) -> PurePosixPath:
    raw = member.name
    if any(ord(character) < 32 or ord(character) == 127 for character in raw):
        _fail("Quarto archive contains a control byte in a member name")
    path = PurePosixPath(raw)
    normalized_parts = tuple(part for part in path.parts if part not in {"", "."})
    if path.is_absolute() or any(part == ".." for part in normalized_parts):
        _fail(f"Quarto archive contains an unsafe member path: {raw!r}")
    if not normalized_parts:
        return PurePosixPath(".")
    return PurePosixPath(*normalized_parts)


def _validate_link_target(
    member_path: PurePosixPath,
    link_name: str,
) -> None:
    target = PurePosixPath(link_name)
    if target.is_absolute() or any(
        ord(character) < 32 or ord(character) == 127
        for character in link_name
    ):
        _fail(
            f"Quarto archive link {str(member_path)!r} has an unsafe target: "
            f"{link_name!r}"
        )
    combined = member_path.parent.joinpath(target)
    depth = 0
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            depth -= 1
        else:
            depth += 1
        if depth < 0:
            _fail(
                f"Quarto archive link {str(member_path)!r} escapes extraction "
                f"storage: {link_name!r}"
            )


def validate_archive_members(members: Iterable[tarfile.TarInfo]) -> None:
    seen: set[PurePosixPath] = set()
    for member in members:
        member_path = _member_path(member)
        if member_path in seen and member_path != PurePosixPath("."):
            _fail(f"Quarto archive contains duplicate member {str(member_path)!r}")
        seen.add(member_path)
        if member.isdev() or member.isfifo():
            _fail(
                f"Quarto archive contains an unsupported special member: "
                f"{member.name!r}"
            )
        if member.issym() or member.islnk():
            _validate_link_target(member_path, member.linkname)


def _extract_archive(archive: Path, destination: Path) -> None:
    try:
        with tarfile.open(archive, mode="r:gz") as bundle:
            members = bundle.getmembers()
            validate_archive_members(members)
            bundle.extractall(destination, members=members, filter="data")
    except TypeError as exc:
        _fail(
            "This Python runtime lacks the required safe tar extraction "
            f"filter; refusing an unfiltered Quarto restore: {exc}"
        )
    except QuartoRestoreError:
        raise
    except (OSError, tarfile.TarError) as exc:
        _fail(f"Could not safely extract Quarto archive {archive}: {exc}")


def _quarto_version(executable: Path) -> str:
    metadata = _require_regular_file(executable, "Quarto executable")
    if not metadata.st_mode & stat.S_IXUSR:
        _fail(f"Quarto executable is not executable: {executable}")
    try:
        environment = {
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
            "PATH": SAFE_TOOL_PATH,
            "TMPDIR": "/tmp",
            "TZ": "UTC",
        }
        result = subprocess.run(
            [str(executable), "--version"],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _fail(f"Could not execute {executable} --version: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        _fail(f"Quarto version check failed for {executable}: {detail}")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if lines != [QUARTO_VERSION]:
        _fail(
            f"Quarto executable reported {result.stdout.strip()!r}; expected "
            f"exactly {QUARTO_VERSION!r}"
        )
    return lines[0]


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lock_payload(token: str) -> str:
    return (
        "owner\tNORAD_QUARTO_RESTORE\n"
        f"pid\t{os.getpid()}\n"
        f"token\t{token}\n"
        f"version\t{QUARTO_VERSION}\n"
    )


def _acquire_lock(path: Path, token: str) -> LockOwnership:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        _fail(f"Quarto restore lock already exists: {path}")
    except OSError as exc:
        _fail(f"Could not create Quarto restore lock {path}: {exc}")
    try:
        payload = _lock_payload(token).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
    except Exception:
        os.close(descriptor)
        try:
            path.unlink()
        except OSError:
            pass
        raise
    os.close(descriptor)
    return LockOwnership(
        path=path,
        token=token,
        device=metadata.st_dev,
        inode=metadata.st_ino,
    )


def _release_lock(ownership: LockOwnership) -> None:
    metadata = _require_regular_file(ownership.path, "owned Quarto restore lock")
    if (
        metadata.st_dev != ownership.device
        or metadata.st_ino != ownership.inode
        or f"token\t{ownership.token}\n"
        not in ownership.path.read_text(encoding="utf-8")
    ):
        _fail(
            "Quarto restore lock identity or ownership changed; refusing cleanup: "
            f"{ownership.path}"
        )
    ownership.path.unlink()


def _download_archive(destination: Path) -> None:
    curl = shutil.which("curl")
    if curl is None:
        _fail("curl is required to download the pinned Quarto archive")
    print(f"Downloading official Quarto archive: {QUARTO_URL}")
    try:
        result = subprocess.run(
            [
                curl,
                "--disable",
                "--fail",
                "--location",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--tlsv1.2",
                "--connect-timeout",
                "30",
                "--max-time",
                "600",
                "--max-filesize",
                "300000000",
                "--silent",
                "--show-error",
                "--output",
                str(destination),
                QUARTO_URL,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        _fail(f"Could not start curl: {exc}")
    if result.returncode != 0:
        _fail(f"Could not download pinned Quarto archive: {result.stderr.strip()}")


def _copy_archive_to_owned_stage(source: Path, destination: Path) -> None:
    """Bind untrusted path input to one owned regular file before verification."""

    source_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        source_flags |= os.O_NOFOLLOW
    try:
        source_descriptor = os.open(source, source_flags)
    except OSError as exc:
        _fail(f"Could not open Quarto archive for a bound copy {source}: {exc}")
    destination_descriptor: int | None = None
    try:
        source_metadata = os.fstat(source_descriptor)
        if not stat.S_ISREG(source_metadata.st_mode):
            _fail(f"Quarto archive must be a regular file: {source}")
        destination_descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        while True:
            block = os.read(source_descriptor, 1024 * 1024)
            if not block:
                break
            offset = 0
            while offset < len(block):
                offset += os.write(destination_descriptor, block[offset:])
        os.fsync(destination_descriptor)
        final_source_metadata = os.fstat(source_descriptor)
        if (
            final_source_metadata.st_dev != source_metadata.st_dev
            or final_source_metadata.st_ino != source_metadata.st_ino
            or final_source_metadata.st_size != source_metadata.st_size
            or final_source_metadata.st_mtime_ns != source_metadata.st_mtime_ns
            or final_source_metadata.st_ctime_ns != source_metadata.st_ctime_ns
        ):
            _fail("Quarto archive changed while it was copied into owned storage")
    except QuartoRestoreError:
        raise
    except OSError as exc:
        _fail(f"Could not copy Quarto archive into owned storage: {exc}")
    finally:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        os.close(source_descriptor)


def _remove_owned_tree(
    path: Path,
    token: str,
    identity: tuple[int, int] | None,
) -> None:
    if not os.path.lexists(path):
        return
    metadata = path.lstat()
    if (
        token not in path.name
        or identity is None
        or (metadata.st_dev, metadata.st_ino) != identity
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(f"Refusing to remove unverified Quarto staging path: {path}")
    shutil.rmtree(path)


def validate_installation(
    target: Path,
    *,
    expected_sha256: str = QUARTO_SHA256,
) -> Path:
    if not os.path.lexists(target):
        _fail(f"Quarto installation does not exist: {target}")
    metadata = target.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail(f"Quarto installation must be a non-symlink directory: {target}")
    _validate_install_receipt(target, expected_sha256)
    executable = target / "bin" / "quarto"
    _quarto_version(executable)
    return executable


def restore_from_archive(
    *,
    archive: Path,
    install_root: Path,
    expected_sha256: str = QUARTO_SHA256,
) -> Path:
    """Verify, extract, and atomically publish one archive.

    ``expected_sha256`` is injectable for focused unit tests. The public CLI
    never accepts an expected checksum and always passes the pinned constant.
    """

    install_root = _explicit_path(install_root, "install root")
    archive = _explicit_path(archive, "Quarto archive")
    _reject_symlink_components(install_root, "install root")
    _reject_symlink_components(archive, "Quarto archive")
    _require_regular_file(archive, "Quarto archive")

    install_root.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(install_root, "install root")
    if install_root.is_symlink() or not install_root.is_dir():
        _fail(f"Install root must be a non-symlink directory: {install_root}")

    target = install_root / QUARTO_VERSION
    if os.path.lexists(target):
        executable = validate_installation(
            target,
            expected_sha256=expected_sha256,
        )
        print(f"Pinned Quarto is already valid: {executable}")
        return executable

    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    lock_path = install_root / f".restore-{QUARTO_VERSION}.lock"
    stage = install_root / f".restore-{QUARTO_VERSION}.{token}.tmp"
    ownership = _acquire_lock(lock_path, token)
    published = False
    published_identity: tuple[int, int] | None = None
    stage_identity: tuple[int, int] | None = None
    recovery_required = False
    recovery_path = (
        install_root / f".restore-{QUARTO_VERSION}.{token}.RECOVERY.txt"
    )
    try:
        if os.path.lexists(target):
            executable = validate_installation(
                target,
                expected_sha256=expected_sha256,
            )
            print(f"Pinned Quarto became available: {executable}")
            return executable
        os.mkdir(stage, 0o700)
        stage_metadata = stage.lstat()
        stage_identity = (stage_metadata.st_dev, stage_metadata.st_ino)
        extract_root = stage / "extracted"
        extract_root.mkdir()
        owned_archive = stage / QUARTO_ARCHIVE_NAME
        _copy_archive_to_owned_stage(archive, owned_archive)

        observed_sha256 = sha256_file(owned_archive)
        if observed_sha256 != expected_sha256:
            _fail(
                "Quarto archive SHA-256 mismatch: "
                f"observed {observed_sha256}; expected {expected_sha256}"
            )
        _extract_archive(owned_archive, extract_root)
        if sha256_file(owned_archive) != observed_sha256:
            _fail("Owned Quarto archive changed while it was being restored")

        executable = extract_root / "bin" / "quarto"
        _quarto_version(executable)
        _write_install_receipt(extract_root, observed_sha256)
        if os.path.lexists(target):
            _fail(f"Quarto target appeared during restore: {target}")
        os.replace(extract_root, target)
        published = True
        target_metadata = target.lstat()
        published_identity = (target_metadata.st_dev, target_metadata.st_ino)
        _fsync_directory(install_root)
        executable = validate_installation(
            target,
            expected_sha256=expected_sha256,
        )
        print(f"Installed pinned Quarto {QUARTO_VERSION}: {executable}")
        return executable
    except Exception as original_exc:
        if (
            published
            and published_identity is not None
            and os.path.lexists(target)
        ):
            try:
                metadata = target.lstat()
                if (
                    metadata.st_dev,
                    metadata.st_ino,
                ) != published_identity or not stat.S_ISDIR(metadata.st_mode):
                    raise QuartoRestoreError(
                        "published Quarto target changed identity"
                    )
                recovery = stage / "published-install"
                os.replace(target, recovery)
                recovery_metadata = recovery.lstat()
                if (
                    recovery_metadata.st_dev,
                    recovery_metadata.st_ino,
                ) != published_identity:
                    raise QuartoRestoreError(
                        "published Quarto target changed during cleanup"
                    )
                shutil.rmtree(recovery)
                _fsync_directory(install_root)
            except (OSError, QuartoRestoreError) as cleanup_exc:
                recovery_required = True
                try:
                    recovery_path.write_text(
                        "Quarto restore rollback was incomplete.\n"
                        f"Original error: {original_exc}\n"
                        f"Rollback error: {cleanup_exc}\n"
                        f"Target: {target}\n"
                        f"Stage: {stage}\n",
                        encoding="utf-8",
                    )
                except OSError:
                    pass
                raise QuartoRestoreError(
                    "Quarto restore failed after publication and cleanup also "
                    "failed; preserve the lock and recovery state under "
                    f"{install_root}: {cleanup_exc}"
                ) from original_exc
        raise
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required:
            try:
                _remove_owned_tree(stage, token, stage_identity)
            except Exception as exc:  # pragma: no cover - filesystem injection
                cleanup_errors.append(f"owned stage cleanup failed: {exc}")
            if not cleanup_errors:
                try:
                    _release_lock(ownership)
                except Exception as exc:  # pragma: no cover - filesystem injection
                    cleanup_errors.append(f"owned lock cleanup failed: {exc}")
        if cleanup_errors:
            recovery_required = True
            try:
                recovery_path.write_text(
                    "Quarto restore cleanup was incomplete.\n"
                    f"Active error: {active}\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Lock: {lock_path}\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            raise QuartoRestoreError(
                "Quarto restore cleanup failed; preserve the lock and recovery "
                f"state under {install_root}: {'; '.join(cleanup_errors)}"
            ) from active


def restore_quarto(install_root: Path, archive: Path | None = None) -> Path:
    if sys.platform != "darwin":
        _fail(
            "The pinned quarto-1.9.38-macos.tar.gz restore is supported only "
            f"on macOS; observed platform {sys.platform!r}"
        )
    install_root = _explicit_path(install_root, "install root")
    _reject_symlink_components(install_root, "install root")

    target = install_root / QUARTO_VERSION
    if os.path.lexists(target):
        executable = validate_installation(
            target,
            expected_sha256=QUARTO_SHA256,
        )
        print(f"Pinned Quarto is already valid: {executable}")
        return executable

    download_root = install_root.parent
    _reject_symlink_components(download_root, "download parent")
    download_root.mkdir(parents=True, exist_ok=True)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    download_stage = download_root / f".quarto-download-{token}.tmp"
    download_stage.mkdir(mode=0o700)
    download_metadata = download_stage.lstat()
    download_identity = (download_metadata.st_dev, download_metadata.st_ino)
    try:
        if archive is None:
            resolved_archive = download_stage / QUARTO_ARCHIVE_NAME
            _download_archive(resolved_archive)
        else:
            resolved_archive = _explicit_path(archive, "Quarto archive")
        return restore_from_archive(
            archive=resolved_archive,
            install_root=install_root,
            expected_sha256=QUARTO_SHA256,
        )
    finally:
        _remove_owned_tree(download_stage, token, download_identity)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        executable = restore_quarto(
            install_root=arguments.install_root,
            archive=arguments.archive,
        )
    except QuartoRestoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Quarto restore complete.")
    print(f"  Version: {QUARTO_VERSION}")
    print(f"  SHA-256: {QUARTO_SHA256}")
    print(f"  Executable: {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
