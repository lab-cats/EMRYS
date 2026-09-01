"""Validated context preparation for one explicit two-view report transaction."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import shlex
import stat
from collections.abc import Callable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from emrys import analyses
from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    SourceCheckoutError,
    matching_checkout_head_commit,
)

from .candidate_display import build_candidate_display
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
    MODULE_RUN_SUMMARY_SCHEMA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    BOUNDARY_BANNER,
    ComputationalResults,
    ScientificContextResults,
    TEMPLATE_RESOURCE,
    FileSnapshot,
    ReportContext,
)
from .receipt import read_receipt_tsv
from .scientific_context import admit_scientific_context_results
from .validation import render_html
from .view import (
    build_evidence_view,
    build_module_evidence_view,
    build_scientific_view,
)
from emrys.reporting._artifact_index.registry import admit_analysis_module


@dataclass(frozen=True, slots=True)
class ReportIdentityOps:
    """Explicit source-provenance observations for focused routing tests."""

    matching_checkout_head_commit: Callable[..., str | None]


DEFAULT_REPORT_IDENTITY_OPS = ReportIdentityOps(
    matching_checkout_head_commit=matching_checkout_head_commit,
)


def render_paired_scientific_report(
    context: analyses.AnalysisReportContextV1,
) -> analyses.AnalysisScientificReportV1:
    """Render the existing paired-CMH scientific view through its module hook."""

    summary = dict(context.run_summary)
    computational, computational_reason = admit_computational_results(
        summary,
        source_root=context.artifact_source_root,
    )
    scientific_context, scientific_context_reason = admit_scientific_context_results(
        summary,
        source_root=context.artifact_source_root,
        computational_results=computational,
    )
    candidate_display = build_candidate_display(
        computational,
        scientific_context,
        scientific_context_reason,
    )
    figures = build_scientific_figures(
        computational,
        computational_reason,
        scientific_context,
        scientific_context_reason,
        candidate_display,
    )
    css = _resource_snapshot(CSS_RESOURCE, "report CSS resource").path.read_text(
        encoding="utf-8"
    )
    view = build_scientific_view(
        summary,
        {},
        computational_results=computational,
        computational_unavailable_reason=computational_reason,
        scientific_context_results=scientific_context,
        scientific_context_unavailable_reason=scientific_context_reason,
        candidate_display=candidate_display,
        scientific_figures=figures,
        result_links=_result_links(
            context.output_dir,
            computational,
            scientific_context,
        ),
    )
    return analyses.AnalysisScientificReportV1(
        interpretation_boundary=BOUNDARY_BANNER,
        html_bytes=render_html(view, css),
    )


def _result_links(
    output_dir: Path,
    computational_results: ComputationalResults | None,
    scientific_context_results: ScientificContextResults | None,
) -> tuple[dict[str, str], ...]:
    links: list[dict[str, str]] = []

    def append(label: str, description: str, target: Path) -> None:
        relative = os.path.relpath(target, start=output_dir)
        links.append(
            {
                "label": label,
                "description": description,
                "href": quote(Path(relative).as_posix(), safe="/._-"),
            }
        )

    if computational_results is not None:
        append(
            "Threshold-passing candidates",
            "Ranked Step 09 result table",
            computational_results.significant_sites.path,
        )
        append(
            "Complete candidate table",
            "All tested Step 09 candidates",
            computational_results.all_sites.path,
        )
    if scientific_context_results is not None:
        append(
            "Candidate context",
            "Step 10 scientific context",
            scientific_context_results.candidate_context.path,
        )
    return tuple(links)


def _inspect_command(source_root: Path, output_root: Path) -> str:
    canonical_roots = (
        source_root / "results" / "reports",
        source_root / "products" / "report",
    )
    if output_root not in canonical_roots:
        return "emrys inspect run --run-root <run-root>"
    return shlex.join(("emrys", "inspect", "run", "--run-root", str(source_root)))


def expected_html_identity(
    context: ReportContext,
    report_view: Literal["scientific", "evidence"],
) -> dict[str, str]:
    identity = {
        "data-report-view": report_view,
        "data-run-id": context.summary["run_id"],
    }
    if report_view == "scientific":
        if context.analysis_module is None:
            identity["data-selected-candidate-count"] = str(
                len(context.candidate_display.candidates)
                if context.candidate_display is not None
                else 0
            )
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


def _render_module_scientific_report(
    summary: dict[str, object],
    *,
    source_root: Path,
    output_dir: Path,
    admitted_module: analyses.LoadedAnalysisModuleV1 | None,
) -> tuple[
    analyses.LoadedAnalysisModuleV1,
    bytes,
    str,
    tuple[FileSnapshot, ...],
]:
    policy = summary["analysis_policy"]["record"]
    assert isinstance(policy, dict)
    module = admit_analysis_module(policy, admitted=admitted_module)
    declared = {
        artifact.adapter: artifact
        for task in module.descriptor.tasks
        for artifact in task.outputs
        if artifact.kind != "validation_report"
    }
    snapshots: list[FileSnapshot] = []
    report_artifacts = []
    for record in summary["artifacts"]:
        if (
            record["scope"]["scope_type"] != "analysis"
            or record["scope"]["scope_id"] != policy["analysis_id"]
            or record["adapter"] not in declared
            or record["source"] is None
        ):
            continue
        source = record["source"]
        declared_path = Path(source["path"])
        path = declared_path if declared_path.is_absolute() else source_root / declared_path
        snapshot = _snapshot_regular(path, f"analysis artifact {record['artifact_id']!r}")
        if snapshot.sha256 != source["sha256"]:
            _fail(
                "Analysis artifact differs from the admitted run summary: "
                f"{record['artifact_id']}"
            )
        artifact = declared[record["adapter"]]
        snapshots.append(snapshot)
        report_artifacts.append(
            analyses.AnalysisReportArtifactV1(
                adapter=record["adapter"],
                artifact_id=record["artifact_id"],
                path=snapshot.path,
                sha256=snapshot.sha256,
                media_type=analyses.ANALYSIS_MEDIA_TYPE_BY_KIND[artifact.kind],
            )
        )
    try:
        rendered = module.descriptor.render_scientific_report(
            analyses.AnalysisReportContextV1(
                run_id=summary["run_id"],
                analysis_id=policy["analysis_id"],
                module_id=module.descriptor.module_id,
                output_dir=output_dir,
                artifact_source_root=source_root,
                run_summary=summary,
                artifacts=tuple(report_artifacts),
            )
        )
    except Exception as exc:
        _fail(f"Analysis module scientific reporter failed: {exc}")
    if (
        not isinstance(rendered, analyses.AnalysisScientificReportV1)
        or not isinstance(rendered.html_bytes, bytes)
        or not rendered.html_bytes
        or not isinstance(rendered.interpretation_boundary, str)
        or not rendered.interpretation_boundary.strip()
        or rendered.interpretation_boundary.strip()
        != rendered.interpretation_boundary
    ):
        _fail("Analysis module returned an invalid scientific report")
    return (
        module,
        rendered.html_bytes,
        rendered.interpretation_boundary,
        tuple(snapshots),
    )


def _resource_snapshot(resource: str, label: str) -> FileSnapshot:
    traversable = files("emrys.reporting").joinpath(resource)
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
    analysis_module: analyses.LoadedAnalysisModuleV1 | None = None,
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

    module_summary = summary["schema_version"] == MODULE_RUN_SUMMARY_SCHEMA_VERSION
    computational_results, computational_unavailable_reason = (
        (None, None)
        if module_summary
        else admit_computational_results(summary, source_root=source_root)
    )
    scientific_context_results, scientific_context_unavailable_reason = (
        (None, None)
        if module_summary
        else admit_scientific_context_results(
            summary,
            source_root=source_root,
            computational_results=computational_results,
        )
    )
    candidate_display = (
        None
        if computational_results is None
        else build_candidate_display(
            computational_results,
            scientific_context_results,
            scientific_context_unavailable_reason,
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
    if not module_summary:
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
    admitted_module = None
    module_input_snapshots: tuple[FileSnapshot, ...] = ()
    report_boundary = "" if module_summary else str(summary["interpretation_boundary"])
    if module_summary:
        (
            admitted_module,
            scientific_html_bytes,
            report_boundary,
            module_input_snapshots,
        ) = _render_module_scientific_report(
            summary,
            source_root=source_root,
            output_dir=output_dir,
            admitted_module=analysis_module,
        )

    try:
        css = css_snapshot.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read report CSS resource: {exc}")
    metadata = {
        "css_path": f"emrys.reporting/{CSS_RESOURCE}",
        "css_sha256": css_snapshot.sha256,
        "jinja_version": JINJA_VERSION,
        "producer_git_commit": producer_git_commit,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
        "state_banner": (
            report_boundary if module_summary else BOUNDARY_BANNER
        ),
        "source_checkout": str(source_checkout.root),
        "artifact_source_root": str(artifact_source_root.root),
        "template_path": f"emrys.reporting/{TEMPLATE_RESOURCE}",
        "template_sha256": template_snapshot.sha256,
    }
    if not module_summary:
        metadata.update(
            figure_format=FIGURE_FORMAT,
            figure_policy_version=FIGURE_POLICY_VERSION,
            figure_renderer="Matplotlib",
            figure_renderer_version=MATPLOTLIB_VERSION,
            logo_renderer="Logomaker",
            logo_renderer_version=LOGOMAKER_VERSION,
        )
    scientific_figures = (
        ()
        if module_summary
        else build_scientific_figures(
            computational_results,
            computational_unavailable_reason,
            scientific_context_results,
            scientific_context_unavailable_reason,
            candidate_display,
        )
    )
    result_links = _result_links(
        output_dir,
        computational_results,
        scientific_context_results,
    )
    if module_summary:
        evidence_view = build_module_evidence_view(
            summary,
            metadata,
            output_dir=output_dir,
            source_root=source_root,
            inspect_command=_inspect_command(source_root, output_root),
            interpretation_boundary=report_boundary,
        )
        evidence_html_bytes = render_html(evidence_view, css)
    else:
        scientific_view = build_scientific_view(
            summary,
            metadata,
            computational_results=computational_results,
            computational_unavailable_reason=computational_unavailable_reason,
            scientific_context_results=scientific_context_results,
            scientific_context_unavailable_reason=(
                scientific_context_unavailable_reason
            ),
            candidate_display=candidate_display,
            scientific_figures=scientific_figures,
            result_links=result_links,
        )
        evidence_view = build_evidence_view(
            summary,
            metadata,
            computational_results=computational_results,
            computational_unavailable_reason=computational_unavailable_reason,
            scientific_context_results=scientific_context_results,
            scientific_context_unavailable_reason=(
                scientific_context_unavailable_reason
            ),
            scientific_figures=scientific_figures,
            result_links=result_links,
            inspect_command=_inspect_command(source_root, output_root),
        )
        scientific_html_bytes = render_html(scientific_view, css)
        evidence_html_bytes = render_html(evidence_view, css)
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
        candidate_display=candidate_display,
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
        analysis_module=admitted_module,
        module_input_snapshots=module_input_snapshots,
        interpretation_boundary=report_boundary,
    )
    for recheck in context.input_rechecks:
        _assert_input_recheck(*recheck)
    return context
