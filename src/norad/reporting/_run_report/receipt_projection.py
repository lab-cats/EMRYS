"""Deterministic summary and receipt projection for report bundles."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from norad.reporting._run_report import html as html_report

from .bundle_models import (
    PRODUCER,
    PRODUCER_VERSION,
    RECEIPT_HEADER,
    REPORT_RECEIPT_SCHEMA_VERSION,
    SUMMARY_HEADER,
    BundleContext,
)

contracts = html_report.contracts


def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


def _validate_receipt(document: Mapping[str, Any]) -> None:
    validator = contracts.schema_validator("report-receipt")
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{part!r}]" for part in first.path)
        _fail(f"Report receipt schema validation failed at {location}: {first.message}")
    try:
        contracts.validate_document_semantics("report-receipt", dict(document))
    except contracts.ContractValidationError as exc:
        _fail(f"Report receipt semantic validation failed: {exc}")
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
                *(item[field] for field in contracts.RUN_SUMMARY_STATUS_FIELDS),
                str(len(item["warnings"])),
                str(len(item["errors"])),
            )
        )

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
                "NA"
                if output["self_contained"] is None
                else str(output["self_contained"]).lower(),
                "NA" if output["page_count"] is None else output["page_count"],
                "NA"
                if output["state_banner_every_page"] is None
                else str(output["state_banner_every_page"]).lower(),
                canonical,
            )
        )
    return stream.getvalue().encode("utf-8")
