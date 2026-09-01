"""Validate one receipt-last scientific-context transaction without invoking R."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from emrys.contracts.scientific_evidence import scientific_context, step08
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = set(scientific_context.VALIDATION_CHECK_IDS)
_BOUND_PREFIXES = (
    "step09_all_sites",
    "step09_significant_sites",
    "step09_summary",
    "reference_fasta",
    "reference_fai",
    "motif_catalog",
    "candidate_context",
    "motif_hits",
    "sequence_logo",
    "motif_statistics",
)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add scientific-context projection validator arguments to a parser."""
    parser.add_argument("--receipt", required=True, type=Path)
    add_output_arguments(parser)


def _discover_bound_paths(receipt: Path) -> tuple[str, dict[str, Path]]:
    """Read only the fixed receipt path roster before one semantic admission."""
    try:
        with receipt.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            if tuple(reader.fieldnames or ()) != (
                scientific_context.SCIENTIFIC_CONTEXT_RECEIPT_HEADER
            ):
                raise step08.ContractError(
                    f"Scientific-context receipt header is invalid: {receipt}"
                )
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise step08.ContractError(
            f"Could not inspect scientific-context receipt paths: {exc}"
        ) from exc
    if len(rows) != 1:
        raise step08.ContractError(
            "Scientific-context receipt must contain exactly one data row."
        )
    row = rows[0]
    analysis_id = row["analysis_id"]
    step08.validate_safe_id("Scientific-context receipt analysis_id", analysis_id)
    paths = {"receipt": receipt}
    for prefix in _BOUND_PREFIXES:
        value = row[f"{prefix}_path"]
        if not value:
            raise step08.ContractError(
                f"Scientific-context receipt {prefix}_path is empty."
            )
        paths[prefix] = lexical_path(Path(value))
    return analysis_id, paths


def _prepared_scope(
    arguments: argparse.Namespace,
) -> tuple[str, dict[str, Path]]:
    """Cache the one lexical receipt inspection shared by runtime and builder."""
    prepared = getattr(arguments, "_scientific_context_scope", None)
    if prepared is None:
        receipt = lexical_path(arguments.receipt)
        prepared = _discover_bound_paths(receipt)
        arguments._scientific_context_scope = prepared
    return prepared


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the single-row Step 10 transaction validation report."""
    analysis_id, paths = _prepared_scope(arguments)
    receipt = paths["receipt"]
    input_snapshots = snapshots(paths, label="Scientific-context transaction")
    transaction, detail = step08.attempt(
        lambda: scientific_context.validate_scientific_context_transaction(receipt)
    )
    return build_report(
        "10",
        analysis_id,
        input_snapshots,
        CHECK_IDS,
        {
            "scientific_context_transaction": (
                transaction is not None,
                detail,
                "one receipt-last transaction with hash-bound Step 09, reference, motif, and four figure-ready outputs",
                "canonical scientific-context transaction admission",
            )
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed scientific-context request."""
    try:
        analysis_id, _ = _prepared_scope(arguments)
    except step08.ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return run_from_args(
        arguments,
        build_validation_report,
        "10",
        CHECK_IDS,
        scope_id=analysis_id,
    )
