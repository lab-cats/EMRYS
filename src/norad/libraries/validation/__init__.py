"""Shared validation API used by NORAD owner-local validators."""

from norad.libraries.validation.errors import ValidationError, fail
from norad.libraries.validation.inputs import (
    Snapshot,
    integer_stdout,
    lexical_path,
    read_bytes,
    regular_snapshot,
    require_executable,
    require_unchanged,
    resolve_from_base,
    snapshots,
    stable_text,
)
from norad.libraries.validation.publication import publish
from norad.libraries.validation.report import (
    HEADER,
    add_output_arguments,
    clean,
    render,
    row,
    row_builder,
    validate_report,
)
from norad.libraries.validation.runtime import Runtime, finish, run, run_from_args
from norad.libraries.validation.tsv import attempt, read_header, read_tsv, sha256_file

__all__ = (
    "HEADER",
    "Runtime",
    "Snapshot",
    "ValidationError",
    "add_output_arguments",
    "attempt",
    "clean",
    "fail",
    "finish",
    "integer_stdout",
    "lexical_path",
    "publish",
    "read_bytes",
    "read_header",
    "read_tsv",
    "regular_snapshot",
    "render",
    "require_executable",
    "require_unchanged",
    "resolve_from_base",
    "row",
    "row_builder",
    "run",
    "run_from_args",
    "sha256_file",
    "snapshots",
    "stable_text",
    "validate_report",
)
