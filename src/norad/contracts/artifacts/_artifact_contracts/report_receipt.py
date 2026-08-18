"""Report-receipt semantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .definitions import ContractValidationError
from .identity import require_unique_key, validate_document_paths


def validate_report_receipt_semantics(document: dict[str, Any]) -> None:
    validate_document_paths(document)
    outputs = document["outputs"]
    require_unique_key(outputs, "output_id", "report outputs")
    output_kinds = {output["kind"] for output in outputs}
    output_paths = {output["path"] for output in outputs}
    if len(output_kinds) != len(outputs):
        raise ContractValidationError("report outputs contain duplicate kinds")
    if len(output_paths) != len(outputs):
        raise ContractValidationError("report outputs contain duplicate paths")
    run_id = document["run_id"]
    expected_output_ids = (
        "scientific-report-html",
        "evidence-report-html",
        "run-summary-tsv",
    )
    expected_outputs = {
        "scientific-report-html": (
            "scientific_html",
            f"{run_id}.scientific_report.html",
        ),
        "evidence-report-html": (
            "evidence_html",
            f"{run_id}.evidence_report.html",
        ),
        "run-summary-tsv": ("run_summary_tsv", f"{run_id}.run_summary.tsv"),
    }
    if {output["output_id"] for output in outputs} != set(expected_output_ids):
        raise ContractValidationError(
            "report output IDs must be exactly scientific-report-html, "
            "evidence-report-html, and run-summary-tsv"
        )
    if tuple(output["output_id"] for output in outputs) != expected_output_ids:
        raise ContractValidationError(
            "report outputs must be ordered scientific-report-html, "
            "evidence-report-html, then run-summary-tsv"
        )
    output_parents: set[Path] = set()
    for output in outputs:
        path = Path(output["path"])
        expected_kind, expected_basename = expected_outputs[output["output_id"]]
        if output["kind"] != expected_kind:
            raise ContractValidationError(
                f"report output {output['output_id']!r} must use kind {expected_kind!r}"
            )
        if path.name != expected_basename:
            raise ContractValidationError(
                f"report {output['kind']} output basename must be {expected_basename!r}"
            )
        output_parents.add(path.parent)
    if len(output_parents) != 1:
        raise ContractValidationError(
            "all report outputs must share one publication directory"
        )
    output_parent = next(iter(output_parents))
    if output_parent.name != run_id:
        raise ContractValidationError(
            "report publication directory name must equal run_id"
        )
    if (input_run_summary_path := Path(document["input_run_summary"]["path"])).name != (
        f"{run_id}.run_summary.json"
    ):
        raise ContractValidationError(
            "report receipt input run-summary basename does not match run_id"
        )
    if input_run_summary_path.parent.name != run_id:
        raise ContractValidationError(
            "report receipt input run-summary directory name must equal run_id"
        )
    require_unique_key(document["truncations"], "table_id", "report truncations")
    for truncation in document["truncations"]:
        if truncation["displayed_row_count"] >= truncation["full_row_count"]:
            raise ContractValidationError(
                f"truncation {truncation['table_id']!r} must display fewer "
                "rows than the full table"
            )
