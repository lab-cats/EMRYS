"""Paired-CMH report-provider entry point."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from emrys.reporting import (
    AnalysisReportContextV1,
    AnalysisReportInputV1,
    AnalysisScientificReportV1,
    admit_report_input,
    render_report_view,
    reporting_resource_path,
)

from .candidate_display import build_candidate_display
from .computational import admit_computational_results
from .constants import BOUNDARY_BANNER
from .figure_models import (
    FIGURE_POLICY_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
)
from .figures import build_scientific_figures
from .scientific_context import admit_scientific_context_results
from .validation import validate_scientific_html
from .view import build_scientific_view


def render_scientific_report(
    context: AnalysisReportContextV1,
) -> AnalysisScientificReportV1:
    """Render the established paired-CMH scientific view from admitted artifacts."""

    summary = dict(context.run_summary)
    artifacts = {artifact.adapter: artifact for artifact in context.artifacts}
    computational, computational_reason = admit_computational_results(
        summary,
        artifacts,
        source_root=context.artifact_source_root,
    )
    scientific_context, scientific_context_reason = admit_scientific_context_results(
        summary,
        artifacts,
        computational_results=computational,
    )
    candidate_display = (
        None
        if computational is None
        else build_candidate_display(
            computational,
            scientific_context,
            scientific_context_reason,
        )
    )
    figures = build_scientific_figures(
        computational,
        computational_reason,
        scientific_context,
        scientific_context_reason,
        candidate_display,
    )
    css_path = reporting_resource_path("styles/run_report.css")
    css = admit_report_input(css_path, "report CSS resource").path.read_text(
        encoding="utf-8"
    )
    link_copy = {
        "step09_cmh_significant_sites_v1": (
            "Threshold-passing candidates",
            "Ranked Step 09 result table",
        ),
        "step09_cmh_all_sites_v1": (
            "Complete candidate table",
            "All tested Step 09 candidates",
        ),
        "step10_candidate_context_v1": (
            "Candidate context",
            "Step 10 scientific context",
        ),
    }
    links = tuple(
        {
            "label": link_copy[artifact.adapter][0],
            "description": link_copy[artifact.adapter][1],
            "href": quote(
                Path(
                    os.path.relpath(artifact.path, start=context.output_dir)
                ).as_posix(),
                safe="/._-",
            ),
        }
        for artifact in context.artifacts
        if artifact.adapter in link_copy
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
        result_links=links,
    )
    html_bytes = render_report_view(view, css)
    validate_scientific_html(
        html_bytes,
        (
            tuple(item.candidate_id for item in candidate_display.candidates)
            if candidate_display is not None
            else ()
        ),
    )
    input_snapshots = {
        snapshot.path: snapshot
        for results in (computational, scientific_context)
        if results is not None
        for snapshot in results.input_snapshots
    }
    identity_only = {
        source.path
        for source in (
            scientific_context.bound_inputs if scientific_context is not None else ()
        )
        if source.role == "reference_fasta"
    }
    return AnalysisScientificReportV1(
        BOUNDARY_BANNER,
        html_bytes,
        tuple(
            AnalysisReportInputV1(
                f"paired-CMH scientific input {path.name!r}",
                path,
                snapshot.sha256,
                path not in identity_only,
            )
            for path, snapshot in sorted(
                input_snapshots.items(), key=lambda item: str(item[0])
            )
        ),
        (
            ("Figure renderer", f"Matplotlib {MATPLOTLIB_VERSION}"),
            ("Logo renderer", f"Logomaker {LOGOMAKER_VERSION}"),
            ("Figure format", "inline SVG"),
            ("Figure policy version", FIGURE_POLICY_VERSION),
        ),
        tuple(
            (
                figure.figure_id,
                figure.status,
                ", ".join(figure.input_roles),
                figure.mapping,
                figure.population,
                "; ".join(
                    f"{asset.panel_id}={asset.svg_sha256}" for asset in figure.assets
                )
                or "Not applicable",
                "; ".join(
                    f"{asset.panel_id}={asset.svg_size_bytes}"
                    for asset in figure.assets
                )
                or "Not applicable",
                figure.unavailable_reason or "None",
            )
            for figure in figures
        ),
    )
