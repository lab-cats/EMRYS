"""Expose NORAD's grouped command-line interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, cast

from norad.analyses.paired_cmh_candidate_ranking import (
    validator as paired_cmh_candidate_ranking_validation_command,
)
from norad.contracts.artifacts import (
    validator as artifact_contracts_validation_command,
)
from norad.evidence.canonical_bam_qc import (
    validator as canonical_bam_qc_validation_command,
)
from norad.evidence.reference_provenance import (
    reconciler as reference_provenance_reconciliation_command,
)
from norad.evidence.rseqc_orientation import (
    validator as rseqc_orientation_validation_command,
)
from norad.evidence.runtime_availability import (
    inspector as runtime_availability_inspection_command,
)
from norad.evidence.scientific_review_package import (
    publisher as scientific_review_package_command,
)
from norad.evidence.storage_inventory import (
    inspector as storage_inventory_inspection_command,
)
from norad.ingestion.sample_manifest_admission import (
    validator as manifest_command,
)
from norad.orchestration.local_pilot import all_pass as all_pass_validation_command
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


class _SubparserCollection(Protocol):
    """Subset of argparse's subparser collection used by this dispatcher."""

    def add_parser(
        self,
        name: str,
        **_options: str,
    ) -> argparse.ArgumentParser: ...


class _ValidationCommand(Protocol):
    """Owner module interface required by the grouped validation CLI."""

    DESCRIPTION: str
    configure_parser: Callable[[argparse.ArgumentParser], None]
    validate_from_args: CommandHandler


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


def _add_validation_command(
    validation_parsers: _SubparserCollection,
    *,
    name: str,
    help_text: str,
    command: _ValidationCommand,
) -> None:
    subject_parser = validation_parsers.add_parser(
        name,
        help=help_text,
        description=command.DESCRIPTION,
    )
    command.configure_parser(subject_parser)
    subject_parser.set_defaults(_command_handler=command.validate_from_args)


def _add_scientific_review_package_command(
    assembly_parsers: _SubparserCollection,
) -> None:
    package_parser = assembly_parsers.add_parser(
        "scientific-review-package",
        help="Assemble one declared scientific-review evidence package.",
        description=scientific_review_package_command.DESCRIPTION,
    )
    scientific_review_package_command.configure_parser(package_parser)
    package_parser.set_defaults(
        _command_handler=scientific_review_package_command.assemble_from_args
    )


def _add_storage_inventory_inspection_command(
    inspection_parsers: _SubparserCollection,
) -> None:
    storage_parser = inspection_parsers.add_parser(
        "storage-inventory",
        help="Inspect declared storage and retention-policy state without mutation.",
        description=storage_inventory_inspection_command.DESCRIPTION,
    )
    storage_inventory_inspection_command.configure_parser(storage_parser)
    storage_parser.set_defaults(
        _command_handler=storage_inventory_inspection_command.inspect_from_args
    )


def _build_artifact_index_from_args(arguments: argparse.Namespace) -> int:
    from norad.reporting._artifact_index import builder  # noqa: PLC0415

    return builder.build_from_args(arguments)


def _build_run_summary_from_args(arguments: argparse.Namespace) -> int:
    from norad.reporting._run_summary import builder  # noqa: PLC0415

    return builder.build_from_args(arguments)


def _build_report_from_args(arguments: argparse.Namespace) -> int:
    from norad.reporting import report  # noqa: PLC0415

    return report.build_from_args(arguments)


def _add_build_commands(
    command_parsers: _SubparserCollection,
) -> None:
    build_parser = command_parsers.add_parser(
        "build",
        help="Build an explicitly declared NORAD output.",
    )
    build_parsers = build_parser.add_subparsers(
        dest="build",
        metavar="SUBJECT",
        required=True,
    )
    artifact_parser = build_parsers.add_parser(
        "artifact-index",
        help="Build one explicit read-only artifact index.",
        description=(
            "Build an explicit read-only NORAD artifact index. Dry-run is "
            "the default; add --execute to publish the receipt-last "
            "transaction."
        ),
    )
    artifact_parser.add_argument(
        "--source-checkout",
        required=True,
        type=Path,
        help="Absolute canonical NORAD source checkout owning producer evidence.",
    )
    artifact_parser.add_argument("--run-id", required=True, help="Immutable run ID.")
    artifact_parser.add_argument(
        "--run-contract",
        required=True,
        type=Path,
        help=(
            "Strict JSON file containing exactly the six-field canonical run contract."
        ),
    )
    artifact_parser.add_argument(
        "--inventory",
        required=True,
        type=Path,
        help="Explicit expected-artifact inventory TSV.",
    )
    artifact_parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    artifact_parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish records, index, and receipt. Default is dry-run.",
    )
    artifact_parser.set_defaults(
        _command_handler=_build_artifact_index_from_args,
        _command_parser=artifact_parser,
    )

    summary_parser = build_parsers.add_parser(
        "run-summary",
        help="Build one deterministic run summary.",
        description=(
            "Build a deterministic run summary from one complete NORAD "
            "artifact-index receipt. Dry-run is the default; add --execute "
            "to publish the receipt-last transaction."
        ),
    )
    summary_parser.add_argument(
        "--source-checkout",
        required=True,
        type=Path,
        help="Absolute canonical NORAD source checkout owning recorded paths.",
    )
    summary_parser.add_argument("--run-id", required=True, help="Immutable run ID.")
    summary_parser.add_argument(
        "--artifact-receipt",
        required=True,
        type=Path,
        help="Exact completed artifact-index receipt TSV.",
    )
    summary_parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Artifact output root containing <run-id>/.",
    )
    summary_parser.add_argument(
        "--science-review-summary",
        type=Path,
        help=(
            "Optional exact committed Step 09c review-summary TSV. It is "
            "never discovered automatically."
        ),
    )
    summary_parser.add_argument(
        "--report-table-approvals",
        type=Path,
        help=(
            "Optional exact report-table approvals TSV. It is never "
            "discovered automatically and must be bound to this run and its "
            "explicit Step 09c scientific-review artifacts."
        ),
    )
    summary_parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the four-file transaction; otherwise only validate.",
    )
    summary_parser.set_defaults(
        _command_handler=_build_run_summary_from_args,
        _command_parser=summary_parser,
    )

    from norad.reporting import report  # noqa: PLC0415

    report_parser = build_parsers.add_parser(
        "report",
        help="Build one self-contained HTML report transaction.",
        description=report.DESCRIPTION,
    )
    report.configure_parser(report_parser)
    report_parser.set_defaults(
        _command_handler=_build_report_from_args,
        _command_parser=report_parser,
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
    _add_build_commands(command_parsers)
    assemble_parser = command_parsers.add_parser(
        "assemble",
        help="Assemble an explicitly declared NORAD evidence package.",
    )
    assembly_parsers = assemble_parser.add_subparsers(
        dest="assembly",
        metavar="SUBJECT",
        required=True,
    )
    _add_scientific_review_package_command(assembly_parsers)
    reconcile_parser = command_parsers.add_parser(
        "reconcile",
        help="Reconcile explicitly declared NORAD evidence.",
    )
    reconciliation_parsers = reconcile_parser.add_subparsers(
        dest="reconciliation",
        metavar="SUBJECT",
        required=True,
    )
    reference_provenance_parser = reconciliation_parsers.add_parser(
        "reference-provenance",
        help="Reconcile one explicitly declared reference bundle without repair.",
        description=reference_provenance_reconciliation_command.DESCRIPTION,
    )
    reference_provenance_reconciliation_command.configure_parser(
        reference_provenance_parser
    )
    reference_provenance_parser.set_defaults(
        _command_handler=(
            reference_provenance_reconciliation_command.reconcile_from_args
        )
    )
    inspect_parser = command_parsers.add_parser(
        "inspect",
        help="Inspect explicitly declared NORAD operational evidence.",
    )
    inspection_parsers = inspect_parser.add_subparsers(
        dest="inspection",
        metavar="SUBJECT",
        required=True,
    )
    runtime_availability_parser = inspection_parsers.add_parser(
        "runtime-availability",
        help="Inspect declared runtime availability without installation or repair.",
        description=runtime_availability_inspection_command.DESCRIPTION,
    )
    runtime_availability_inspection_command.configure_parser(
        runtime_availability_parser
    )
    runtime_availability_parser.set_defaults(
        _command_handler=runtime_availability_inspection_command.inspect_from_args
    )
    _add_storage_inventory_inspection_command(inspection_parsers)
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
    _add_validation_command(
        validation_parsers,
        name="all-pass",
        help_text="Require every row in one owner-validation report to pass.",
        command=all_pass_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="artifact-contracts",
        help_text="Validate explicit artifact schemas, records, and inventories.",
        command=artifact_contracts_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="manifest",
        help_text="Validate a sample manifest.",
        command=manifest_command,
    )
    _add_validation_command(
        validation_parsers,
        name="bed12",
        help_text="Validate one BED12 against its source GTF.",
        command=bed12_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="canonical-bam",
        help_text="Validate one canonical BAM/BAI pair.",
        command=canonical_bam_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="canonical-bam-qc",
        help_text="Validate canonical-BAM quickcheck and flagstat evidence.",
        command=canonical_bam_qc_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="cohort-candidate-preprocessing",
        help_text="Validate one cohort candidate preprocessing transaction.",
        command=cohort_candidate_preprocessing_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="duplicate-marking",
        help_text="Validate duplicate-marked BAM/BAI and Picard metrics.",
        command=duplicate_marking_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="fasta-sidecars",
        help_text="Validate FASTA index and dictionary sidecars.",
        command=fasta_sidecars_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="mechanical-orientation",
        help_text="Validate mechanical-orientation BAM/BAI pairs and counts.",
        command=mechanical_orientation_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="paired-cmh-candidate-ranking",
        help_text="Validate one paired-CMH candidate-ranking transaction.",
        command=paired_cmh_candidate_ranking_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="partitioned-cohort-mpileup",
        help_text="Validate one partitioned-cohort mpileup VCF transaction.",
        command=partitioned_cohort_mpileup_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="rseqc-orientation",
        help_text="Validate one RSeQC paired-orientation report.",
        command=rseqc_orientation_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="split-n-cigar",
        help_text="Validate split-N-cigar BAM/BAI and reference sidecars.",
        command=split_n_cigar_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="star-index",
        help_text="Validate one STAR index against its references.",
        command=star_index_validation_command,
    )
    _add_validation_command(
        validation_parsers,
        name="star-alignment",
        help_text="Validate one STAR alignment output set.",
        command=star_alignment_validation_command,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and dispatch one supported NORAD command."""
    if mismatch := _checkout_mismatch():
        print(f"norad: error: {mismatch}", file=sys.stderr)
        return 2
    parser = build_parser()
    arguments, unrecognized = parser.parse_known_args(argv)
    if unrecognized:
        error_parser = cast(
            argparse.ArgumentParser,
            getattr(arguments, "_command_parser", parser),
        )
        error_parser.error(f"unrecognized arguments: {' '.join(unrecognized)}")
    handler = cast(CommandHandler, arguments._command_handler)
    return handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
