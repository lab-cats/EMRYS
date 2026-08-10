"""Expose NORAD's grouped command-line interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

from norad.evidence.canonical_bam_qc import (
    validator as canonical_bam_qc_validation_command,
)
from norad.evidence.rseqc_orientation import (
    validator as rseqc_orientation_validation_command,
)
from norad.ingestion.sample_manifest_admission import (
    validator as manifest_command,
)
from norad.stages.canonical_bam import validator as canonical_bam_validation_command
from norad.stages.cohort_candidate_preprocessing import (
    validator as cohort_candidate_preprocessing_validation_command,
)
from norad.stages.duplicate_marking import (
    validator as duplicate_marking_validation_command,
)
from norad.stages.fasta_sidecars import validator as fasta_sidecars_validation_command
from norad.stages.gtf_to_bed12 import (
    converter as gtf_to_bed12_command,
)
from norad.stages.gtf_to_bed12 import validator as bed12_validation_command
from norad.stages.mechanical_orientation import (
    validator as mechanical_orientation_validation_command,
)
from norad.stages.partitioned_cohort_mpileup import (
    validator as partitioned_cohort_mpileup_validation_command,
)
from norad.stages.split_n_cigar import validator as split_n_cigar_validation_command
from norad.stages.star_alignment import validator as star_alignment_validation_command
from norad.stages.star_index import validator as star_index_validation_command

CommandHandler = Callable[[argparse.Namespace], int]


def _find_checkout_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        configuration_path = candidate / "pyproject.toml"
        package_path = candidate / "src" / "norad" / "__init__.py"
        if not configuration_path.is_file() or not package_path.is_file():
            continue
        try:
            configuration = tomllib.loads(
                configuration_path.read_text(encoding="utf-8")
            )
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if configuration.get("project", {}).get("name") == "norad-rna-workflow":
            return candidate
    return None


def _checkout_mismatch() -> str | None:
    checkout_root = _find_checkout_root(Path.cwd().resolve())
    if checkout_root is None:
        return None
    expected_package = checkout_root / "src" / "norad"
    imported_package = Path(__file__).resolve().parent
    if imported_package == expected_package.resolve():
        return None
    return (
        f"selected interpreter imports NORAD from {imported_package}, "
        f"not the current checkout at {expected_package}"
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the public parser from owner-supplied command definitions."""
    parser = argparse.ArgumentParser(
        prog="norad",
        description="Run an explicitly installed NORAD command.",
    )
    command_parsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
        required=True,
    )
    convert_parser = command_parsers.add_parser(
        "convert",
        help="Convert an explicitly selected NORAD input.",
    )
    conversion_parsers = convert_parser.add_subparsers(
        dest="conversion",
        metavar="SUBJECT",
        required=True,
    )
    gtf_to_bed12_parser = conversion_parsers.add_parser(
        "gtf-to-bed12",
        help="Convert GTF transcript models to BED12.",
        description=gtf_to_bed12_command.DESCRIPTION,
    )
    gtf_to_bed12_command.configure_parser(gtf_to_bed12_parser)
    gtf_to_bed12_parser.set_defaults(
        _command_handler=gtf_to_bed12_command.convert_from_args
    )

    validate_parser = command_parsers.add_parser(
        "validate",
        help="Validate an explicitly selected NORAD input or artifact.",
    )
    validation_parsers = validate_parser.add_subparsers(
        dest="validation",
        metavar="SUBJECT",
        required=True,
    )
    manifest_parser = validation_parsers.add_parser(
        "manifest",
        help="Validate a sample manifest.",
        description=manifest_command.DESCRIPTION,
    )
    manifest_command.configure_parser(manifest_parser)
    manifest_parser.set_defaults(_command_handler=manifest_command.validate_from_args)
    bed12_parser = validation_parsers.add_parser(
        "bed12",
        help="Validate one BED12 against its source GTF.",
        description=bed12_validation_command.DESCRIPTION,
    )
    bed12_validation_command.configure_parser(bed12_parser)
    bed12_parser.set_defaults(
        _command_handler=bed12_validation_command.validate_from_args
    )
    canonical_bam_parser = validation_parsers.add_parser(
        "canonical-bam",
        help="Validate one canonical BAM/BAI pair.",
        description=canonical_bam_validation_command.DESCRIPTION,
    )
    canonical_bam_validation_command.configure_parser(canonical_bam_parser)
    canonical_bam_parser.set_defaults(
        _command_handler=canonical_bam_validation_command.validate_from_args
    )
    canonical_bam_qc_parser = validation_parsers.add_parser(
        "canonical-bam-qc",
        help="Validate canonical-BAM quickcheck and flagstat evidence.",
        description=canonical_bam_qc_validation_command.DESCRIPTION,
    )
    canonical_bam_qc_validation_command.configure_parser(canonical_bam_qc_parser)
    canonical_bam_qc_parser.set_defaults(
        _command_handler=canonical_bam_qc_validation_command.validate_from_args
    )
    cohort_candidate_preprocessing_parser = validation_parsers.add_parser(
        "cohort-candidate-preprocessing",
        help="Validate one cohort candidate preprocessing transaction.",
        description=cohort_candidate_preprocessing_validation_command.DESCRIPTION,
    )
    cohort_candidate_preprocessing_validation_command.configure_parser(
        cohort_candidate_preprocessing_parser
    )
    cohort_candidate_preprocessing_parser.set_defaults(
        _command_handler=(
            cohort_candidate_preprocessing_validation_command.validate_from_args
        )
    )
    duplicate_marking_parser = validation_parsers.add_parser(
        "duplicate-marking",
        help="Validate duplicate-marked BAM/BAI and Picard metrics.",
        description=duplicate_marking_validation_command.DESCRIPTION,
    )
    duplicate_marking_validation_command.configure_parser(duplicate_marking_parser)
    duplicate_marking_parser.set_defaults(
        _command_handler=duplicate_marking_validation_command.validate_from_args
    )
    fasta_sidecars_parser = validation_parsers.add_parser(
        "fasta-sidecars",
        help="Validate FASTA index and dictionary sidecars.",
        description=fasta_sidecars_validation_command.DESCRIPTION,
    )
    fasta_sidecars_validation_command.configure_parser(fasta_sidecars_parser)
    fasta_sidecars_parser.set_defaults(
        _command_handler=fasta_sidecars_validation_command.validate_from_args
    )
    mechanical_orientation_parser = validation_parsers.add_parser(
        "mechanical-orientation",
        help="Validate mechanical-orientation BAM/BAI pairs and counts.",
        description=mechanical_orientation_validation_command.DESCRIPTION,
    )
    mechanical_orientation_validation_command.configure_parser(
        mechanical_orientation_parser
    )
    mechanical_orientation_parser.set_defaults(
        _command_handler=mechanical_orientation_validation_command.validate_from_args
    )
    partitioned_cohort_mpileup_parser = validation_parsers.add_parser(
        "partitioned-cohort-mpileup",
        help="Validate one partitioned-cohort mpileup VCF transaction.",
        description=partitioned_cohort_mpileup_validation_command.DESCRIPTION,
    )
    partitioned_cohort_mpileup_validation_command.configure_parser(
        partitioned_cohort_mpileup_parser
    )
    partitioned_cohort_mpileup_parser.set_defaults(
        _command_handler=(
            partitioned_cohort_mpileup_validation_command.validate_from_args
        )
    )
    rseqc_orientation_parser = validation_parsers.add_parser(
        "rseqc-orientation",
        help="Validate one RSeQC paired-orientation report.",
        description=rseqc_orientation_validation_command.DESCRIPTION,
    )
    rseqc_orientation_validation_command.configure_parser(rseqc_orientation_parser)
    rseqc_orientation_parser.set_defaults(
        _command_handler=rseqc_orientation_validation_command.validate_from_args
    )
    split_n_cigar_parser = validation_parsers.add_parser(
        "split-n-cigar",
        help="Validate split-N-cigar BAM/BAI and reference sidecars.",
        description=split_n_cigar_validation_command.DESCRIPTION,
    )
    split_n_cigar_validation_command.configure_parser(split_n_cigar_parser)
    split_n_cigar_parser.set_defaults(
        _command_handler=split_n_cigar_validation_command.validate_from_args
    )
    star_index_parser = validation_parsers.add_parser(
        "star-index",
        help="Validate one STAR index against its references.",
        description=star_index_validation_command.DESCRIPTION,
    )
    star_index_validation_command.configure_parser(star_index_parser)
    star_index_parser.set_defaults(
        _command_handler=star_index_validation_command.validate_from_args
    )
    star_alignment_parser = validation_parsers.add_parser(
        "star-alignment",
        help="Validate one STAR alignment output set.",
        description=star_alignment_validation_command.DESCRIPTION,
    )
    star_alignment_validation_command.configure_parser(star_alignment_parser)
    star_alignment_parser.set_defaults(
        _command_handler=star_alignment_validation_command.validate_from_args
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and dispatch one supported NORAD command."""
    if mismatch := _checkout_mismatch():
        print(f"norad: error: {mismatch}", file=sys.stderr)
        return 2
    arguments = build_parser().parse_args(argv)
    handler = cast(CommandHandler, arguments._command_handler)
    return handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
