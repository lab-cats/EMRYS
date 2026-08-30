"""Expose EMRYS's grouped command-line interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path
from typing import Protocol, cast

from emrys.analyses.paired_cmh_candidate_ranking import (
    validator as paired_cmh_candidate_ranking_validation_command,
)
from emrys.analyses.scientific_context_projection import (
    validator as scientific_context_projection_validation_command,
)
from emrys.contracts.artifacts import (
    validator as artifact_contracts_validation_command,
)
from emrys.evidence.canonical_bam_qc import (
    validator as canonical_bam_qc_validation_command,
)
from emrys.evidence.reference_provenance import (
    reconciler as reference_provenance_reconciliation_command,
)
from emrys.evidence.rseqc_orientation import (
    validator as rseqc_orientation_validation_command,
)
from emrys.evidence.runtime_availability import (
    inspector as runtime_availability_inspection_command,
)
from emrys.evidence.storage_inventory import (
    inspector as storage_inventory_inspection_command,
)
from emrys.evidence.storage_inventory import (
    qualification as storage_qualification_inspection_command,
)
from emrys.ingestion.sample_manifest_admission import (
    validator as manifest_command,
)
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    require_controlled_python_runtime,
)
from emrys.orchestration.local_pilot import all_pass as all_pass_validation_command
from emrys.orchestration.local_pilot import doctor as local_pilot_doctor_command
from emrys.orchestration.local_pilot import control as local_pilot_control_command
from emrys.orchestration.local_pilot import onboarding as local_pilot_onboarding_command
from emrys.orchestration.local_pilot import (
    synthetic_fixture as local_pilot_synthetic_fixture_command,
)
from emrys.stages.canonical_bam import validator as canonical_bam_validation_command
from emrys.stages.cohort_candidate_preprocessing import (
    validator as cohort_candidate_preprocessing_validation_command,
)
from emrys.stages.duplicate_marking import (
    validator as duplicate_marking_validation_command,
)
from emrys.stages.fasta_sidecars import validator as fasta_sidecars_validation_command
from emrys.stages.gtf_to_bed12 import (
    converter as gtf_to_bed12_command,
)
from emrys.stages.gtf_to_bed12 import validator as bed12_validation_command
from emrys.stages.mechanical_orientation import (
    validator as mechanical_orientation_validation_command,
)
from emrys.stages.partitioned_cohort_mpileup import (
    validator as partitioned_cohort_mpileup_validation_command,
)
from emrys.stages.split_n_cigar import validator as split_n_cigar_validation_command
from emrys.stages.star_alignment import validator as star_alignment_validation_command
from emrys.stages.star_index import validator as star_index_validation_command

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
        package_path = candidate / "src" / "emrys" / "__init__.py"
        if not configuration_path.is_file() or not package_path.is_file():
            continue
        try:
            configuration = tomllib.loads(
                configuration_path.read_text(encoding="utf-8")
            )
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if configuration.get("project", {}).get("name") == "emrys-rna-workflow":
            return candidate
    return None


def _checkout_mismatch() -> str | None:
    checkout_root = _find_checkout_root(Path.cwd().resolve())
    if checkout_root is None:
        return None
    expected_package = checkout_root / "src" / "emrys"
    imported_package = Path(__file__).resolve().parent
    if imported_package == expected_package.resolve():
        return None
    return (
        f"selected interpreter imports EMRYS from {imported_package}, "
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


def _add_storage_qualification_inspection_command(
    inspection_parsers: _SubparserCollection,
) -> None:
    storage_parser = inspection_parsers.add_parser(
        "storage-qualification",
        help="Qualify workflow storage across compute and head nodes.",
        description=storage_qualification_inspection_command.__doc__,
    )
    storage_qualification_inspection_command.configure_parser(storage_parser)
    storage_parser.set_defaults(
        _command_handler=storage_qualification_inspection_command.qualify_from_args
    )


def _add_onboarding_commands(command_parsers: _SubparserCollection) -> None:
    init_parser = command_parsers.add_parser(
        "init",
        help="Initialize one explicit create-absent EMRYS input set.",
    )
    init_parsers = init_parser.add_subparsers(
        dest="initialization",
        metavar="SUBJECT",
        required=True,
    )
    project_parser = init_parsers.add_parser(
        "project",
        help="Create one validated Project root around existing inputs.",
        description=(
            "Collect the current scientific inputs, validate them, then plan or "
            "publish one absent Project root with owned run, log, and runtime "
            "directories. Input data remains in place."
        ),
    )
    local_pilot_onboarding_command.configure_project_init_parser(project_parser)
    project_parser.set_defaults(
        _command_handler=local_pilot_onboarding_command.init_project_from_args
    )
    manifests_parser = init_parsers.add_parser(
        "manifests",
        help="Draft strict sample and optional partition manifests from paths.",
        description="Infer structural pairs and require explicit biological metadata.",
    )
    local_pilot_onboarding_command.configure_manifest_init_parser(manifests_parser)
    manifests_parser.set_defaults(
        _command_handler=local_pilot_onboarding_command.init_manifests_from_args
    )
    synthetic_parser = init_parsers.add_parser(
        "synthetic",
        help="Create a deterministic four-library synthetic Project.",
        description=local_pilot_synthetic_fixture_command.DESCRIPTION,
    )
    local_pilot_synthetic_fixture_command.configure_parser(synthetic_parser)
    synthetic_parser.set_defaults(
        _command_handler=local_pilot_synthetic_fixture_command.init_from_args
    )

    runtime_parser = command_parsers.add_parser(
        "runtime",
        help="Discover and admit the active Project runtime.",
    )
    runtime_parsers = runtime_parser.add_subparsers(
        dest="runtime_operation",
        metavar="SUBJECT",
        required=True,
    )
    discover_parser = runtime_parsers.add_parser(
        "discover",
        help="Inspect the active environment and admit one Project runtime.",
        description=(
            "Discover one unambiguous fixed-workflow runtime, run its readiness "
            "probes, and optionally publish the Project-owned profile. Discovery "
            "is read-only unless --execute is supplied."
        ),
    )
    local_pilot_onboarding_command.configure_runtime_discovery_parser(discover_parser)
    discover_parser.set_defaults(
        _command_handler=local_pilot_onboarding_command.discover_runtime_from_args
    )


def _admit_controlled_runtime() -> bool:
    try:
        require_controlled_python_runtime()
    except SourceCheckoutError as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return False
    return True


def _controlled_local_pilot_from_args(
    arguments: argparse.Namespace,
    *,
    command: Callable[..., int],
) -> int:
    if not _admit_controlled_runtime():
        return 2
    return command(arguments)


def build_parser() -> argparse.ArgumentParser:
    """Build the public parser from owner-supplied command definitions."""
    parser = argparse.ArgumentParser(
        prog="emrys",
        description="Run an explicitly installed EMRYS command.",
    )
    command_parsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
        required=True,
    )
    _add_onboarding_commands(command_parsers)
    doctor_parser = command_parsers.add_parser(
        "doctor",
        help="Diagnose Project readiness and explicitly repair managed runtime state.",
        description=local_pilot_doctor_command.DESCRIPTION,
    )
    local_pilot_doctor_command.configure_parser(doctor_parser)
    doctor_parser.set_defaults(
        _command_handler=local_pilot_doctor_command.doctor_from_args
    )
    run_parser = command_parsers.add_parser(
        "run",
        help="Plan or execute the fixed local CMH pipeline.",
        description=local_pilot_control_command.RUN_DESCRIPTION,
    )
    local_pilot_control_command.configure_run_parser(run_parser)
    run_parser.set_defaults(
        _command_handler=partial(
            _controlled_local_pilot_from_args,
            command=local_pilot_control_command.run_from_args,
        ),
        _command_parser=run_parser,
    )
    resume_parser = command_parsers.add_parser(
        "resume",
        help="Plan or resume one failed or interrupted Run.",
        description=local_pilot_control_command.RESUME_DESCRIPTION,
    )
    local_pilot_control_command.configure_resume_parser(resume_parser)
    resume_parser.set_defaults(
        _command_handler=partial(
            _controlled_local_pilot_from_args,
            command=local_pilot_control_command.resume_from_args,
        ),
        _command_parser=resume_parser,
    )
    report_parser = command_parsers.add_parser(
        "report",
        help="Plan, generate, or reuse reports for one completed Run.",
        description=local_pilot_control_command.REPORT_DESCRIPTION,
    )
    local_pilot_control_command.configure_report_parser(report_parser)
    report_parser.set_defaults(
        _command_handler=partial(
            _controlled_local_pilot_from_args,
            command=local_pilot_control_command.report_from_args,
        ),
        _command_parser=report_parser,
    )
    reconcile_parser = command_parsers.add_parser(
        "reconcile",
        help="Reconcile explicitly declared EMRYS evidence.",
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
        help="Inspect explicitly declared EMRYS operational evidence.",
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
    _add_storage_qualification_inspection_command(inspection_parsers)
    local_run_parser = inspection_parsers.add_parser(
        "run",
        help="Derive one Run state without repair.",
        description=local_pilot_control_command.INSPECT_DESCRIPTION,
    )
    local_pilot_control_command.configure_inspect_parser(local_run_parser)
    local_run_parser.set_defaults(
        _command_handler=partial(
            _controlled_local_pilot_from_args,
            command=local_pilot_control_command.inspect_from_args,
        ),
        _command_parser=local_run_parser,
    )
    convert_parser = command_parsers.add_parser(
        "convert",
        help="Convert an explicitly selected EMRYS input.",
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
        help="Validate an explicitly selected EMRYS input or artifact.",
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
    project_parser = validation_parsers.add_parser(
        "project",
        help="Validate one scientist-authored Project before requiring tools.",
        description=local_pilot_onboarding_command.DESCRIPTION,
    )
    local_pilot_onboarding_command.configure_validation_parser(project_parser)
    project_parser.set_defaults(
        _command_handler=local_pilot_onboarding_command.validate_from_args
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
        name="scientific-context-projection",
        help_text="Validate one scientific-context projection transaction.",
        command=scientific_context_projection_validation_command,
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
    """Parse and dispatch one supported EMRYS command."""
    if mismatch := _checkout_mismatch():
        print(f"emrys: error: {mismatch}", file=sys.stderr)
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
