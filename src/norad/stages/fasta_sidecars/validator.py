"""Validate explicit Step 00c FASTA, FAI, and DICT contig contracts."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Callable
from pathlib import Path

from norad.libraries.references.contigs import (
    ReferenceContigError,
    parse_dict,
    parse_fai,
    parse_fasta,
)
from norad.libraries.validation import (
    Snapshot,
    ValidationError,
    add_output_arguments,
    build_report,
    clean,
    fail,
    lexical_path,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "fasta_structure",
    "fai_structure",
    "dict_structure",
    "fai_contig_agreement",
    "dict_contig_agreement",
}

Contigs = list[tuple[str, int]]
ContigParser = Callable[[Path], Contigs]
ValidationCheck = tuple[bool, object, object, str]
ROLE_PARSERS: tuple[tuple[str, ContigParser], ...] = (
    ("fasta", parse_fasta),
    ("fai", parse_fai),
    ("dict", parse_dict),
)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the FASTA-sidecar validator owner's arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--reference-dict", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 00c report from explicit reference inputs."""
    reference_paths = {
        "fasta": lexical_path(arguments.reference_fasta),
        "fai": lexical_path(arguments.reference_fai),
        "dict": lexical_path(arguments.reference_dict),
    }
    input_snapshots = snapshots(reference_paths, label="Reference")
    contigs_by_role: dict[str, Contigs] = {}
    parse_errors_by_role: dict[str, str] = {}
    for role, parser in ROLE_PARSERS:
        try:
            contigs_by_role[role] = parser(reference_paths[role])
        except ReferenceContigError as exc:
            parse_errors_by_role[role] = clean(exc)
        except (OSError, UnicodeError, csv.Error) as exc:
            fail(str(exc))

    checks: dict[str, ValidationCheck] = {}
    for role, _ in ROLE_PARSERS:
        checks[f"{role}_structure"] = (
            role in contigs_by_role,
            len(contigs_by_role.get(role, []))
            if role in contigs_by_role
            else parse_errors_by_role.get(role, "invalid"),
            "nonempty unique contigs",
            f"{role.upper()} contig structure",
        )
    for role in ("fai", "dict"):
        matches_fasta = (
            "fasta" in contigs_by_role
            and role in contigs_by_role
            and contigs_by_role[role] == contigs_by_role["fasta"]
        )
        checks[f"{role}_contig_agreement"] = (
            matches_fasta,
            len(contigs_by_role.get(role, []))
            if role in contigs_by_role
            else "invalid",
            len(contigs_by_role.get("fasta", []))
            if "fasta" in contigs_by_role
            else "invalid",
            f"ordered {role.upper()} names and lengths equal FASTA",
        )
    return build_report(
        "00c",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        checks,
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 00c FASTA-sidecar request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "00c",
        CHECK_IDS,
        caught_errors=(ValidationError, ReferenceContigError),
    )
