"""Build one deterministic, self-contained NORAD two-view report transaction."""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.libraries.source_authority import (
    ArtifactSourceRoot,
    ArtifactSourceRootError,
    SourceCheckout,
    SourceCheckoutError,
    admit_artifact_source_root,
    admit_source_checkout,
)
from norad.reporting._run_report.models import RECEIPT_HEADER, ReportRenderError

DESCRIPTION = (
    "Build self-contained scientific and evidence Jinja HTML reports, a "
    "deterministic run-summary TSV, and one receipt-last v4 transaction from an "
    "explicit canonical run summary. "
    "Dry-run is the default; rendering never runs analysis or promotes evidence."
)


@dataclass(frozen=True)
class ReportPublicationOps:
    """Narrow immutable filesystem and recovery seams for fault testing."""

    link: Callable[[Path, Path], None]
    unlink: Callable[[Path], None]
    fsync_file: Callable[[Path], None]
    fsync_directory: Callable[[Path], None]
    acquire_lock: Callable[[Any, str, Callable[[int, bytes], int]], Any]
    lock_write: Callable[[int, bytes], int]
    release_lock: Callable[[Any], None]
    remove_owned_stage: Callable[[Path, str, tuple[int, int] | None], None]
    write_owned_file: Callable[[Path, bytes], None]
    write_recovery_marker: Callable[[Path, str], None]
    install_signal_handlers: Callable[[], dict[int, Any]]
    restore_signal_handlers: Callable[[dict[int, Any]], None]
    make_token: Callable[[], str]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the installed ``norad build report`` route."""

    parser.add_argument(
        "--source-checkout",
        required=True,
        type=Path,
        help=(
            "Absolute canonical NORAD source checkout governing executing-package "
            "identity and renderer provenance."
        ),
    )
    parser.add_argument(
        "--artifact-source-root",
        required=True,
        type=Path,
        help=(
            "Absolute canonical root resolving contract-relative run-summary "
            "and computational-result paths."
        ),
    )
    parser.add_argument(
        "--run-summary",
        required=True,
        type=Path,
        help="Explicit canonical <run-id>.run_summary.json input.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish both HTML views, summary TSV, and receipt. Omit for dry-run.",
    )


def default_publication_ops() -> ReportPublicationOps:
    from norad.reporting._run_report import transaction

    return ReportPublicationOps(
        link=lambda source, target: os.link(source, target, follow_symlinks=False),
        unlink=lambda path: path.unlink(),
        fsync_file=transaction._fsync_file,
        fsync_directory=transaction._fsync_directory,
        acquire_lock=transaction._acquire_lock,
        lock_write=os.write,
        release_lock=transaction._release_lock,
        remove_owned_stage=transaction._remove_owned_stage,
        write_owned_file=transaction._write_owned_file,
        write_recovery_marker=transaction._write_recovery_marker,
        install_signal_handlers=transaction._install_publication_signal_handlers,
        restore_signal_handlers=transaction._restore_signal_handlers,
        make_token=lambda: f"{os.getpid()}-{uuid.uuid4().hex}",
    )


def _admit_source_authorities(
    arguments: argparse.Namespace,
) -> tuple[SourceCheckout, ArtifactSourceRoot]:
    try:
        source_checkout = admit_source_checkout(
            root=arguments.source_checkout,
            package_root=Path(__file__).resolve().parents[1],
        )
        artifact_source_root = admit_artifact_source_root(
            root=arguments.artifact_source_root,
        )
        return source_checkout, artifact_source_root
    except (ArtifactSourceRootError, SourceCheckoutError) as exc:
        raise ReportRenderError(str(exc)) from exc


def prepare_report(
    arguments: argparse.Namespace,
) -> Any:
    """Prepare and validate one side-effect-free report context."""

    from norad.reporting._run_report.context import prepare_context

    source_checkout, artifact_source_root = _admit_source_authorities(arguments)
    return prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )


def serialize_receipt(document: dict[str, Any]) -> bytes:
    """Serialize the supported v4 receipt TSV deterministically."""

    from norad.reporting._run_report.receipt import receipt_tsv_bytes

    return receipt_tsv_bytes(document)


def print_plan(context: Any) -> None:
    print("NORAD static run-report plan:")
    print(f"  Mode: {'execute' if context.execute else 'dry-run'}")
    print(f"  Source checkout: {context.source_checkout.root}")
    print(f"  Artifact source root: {context.artifact_source_root.root}")
    print(f"  Renderer Git commit: {context.producer_git_commit}")
    print(f"  Run ID: {context.summary['run_id']}")
    print(f"  Run summary: {context.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.run_summary_snapshot.sha256}")
    print(f"  Interpretation boundary: {context.summary['interpretation_boundary']}")
    print(f"  Boundary banner: {context.render_metadata['state_banner']}")
    print(f"  Renderer: Jinja2 {context.render_metadata['jinja_version']}")
    print(f"  Scientific HTML: {context.output_scientific_html}")
    print(f"  Evidence HTML: {context.output_evidence_html}")
    print(f"  Summary TSV: {context.output_summary_tsv}")
    print(f"  Receipt (published last): {context.output_receipt}")
    print("  Report meaning: rendering does not establish validation.")


def build_from_args(
    arguments: argparse.Namespace,
    *,
    publication_ops: ReportPublicationOps | None = None,
) -> int:
    """Validate, plan, and optionally publish one report transaction."""

    from norad.reporting._run_report.models import ReportRenderError
    from norad.reporting._run_report.publication import publish_report

    try:
        context = prepare_report(arguments)
        print_plan(context)
        if context.execute:
            publish_report(context, publication_ops or default_publication_ops())
            print(f"Published report transaction: {context.output_receipt}")
        else:
            print(
                "Dry-run only. Add --execute to publish; no output, lock, or "
                "scratch path was created."
            )
        return 0
    except ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return build_from_args(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
