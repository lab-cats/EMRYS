"""Validate one explicit Step 00a STAR index without modifying it."""

from __future__ import annotations

import argparse
from functools import partial
from pathlib import Path

from emrys.libraries.alignments.star import (
    REQUIRED_INDEX_MEMBERS,
    parse_fasta,
    parse_parameters,
    parse_star_index_contigs,
)
from emrys.libraries.validation import (
    Snapshot,
    ValidationError,
    add_output_arguments,
    build_report,
    fail,
    lexical_path,
    regular_snapshot,
    resolve_from_base,
    run_from_args,
    stable_text,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "index_members",
    "fasta_identity",
    "gtf_identity",
    "contig_names_lengths",
    "sjdb_overhang",
    "genome_sa_index_nbases",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the STAR-index validator owner's arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--index-dir", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-gtf", required=True, type=Path)
    parser.add_argument(
        "--parameter-path-base",
        required=True,
        type=Path,
        help="Explicit base for relative paths recorded in genomeParameters.txt.",
    )
    parser.add_argument("--expected-sjdb-overhang", required=True, type=int)
    parser.add_argument("--expected-genome-sa-index-nbases", required=True, type=int)
    add_output_arguments(parser)


def _inspect_required_members(
    index_dir: Path,
) -> tuple[dict[Path, Snapshot], list[str]]:
    snapshots: dict[Path, Snapshot] = {}
    missing_members: list[str] = []
    for member_name in REQUIRED_INDEX_MEMBERS:
        member_path = index_dir / member_name
        try:
            snapshots[member_path] = regular_snapshot(
                member_path,
                f"STAR index member {member_name}",
            )
        except ValidationError:
            missing_members.append(member_name)
    return snapshots, missing_members


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 00a report from explicit inputs."""
    if not arguments.scope_id or any(
        character.isspace() for character in arguments.scope_id
    ):
        fail("scope-id must be nonempty and contain no whitespace")
    if arguments.expected_sjdb_overhang < 0:
        fail("expected-sjdb-overhang must be nonnegative")
    if arguments.expected_genome_sa_index_nbases < 1:
        fail("expected-genome-sa-index-nbases must be positive")

    index_dir = lexical_path(arguments.index_dir)
    if not index_dir.is_dir() or index_dir.is_symlink():
        fail(f"STAR index directory must be an existing real directory: {index_dir}")
    parameter_path_base = lexical_path(arguments.parameter_path_base)
    if not parameter_path_base.is_dir() or parameter_path_base.is_symlink():
        fail(
            "Parameter path base must be an existing real directory: "
            f"{parameter_path_base}"
        )
    fasta_path = lexical_path(arguments.reference_fasta)
    gtf_path = lexical_path(arguments.reference_gtf)

    snapshots, missing_members = _inspect_required_members(index_dir)
    members_pass = not missing_members
    try:
        parameters, parameter_snapshot = parse_parameters(
            index_dir / "genomeParameters.txt"
        )
        fasta_records, fasta_snapshot = parse_fasta(fasta_path)
        star_records, (names_snapshot, lengths_snapshot) = parse_star_index_contigs(
            index_dir
        )
    except ValueError as exc:
        fail(str(exc))

    snapshots[index_dir / "genomeParameters.txt"] = parameter_snapshot
    snapshots[fasta_path] = fasta_snapshot
    _, gtf_snapshot = stable_text(gtf_path, "Reference GTF")
    snapshots[gtf_path] = gtf_snapshot
    snapshots[index_dir / "chrName.txt"] = names_snapshot
    snapshots[index_dir / "chrLength.txt"] = lengths_snapshot

    fasta_values = parameters.get("genomeFastaFiles", [])
    gtf_values = parameters.get("sjdbGTFfile", [])
    overhang_values = parameters.get("sjdbOverhang", [])
    genome_sa_values = parameters.get("genomeSAindexNbases", [])
    fasta_match = (
        len(fasta_values) == 1
        and resolve_from_base(parameter_path_base, fasta_values[0]) == fasta_path
    )
    gtf_match = (
        len(gtf_values) == 1
        and resolve_from_base(parameter_path_base, gtf_values[0]) == gtf_path
    )
    try:
        observed_overhang = (
            int(overhang_values[0]) if len(overhang_values) == 1 else None
        )
    except ValueError:
        observed_overhang = None
    try:
        observed_genome_sa = (
            int(genome_sa_values[0]) if len(genome_sa_values) == 1 else None
        )
    except ValueError:
        observed_genome_sa = None
    contigs_match = star_records == fasta_records

    return build_report(
        "00a",
        arguments.scope_id,
        snapshots,
        CHECK_IDS,
        {
            "index_members": (
                members_pass,
                len(REQUIRED_INDEX_MEMBERS) - len(missing_members),
                len(REQUIRED_INDEX_MEMBERS),
                "all required members present"
                if members_pass
                else "missing: " + ",".join(missing_members),
            ),
            "fasta_identity": (
                fasta_match,
                fasta_values[0] if len(fasta_values) == 1 else "invalid",
                str(fasta_path),
                "genomeFastaFiles resolves to the explicit FASTA",
            ),
            "gtf_identity": (
                gtf_match,
                gtf_values[0] if len(gtf_values) == 1 else "invalid",
                str(gtf_path),
                "sjdbGTFfile resolves to the explicit GTF",
            ),
            "contig_names_lengths": (
                contigs_match,
                f"{len(star_records)} STAR contigs",
                f"{len(fasta_records)} FASTA contigs",
                "ordered contig names and lengths agree"
                if contigs_match
                else "ordered contig names or lengths differ",
            ),
            "sjdb_overhang": (
                observed_overhang == arguments.expected_sjdb_overhang,
                observed_overhang if observed_overhang is not None else "invalid",
                arguments.expected_sjdb_overhang,
                "configured STAR splice-junction overhang",
            ),
            "genome_sa_index_nbases": (
                observed_genome_sa == arguments.expected_genome_sa_index_nbases,
                observed_genome_sa if observed_genome_sa is not None else "invalid",
                arguments.expected_genome_sa_index_nbases,
                "configured STAR genome suffix-array index length",
            ),
        },
    )


def _print_context(arguments: argparse.Namespace) -> None:
    print("Step: 00a")
    print(f"Scope: {arguments.scope_id}")
    print(f"STAR index: {arguments.index_dir}")
    print(f"Parameter path base: {arguments.parameter_path_base}")
    print(f"Output: {arguments.output}")


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 00a STAR-index request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "00a",
        CHECK_IDS,
        before_report=partial(_print_context, arguments),
    )
