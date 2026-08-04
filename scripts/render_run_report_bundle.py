#!/usr/bin/env python3
"""Publish a validated NORAD HTML/PDF/TSV report bundle atomically.

This module coordinates the established HTML renderer with a deterministic
format-neutral PDF view. It consumes one explicit canonical run summary,
never discovers analysis inputs, and publishes a receipt last. Rendering does
not execute analysis or promote computational, scientific, or biological
state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker
from pypdf import PdfReader

import render_run_report as html_report


contracts = html_report.contracts


PRODUCER = "render_run_report"
PRODUCER_VERSION = "1.1.0"
REPORT_RECEIPT_SCHEMA_VERSION = "1.1.0"
PDF_TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "run_report_pdf.qmd"
)
PDF_BODY_MARKER = "{{NORAD_REPORT_PDF_BODY}}"
RECEIPT_HEADER = (
    "schema_name",
    "schema_version",
    "run_id",
    "attempt_id",
    "generated_at",
    "science_status",
    "requested_formats",
    "output_id",
    "kind",
    "path",
    "sha256",
    "size_bytes",
    "media_type",
    "self_contained",
    "page_count",
    "state_banner_every_page",
    "report_receipt_json",
)
SUMMARY_HEADER = (
    "run_id",
    "science_status",
    "step_id",
    "scope_type",
    "scope_id",
    "aggregate_state",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "warning_count",
    "error_count",
)
PDF_SECTION_MARKERS = (
    "NORAD consolidated run report",
    "Run identity",
    "Evidence status",
    "Limitations",
    "CMH-ranked candidates",
    "Evidence and methods",
)


@dataclass(frozen=True)
class BundleContext:
    html: html_report.RenderContext
    formats: str
    requested_formats: tuple[str, ...]
    pdf_template_snapshot: html_report.FileSnapshot
    output_pdf: Path
    output_summary_tsv: Path
    output_receipt: Path
    stable_paths: tuple[Path, ...]
    previous_snapshots: Mapping[Path, html_report.FileSnapshot]
    pandoc_version: str
    execute: bool

    @property
    def input_snapshots(self) -> tuple[html_report.FileSnapshot, ...]:
        return (*self.html.input_snapshots, self.pdf_template_snapshot)


def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one canonical NORAD run summary as an atomic static "
            "HTML/PDF/TSV bundle. Dry-run is the default."
        )
    )
    parser.add_argument("--run-summary", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--quarto-bin", required=True, type=Path)
    parser.add_argument(
        "--formats",
        choices=("html", "pdf", "all"),
        default="all",
    )
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def _tool_first_line(path: Path, arguments: Sequence[str], label: str) -> str:
    command = [str(path), *arguments]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=html_report._sanitized_tool_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail(f"Could not inspect {label}: {exc}")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        _fail(f"Could not inspect {label}: {detail}")
    line = result.stdout.splitlines()[0].strip() if result.stdout else ""
    if not line:
        _fail(f"{label} returned no version text")
    return line


def _read_receipt_tsv(path: Path) -> dict[str, Any]:
    snapshot = html_report._snapshot_regular(path, "report output receipt")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != RECEIPT_HEADER:
                _fail("Existing report receipt has an unexpected header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not read existing report receipt: {exc}")
    if not rows:
        _fail("Existing report receipt must contain output rows")
    values = {row["report_receipt_json"] for row in rows}
    if len(values) != 1:
        _fail("Existing report receipt rows disagree on canonical JSON")
    try:
        document = json.loads(values.pop())
    except json.JSONDecodeError as exc:
        _fail(f"Existing report receipt JSON is invalid: {exc}")
    _validate_receipt(document)
    if [row["output_id"] for row in rows] != [
        item["output_id"] for item in document["outputs"]
    ]:
        _fail("Existing report receipt row order differs from its JSON record")
    html_report._assert_snapshot(snapshot, "report output receipt")
    return document


def _validate_receipt(document: Mapping[str, Any]) -> None:
    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["report-receipt"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{part!r}]" for part in first.path)
        _fail(f"Report receipt schema validation failed at {location}: {first.message}")
    try:
        contracts.validate_document_semantics("report-receipt", dict(document))
    except contracts.ContractValidationError as exc:
        _fail(f"Report receipt semantic validation failed: {exc}")


def _validate_existing_bundle(
    receipt_path: Path,
    output_dir: Path,
    known_paths: Sequence[Path],
) -> dict[Path, html_report.FileSnapshot]:
    present = [path for path in known_paths if os.path.lexists(path)]
    if not present:
        return {}
    if not os.path.lexists(receipt_path):
        html_only = len(present) == 1 and present[0].name.endswith(".run_report.html")
        if not html_only:
            _fail(
                "Existing report outputs are incomplete: only a valid "
                "HTML-only predecessor may exist without a bundle receipt"
            )
        snapshot = html_report._snapshot_regular(present[0], "HTML-only predecessor")
        html_report.validate_rendered_html(present[0], expected_banner=None)
        html_report._assert_snapshot(snapshot, "HTML-only predecessor")
        return {present[0]: snapshot}
    document = _read_receipt_tsv(receipt_path)
    snapshots: dict[Path, html_report.FileSnapshot] = {}
    declared: list[Path] = []
    for output in document["outputs"]:
        path = Path(output["path"])
        if path.parent != output_dir:
            _fail("Existing report receipt output is outside its run directory")
        snapshot = html_report._snapshot_regular(path, f"existing {output['kind']} output")
        if snapshot.sha256 != output["sha256"] or snapshot.size_bytes != output["size_bytes"]:
            _fail(f"Existing report output does not match its receipt: {path}")
        declared.append(path)
        snapshots[path] = snapshot
    receipt_snapshot = html_report._snapshot_regular(receipt_path, "existing report receipt")
    snapshots[receipt_path] = receipt_snapshot
    unexpected = set(present) - set(declared) - {receipt_path}
    if unexpected:
        _fail(
            "Existing report directory contains known outputs not declared by "
            f"its receipt: {sorted(str(path) for path in unexpected)}"
        )
    return snapshots


def prepare_context(arguments: argparse.Namespace) -> BundleContext:
    requested = (
        ("html", "pdf")
        if arguments.formats == "all"
        else (arguments.formats,)
    )
    base_arguments = argparse.Namespace(
        run_summary=arguments.run_summary,
        output_root=arguments.output_root,
        quarto_bin=arguments.quarto_bin,
        formats="html",
        execute=arguments.execute,
    )
    html_context = html_report.prepare_context(base_arguments)
    run_id = html_context.summary["run_id"]
    output_pdf = html_context.output_dir / f"{run_id}.run_report.pdf"
    output_summary_tsv = html_context.output_dir / f"{run_id}.run_summary.tsv"
    output_receipt = html_context.output_dir / f"{run_id}.report_outputs.tsv"
    bundle_lock = html_context.output_dir / f".{run_id}.report-bundle.lock"
    html_context = replace(
        html_context,
        lock_path=bundle_lock,
        previous_output_snapshot=None,
    )
    pdf_template_snapshot = html_report._snapshot_regular(
        PDF_TEMPLATE,
        "PDF report template",
    )
    stable_paths = tuple(
        path
        for path in (
            html_context.output_html,
            output_pdf,
            output_summary_tsv,
            output_receipt,
        )
    )
    for path in (*stable_paths, bundle_lock):
        html_report._reject_symlink_components(path, "report bundle path")
    if os.path.lexists(bundle_lock):
        _fail(f"Report bundle lock already exists: {bundle_lock}")
    previous = _validate_existing_bundle(
        output_receipt,
        html_context.output_dir,
        stable_paths,
    )
    pandoc_version = _tool_first_line(
        html_context.quarto_path,
        ("pandoc", "--version"),
        "bundled Pandoc",
    ).removeprefix("pandoc ").strip()
    return BundleContext(
        html=html_context,
        formats=arguments.formats,
        requested_formats=requested,
        pdf_template_snapshot=pdf_template_snapshot,
        output_pdf=output_pdf,
        output_summary_tsv=output_summary_tsv,
        output_receipt=output_receipt,
        stable_paths=stable_paths,
        previous_snapshots=previous,
        pandoc_version=pandoc_version,
        execute=arguments.execute,
    )


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
                (
                    "- Selection set: "
                    f"`{_markdown_escape(row['selection_set'])}`"
                ),
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
    for label, key in (
        ("Summary state", "summary_state"),
        ("Implementation", "implementation_status"),
        ("Local testing", "local_test_status"),
        ("Runtime validation", "runtime_validation_status"),
        ("Cluster dry-run", "cluster_dry_run_status"),
        ("Cluster proof", "cluster_proof_status"),
    ):
        value = summary[key] if key == "summary_state" else rollup[key]
        lines.append(f"| {label} | `{_markdown_escape(value)}` |")
    failed_scopes = [
        item for item in summary["expected_scopes"]
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
        table for table in context.html.tables
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
    environment["SOURCE_DATE_EPOCH"] = html_report._source_date_epoch(context.html.summary)
    environment["DENO_DIR"] = str(stage / ".deno")
    environment["TMPDIR"] = str(stage / ".runtime-tmp")
    Path(environment["TMPDIR"]).mkdir(mode=0o700, exist_ok=True)
    print("Quarto render command:")
    print(f"  {shlex.join(command)}")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=stage,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            html_report._terminate_process_group(process)
            _fail(f"Quarto render exceeded the 300-second timeout: {exc}")
    except OSError as exc:
        if process is not None:
            html_report._terminate_process_group(process)
        _fail(f"Could not execute Quarto render: {exc}")
    except BaseException:
        if process is not None:
            html_report._terminate_process_group(process)
        raise
    assert process is not None
    if stdout.strip():
        print(stdout.rstrip())
    if stderr.strip():
        print(stderr.rstrip(), file=sys.stderr)
    if process.returncode != 0:
        _fail(
            f"Quarto {target} render failed with exit {process.returncode}: "
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
            marker for marker, position in zip(PDF_SECTION_MARKERS, positions)
            if position < 0
        ]
        _fail(f"Rendered PDF lacks required extractable text: {missing}")
    if positions != sorted(positions):
        _fail("Rendered PDF section text is not in the required order")
    html_report._assert_snapshot(snapshot, "rendered PDF report")
    return len(page_texts)


def _summary_tsv_bytes(context: BundleContext) -> bytes:
    rows = []
    summary = context.html.summary
    for item in summary["expected_scopes"]:
        scope = item["scope"]
        rows.append(
            (
                summary["run_id"],
                summary["science_status"],
                scope["step_id"],
                scope["scope_type"],
                scope["scope_id"],
                item["aggregate_state"],
                item["implementation_status"],
                item["local_test_status"],
                item["runtime_validation_status"],
                item["cluster_dry_run_status"],
                item["cluster_proof_status"],
                str(len(item["warnings"])),
                str(len(item["errors"])),
            )
        )
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(SUMMARY_HEADER)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _validate_summary_tsv(path: Path, context: BundleContext) -> None:
    snapshot = html_report._snapshot_regular(path, "exported run-summary TSV")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        rows = list(reader)
    if not rows or tuple(rows[0]) != SUMMARY_HEADER:
        _fail("Exported run-summary TSV has an unexpected header")
    if len(rows) - 1 != len(context.html.summary["expected_scopes"]):
        _fail("Exported run-summary TSV row count does not match expected scopes")
    if any(len(row) != len(SUMMARY_HEADER) for row in rows[1:]):
        _fail("Exported run-summary TSV contains a malformed row")
    html_report._assert_snapshot(snapshot, "exported run-summary TSV")


def _truncations(context: BundleContext) -> list[dict[str, Any]]:
    return [
        {
            "table_id": table.table_id,
            "report_section": (
                "cmh-ranked-candidates"
                if table.role in {"candidate_selection", "candidate_adjudication"}
                else table.role.replace("_", "-")
            ),
            "full_table_path": str(table.path),
            "full_table_sha256": table.sha256,
            "full_row_count": table.row_count,
            "displayed_row_count": table.displayed_row_count,
        }
        for table in context.html.tables
        if table.truncated
    ]


def _receipt_document(
    context: BundleContext,
    staged_outputs: Sequence[tuple[str, str, Path, Path, int | None]],
) -> dict[str, Any]:
    summary = context.html.summary
    descriptors = []
    for output_id, kind, staged, final, page_count in staged_outputs:
        snapshot = html_report._snapshot_regular(staged, f"staged {kind} output")
        descriptors.append(
            {
                "output_id": output_id,
                "kind": kind,
                "path": str(final),
                "sha256": snapshot.sha256,
                "size_bytes": snapshot.size_bytes,
                "media_type": {
                    "html": "text/html",
                    "pdf": "application/pdf",
                    "run_summary_tsv": "text/tab-separated-values",
                }[kind],
                "self_contained": True if kind == "html" else None,
                "page_count": page_count if kind == "pdf" else None,
                "state_banner_every_page": True if kind == "pdf" else None,
            }
        )
    identity = hashlib.sha256(
        (
            context.html.run_summary_snapshot.sha256
            + "\0"
            + ",".join(context.requested_formats)
            + "\0"
            + context.html.template_snapshot.sha256
            + "\0"
            + context.pdf_template_snapshot.sha256
        ).encode("utf-8")
    ).hexdigest()[:20]
    document = {
        "schema_name": "norad.report_receipt",
        "schema_version": REPORT_RECEIPT_SCHEMA_VERSION,
        "record_type": "report_receipt",
        "run_id": summary["run_id"],
        "attempt_id": f"report-{identity}",
        "generated_at": summary["generated_at"],
        "publication_state": "complete",
        "transaction_state": "complete",
        "science_status": summary["science_status"],
        "readiness_authorization": None,
        "input_run_summary": {
            "path": str(context.html.run_summary_path),
            "sha256": context.html.run_summary_snapshot.sha256,
            "schema_name": summary["schema_name"],
            "schema_version": summary["schema_version"],
        },
        "requested_formats": list(context.requested_formats),
        "renderer": {
            "name": "quarto",
            "version": html_report.QUARTO_VERSION,
            "executable": str(context.html.quarto_path),
            "pandoc_version": context.pandoc_version,
            "pdf_engine": "typst" if "pdf" in context.requested_formats else None,
        },
        "template": {
            "path": str(
                context.pdf_template_snapshot.path
                if "pdf" in context.requested_formats
                else context.html.template_snapshot.path
            ),
            "sha256": (
                context.pdf_template_snapshot.sha256
                if "pdf" in context.requested_formats
                else context.html.template_snapshot.sha256
            ),
        },
        "outputs": descriptors,
        "state_banner": html_report.SCIENCE_BANNERS[summary["science_status"]],
        "truncations": _truncations(context),
        "schema_versions": {
            "artifact_record": "1.0.0",
            "scientific_review_record": "1.1.0",
            "run_summary": "1.1.0",
            "report_receipt": "1.1.0",
        },
        "analysis_execution_performed": False,
        "external_network_assets_used": False,
        "validation_claimed": False,
        "warnings": list(summary["warnings"]),
        "errors": [],
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": summary["provenance"]["git_commit"],
            "created_at": summary["generated_at"],
        },
    }
    _validate_receipt(document)
    return document


def _receipt_tsv_bytes(document: Mapping[str, Any]) -> bytes:
    from io import StringIO

    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(RECEIPT_HEADER)
    formats = ",".join(document["requested_formats"])
    for output in document["outputs"]:
        writer.writerow(
            (
                document["schema_name"],
                document["schema_version"],
                document["run_id"],
                document["attempt_id"],
                document["generated_at"],
                document["science_status"],
                formats,
                output["output_id"],
                output["kind"],
                output["path"],
                output["sha256"],
                output["size_bytes"],
                output["media_type"],
                "NA" if output["self_contained"] is None else str(output["self_contained"]).lower(),
                "NA" if output["page_count"] is None else output["page_count"],
                "NA" if output["state_banner_every_page"] is None else str(output["state_banner_every_page"]).lower(),
                canonical,
            )
        )
    return stream.getvalue().encode("utf-8")


def _recheck_inputs(context: BundleContext) -> None:
    html_report._recheck_inputs(context.html)
    html_report._assert_snapshot(context.pdf_template_snapshot, "PDF report template")


def _assert_predecessors(context: BundleContext) -> None:
    for path in context.stable_paths:
        previous = context.previous_snapshots.get(path)
        if previous is None:
            if os.path.lexists(path):
                _fail(f"Report output appeared after preflight: {path}")
        else:
            html_report._assert_snapshot(previous, f"existing report output {path.name}")


def publish_bundle(context: BundleContext) -> None:
    created = html_report._create_directories(context.html.output_dir)
    directory_meta = context.html.output_dir.lstat()
    directory_identity = (directory_meta.st_dev, directory_meta.st_ino)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.html.output_dir / f".run-report-bundle.{token}.tmp"
    recovery = context.html.output_dir / f".{context.html.summary['run_id']}.report-bundle.{token}.RECOVERY.txt"
    ownership: html_report.LockOwnership | None = None
    handlers: dict[int, Any] | None = None
    stage_identity: tuple[int, int] | None = None
    backups: dict[Path, tuple[Path, html_report.FileSnapshot]] = {}
    published: dict[Path, html_report.FileSnapshot] = {}
    committed = False
    recovery_required = False

    def assert_directory() -> None:
        metadata = context.html.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != directory_identity
        ):
            _fail("Report output directory changed identity during publication")

    try:
        handlers = html_report._install_publication_signal_handlers()
        ownership = html_report._acquire_lock(context.html, token)
        assert_directory()
        _assert_predecessors(context)
        os.mkdir(stage, 0o700)
        metadata = stage.lstat()
        stage_identity = (metadata.st_dev, metadata.st_ino)
        _recheck_inputs(context)
        staged_outputs: list[tuple[str, str, Path, Path, int | None]] = []
        if "html" in context.requested_formats:
            rendered_html = html_report._render_with_quarto(context.html, stage)
            staged_outputs.append(("run-report-html", "html", rendered_html, context.html.output_html, None))
        if "pdf" in context.requested_formats:
            source = stage / f"{context.html.summary['run_id']}.run_report_pdf.qmd"
            html_report._write_owned_file(source, _pdf_body(context))
            rendered_pdf = _run_quarto(
                context,
                stage,
                source=source,
                target="typst",
                output_name=context.output_pdf.name,
            )
            page_count = _validate_pdf(
                rendered_pdf,
                html_report.SCIENCE_BANNERS[context.html.summary["science_status"]],
            )
            staged_outputs.append(("run-report-pdf", "pdf", rendered_pdf, context.output_pdf, page_count))
        staged_summary = stage / context.output_summary_tsv.name
        html_report._write_owned_file(staged_summary, _summary_tsv_bytes(context))
        _validate_summary_tsv(staged_summary, context)
        staged_outputs.append(("run-summary-tsv", "run_summary_tsv", staged_summary, context.output_summary_tsv, None))
        receipt_document = _receipt_document(context, staged_outputs)
        staged_receipt = stage / context.output_receipt.name
        html_report._write_owned_file(staged_receipt, _receipt_tsv_bytes(receipt_document))
        read_back = _read_receipt_tsv(staged_receipt)
        if read_back != receipt_document:
            _fail("Staged report receipt did not round-trip deterministically")
        _recheck_inputs(context)
        assert_directory()
        _assert_predecessors(context)

        for final, snapshot in context.previous_snapshots.items():
            backup = context.html.output_dir / f".{final.name}.{token}.previous"
            if os.path.lexists(backup):
                _fail(f"Report backup path unexpectedly exists: {backup}")
            os.link(final, backup, follow_symlinks=False)
            backup_snapshot = html_report._capture_moved_snapshot(
                backup, snapshot, f"backed-up prior {final.name}"
            )
            backups[final] = (backup, backup_snapshot)
        for final in tuple(context.previous_snapshots):
            backup, backup_snapshot = backups[final]
            html_report._capture_moved_snapshot(
                final,
                backup_snapshot,
                f"prior {final.name} after backup link",
            )
            final.unlink()
            refreshed = html_report._snapshot_regular(
                backup,
                f"prior {final.name} backup after unlink",
            )
            if (
                refreshed.device,
                refreshed.inode,
                refreshed.size_bytes,
                refreshed.sha256,
            ) != (
                backup_snapshot.device,
                backup_snapshot.inode,
                backup_snapshot.size_bytes,
                backup_snapshot.sha256,
            ):
                _fail(f"Prior report backup changed content or identity: {backup}")
            backups[final] = (backup, refreshed)
        html_report._fsync_directory(context.html.output_dir)

        publication_order = [item for item in staged_outputs]
        publication_order.append(("report-receipt", "receipt", staged_receipt, context.output_receipt, None))
        for _, kind, staged, final, _ in publication_order:
            if os.path.lexists(final):
                _fail(f"Final report path appeared during publication: {final}")
            staged_snapshot = html_report._snapshot_regular(staged, f"staged {kind}")
            os.link(staged, final, follow_symlinks=False)
            published[final] = html_report._capture_moved_snapshot(
                final, staged_snapshot, f"published {kind}"
            )
            html_report._fsync_file(final)
            html_report._fsync_directory(context.html.output_dir)
        _read_receipt_tsv(context.output_receipt)
        if "html" in context.requested_formats:
            html_report.validate_rendered_html(
                context.html.output_html,
                expected_banner=html_report.SCIENCE_BANNERS[context.html.summary["science_status"]],
                expected_identity=html_report._expected_html_identity(context.html),
            )
        if "pdf" in context.requested_formats:
            _validate_pdf(
                context.output_pdf,
                html_report.SCIENCE_BANNERS[context.html.summary["science_status"]],
            )
        _validate_summary_tsv(context.output_summary_tsv, context)
        _recheck_inputs(context)
        committed = True
    except BaseException as original:
        rollback_errors: list[str] = []
        try:
            assert_directory()
            for final, snapshot in reversed(tuple(published.items())):
                if os.path.lexists(final):
                    html_report._assert_snapshot(snapshot, f"owned published {final.name}")
                    final.unlink()
            for final, (backup, backup_snapshot) in backups.items():
                if os.path.lexists(final):
                    html_report._capture_moved_snapshot(
                        final,
                        backup_snapshot,
                        f"prior {final.name} that remained in place",
                    )
                    backup.unlink()
                    continue
                html_report._assert_snapshot(backup_snapshot, f"prior backup {backup.name}")
                os.link(backup, final, follow_symlinks=False)
                html_report._capture_moved_snapshot(final, backup_snapshot, f"restored {final.name}")
                backup.unlink()
            html_report._fsync_directory(context.html.output_dir)
        except BaseException as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            recovery_required = True
            html_report._write_recovery_marker(
                recovery,
                "Report bundle rollback was incomplete.\n"
                f"Original error: {original}\n"
                f"Rollback errors: {'; '.join(rollback_errors)}\n"
                f"Stage: {stage}\nLock: {context.html.lock_path}\n",
            )
            raise html_report.ReportRenderError(
                "Report bundle publication failed and rollback was incomplete; "
                "preserve the owned lock and recovery state"
            ) from original
        if isinstance(original, html_report.ReportRenderError):
            raise
        if isinstance(original, (KeyboardInterrupt, SystemExit)):
            raise
        raise html_report.ReportRenderError(str(original)) from original
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required:
            try:
                html_report._remove_owned_stage(stage, token, stage_identity)
                for _, (backup, backup_snapshot) in backups.items():
                    if os.path.lexists(backup):
                        if not committed:
                            _fail(f"Unexpected backup remains after rollback: {backup}")
                        html_report._assert_snapshot(backup_snapshot, f"committed backup {backup.name}")
                        backup.unlink()
                html_report._fsync_directory(context.html.output_dir)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if ownership is not None and not recovery_required and not cleanup_errors:
            try:
                html_report._release_lock(ownership)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if handlers is not None:
            html_report._restore_signal_handlers(handlers)
        if cleanup_errors:
            html_report._write_recovery_marker(
                recovery,
                "Report bundle cleanup was incomplete.\n"
                f"Active error: {active}\n"
                f"Cleanup errors: {'; '.join(cleanup_errors)}\n",
            )
            raise html_report.ReportRenderError(
                "Report bundle cleanup failed; preserve recovery evidence: "
                + "; ".join(cleanup_errors)
            ) from active
        if active is not None and not context.previous_snapshots:
            html_report._remove_empty_created_directories(created)


def print_plan(context: BundleContext) -> None:
    print("NORAD static run-report bundle plan:")
    print(f"  Mode: {'execute' if context.execute else 'dry-run'}")
    print(f"  Run ID: {context.html.summary['run_id']}")
    print(f"  Run summary: {context.html.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.html.run_summary_snapshot.sha256}")
    print(f"  Requested formats: {','.join(context.requested_formats)}")
    print(f"  Science status: {context.html.summary['science_status']}")
    print(f"  State banner: {html_report.SCIENCE_BANNERS[context.html.summary['science_status']]}")
    print(f"  Quarto: {context.html.quarto_path}")
    print(f"  Pandoc: {context.pandoc_version}")
    if "html" in context.requested_formats:
        print(f"  HTML output: {context.html.output_html}")
    if "pdf" in context.requested_formats:
        print(f"  PDF output: {context.output_pdf}")
    print(f"  Summary TSV: {context.output_summary_tsv}")
    print(f"  Receipt (published last): {context.output_receipt}")
    print("  Report meaning: rendering does not establish validation.")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        context = prepare_context(parse_arguments(argv))
        print_plan(context)
        if context.execute:
            publish_bundle(context)
            print(f"Published report bundle: {context.output_receipt}")
        else:
            print(
                "Dry-run only. Add --execute to publish; no output, lock, or "
                "scratch path was created."
            )
        return 0
    except html_report.ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
