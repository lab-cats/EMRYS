"""Curated artifact-index API for sibling reporting owners."""

from __future__ import annotations

from .contracts import contracts
from .core import (
    canonical_json_bytes,
    get_git_commit,
    load_run_contract,
    safe_tsv,
    sha256_bytes,
    utc_now,
)
from .models import (
    ARTIFACT_INDEX_HEADER,
    ARTIFACT_RECEIPT_HEADER,
    RUN_CONTRACT_FIELDS,
    SHA256_RE,
    ArtifactIndexError,
)
from .publication import (
    acquire_lock,
    fsync_directory,
    install_publication_signal_handlers,
    release_owned_lock,
    remove_owned,
    restore_signal_handlers,
    write_bytes_exclusive,
)
from .records import read_exact_tsv, tsv_bytes
from .source_checkout import (
    SourceCheckout,
    SourceCheckoutError,
    admit_source_checkout,
)
from .validation import validate_published_transaction

__all__ = (
    "ARTIFACT_INDEX_HEADER",
    "ARTIFACT_RECEIPT_HEADER",
    "RUN_CONTRACT_FIELDS",
    "SHA256_RE",
    "ArtifactIndexError",
    "SourceCheckout",
    "SourceCheckoutError",
    "acquire_lock",
    "admit_source_checkout",
    "canonical_json_bytes",
    "contracts",
    "fsync_directory",
    "get_git_commit",
    "install_publication_signal_handlers",
    "load_run_contract",
    "read_exact_tsv",
    "release_owned_lock",
    "remove_owned",
    "restore_signal_handlers",
    "safe_tsv",
    "sha256_bytes",
    "tsv_bytes",
    "utc_now",
    "validate_published_transaction",
    "write_bytes_exclusive",
)
