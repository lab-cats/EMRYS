"""Build a read-only, explicit artifact index for one immutable NORAD run.

The command never discovers pipeline inputs, invokes analysis software, or
changes native Step 00a-09c outputs. Every source comes from one validated
inventory row. Dry-run is the default; execute mode publishes one JSON record
per row, an inventory-ordered TSV index, and a receipt last as a
rollback-protected transaction.
"""

from __future__ import annotations

import signal as signal
import sys
import uuid as uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from norad.reporting._artifact_index import api as _api_owner
from norad.reporting._artifact_index import contracts as _contract_owners
from norad.reporting._artifact_index import core as _core_owner
from norad.reporting._artifact_index import models as _models_owner
from norad.reporting._artifact_index import publication as _publication_owner
from norad.reporting._artifact_index import records as _records_owner
from norad.reporting._artifact_index import registry as _registry_owner
from norad.reporting._artifact_index.binary_readers import (
    BGZF_EOF_BLOCK as BGZF_EOF_BLOCK,
)
from norad.reporting._artifact_index.context import prepare_context as _prepare_context
from norad.reporting._artifact_index.context import print_context
from norad.reporting._artifact_index.context import (
    recheck_inputs as recheck_inputs,
)
from norad.reporting._artifact_index.models import (
    ArtifactIndexError,
    BuildContext,
)
from norad.reporting._artifact_index.source_checkout import (
    SourceCheckoutError,
    admit_source_checkout,
)
from norad.reporting._artifact_index.validation import (
    validate_published_transaction,
)

if TYPE_CHECKING:
    import argparse as _argparse

    from norad.reporting._artifact_index.source_checkout import (
        SourceCheckout as _SourceCheckout,
    )

contracts = _api_owner.contracts
step08 = _contract_owners.step08
step09 = _contract_owners.step09
review_package = _contract_owners.review_package

# Publication resolves these bindings from the private builder at call time so
# focused fault injection continues to exercise the real transaction owner.
ADAPTER_REGISTRY = _core_owner.ADAPTER_REGISTRY
os = _publication_owner.os
LockOwnership = _models_owner.LockOwnership
get_git_commit = _api_owner.get_git_commit
canonical_json_bytes = _api_owner.canonical_json_bytes
safe_tsv = _api_owner.safe_tsv
utc_now = _api_owner.utc_now
load_run_contract = _api_owner.load_run_contract
sha256_bytes = _api_owner.sha256_bytes

RUN_CONTRACT_FIELDS = _api_owner.RUN_CONTRACT_FIELDS
SHA256_RE = _api_owner.SHA256_RE
VALIDATION_REPORT_HEADER = _models_owner.VALIDATION_REPORT_HEADER

ARTIFACT_INDEX_HEADER = _api_owner.ARTIFACT_INDEX_HEADER
ARTIFACT_RECEIPT_HEADER = _api_owner.ARTIFACT_RECEIPT_HEADER
build_index_rows = _records_owner.build_index_rows
build_receipt_row = _records_owner.build_receipt_row
producer_evidence = _records_owner.producer_evidence
STEP_PRODUCERS = _records_owner.STEP_PRODUCERS
read_exact_tsv = _api_owner.read_exact_tsv
tsv_bytes = _api_owner.tsv_bytes
inventory_rows_from_published_index = _records_owner.inventory_rows_from_published_index
load_existing_receipt = _records_owner.load_existing_receipt
validate_existing_identity = _records_owner.validate_existing_identity

write_bytes_exclusive = _api_owner.write_bytes_exclusive
fsync_directory = _api_owner.fsync_directory
acquire_lock = _api_owner.acquire_lock
release_owned_lock = _api_owner.release_owned_lock
remove_owned = _api_owner.remove_owned
install_publication_signal_handlers = _api_owner.install_publication_signal_handlers
restore_signal_handlers = _api_owner.restore_signal_handlers

STEP06_COUNTS_HEADER = _registry_owner.STEP06_COUNTS_HEADER
STEP07_RECEIPT_HEADER = _registry_owner.STEP07_RECEIPT_HEADER


def validate_existing_transaction(
    *,
    existing: Mapping[str, str],
    run_id: str,
    run_contract: Mapping[str, Any],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
    source_root: Path = contracts.REPO_ROOT,
) -> None:
    """Validate a predecessor through this builder's patchable validator."""

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
        source_root=source_root,
    )


def prepare_context(
    arguments: _argparse.Namespace,
    *,
    source_checkout: _SourceCheckout,
) -> BuildContext:
    """Build through the explicitly admitted source authority."""

    return _prepare_context(arguments, source_checkout=source_checkout)


def publish_context(context: BuildContext) -> None:
    """Delegate through this builder's live fault-injection bindings."""

    _publication_owner.publish_context(
        context,
        facade=sys.modules[__name__],
    )


def build_from_args(arguments: _argparse.Namespace) -> int:
    """Build or publish one explicitly rooted artifact-index transaction."""
    try:
        source_checkout = admit_source_checkout(
            root=arguments.source_checkout,
            package_root=Path(__file__).resolve().parents[2],
        )
        context = prepare_context(
            arguments,
            source_checkout=source_checkout,
        )
        print_context(context, arguments.execute)
        if arguments.execute:
            publish_context(context)
            print(f"Published artifact index: {context.artifacts_path}")
            print(f"Published receipt last: {context.receipt_path}")
    except (
        ArtifactIndexError,
        SourceCheckoutError,
        contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0
