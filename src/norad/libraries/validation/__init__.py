"""Shared validation API used by NORAD owner-local validators."""

from norad.libraries.validation.errors import ValidationError, fail
from norad.libraries.validation.inputs import (
    Snapshot,
    regular_snapshot,
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
from norad.libraries.validation.runtime import Runtime, finish

__all__ = (
    "HEADER",
    "Runtime",
    "Snapshot",
    "ValidationError",
    "clean",
    "fail",
    "finish",
    "publish",
    "regular_snapshot",
    "render",
    "require_unchanged",
    "row",
    "stable_text",
    "validate_report",
)

