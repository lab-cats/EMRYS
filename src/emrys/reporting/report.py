"""Build one deterministic, self-contained EMRYS two-view report transaction."""

from __future__ import annotations

import argparse
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from emrys import analyses

from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    ArtifactSourceRootError,
    SourceCheckout,
    SourceCheckoutError,
    admit_artifact_source_root,
    admit_source_checkout,
)
from emrys.reporting._run_report.models import ReportRenderError


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


def default_publication_ops() -> ReportPublicationOps:
    from emrys.reporting._run_report import transaction

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
    *,
    analysis_module: analyses.LoadedAnalysisModuleV1 | None = None,
) -> Any:
    """Prepare and validate one report context without durable output state."""

    from emrys.reporting._run_report.context import prepare_context

    source_checkout, artifact_source_root = _admit_source_authorities(arguments)
    return prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        analysis_module=analysis_module,
    )
