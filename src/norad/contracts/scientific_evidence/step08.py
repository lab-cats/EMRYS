"""Validate the neutral Step 08 scientific-evidence table contract."""

from __future__ import annotations

import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[3])
sys.path[:] = list(dict.fromkeys((src_root, *sys.path)))

from norad.contracts.scientific_evidence import _step08_definitions as _definitions
from norad.contracts.scientific_evidence import _step08_manifests as _manifests
from norad.contracts.scientific_evidence import _step08_support as _support
from norad.contracts.scientific_evidence import _step08_tables as _tables

# Preserve the complete established contract surface and shared identities.
ContractError = _definitions.ContractError
Table = _definitions.Table
SAFE_ID_RE = _definitions.SAFE_ID_RE
SHA256_RE = _definitions.SHA256_RE
NA_VALUE = _definitions.NA_VALUE
ORIENTATIONS = _definitions.ORIENTATIONS
STEP08_METADATA_HEADER = _definitions.STEP08_METADATA_HEADER
STEP08_INPUTS_HEADER = _definitions.STEP08_INPUTS_HEADER
STEP08_SUMMARY_HEADER = _definitions.STEP08_SUMMARY_HEADER
STEP08_AGGREGATE_COUNT_FIELDS = _definitions.STEP08_AGGREGATE_COUNT_FIELDS
STEP08_PARTITION_COUNT_FIELDS = _definitions.STEP08_PARTITION_COUNT_FIELDS
SAMPLE_MANIFEST_REQUIRED = _definitions.SAMPLE_MANIFEST_REQUIRED
SAMPLE_MANIFEST_ALLOWED = _definitions.SAMPLE_MANIFEST_ALLOWED
PARTITION_MANIFEST_HEADER = _definitions.PARTITION_MANIFEST_HEADER
alignment_orientation = _definitions.alignment_orientation

T = _support.T
report = _support.report
read_strict_tsv = _support.read_strict_tsv
fail = _support.fail
attempt = _support.attempt
sample_block_header = _support.sample_block_header
validate_safe_id = _support.validate_safe_id
validate_enum = _support.validate_enum
parse_nonnegative_int = _support.parse_nonnegative_int
parse_number = _support.parse_number
values_close = _support.values_close
sha256_file = _support.sha256_file
require_file = _support.require_file
read_tsv = _support.read_tsv
ensure_unique = _support.ensure_unique
require_text = _support.require_text
validate_hash = _support.validate_hash

validate_sample_manifest = _manifests.validate_sample_manifest
validate_partition_manifest = _manifests.validate_partition_manifest
validate_step08_inputs = _tables.validate_step08_inputs
validate_step08_sites = _tables.validate_step08_sites
validate_step08_summary = _tables.validate_step08_summary
