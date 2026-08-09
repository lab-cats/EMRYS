"""Compatibility owner for run-summary reduction and semantic validation."""

from __future__ import annotations

from . import run_summary_status as _status
from . import run_summary_validation as _validation
from .core import ContractValidationError as ContractValidationError

RUN_SUMMARY_STATUS_FIELDS = _status.RUN_SUMMARY_STATUS_FIELDS
AGGREGATE_ARTIFACT_STATES = _status.AGGREGATE_ARTIFACT_STATES
artifact_rollup_state = _status.artifact_rollup_state
aggregate_equal_or_mixed = _status.aggregate_equal_or_mixed
aggregate_artifact_state = _status.aggregate_artifact_state
artifact_status_dimensions = _status.artifact_status_dimensions
scope_key = _status.scope_key

_validate_scope_statuses = _validation._validate_scope_statuses
validate_run_summary_semantics = _validation.validate_run_summary_semantics
