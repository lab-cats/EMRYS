"""Deterministic PDF projection, Quarto rendering, and validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from norad.reporting._run_report import html as html_report

from .bundle_models import (
    PDF_BODY_MARKER,
    PDF_SECTION_MARKERS,
    BundleContext,
)

contracts = html_report.contracts


def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


def _markdown_escape(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _pdf_hash(value: str) -> str:
    """Keep long fixed-width hashes readable within a portrait PDF."""

    midpoint = len(value) // 2
    return f"`{value[:midpoint]}` `{value[midpoint:]}`"


def _pdf_code(value: Any) -> str:
    text = str(value).replace("`", "'").replace("\n", " ")
    return f"`{text}`"


def _pdf_candidate_summary(table: html_report.ApprovedTable) -> list[str]:
    """Render approved candidate rows as compact records, not wide tables."""

    lines = [
        f"Table ID: `{_markdown_escape(table.table_id)}`  ",
        f"Artifact ID: `{_markdown_escape(table.artifact_id)}`  ",
        f"Source file: `{_markdown_escape(table.path.name)}`  ",
        f"SHA-256: {_pdf_hash(table.sha256)}  ",
        f"Rows: {table.row_count}; displayed: {table.displayed_row_count}",
        "",
    ]
    if not table.header or not table.display_rows:
        return lines

    for index, values in enumerate(table.display_rows, start=1):
        row = dict(zip(table.header, values))
        lines.extend(
            [
                f"#### Candidate {index}",
                "",
                f"- Candidate ID: {_pdf_code(row['candidate_id'])}",
                (f"- Selection set: `{_markdown_escape(row['selection_set'])}`"),
            ]
        )
        if table.role == "candidate_selection":
            lines.extend(
                [
                    (
                        "- Rank and call: "
                        f"`{_markdown_escape(row['rank'])}`; "
                        f"`{_markdown_escape(row['source_call_status'])}`"
                    ),
                    (
                        "- CMH FDR, common OR, and delta: "
                        f"`{_markdown_escape(row['source_fdr'])}`; "
                        f"`{_markdown_escape(row['source_common_or'])}`; "
                        f"`{_markdown_escape(row['source_delta'])}`"
                    ),
                    (
                        "- Selection reason: "
                        f"{_markdown_escape(row['selection_reason'])}"
                    ),
                ]
            )
        else:
            lines.extend(
                [
                    (
                        "- Adjudication: "
                        f"`{_markdown_escape(row['adjudication_status'])}`"
                    ),
                    (
                        "- Annotation, matched DNA, orthogonal evidence: "
                        f"`{_markdown_escape(row['annotation_status'])}`; "
                        f"`{_markdown_escape(row['matched_dna_status'])}`; "
                        f"`{_markdown_escape(row['orthogonal_evidence_status'])}`"
                    ),
                    f"- Reason: {_markdown_escape(row['reason'])}",
                ]
            )
        lines.append("")
    return lines


def _pdf_body(context: BundleContext) -> bytes:
    summary = context.html.summary
    banner = html_report.SCIENCE_BANNERS[summary["science_status"]]
    escaped_banner = banner.replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        "```{=typst}",
        f'#set page(header: context [#align(center)[#text(size: 7pt, weight: "bold")[{escaped_banner}]]])',
        "```",
        "",
        f"# {PDF_SECTION_MARKERS[0]}",
        "",
        f"**{banner}**",
        "",
        "Report generation does not establish computational or scientific validation.",
        "",
        f"## {PDF_SECTION_MARKERS[1]}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Run ID | `{_markdown_escape(summary['run_id'])}` |",
        f"| Run-summary schema | `{_markdown_escape(summary['schema_version'])}` |",
        (
            "| Run-summary SHA-256 | "
            f"{_pdf_hash(context.html.run_summary_snapshot.sha256)} |"
        ),
        f"| Primary analysis | `{_markdown_escape(summary['run_contract']['primary_analysis_id'])}` |",
        "",
        f"## {PDF_SECTION_MARKERS[2]}",
        "",
        "| Field | Status |",
        "|---|---|",
    ]
    rollup = summary["computational_rollup"]
    status_labels = (
        "Summary state",
        "Implementation",
        "Local testing",
        "Runtime validation",
        "Cluster dry-run",
        "Cluster proof",
    )
    status_values = (
        summary["summary_state"],
        *(rollup[field] for field in contracts.RUN_SUMMARY_STATUS_FIELDS),
    )
    for label, value in zip(status_labels, status_values):
        lines.append(f"| {label} | `{_markdown_escape(value)}` |")
    failed_scopes = [
        item
        for item in summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    lines.extend(["", "### Failed expected scopes", ""])
    if failed_scopes:
        for item in failed_scopes:
            scope = item["scope"]
            lines.append(
                f"- {_markdown_escape(scope['step_id'])} "
                f"{_markdown_escape(scope['scope_type'])} "
                f"{_markdown_escape(scope['scope_id'])} failed"
            )
    else:
        lines.append("- None.")
    lines.extend(["", f"## {PDF_SECTION_MARKERS[3]}", ""])
    if summary["limitations"]:
        for limitation in summary["limitations"]:
            lines.append(
                f"- **{_markdown_escape(limitation['limitation_id'])} "
                f"({_markdown_escape(limitation['status'])})**: "
                f"{_markdown_escape(limitation['description'])} "
                f"Impact: {_markdown_escape(limitation['impact'])}"
            )
    else:
        lines.append("- No limitations were declared in the canonical summary.")
    lines.extend(["", f"## {PDF_SECTION_MARKERS[4]}", ""])
    candidate_tables = [
        table
        for table in context.html.tables
        if table.role in {"candidate_selection", "candidate_adjudication"}
    ]
    if not candidate_tables:
        lines.append(
            "No candidate table was explicitly authorized by the canonical run summary."
        )
    for table in candidate_tables:
        lines.extend(
            [
                f"### {_markdown_escape(table.title)}",
                "",
                *_pdf_candidate_summary(table),
            ]
        )
    lines.extend(
        [
            f"## {PDF_SECTION_MARKERS[5]}",
            "",
            "This static report consumes one explicit validated canonical run summary.",
            "Supplemental tables are included only when authorized by exact path, hash, row count, and role.",
            "No analysis engine was executed and no validation state was promoted.",
            "",
            "### Expected-scope matrix",
            "",
            (
                "Each expected scope is listed with its aggregate, runtime, "
                "and cluster-proof status."
            ),
            "",
        ]
    )
    for item in summary["expected_scopes"]:
        scope = item["scope"]
        lines.append(
            "- Step "
            f"{_markdown_escape(scope['step_id'])} - "
            f"{_markdown_escape(scope['scope_type'])} / "
            f"{_markdown_escape(scope['scope_id'])}: aggregate "
            f"{_markdown_escape(item['aggregate_state'])}; runtime "
            f"{_markdown_escape(item['runtime_validation_status'])}; "
            "cluster proof "
            f"{_markdown_escape(item['cluster_proof_status'])}."
        )
    template = context.pdf_template_snapshot.path.read_text(encoding="utf-8")
    if template.count(PDF_BODY_MARKER) != 1:
        _fail("PDF report template must contain exactly one body marker")
    if "```{" in template:
        _fail("Tracked PDF template must contain no executable code cells")
    return template.replace(PDF_BODY_MARKER, "\n".join(lines)).encode("utf-8")


def _run_quarto(
    context: BundleContext,
    stage: Path,
    *,
    source: Path,
    target: str,
    output_name: str,
) -> Path:
    command = [
        str(context.html.quarto_path),
        "render",
        source.name,
        "--to",
        target,
        "--output",
        output_name,
        "--no-execute",
    ]
    environment = html_report._sanitized_tool_environment()
    environment["SOURCE_DATE_EPOCH"] = html_report._source_date_epoch(
        context.html.summary
    )
    environment["DENO_DIR"] = str(stage / ".deno")
    environment["TMPDIR"] = str(stage / ".runtime-tmp")
    Path(environment["TMPDIR"]).mkdir(mode=0o700, exist_ok=True)
    returncode, stdout, stderr = html_report._run_quarto_process(
        command, stage, environment, _fail
    )
    if stderr.strip():
        print(stderr.rstrip(), file=sys.stderr)
    if returncode != 0:
        _fail(
            f"Quarto {target} render failed with exit {returncode}: "
            f"{stderr.strip() or stdout.strip()}"
        )
    output = stage / output_name
    if not output.is_file():
        _fail(f"Quarto did not publish the expected staged output: {output}")
    return output


def _validate_pdf(path: Path, banner: str) -> int:
    snapshot = html_report._snapshot_regular(path, "rendered PDF report")
    payload = path.read_bytes()
    if not payload.startswith(b"%PDF-"):
        _fail("Rendered PDF lacks the %PDF- signature")
    if not payload.rstrip().endswith(b"%%EOF"):
        _fail("Rendered PDF lacks the %%EOF marker")
    try:
        reader = PdfReader(path, strict=True)
        page_texts = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:
        _fail(f"Rendered PDF could not be parsed by pinned pypdf: {exc}")
    if not page_texts:
        _fail("Rendered PDF has no pages")
    normalized_banner = " ".join(banner.split())
    for index, text in enumerate(page_texts, start=1):
        if normalized_banner not in " ".join(text.split()):
            _fail(f"Rendered PDF page {index} lacks the required state banner")
    combined = "\n".join(page_texts)
    positions = [combined.find(marker) for marker in PDF_SECTION_MARKERS]
    if any(position < 0 for position in positions):
        missing = [
            marker
            for marker, position in zip(PDF_SECTION_MARKERS, positions)
            if position < 0
        ]
        _fail(f"Rendered PDF lacks required extractable text: {missing}")
    if positions != sorted(positions):
        _fail("Rendered PDF section text is not in the required order")
    html_report._assert_snapshot(snapshot, "rendered PDF report")
    return len(page_texts)
