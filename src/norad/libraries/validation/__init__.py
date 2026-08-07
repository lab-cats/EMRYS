"""Shared validation API used by NORAD owner-local validators."""

from norad.libraries.validation.errors import ValidationError, fail
from norad.libraries.validation.inputs import (
    Snapshot,
    regular_snapshot,
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
from norad.libraries.validation.tsv import attempt, read_header
from norad.libraries.validation.runtime import Runtime, finish

__all__ = (
    "HEADER",
    "attempt",
    "Runtime",
    "Snapshot",
    "integer_stdout",
    "ValidationError",
    "clean",
    "fail",
    "finish",
    "publish",
    "regular_snapshot",
    "render",
    "require_unchanged",
    "row",
    "read_header",
    "stable_text",
    "validate_report",
)
