"""Shared validation API used by NORAD owner-local validators."""

from norad.libraries.validation.errors import ValidationError, fail
from norad.libraries.validation.inputs import (
    Snapshot,
    lexical_path,
    resolve_from_base,
    snapshots,
    regular_snapshot,
    read_bytes,
    integer_stdout,
    require_unchanged,
    stable_text,
)
from norad.libraries.validation.publication import publish
from norad.libraries.validation.report import (
    HEADER,
    clean,
    render,
    row,
    validate_report,
)
from norad.libraries.validation.tsv import attempt, read_header, read_tsv, sha256_file
from norad.libraries.validation.runtime import Runtime, finish

__all__ = (
    "HEADER",
    "attempt",
    "Runtime",
    "Snapshot",
    "lexical_path",
    "resolve_from_base",
    "snapshots",
    "integer_stdout",
    "ValidationError",
    "clean",
    "fail",
    "finish",
    "publish",
    "regular_snapshot",
    "read_bytes",
    "render",
    "require_unchanged",
    "row",
    "read_header",
    "read_tsv",
    "sha256_file",
    "stable_text",
    "validate_report",
)
