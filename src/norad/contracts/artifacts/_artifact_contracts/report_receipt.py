"""Report-receipt semantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import (
    ContractValidationError,
    require_unique_key,
    validate_document_paths,
)


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
    expected_kinds = set(document["requested_formats"]) | {"run_summary_tsv"}
    if output_kinds != expected_kinds:
        raise ContractValidationError(
            "report output kinds must exactly match requested formats plus "
            "run_summary_tsv"
        )
    expected_basenames = {
        "html": f"{document['run_id']}.run_report.html",
        "pdf": f"{document['run_id']}.run_report.pdf",
        "run_summary_tsv": f"{document['run_id']}.run_summary.tsv",
    }
    output_parents: set[Path] = set()
    for output in outputs:
        path = Path(output["path"])
        if path.name != expected_basenames[output["kind"]]:
            raise ContractValidationError(
                f"report {output['kind']} output basename must be "
                f"{expected_basenames[output['kind']]!r}"
            )
        output_parents.add(path.parent)
    if len(output_parents) != 1:
        raise ContractValidationError(
            "all report outputs must share one publication directory"
        )
    output_parent = next(iter(output_parents))
    if output_parent.name != document["run_id"]:
        raise ContractValidationError(
            "report publication directory name must equal run_id"
        )
    if (input_run_summary_path := Path(document["input_run_summary"]["path"])).name != (
        f"{document['run_id']}.run_summary.json"
    ):
        raise ContractValidationError(
            "report receipt input run-summary basename does not match run_id"
        )
    if input_run_summary_path.parent.name != document["run_id"]:
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
