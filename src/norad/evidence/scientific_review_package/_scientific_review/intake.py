"""Compatibility facade for scientific-review intake and manifests."""

from __future__ import annotations

from ._evidence_manifest import validate_evidence_manifest
from ._intake_models import Artifact, ReviewContext
from ._intake_support import (
    artifact_from_binary,
    artifact_from_table,
    category_is_complete,
    complement_base,
    register_artifact,
    require_directory,
    resolve_declared_path,
    split_ids,
    step09_paths,
    validate_candidate_reference,
    validate_iso_date,
    validate_supporting_ids,
    write_tsv,
)
from ._review_plan import validate_review_plan

__all__ = [
    "Artifact",
    "ReviewContext",
    "artifact_from_binary",
    "artifact_from_table",
    "category_is_complete",
    "complement_base",
    "register_artifact",
    "require_directory",
    "resolve_declared_path",
    "split_ids",
    "step09_paths",
    "validate_candidate_reference",
    "validate_evidence_manifest",
    "validate_iso_date",
    "validate_review_plan",
    "validate_supporting_ids",
    "write_tsv",
]
