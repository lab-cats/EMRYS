"""Expose EMRYS's grouped command-line interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

import emrys.analyses.paired_cmh_candidate_ranking.validator as paired_cmh_candidate_ranking_validation_command
import emrys.analyses.paired_cmh_candidate_ranking.scientific_context_projection.validator as scientific_context_projection_validation_command
import emrys.contracts.artifacts.validator as artifact_contracts_validation_command
import emrys.evidence.canonical_bam_qc.validator as canonical_bam_qc_validation_command
import emrys.evidence.reference_provenance.reconciler as reference_provenance_reconciliation_command
import emrys.evidence.rseqc_orientation.validator as rseqc_orientation_validation_command
import emrys.evidence.runtime_availability.inspector as runtime_availability_inspection_command
import emrys.evidence.storage_inventory.inspector as storage_inventory_inspection_command
import emrys.evidence.storage_inventory.qualification as storage_qualification_inspection_command
import emrys.ingestion.sample_manifest_admission.validator as manifest_command
import emrys.orchestration.local_pilot.all_pass as all_pass_validation_command
import emrys.orchestration.local_pilot.control as local_pilot_control_command
import emrys.orchestration.local_pilot.doctor as local_pilot_doctor_command
import emrys.orchestration.local_pilot.onboarding as local_pilot_onboarding_command
import emrys.orchestration.local_pilot.synthetic_fixture as local_pilot_synthetic_fixture_command
import emrys.stages.canonical_bam.validator as canonical_bam_validation_command
import emrys.stages.cohort_candidate_preprocessing.validator as cohort_candidate_preprocessing_validation_command
import emrys.stages.duplicate_marking.validator as duplicate_marking_validation_command
import emrys.stages.fasta_sidecars.validator as fasta_sidecars_validation_command
import emrys.stages.gtf_to_bed12.converter as gtf_to_bed12_command
import emrys.stages.gtf_to_bed12.validator as bed12_validation_command
import emrys.stages.mechanical_orientation.validator as mechanical_orientation_validation_command
import emrys.stages.partitioned_cohort_mpileup.validator as partitioned_cohort_mpileup_validation_command
import emrys.stages.split_n_cigar.validator as split_n_cigar_validation_command
import emrys.stages.star_alignment.validator as star_alignment_validation_command
import emrys.stages.star_index.validator as star_index_validation_command
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    require_controlled_python_runtime,
)

CommandHandler = Callable[[argparse.Namespace], int]
_PROJECT_INIT_SUBJECT = "_project"


_VALIDATION_OWNERS = (
    ("all-pass", all_pass_validation_command),
    ("artifact-contracts", artifact_contracts_validation_command),
    ("manifest", manifest_command),
    ("bed12", bed12_validation_command),
    ("canonical-bam", canonical_bam_validation_command),
    ("canonical-bam-qc", canonical_bam_qc_validation_command),
    ("cohort-candidate-preprocessing", cohort_candidate_preprocessing_validation_command),
    ("duplicate-marking", duplicate_marking_validation_command),
    ("fasta-sidecars", fasta_sidecars_validation_command),
    ("mechanical-orientation", mechanical_orientation_validation_command),
    ("paired-cmh-candidate-ranking", paired_cmh_candidate_ranking_validation_command),
    ("scientific-context-projection", scientific_context_projection_validation_command),
    ("partitioned-cohort-mpileup", partitioned_cohort_mpileup_validation_command),
    ("rseqc-orientation", rseqc_orientation_validation_command),
    ("split-n-cigar", split_n_cigar_validation_command),
    ("star-index", star_index_validation_command),
    ("star-alignment", star_alignment_validation_command),
)


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


def _add_owned_command(
    parsers: Any,
    name: str,
    owner: Any,
    action: str,
    help_text: str | None = None,
    description: str | None = None,
    configure_action: str | None = None,
    *,
    controlled: bool = False,
    **parser_options: object,
) -> None:
    description = description or getattr(
        owner,
        f"{action.upper()}_DESCRIPTION",
        getattr(owner, "DESCRIPTION", owner.__doc__),
    )
    command_parser = parsers.add_parser(
        name,
        help=help_text or description,
        description=description,
        **parser_options,
    )
    configure = getattr(
        owner,
        f"configure_{configure_action or action}_parser",
        None,
    ) or owner.configure_parser
    configure(command_parser)
    defaults: dict[str, object] = {
        "_command_handler": getattr(owner, f"{action}_from_args")
    }
    if controlled:
        defaults.update(_command_parser=command_parser, _requires_controlled_runtime=True)
    command_parser.set_defaults(**defaults)


def _add_group(
    parsers: Any,
    name: str,
    help_text: str,
    destination: str,
    commands: Sequence[tuple[Any, ...]],
    *,
    required: bool = True,
) -> argparse.ArgumentParser:
    parser = parsers.add_parser(name, help=help_text)
    children = parser.add_subparsers(
        dest=destination,
        metavar="SUBJECT",
        required=required,
    )
    for command in commands:
        _add_owned_command(children, *command)
    return parser


def _add_onboarding_commands(command_parsers: Any) -> None:
    init_parser = command_parsers.add_parser(
        "init",
        help="Initialize one explicit create-absent EMRYS input set.",
    )
    init_parsers = init_parser.add_subparsers(
        dest="initialization",
        metavar="SUBJECT",
        required=True,
    )
    _add_owned_command(
        init_parsers,
        _PROJECT_INIT_SUBJECT,
        local_pilot_onboarding_command,
        "init_project",
        argparse.SUPPRESS,
        (
            "Collect the current scientific inputs, validate them, then plan or "
            "publish one absent Project root with owned run, log, and runtime "
            "directories. Input data remains in place."
        ),
        "project_init",
        prog="emrys init",
        epilog=(
            "Specialist routes: `emrys init manifests ...` drafts input tables; "
            "`emrys init synthetic ...` creates the supported test Project."
        ),
    )
    _add_owned_command(
        init_parsers,
        "manifests",
        local_pilot_onboarding_command,
        "init_manifests",
        "Draft strict sample and optional partition manifests from paths.",
        "Infer structural pairs and require explicit biological metadata.",
        "manifest_init",
    )
    _add_owned_command(
        init_parsers,
        "synthetic",
        local_pilot_synthetic_fixture_command,
        "init",
        "Create a deterministic four-library synthetic Project.",
    )

    _add_group(
        command_parsers,
        "runtime",
        "Discover and admit the active Project runtime.",
        "runtime_operation",
        ((
            "discover", local_pilot_onboarding_command, "discover_runtime",
            "Inspect the active environment and admit one Project runtime.",
            "Discover one unambiguous fixed-workflow runtime, run its readiness "
            "probes, and optionally publish the Project-owned inventory. Discovery "
            "is read-only unless --execute is supplied.", "runtime_discovery",
        ),),
    )


def _admit_controlled_runtime() -> bool:
    try:
        require_controlled_python_runtime()
    except SourceCheckoutError as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return False
    return True


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
    _add_owned_command(
        command_parsers,
        "doctor",
        local_pilot_doctor_command,
        "doctor",
        "Diagnose Project readiness and explicitly repair managed runtime state.",
    )
    for command in (
        ("run", local_pilot_control_command, "run", "Plan or execute one selected Project Analysis."),
        ("resume", local_pilot_control_command, "resume", "Plan or resume one failed or interrupted Run."),
        ("report", local_pilot_control_command, "report", "Plan, generate, or reuse reports for one completed Run."),
        ("inspect", local_pilot_control_command, "inspect", "Inspect one Project-local Run without mutation."),
    ):
        _add_owned_command(command_parsers, *command, controlled=True)
    _add_group(
        command_parsers,
        "reconcile",
        "Reconcile explicitly declared EMRYS evidence.",
        "reconciliation",
        ((
            "reference-provenance",
            reference_provenance_reconciliation_command,
            "reconcile",
            "Reconcile one explicitly declared reference bundle without repair.",
        ),),
    )
    _add_group(
        command_parsers,
        "debug",
        "Inspect explicitly declared technical EMRYS evidence.",
        "debug_subject",
        (
            ("runtime-availability", runtime_availability_inspection_command, "inspect", "Inspect declared runtime availability without installation or repair."),
            ("storage-inventory", storage_inventory_inspection_command, "inspect", "Inspect declared storage and retention-policy state without mutation."),
            ("storage-qualification", storage_qualification_inspection_command, "qualify", "Qualify workflow storage across compute and head nodes."),
        ),
    )
    _add_group(
        command_parsers,
        "convert",
        "Convert an explicitly selected EMRYS input.",
        "conversion",
        (("gtf-to-bed12", gtf_to_bed12_command, "convert", "Convert GTF transcript models to BED12."),),
    )

    validate_parser = command_parsers.add_parser(
        "validate",
        help="Validate the current Project or one specialist input.",
        description=local_pilot_onboarding_command.DESCRIPTION,
    )
    local_pilot_onboarding_command.configure_validation_parser(validate_parser)
    validate_parser.set_defaults(
        _command_handler=local_pilot_onboarding_command.validate_from_args,
        _command_parser=validate_parser,
    )
    validation_parsers = validate_parser.add_subparsers(
        dest="validation",
        metavar="SUBJECT",
    )
    for name, owner in _VALIDATION_OWNERS:
        _add_owned_command(validation_parsers, name, owner, "validate")
    return parser


def _normalize_public_argv(argv: Sequence[str]) -> tuple[str, ...]:
    """Route ordinary named-Project initialization through its private parser."""

    values = tuple(argv)
    if values[:1] == ("init",) and values[1:2] not in {
        ("manifests",),
        ("synthetic",),
    }:
        return ("init", _PROJECT_INIT_SUBJECT, *values[1:])
    return values


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and dispatch one supported EMRYS command."""
    if mismatch := _checkout_mismatch():
        print(f"emrys: error: {mismatch}", file=sys.stderr)
        return 2
    parser = build_parser()
    supplied = sys.argv[1:] if argv is None else argv
    arguments, unrecognized = parser.parse_known_args(_normalize_public_argv(supplied))
    if unrecognized:
        error_parser = cast(
            argparse.ArgumentParser,
            getattr(arguments, "_command_parser", parser),
        )
        error_parser.error(f"unrecognized arguments: {' '.join(unrecognized)}")
    if getattr(arguments, "_requires_controlled_runtime", False) and not _admit_controlled_runtime():
        return 2
    handler = cast(CommandHandler, arguments._command_handler)
    return handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
