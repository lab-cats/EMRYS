"""Compatibility owner for shared artifact-contract primitives."""

from __future__ import annotations

from . import definitions as _definitions
from . import evidence as _evidence
from . import identity as _identity
from . import schema as _schema

# Existing private consumers and the public validator import these names from
# core. Keep that identity stable while implementation ownership stays bounded.
REPO_ROOT = _definitions.REPO_ROOT
SCHEMA_ROOT = _definitions.SCHEMA_ROOT
COMMON_SCHEMA_PATH = _definitions.COMMON_SCHEMA_PATH
SCHEMA_FILES = _definitions.SCHEMA_FILES
INVENTORY_HEADER = _definitions.INVENTORY_HEADER
SAFE_ID_RE = _definitions.SAFE_ID_RE
BOOLEAN_VALUES = _definitions.BOOLEAN_VALUES
SCOPE_TYPES = _definitions.SCOPE_TYPES
SCIENCE_INPUT_ROLES = _definitions.SCIENCE_INPUT_ROLES
SCIENCE_UPSTREAM_ROLE_CONTRACTS = _definitions.SCIENCE_UPSTREAM_ROLE_CONTRACTS
RUN_CONTRACT_COMPONENT_FIELDS = _definitions.RUN_CONTRACT_COMPONENT_FIELDS
ContractValidationError = _definitions.ContractValidationError

reject_duplicate_json_keys = _schema.reject_duplicate_json_keys
reject_nonstandard_json_constant = _schema.reject_nonstandard_json_constant
load_json_object = _schema.load_json_object
load_schema = _schema.load_schema
load_schema_registry = _schema.load_schema_registry
schema_validator = _schema.schema_validator
schema_errors = _schema.schema_errors
validate_all_schemas = _schema.validate_all_schemas
format_json_path = _schema.format_json_path
sha256_file = _schema.sha256_file

canonical_run_contract_sha256 = _identity.canonical_run_contract_sha256
validate_run_contract = _identity.validate_run_contract
validate_resolved_path = _identity.validate_resolved_path
validate_document_paths = _identity.validate_document_paths
require_unique_key = _identity.require_unique_key
validate_attempt_graph = _identity.validate_attempt_graph
resolve_contract_path = _identity.resolve_contract_path

require_status_evidence = _evidence.require_status_evidence
require_evidence_roles = _evidence.require_evidence_roles
validate_evidence_references = _evidence.validate_evidence_references
validate_computational_statuses = _evidence.validate_computational_statuses
