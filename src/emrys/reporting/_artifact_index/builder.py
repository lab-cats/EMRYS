"""Build a read-only, explicit artifact index for one immutable EMRYS run.

The command never discovers pipeline inputs, invokes analysis software, or
changes native Step 00a-10 outputs. Every source comes from one validated
inventory row. Dry-run is the default; execute mode publishes one JSON record
per row, an inventory-ordered TSV index, and a receipt last as a
rollback-protected transaction.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from emrys.contracts.artifacts import api as contracts
from emrys.libraries.source_authority import (
    ArtifactSourceRootError,
    SourceCheckoutError,
    admit_artifact_source_root,
    admit_source_checkout,
)

from .context import prepare_context, print_context
from .models import ArtifactIndexError
from .publication import publish_context

if TYPE_CHECKING:
    import argparse


def build_from_args(arguments: argparse.Namespace) -> int:
    """Build or publish one explicitly rooted artifact-index transaction."""
    try:
        source_checkout = admit_source_checkout(
            root=arguments.source_checkout,
            package_root=Path(__file__).resolve().parents[2],
        )
        artifact_source_root = admit_artifact_source_root(
            root=arguments.artifact_source_root,
        )
        context = prepare_context(
            arguments,
            source_checkout=source_checkout,
            artifact_source_root=artifact_source_root,
        )
        print_context(context, arguments.execute)
        if arguments.execute:
            publish_context(context)
            print(f"Published artifact index: {context.artifacts_path}")
            print(f"Published receipt last: {context.receipt_path}")
    except (
        ArtifactIndexError,
        ArtifactSourceRootError,
        SourceCheckoutError,
        contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0
