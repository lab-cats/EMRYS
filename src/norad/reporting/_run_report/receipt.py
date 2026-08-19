"""Deterministic report-summary and v4 receipt projection."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts

from .inputs import _assert_snapshot, _fail, _snapshot_regular
from .models import (
    CSS_RESOURCE,
    INTERPRETATION_BOUNDARY,
    JINJA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    RECEIPT_HEADER,
    REPORT_RECEIPT_SCHEMA_VERSION,
    SUMMARY_HEADER,
    TEMPLATE_RESOURCE,
    ReportContext,
)


def validate_receipt(document: Mapping[str, Any]) -> None:
    validator = contracts.schema_validator("report-receipt")
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{part!r}]" for part in first.path)
        _fail(f"Report receipt schema validation failed at {location}: {first.message}")
    try:
        contracts.validate_report_receipt_semantics(dict(document))
    except contracts.ContractValidationError as exc:
        _fail(f"Report receipt semantic validation failed: {exc}")


def summary_tsv_bytes(context: ReportContext) -> bytes:
    rows = []
    summary = context.summary
    for item in summary["expected_scopes"]:
        scope = item["scope"]
        rows.append(
            (
                summary["run_id"],
                summary["interpretation_boundary"],
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


def validate_summary_tsv(path: Path, context: ReportContext) -> None:
    snapshot = _snapshot_regular(path, "exported run-summary TSV")
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream, delimiter="\t"))
    if not rows or tuple(rows[0]) != SUMMARY_HEADER:
        _fail("Exported run-summary TSV has an unexpected header")
    if len(rows) - 1 != len(context.summary["expected_scopes"]):
        _fail("Exported run-summary TSV row count does not match expected scopes")
    if any(len(row) != len(SUMMARY_HEADER) for row in rows[1:]):
        _fail("Exported run-summary TSV contains a malformed row")
    _assert_snapshot(snapshot, "exported run-summary TSV")


def _truncations(context: ReportContext) -> list[dict[str, Any]]:
    computational_tables = (
        context.computational_results.tables
        if context.computational_results is not None
        else ()
    )
    computational = [
        {
            "table_id": table.table_id,
            "report_section": "computational-results-section",
            "full_table_path": str(table.path),
            "full_table_sha256": table.sha256,
            "full_row_count": table.row_count,
            "displayed_row_count": table.displayed_row_count,
        }
        for table in computational_tables
        if table.truncated
    ]
    return computational


def receipt_document(
    context: ReportContext,
    staged_outputs: Sequence[tuple[str, str, Path, Path]],
) -> dict[str, Any]:
    descriptors = []
    for output_id, kind, staged, final in staged_outputs:
        snapshot = _snapshot_regular(staged, f"staged {kind} output")
        descriptor = {
            "output_id": output_id,
            "kind": kind,
            "path": str(final),
            "sha256": snapshot.sha256,
            "size_bytes": snapshot.size_bytes,
            "media_type": {
                "scientific_html": "text/html",
                "evidence_html": "text/html",
                "run_summary_tsv": "text/tab-separated-values",
            }[kind],
        }
        if kind in {"scientific_html", "evidence_html"}:
            descriptor["self_contained"] = True
        descriptors.append(descriptor)
    identity = hashlib.sha256(
        (
            "\0".join(snapshot.sha256 for snapshot in context.input_snapshots)
            + "\0"
            + JINJA_VERSION
            + "\0"
            + context.render_metadata["figure_renderer_version"]
            + "\0"
            + context.render_metadata["logo_renderer_version"]
            + "\0"
            + context.render_metadata["figure_policy_version"]
            + "\0"
            + PRODUCER_VERSION
        ).encode("utf-8")
    ).hexdigest()[:20]
    summary = context.summary
    document = {
        "schema_name": "norad.report_receipt",
        "schema_version": REPORT_RECEIPT_SCHEMA_VERSION,
        "record_type": "report_receipt",
        "run_id": summary["run_id"],
        "attempt_id": f"report-{identity}",
        "generated_at": summary["generated_at"],
        "publication_state": "complete",
        "transaction_state": "complete",
        "interpretation_boundary": INTERPRETATION_BOUNDARY,
        "input_run_summary": {
            "path": str(context.run_summary_path),
            "sha256": context.run_summary_snapshot.sha256,
            "schema_name": summary["schema_name"],
            "schema_version": summary["schema_version"],
        },
        "renderer": {"name": "Jinja2", "version": JINJA_VERSION},
        "template": {
            "path": f"norad.reporting/{TEMPLATE_RESOURCE}",
            "sha256": context.template_snapshot.sha256,
        },
        "stylesheet": {
            "path": f"norad.reporting/{CSS_RESOURCE}",
            "sha256": context.css_snapshot.sha256,
        },
        "outputs": descriptors,
        "state_banner": context.render_metadata["state_banner"],
        "truncations": _truncations(context),
        "schema_versions": {
            "artifact_record": "2.0.0",
            "run_summary": "2.0.0",
            "report_receipt": REPORT_RECEIPT_SCHEMA_VERSION,
        },
        "analysis_execution_performed": False,
        "external_network_assets_used": False,
        "validation_claimed": False,
        "warnings": list(summary["warnings"]),
        "errors": [],
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": context.producer_git_commit,
            "created_at": summary["generated_at"],
        },
    }
    validate_receipt(document)
    return document


def receipt_tsv_bytes(document: Mapping[str, Any]) -> bytes:
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(RECEIPT_HEADER)
    for output in document["outputs"]:
        writer.writerow(
            (
                document["schema_name"],
                document["schema_version"],
                document["run_id"],
                document["attempt_id"],
                document["generated_at"],
                document["interpretation_boundary"],
                output["output_id"],
                output["kind"],
                output["path"],
                output["sha256"],
                output["size_bytes"],
                output["media_type"],
                "true" if output.get("self_contained") is True else "",
                canonical,
            )
        )
    return stream.getvalue().encode("utf-8")


def read_receipt_tsv(path: Path) -> dict[str, Any]:
    snapshot = _snapshot_regular(path, "report output receipt")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != RECEIPT_HEADER:
                _fail("Existing report receipt is not the v4 receipt header")
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
    validate_receipt(document)
    expected = receipt_tsv_bytes(document)
    if (
        snapshot.size_bytes != len(expected)
        or snapshot.sha256 != hashlib.sha256(expected).hexdigest()
    ):
        _fail(
            "Existing report receipt TSV columns differ from their canonical "
            "JSON record"
        )
    _assert_snapshot(snapshot, "report output receipt")
    return document
