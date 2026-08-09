"""Compatibility facade for strict text and tabular artifact readers."""

from __future__ import annotations

from norad.libraries.validation.mpileup import VCF_FIXED_COLUMNS

from ._text_common import inspect_nonempty_text, iter_text_lines
from ._text_genomic import (
    inspect_bed12,
    inspect_dict,
    inspect_fai,
    inspect_fasta,
    inspect_picard_metrics,
    inspect_star_sj,
    inspect_vcf,
)
from ._text_tabular import (
    extract_parameters,
    inspect_tsv,
    validate_native_run_anchors,
    validate_sample_block_header,
)
from .models import (
    ANCHOR_HASH_FIELDS,
    SHA256_RE,
    STEP09C_CATEGORY_ADAPTERS,
    AdapterSpec,
    ArtifactIndexError,
)

__all__ = [
    "ANCHOR_HASH_FIELDS",
    "SHA256_RE",
    "STEP09C_CATEGORY_ADAPTERS",
    "VCF_FIXED_COLUMNS",
    "AdapterSpec",
    "ArtifactIndexError",
    "extract_parameters",
    "inspect_bed12",
    "inspect_dict",
    "inspect_fai",
    "inspect_fasta",
    "inspect_nonempty_text",
    "inspect_picard_metrics",
    "inspect_star_sj",
    "inspect_tsv",
    "inspect_vcf",
    "iter_text_lines",
    "validate_native_run_anchors",
    "validate_sample_block_header",
]
