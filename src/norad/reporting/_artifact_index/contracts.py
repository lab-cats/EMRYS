"""Neutral contract owners used by artifact-index reporting."""

from __future__ import annotations

from norad.contracts.artifacts import api as contracts
from norad.contracts.scientific_evidence import review_package, step08, step09

if step09.step08 is not step08:
    raise ImportError(
        "Step 09 contract and artifact indexing resolved different Step 08 objects"
    )
if step09.ContractError is not step08.ContractError or step09.Table is not step08.Table:
    raise ImportError("Step 09 contract resolved different shared identities")

__all__ = ("contracts", "review_package", "step08", "step09")
