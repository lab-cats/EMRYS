"""Deterministic report output and versioned receipt projection."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts

from .inputs import _assert_snapshot, _fail, _snapshot_regular
from .models import (
    CSS_RESOURCE,
    JINJA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    RECEIPT_HEADER,
    REPORT_RECEIPT_SCHEMA_VERSION,
    TEMPLATE_RESOURCE,
    ReportContext,
)


def validate_receipt(document: Mapping[str, Any]) -> None:
    version = str(document.get("schema_version", ""))
    if version not in {
        REPORT_RECEIPT_SCHEMA_VERSION,
    }:
        _fail(f"Unsupported report receipt schema version: {version!r}")
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


def receipt_document(
    context: ReportContext,
    output_bytes: Sequence[bytes],
) -> dict[str, Any]:
    descriptors = []
    for (output_id, kind, _suffix), final, payload in zip(
        contracts.REPORT_OUTPUTS, context.stable_paths[:-1], output_bytes, strict=True
    ):
        descriptor = {
            "output_id": output_id,
            "kind": kind,
            "path": str(final),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "media_type": "text/html",
            "self_contained": True,
        }
        descriptors.append(descriptor)
    version = REPORT_RECEIPT_SCHEMA_VERSION
    summary = context.summary
    core_renderer = {
        "producer": PRODUCER,
        "producer_version": PRODUCER_VERSION,
        "package": "emrys",
        "content_sha256": context.render_metadata["renderer_package_sha256"],
        "template_engine": "Jinja2",
        "template_engine_version": JINJA_VERSION,
    }
    common = {
        "schema_name": "emrys.report_receipt",
        "schema_version": version,
        "record_type": "report_receipt",
        "run_id": summary["run_id"],
        "generated_at": summary["generated_at"],
        "publication_state": "complete",
        "transaction_state": "complete",
        "interpretation_boundary": context.interpretation_boundary,
        "input_run_summary": {
            "path": str(context.run_summary_path),
            "sha256": context.run_summary_snapshot.sha256,
            "schema_name": summary["schema_name"],
            "schema_version": summary["schema_version"],
        },
        "inputs": [
            {
                "path": str(snapshot.path),
                "sha256": snapshot.sha256,
                "size_bytes": snapshot.size_bytes,
                "rehash_content": rehash,
            }
            for snapshot, _label, rehash in context.report_input_rechecks
            if snapshot.path
            not in {context.template_snapshot.path, context.css_snapshot.path}
        ],
        "template": {
            "path": f"emrys.reporting/{TEMPLATE_RESOURCE}",
            "sha256": context.template_snapshot.sha256,
        },
        "stylesheet": {
            "path": f"emrys.reporting/{CSS_RESOURCE}",
            "sha256": context.css_snapshot.sha256,
        },
        "outputs": descriptors,
        "state_banner": context.render_metadata["state_banner"],
        "schema_versions": {
            "artifact_entry": "4.0.0",
            "run_summary": summary["schema_version"],
            "report_receipt": version,
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
            "installed_package": context.installed_package.record,
            "created_at": summary["generated_at"],
        },
    }
    document = {
        **common,
        "analysis_policy": {
            "path": str(context.analysis_policy_path),
            "sha256": context.analysis_policy_snapshot.sha256,
            "size_bytes": context.analysis_policy_snapshot.size_bytes,
            "schema_version": context.analysis_policy["schema_version"],
        },
        "scientific_renderer": {
            **context.scientific_renderer,
            "module_version": context.analysis_module.descriptor.module_version,
            "core_support": core_renderer,
        },
        "evidence_renderer": core_renderer,
    }
    validate_receipt(document)
    return document


def output_bytes(context: ReportContext) -> tuple[bytes, ...]:
    """Project both reports and their receipt together."""

    outputs = (
        context.scientific_html_bytes,
        context.evidence_html_bytes,
    )
    return (*outputs, receipt_tsv_bytes(receipt_document(context, outputs)))


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
                _fail("Existing report receipt does not use the supported TSV header")
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
