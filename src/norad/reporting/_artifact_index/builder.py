"""Build a read-only, explicit artifact index for one immutable NORAD run.

The command never discovers pipeline inputs, invokes analysis software, or
changes native Step 00a-09c outputs. Every source comes from one validated
inventory row. Dry-run is the default; execute mode publishes one JSON record
per row, an inventory-ordered TSV index, and a receipt last as a
rollback-protected transaction.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from norad.contracts.artifacts import api as contracts

from .context import prepare_context, print_context
from .models import ArtifactIndexError
from .publication import publish_context
from .source_checkout import SourceCheckoutError, admit_source_checkout

if TYPE_CHECKING:
    import argparse


def build_from_args(arguments: argparse.Namespace) -> int:
    """Build or publish one explicitly rooted artifact-index transaction."""
    try:
        source_checkout = admit_source_checkout(
            root=arguments.source_checkout,
            package_root=Path(__file__).resolve().parents[2],
        )
        context = prepare_context(arguments, source_checkout=source_checkout)
        print_context(context, arguments.execute)
        if arguments.execute:
            publish_context(context)
            print(f"Published artifact index: {context.artifacts_path}")
            print(f"Published receipt last: {context.receipt_path}")
    except (
        ArtifactIndexError,
        SourceCheckoutError,
        contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0
