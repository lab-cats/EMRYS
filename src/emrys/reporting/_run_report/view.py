"""Core-owned evidence and operations report projection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import COMPUTATIONAL_STATUS_FIELDS


def _display(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _table(
    table_id: str,
    caption: str,
    header: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    row_headers: bool = False,
) -> dict[str, Any]:
    return {
        "kind": "table",
        "id": table_id,
        "caption": caption,
        "header": tuple(header),
        "rows": [tuple(_display(value) for value in row) for row in rows],
        "row_headers": row_headers,
        "wide": len(header) > 6,
    }


def _pairs(
    table_id: str, caption: str, rows: Iterable[tuple[str, Any]]
) -> dict[str, Any]:
    return _table(table_id, caption, ("Field", "Value"), rows, row_headers=True)


def _empty(message: str) -> dict[str, Any]:
    return {"kind": "empty", "message": message}


def _note(message: str) -> dict[str, Any]:
    return {"kind": "note", "message": message, "notice": False}


def _section(section_id: str, title: str, *blocks: dict[str, Any]) -> dict[str, Any]:
    return {"id": section_id, "title": title, "blocks": blocks}


def _category(
    category_id: str,
    title: str,
    *sections: dict[str, Any],
    open: bool,
) -> dict[str, Any]:
    return {"id": category_id, "title": title, "sections": sections, "open": open}


def _artifact_overview(summary: Mapping[str, Any]) -> dict[str, Any]:
    rollup = summary["computational_rollup"]
    categories = (
        ("complete", rollup["complete_artifact_count"], "#287a5d"),
        ("missing", rollup["missing_artifact_count"], "#64748b"),
        ("incomplete", rollup["incomplete_artifact_count"], "#b7791f"),
        ("failed", rollup["failed_artifact_count"], "#b42318"),
        (
            "externally unavailable",
            rollup["externally_unavailable_artifact_count"],
            "#6b5ca5",
        ),
    )
    total = rollup["expected_artifact_count"]
    width = 720
    cursor = 0.0
    segments = []
    for name, count, color in categories:
        segment_width = width * count / total if total else 0
        if count:
            segments.append(
                {
                    "x": f"{cursor:.3f}",
                    "width": f"{segment_width:.3f}",
                    "color": color,
                    "name": name,
                    "count": count,
                }
            )
        cursor += segment_width
    return {
        "kind": "artifact_overview",
        "width": width,
        "height": 82,
        "total": total,
        "segments": segments,
        "legend": [{"name": name, "count": count} for name, count, _ in categories],
        "description": ", ".join(f"{name}: {count}" for name, count, _ in categories),
    }


def _run_identity(
    summary: Mapping[str, Any],
    analysis_policy: Mapping[str, Any] | None,
) -> dict[str, Any]:
    contract = summary["run_contract"]
    policy_binding = summary.get("analysis_policy")
    module = None if analysis_policy is None else analysis_policy.get("module")
    module_rows = (
        ()
        if not isinstance(module, Mapping)
        else (
            ("Analysis module", module["module_id"]),
            ("Analysis-module version", module["module_version"]),
            ("Distribution", module["distribution_name"]),
            ("Distribution version", module["distribution_version"]),
        )
    )
    policy_rows = (
        ()
        if not isinstance(policy_binding, Mapping)
        else (
            ("Analysis policy", policy_binding["path"]),
            ("Analysis-policy SHA-256", policy_binding["sha256"]),
        )
    )
    return _pairs(
        "run-identity",
        "Immutable Run, analysis, and source identities",
        (
            ("Run ID", summary["run_id"]),
            ("Run-summary schema", summary["schema_version"]),
            ("Summary state", summary["summary_state"]),
            ("Generated at", summary["generated_at"]),
            ("Run-contract SHA-256", contract["run_contract_sha256"]),
            ("Sample-manifest SHA-256", contract["sample_manifest_sha256"]),
            ("Reference-contract SHA-256", contract["reference_contract_sha256"]),
            ("Partition-manifest SHA-256", contract["partition_manifest_sha256"]),
            ("Primary analysis ID", contract["primary_analysis_id"]),
            (
                "Primary-analysis-policy SHA-256",
                contract["primary_analysis_policy_sha256"],
            ),
            *policy_rows,
            *module_rows,
            ("Inventory", summary["inventory"]["path"]),
            ("Inventory SHA-256", summary["inventory"]["sha256"]),
            ("Artifact receipt", summary["artifact_receipt"]["path"]),
            ("Artifact-receipt SHA-256", summary["artifact_receipt"]["sha256"]),
        ),
    )


def _status(summary: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    rollup = summary["computational_rollup"]
    failed = [
        f"{item['scope']['step_id']} {item['scope']['scope_type']} "
        f"{item['scope']['scope_id']} {item['aggregate_state']}"
        for item in summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    return (
        _pairs(
            "computational-status",
            "Computational status dimensions",
            ((label, rollup[field]) for label, field in COMPUTATIONAL_STATUS_FIELDS),
        ),
        _artifact_overview(summary),
        *((_note("Failed expected scopes: " + "; ".join(failed)),) if failed else ()),
    )


def _limitations(summary: Mapping[str, Any]) -> dict[str, Any]:
    items = summary["limitations"]
    if not items:
        return _empty("No computational limitations are recorded.")
    return _table(
        "limitations",
        "Recorded computational limitations and impact",
        ("Limitation", "Status", "Description", "Impact", "Evidence IDs"),
        (
            (
                item["limitation_id"],
                item["status"],
                item["description"],
                item["impact"],
                ", ".join(item["evidence_ids"]) or "None declared",
            )
            for item in items
        ),
    )


def _scope_matrix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "expected-scope-matrix",
        "Every expected computational scope",
        (
            "Step",
            "Scope type",
            "Scope ID",
            "Evidence state",
            "Implementation",
            "Local test",
            "Runtime",
            "Cluster dry-run",
            "Cluster proof",
            "Artifact IDs",
        ),
        (
            (
                item["scope"]["step_id"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
                item["aggregate_state"],
                *(item[field] for _, field in COMPUTATIONAL_STATUS_FIELDS),
                ", ".join(item["artifact_ids"]),
            )
            for item in summary["expected_scopes"]
        ),
    )


def _analysis_sources(summary: Mapping[str, Any]) -> dict[str, Any]:
    analysis_id = summary["run_contract"]["primary_analysis_id"]
    rows = (
        (
            artifact["artifact_id"],
            artifact["adapter"],
            artifact["availability_status"],
            artifact["source"]["path"] if artifact["source"] else None,
            artifact["source"]["sha256"] if artifact["source"] else None,
        )
        for artifact in summary["artifacts"]
        if artifact["scope"]["scope_type"] == "analysis"
        and artifact["scope"]["scope_id"] == analysis_id
    )
    return _table(
        "analysis-report-sources",
        "Admitted analysis artifacts available to the scientific reporter",
        ("Artifact", "Adapter", "Availability", "Path", "SHA-256"),
        rows,
    )


def _report_inputs(inputs: tuple[tuple[str, str, str, str], ...]) -> dict[str, Any]:
    return (
        _table(
            "analysis-input-records",
            "Additional scientific-renderer inputs bound for receipt-last recheck",
            ("Label", "Path", "SHA-256", "Final verification"),
            inputs,
        )
        if inputs
        else _empty("No additional scientific-renderer inputs were opened.")
    )


def _qc_metrics(summary: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
        (
            artifact["artifact_id"],
            metric["metric_id"],
            metric["name"],
            metric["value"],
            metric["unit"],
            metric["status"],
        )
        for artifact in summary["artifacts"]
        for metric in artifact["metrics"]
    ]
    return (
        _table(
            "qc-metrics",
            "Canonical artifact-level QC metrics",
            ("Artifact", "Metric ID", "Name", "Value", "Unit", "Status"),
            rows,
        )
        if rows
        else _empty("No artifact-level QC metrics are present.")
    )


def _artifact_appendix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "artifact-evidence-index",
        "Expected artifact evidence and selected source records",
        (
            "Artifact",
            "Adapter",
            "Step",
            "Scope",
            "Availability",
            "Completion",
            "Source path",
            "Source SHA-256",
        ),
        (
            (
                artifact["artifact_id"],
                artifact["adapter"],
                artifact["scope"]["step_id"],
                f"{artifact['scope']['scope_type']}:{artifact['scope']['scope_id']}",
                artifact["availability_status"],
                artifact["completion_status"],
                artifact["source"]["path"] if artifact["source"] else None,
                artifact["source"]["sha256"] if artifact["source"] else None,
            )
            for artifact in summary["artifacts"]
        ),
    )


def _tools_and_issues(summary: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    tools = _table(
        "software-provenance",
        "Aggregate software provenance",
        ("Tool", "Version", "Role", "Path", "SHA-256"),
        (
            (tool["name"], tool["version"], tool["role"], tool["path"], tool["sha256"])
            for tool in summary["tools"]
        ),
    )
    issues = [
        (level[:-1], item["code"], item["message"])
        for level in ("warnings", "errors")
        for item in summary[level]
    ]
    return (
        tools,
        _table(
            "run-summary-issues",
            "Aggregate warnings and errors",
            ("Level", "Code", "Message"),
            issues,
        )
        if issues
        else _empty("No aggregate run-summary warnings or errors are recorded."),
    )


def _provenance(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    renderer_details: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    policy = summary.get("analysis_policy")
    return _pairs(
        "report-renderer-provenance",
        "Core evidence renderer provenance",
        (
            ("Run-summary input", metadata["run_summary_path"]),
            ("Run-summary SHA-256", metadata["run_summary_sha256"]),
            ("Renderer", f"{metadata['renderer']} {metadata['renderer_version']}"),
            ("Renderer package SHA-256", metadata["renderer_package_sha256"]),
            ("Jinja2", metadata["jinja_version"]),
            ("Template SHA-256", metadata["template_sha256"]),
            ("CSS SHA-256", metadata["css_sha256"]),
            *((
                ("Analysis policy SHA-256", policy["sha256"]),
            ) if isinstance(policy, Mapping) else ()),
            *renderer_details,
        ),
    )


def _attempts(
    summary: Mapping[str, Any], inspect_command: str
) -> tuple[dict[str, Any], ...]:
    return (
        _note(f"Inspect this Run: {inspect_command}"),
        _table(
            "run-attempt-lineage",
            "Immutable execution-attempt lineage",
            ("Attempt", "State", "Started", "Finished", "Exit code", "Supersedes"),
            (
                (
                    item["attempt_id"],
                    item["state"],
                    item["started_at"],
                    item["finished_at"],
                    item["exit_code"],
                    item["supersedes_attempt_id"],
                )
                for item in summary["attempts"]
            ),
        ),
    )


def build_evidence_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    banner: str,
    result_links: tuple[dict[str, str], ...] = (),
    inspect_command: str = "emrys inspect <RUN>",
    renderer_details: tuple[tuple[str, str], ...] = (),
    figure_evidence: tuple[tuple[str, ...], ...] = (),
    report_inputs: tuple[tuple[str, str, str, str], ...] = (),
    analysis_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the single core evidence and operations view for every module."""

    return {
        "report_view": "evidence",
        "document_title": f"EMRYS evidence and operations report: {summary['run_id']}",
        "heading": f"EMRYS evidence and operations report: {summary['run_id']}",
        "run_id": summary["run_id"],
        "boundary_class": "evidence-boundary",
        "banner": banner,
        "introduction": (
            "This read-only core view records immutable Run identity, admitted "
            "artifacts, evidence, and operations without scientific interpretation."
        ),
        "end_note": "End of evidence report. Reporting changed no Run state.",
        "metadata": dict(metadata),
        "selected_candidate_ids": (),
        "result_links": result_links,
        "categories": (
            _category(
                "overview-category",
                "Run overview",
                _section(
                    "run-identity-section",
                    "Run identity",
                    _run_identity(summary, analysis_policy),
                ),
                _section("status-section", "Computational status", *_status(summary)),
                _section("limitations-section", "Limitations", _limitations(summary)),
                _section(
                    "scope-matrix-section", "Expected scopes", _scope_matrix(summary)
                ),
                open=True,
            ),
            _category(
                "evidence-category",
                "Evidence and provenance",
                _section(
                    "analysis-sources-section",
                    "Analysis sources",
                    _analysis_sources(summary),
                    _report_inputs(report_inputs),
                    (
                        _table(
                            "scientific-figure-provenance",
                            "Scientific-figure inputs, mappings, outputs, and availability",
                            (
                                "Figure ID",
                                "Status",
                                "Input roles",
                                "Mapping",
                                "Population",
                                "SVG asset SHA-256",
                                "SVG asset bytes",
                                "Unavailable reason",
                            ),
                            figure_evidence,
                        )
                        if figure_evidence
                        else _empty("No scientific-figure evidence was supplied.")
                    ),
                ),
                _section("qc-metrics-section", "QC metrics", _qc_metrics(summary)),
                _section(
                    "artifact-appendix-section",
                    "Artifact appendix",
                    _artifact_appendix(summary),
                ),
                _section(
                    "tools-issues-section",
                    "Tools and issues",
                    *_tools_and_issues(summary),
                ),
                _section(
                    "report-provenance-section",
                    "Report provenance",
                    _provenance(summary, metadata, renderer_details),
                ),
                open=False,
            ),
            _category(
                "operations-category",
                "Operations",
                _section(
                    "attempt-lineage-section",
                    "Attempt lineage",
                    *_attempts(summary, inspect_command),
                ),
                open=False,
            ),
        ),
    }
