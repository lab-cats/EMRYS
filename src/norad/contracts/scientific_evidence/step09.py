"""Validate the neutral Step 09 scientific-evidence output contract."""

from __future__ import annotations

import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[3])
sys.path[:] = list(dict.fromkeys((src_root, *sys.path)))

from norad.contracts.scientific_evidence import _step09_definitions as _definitions
from norad.contracts.scientific_evidence import _step09_semantics as _semantics
from norad.contracts.scientific_evidence import _step09_support as _support
from norad.contracts.scientific_evidence import _step09_tables as _tables
from norad.contracts.scientific_evidence import step08
from norad.libraries.alignments import orientation as _orientation

# Preserve the complete established contract surface and shared identities.
ContractError = step08.ContractError
Table = step08.Table
NA_VALUE = _definitions.NA_VALUE
values_close = step08.values_close
read_tsv = step08.read_tsv
LEGACY_PROVISIONAL_ORIENTATION_POLICY = (
    _orientation.LEGACY_PROVISIONAL_ORIENTATION_POLICY
)
IS_LEGACY_ORIENTATION_POLICY = _orientation.validate_legacy_orientation_policy
STEP09_RESULT_HEADER = _definitions.STEP09_RESULT_HEADER
STEP09_SUMMARY_HEADER = _definitions.STEP09_SUMMARY_HEADER
STEP09_MUTATION_HEADER = _definitions.STEP09_MUTATION_HEADER
CANONICAL_MUTATIONS = _definitions.CANONICAL_MUTATIONS
STEP09_TEST_STATUSES = _definitions.STEP09_TEST_STATUSES
STEP09_CALL_STATUSES = _definitions.STEP09_CALL_STATUSES
STEP09_BACKGROUND_STATUSES = _definitions.STEP09_BACKGROUND_STATUSES
STEP09_STATUS_COUNT_FIELDS = _definitions.STEP09_STATUS_COUNT_FIELDS

parse_nonnegative_or_infinite = _support.parse_nonnegative_or_infinite
resolve_recorded_path = _support.resolve_recorded_path
validate_pdf = _support.validate_pdf
count_status = _support.count_status
paired_samples = _support.paired_samples
validate_step09_results = _tables.validate_step09_results
validate_step09_summary = _tables.validate_step09_summary
validate_step09_result_semantics = _semantics.validate_step09_result_semantics
validate_significant_subset = _semantics.validate_significant_subset
validate_mutation_spectrum = _tables.validate_mutation_spectrum
