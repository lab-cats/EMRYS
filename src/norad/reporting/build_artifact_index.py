#!/usr/bin/env python3
"""Build a read-only, explicit artifact index for one immutable NORAD run.

The command never discovers pipeline inputs, invokes analysis software, or
changes native Step 00a-09c outputs. Every source comes from one validated
inventory row. Dry-run is the default; execute mode publishes one JSON record
per row, an inventory-ordered TSV index, and a receipt last as a
rollback-protected transaction.
"""

from __future__ import annotations

import os
import shutil
import signal as signal
import sys
import uuid as uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

src_root = str(Path(__file__).resolve().parents[2])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.reporting import _signals
from norad.reporting._artifact_index import contracts as _contract_owners
from norad.reporting._artifact_index import core as _core_owner
from norad.reporting._artifact_index import models as _models_owner
from norad.reporting._artifact_index import publication as _publication_owner
from norad.reporting._artifact_index import records as _records_owner
from norad.reporting._artifact_index import registry as _registry_owner
from norad.reporting._artifact_index.binary_readers import (
    BGZF_EOF_BLOCK as BGZF_EOF_BLOCK,
)
from norad.reporting._artifact_index.context import (
    prepare_context,
    print_context,
)
from norad.reporting._artifact_index.context import (
    recheck_inputs as recheck_inputs,
)
from norad.reporting._artifact_index.models import (
    ArtifactIndexError,
    BuildContext,
    LockOwnership,
)
from norad.reporting._artifact_index.validation import (
    validate_published_transaction,
)

contracts = _contract_owners.contracts
step08 = _contract_owners.step08
step09 = _contract_owners.step09
review_package = _contract_owners.review_package

# The exact script path remains the public CLI and compatibility facade. These
# bindings intentionally preserve its established direct-import surface.
ADAPTER_REGISTRY = _core_owner.ADAPTER_REGISTRY
parse_args = _core_owner.parse_args
get_git_commit = _core_owner.get_git_commit
canonical_json_bytes = _core_owner.canonical_json_bytes
safe_tsv = _core_owner.safe_tsv
utc_now = _core_owner.utc_now
load_run_contract = _core_owner.load_run_contract
sha256_bytes = _core_owner.sha256_bytes

RUN_CONTRACT_FIELDS = _models_owner.RUN_CONTRACT_FIELDS
SHA256_RE = _models_owner.SHA256_RE
VALIDATION_REPORT_HEADER = _models_owner.VALIDATION_REPORT_HEADER

ARTIFACT_INDEX_HEADER = _records_owner.ARTIFACT_INDEX_HEADER
ARTIFACT_RECEIPT_HEADER = _records_owner.ARTIFACT_RECEIPT_HEADER
build_index_rows = _records_owner.build_index_rows
build_receipt_row = _records_owner.build_receipt_row
producer_evidence = _records_owner.producer_evidence
STEP_PRODUCERS = _records_owner.STEP_PRODUCERS
read_exact_tsv = _records_owner.read_exact_tsv
tsv_bytes = _records_owner.tsv_bytes
inventory_rows_from_published_index = _records_owner.inventory_rows_from_published_index
load_existing_receipt = _records_owner.load_existing_receipt
validate_existing_identity = _records_owner.validate_existing_identity

STEP06_COUNTS_HEADER = _registry_owner.STEP06_COUNTS_HEADER
STEP07_RECEIPT_HEADER = _registry_owner.STEP07_RECEIPT_HEADER


class _LiveFacadeBindings:
    """Resolve patchable operations from this exact loaded module instance."""

    def __getattr__(self, name: str) -> Any:
        try:
            return globals()[name]
        except KeyError as exc:  # pragma: no cover - internal programming error
            raise AttributeError(name) from exc


_PUBLICATION_BINDINGS = _LiveFacadeBindings()


def validate_existing_transaction(
    *,
    existing: Mapping[str, str],
    run_id: str,
    run_contract: Mapping[str, Any],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
) -> None:
    """Validate a predecessor through this facade's patchable validator."""

    previous_inventory_rows = inventory_rows_from_published_index(artifacts_path)
    validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract,
        run_contract_path=Path(existing["run_contract_path"]),
        run_contract_file_sha256=existing["run_contract_file_sha256"],
        inventory_path=Path(existing["inventory_path"]),
        inventory_sha256=existing["inventory_sha256"],
        inventory_rows=previous_inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        require_current_source_locations=False,
    )


def write_bytes_exclusive(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not write temporary file {path}: {exc}"
        ) from exc


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not open directory for durability sync {path}: {exc}"
        ) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not durability-sync directory {path}: {exc}"
        ) from exc
    finally:
        os.close(descriptor)


def acquire_lock(
    lock_path: Path,
    run_id: str,
    run_token: str,
) -> LockOwnership:
    payload = (
        f"run_id\t{run_id}\npid\t{os.getpid()}\nrun_token\t{run_token}\n"
    ).encode()
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        ) from exc
    except OSError as exc:
        raise ArtifactIndexError(f"Could not acquire lock {lock_path}: {exc}") from exc
    stat_result = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            lock_path.unlink()
        except OSError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not write lock metadata and could not remove the "
                f"incomplete owned lock {lock_path}: {exc}; {cleanup_exc}"
            ) from exc
        raise ArtifactIndexError(f"Could not write lock metadata: {exc}") from exc
    return LockOwnership(
        device=stat_result.st_dev,
        inode=stat_result.st_ino,
        run_token=run_token,
    )


def release_owned_lock(
    lock_path: Path,
    ownership: LockOwnership,
) -> None:
    try:
        if lock_path.is_symlink():
            raise ArtifactIndexError(
                f"Owned lock was replaced by a symlink: {lock_path}"
            )
        with lock_path.open(encoding="utf-8") as stream:
            stat_result = os.fstat(stream.fileno())
            payload = stream.read()
    except FileNotFoundError as exc:
        raise ArtifactIndexError(
            f"Owned lock disappeared before cleanup: {lock_path}"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(
            f"Could not verify owned lock before cleanup: {lock_path}: {exc}"
        ) from exc
    if (
        stat_result.st_dev != ownership.device
        or stat_result.st_ino != ownership.inode
        or f"run_token\t{ownership.run_token}\n" not in payload
    ):
        raise ArtifactIndexError(
            f"Owned lock identity changed before cleanup: {lock_path}"
        )
    try:
        lock_path.unlink()
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not remove verified owned lock {lock_path}: {exc}"
        ) from exc


def remove_owned(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def install_publication_signal_handlers() -> dict[int, Any]:
    return _signals.install(ArtifactIndexError, "Artifact-index", "publication")


restore_signal_handlers = _signals.restore


def publish_context(context: BuildContext) -> None:
    """Delegate through this module's live compatibility bindings."""

    _publication_owner.publish_context(
        context,
        facade=_PUBLICATION_BINDINGS,
    )


def main() -> int:
    arguments = parse_args()
    try:
        context = prepare_context(arguments)
        print_context(context, arguments.execute)
        if arguments.execute:
            publish_context(context)
            print(f"Published artifact index: {context.artifacts_path}")
            print(f"Published receipt last: {context.receipt_path}")
    except (
        ArtifactIndexError,
        contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
