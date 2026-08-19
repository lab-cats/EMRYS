"""Validated context preparation for one explicit two-view report transaction."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import stat
from collections.abc import Callable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal

from norad.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    SourceCheckoutError,
    matching_checkout_head_commit,
)

from .computational import admit_computational_results
from .figures import build_scientific_figures
from .inputs import (
    _assert_input_recheck,
    _assert_snapshot,
    _explicit_path,
    _fail,
    _load_run_summary,
    _reject_symlink_components,
    _snapshot_regular,
)
from .models import (
    CSS_RESOURCE,
    FIGURE_FORMAT,
    FIGURE_POLICY_VERSION,
    JINJA_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    BOUNDARY_BANNER,
    TEMPLATE_RESOURCE,
    FileSnapshot,
    ReportContext,
)
from .receipt import read_receipt_tsv
from .scientific_context import admit_scientific_context_results
from .validation import render_html
from .view import build_evidence_view, build_scientific_view


@dataclass(frozen=True, slots=True)
class ReportIdentityOps:
    """Explicit source-provenance observations for focused routing tests."""

    matching_checkout_head_commit: Callable[..., str | None]


DEFAULT_REPORT_IDENTITY_OPS = ReportIdentityOps(
    matching_checkout_head_commit=matching_checkout_head_commit,
)


def expected_html_identity(
    context: ReportContext,
    report_view: Literal["scientific", "evidence"],
) -> dict[str, str]:
    identity = {
        "data-report-view": report_view,
        "data-run-id": context.summary["run_id"],
    }
    if report_view == "scientific":
        return identity
    metadata = context.render_metadata
    identity.update(
        {
            "data-css-sha256": metadata["css_sha256"],
            "data-jinja-version": metadata["jinja_version"],
            "data-renderer-version": metadata["renderer_version"],
            "data-run-summary-sha256": metadata["run_summary_sha256"],
            "data-template-sha256": metadata["template_sha256"],
        }
    )
    return identity


def _resource_snapshot(resource: str, label: str) -> FileSnapshot:
    traversable = files("norad.reporting").joinpath(resource)
    return _snapshot_regular(Path(str(traversable)), label)


def _validate_output_root(output_root: Path, output_dir: Path) -> None:
    if os.path.lexists(output_root):
        metadata = output_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output root must be a non-symlink directory when it "
                f"exists: {output_root}"
            )
    if os.path.lexists(output_dir):
        metadata = output_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output directory must be a non-symlink directory when "
                f"it exists: {output_dir}"
            )


def _existing_outputs(
    output_dir: Path,
    output_scientific_html: Path,
    output_evidence_html: Path,
    output_summary_tsv: Path,
    output_receipt: Path,
    retired_html: Path,
    retired_pdf: Path,
) -> dict[Path, FileSnapshot]:
    retired = (retired_html, retired_pdf)
    known = (
        output_scientific_html,
        output_evidence_html,
        output_summary_tsv,
        output_receipt,
        *retired,
    )
    present = [path for path in known if os.path.lexists(path)]
    if not present:
        return {}
    if any(path in present for path in retired) or not os.path.lexists(output_receipt):
        _fail(
            "Existing report outputs are incomplete or use a retired contract. "
            "Use a fresh output root or an explicitly approved migration; the v4 "
            "publisher will not adopt or overwrite them."
        )
    try:
        document = read_receipt_tsv(output_receipt)
    except Exception as exc:
        _fail(
            "Existing report receipt is not the active v4 contract. Use a fresh "
            f"output root or an explicitly approved migration: {exc}"
        )
    snapshots: dict[Path, FileSnapshot] = {}
    for output in document["outputs"]:
        path = Path(output["path"])
        if path.parent != output_dir:
            _fail("Existing report receipt output is outside its run directory")
        snapshot = _snapshot_regular(path, f"existing {output['kind']} output")
        if (
            snapshot.sha256 != output["sha256"]
            or snapshot.size_bytes != output["size_bytes"]
        ):
            _fail(f"Existing report output does not match its receipt: {path}")
        snapshots[path] = snapshot
    receipt_snapshot = _snapshot_regular(output_receipt, "existing report receipt")
    snapshots[output_receipt] = receipt_snapshot
    if set(present) != set(snapshots):
        _fail("Existing report outputs differ from the active v4 receipt")
    return snapshots


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
    identity_ops: ReportIdentityOps = DEFAULT_REPORT_IDENTITY_OPS,
) -> ReportContext:
    source_root = artifact_source_root.root
    run_summary_path = _explicit_path(arguments.run_summary, "run-summary path")
    run_summary_snapshot = _snapshot_regular(run_summary_path, "run-summary document")
    summary = _load_run_summary(run_summary_path, source_root=source_root)
    _assert_snapshot(run_summary_snapshot, "run-summary document")
    run_id = summary["run_id"]
    expected_name = f"{run_id}.run_summary.json"
    if run_summary_path.name != expected_name or run_summary_path.parent.name != run_id:
        _fail(
            "Canonical run-summary input must use "
            f"<run-id>/{expected_name}; observed {run_summary_path}"
        )

    computational_results, computational_unavailable_reason = (
        admit_computational_results(summary, source_root=source_root)
    )
    scientific_context_results, scientific_context_unavailable_reason = (
        admit_scientific_context_results(
            summary,
            source_root=source_root,
            computational_results=computational_results,
        )
    )
    try:
        package_root = Path(__file__).resolve().parents[2]
        producer_git_commit = (
            identity_ops.matching_checkout_head_commit(
                source_checkout=source_checkout,
                package_root=package_root,
            )
            or "local_build"
        )
    except SourceCheckoutError as exc:
        _fail(str(exc))
    template_snapshot = _resource_snapshot(TEMPLATE_RESOURCE, "report Jinja template")
    css_snapshot = _resource_snapshot(CSS_RESOURCE, "report CSS resource")
    installed_jinja = importlib.metadata.version("Jinja2")
    if installed_jinja != JINJA_VERSION:
        _fail(
            f"Installed Jinja2 version must match the lock: observed "
            f"{installed_jinja}; expected {JINJA_VERSION}"
        )
    installed_matplotlib = importlib.metadata.version("matplotlib")
    if installed_matplotlib != MATPLOTLIB_VERSION:
        _fail(
            "Installed Matplotlib version must match the lock: observed "
            f"{installed_matplotlib}; expected {MATPLOTLIB_VERSION}"
        )
    installed_logomaker = importlib.metadata.version("logomaker")
    if installed_logomaker != LOGOMAKER_VERSION:
        _fail(
            "Installed Logomaker version must match the lock: observed "
            f"{installed_logomaker}; expected {LOGOMAKER_VERSION}"
        )

    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_scientific_html = output_dir / f"{run_id}.scientific_report.html"
    output_evidence_html = output_dir / f"{run_id}.evidence_report.html"
    output_summary_tsv = output_dir / f"{run_id}.run_summary.tsv"
    output_receipt = output_dir / f"{run_id}.report_outputs.tsv"
    retired_html = output_dir / f"{run_id}.run_report.html"
    retired_pdf = output_dir / f"{run_id}.run_report.pdf"
    lock_path = output_dir / f".{run_id}.report.lock"
    stable_paths = (
        output_scientific_html,
        output_evidence_html,
        output_summary_tsv,
        output_receipt,
    )
    for path in (output_dir, *stable_paths, retired_html, retired_pdf, lock_path):
        _reject_symlink_components(path, "report publication path")
    _validate_output_root(output_root, output_dir)
    if os.path.lexists(lock_path):
        _fail(f"Report publication lock already exists: {lock_path}")
    previous = _existing_outputs(
        output_dir,
        output_scientific_html,
        output_evidence_html,
        output_summary_tsv,
        output_receipt,
        retired_html,
        retired_pdf,
    )

    try:
        css = css_snapshot.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read report CSS resource: {exc}")
    metadata = {
        "css_path": f"norad.reporting/{CSS_RESOURCE}",
        "css_sha256": css_snapshot.sha256,
        "figure_format": FIGURE_FORMAT,
        "figure_policy_version": FIGURE_POLICY_VERSION,
        "figure_renderer": "Matplotlib",
        "figure_renderer_version": MATPLOTLIB_VERSION,
        "logo_renderer": "Logomaker",
        "logo_renderer_version": LOGOMAKER_VERSION,
        "jinja_version": JINJA_VERSION,
        "producer_git_commit": producer_git_commit,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
        "state_banner": BOUNDARY_BANNER,
        "source_checkout": str(source_checkout.root),
        "artifact_source_root": str(artifact_source_root.root),
        "template_path": f"norad.reporting/{TEMPLATE_RESOURCE}",
        "template_sha256": template_snapshot.sha256,
    }
    scientific_figures = build_scientific_figures(
        computational_results,
        computational_unavailable_reason,
        scientific_context_results,
        scientific_context_unavailable_reason,
    )
    scientific_html_bytes = render_html(
        build_scientific_view(
            summary,
            metadata,
            computational_results=computational_results,
            computational_unavailable_reason=computational_unavailable_reason,
            scientific_figures=scientific_figures,
        ),
        css,
    )
    evidence_html_bytes = render_html(
        build_evidence_view(
            summary,
            metadata,
            computational_results=computational_results,
            computational_unavailable_reason=computational_unavailable_reason,
            scientific_context_results=scientific_context_results,
            scientific_context_unavailable_reason=(
                scientific_context_unavailable_reason
            ),
            scientific_figures=scientific_figures,
        ),
        css,
    )
    context = ReportContext(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        producer_git_commit=producer_git_commit,
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        computational_results=computational_results,
        computational_unavailable_reason=computational_unavailable_reason,
        scientific_context_results=scientific_context_results,
        scientific_context_unavailable_reason=scientific_context_unavailable_reason,
        scientific_figures=scientific_figures,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_scientific_html=output_scientific_html,
        output_evidence_html=output_evidence_html,
        output_summary_tsv=output_summary_tsv,
        output_receipt=output_receipt,
        lock_path=lock_path,
        stable_paths=stable_paths,
        previous_snapshots=previous,
        render_metadata=metadata,
        scientific_html_bytes=scientific_html_bytes,
        evidence_html_bytes=evidence_html_bytes,
        execute=arguments.execute,
    )
    for recheck in context.input_rechecks:
        _assert_input_recheck(*recheck)
    return context
