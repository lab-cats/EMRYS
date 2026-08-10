"""Expose NORAD's grouped command-line interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

from norad.ingestion.sample_manifest_admission import (
    validator as manifest_command,
)
from norad.stages.fasta_sidecars import validator as fasta_sidecars_validation_command
from norad.stages.gtf_to_bed12 import (
    converter as gtf_to_bed12_command,
)
from norad.stages.gtf_to_bed12 import validator as bed12_validation_command
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
    fasta_sidecars_parser = validation_parsers.add_parser(
        "fasta-sidecars",
        help="Validate FASTA index and dictionary sidecars.",
        description=fasta_sidecars_validation_command.DESCRIPTION,
    )
    fasta_sidecars_validation_command.configure_parser(fasta_sidecars_parser)
    fasta_sidecars_parser.set_defaults(
        _command_handler=fasta_sidecars_validation_command.validate_from_args
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
