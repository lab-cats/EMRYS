"""Shared validation API used by EMRYS owner-local validators."""

from emrys.libraries.validation.errors import ValidationError, fail
from emrys.libraries.validation.inputs import (
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
from emrys.libraries.validation.publication import publish
from emrys.libraries.validation.report import (
    HEADER,
    add_output_arguments,
    build_report,
    clean,
    render,
    row,
    validate_report,
)
from emrys.libraries.validation.runtime import Runtime, finish, run, run_from_args
from emrys.libraries.validation.tsv import attempt, read_header, read_tsv, sha256_file

__all__ = (
    "HEADER",
    "Runtime",
    "Snapshot",
    "ValidationError",
    "add_output_arguments",
    "attempt",
    "build_report",
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
    "run",
    "run_from_args",
    "sha256_file",
    "snapshots",
    "stable_text",
    "validate_report",
)
