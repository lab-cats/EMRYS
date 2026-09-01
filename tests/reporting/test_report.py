"""Behavior, security, receipt, and recovery tests for two-view reporting."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from importlib.resources import files
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jinja2 import StrictUndefined, UndefinedError

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1
from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
)
from emrys.reporting import report as REPORT, transaction_validation
from emrys.reporting._artifact_index import context as artifact_context
from emrys.reporting._artifact_index import core as artifact_core
from emrys.reporting._artifact_index import publication as artifact_publication
from emrys.reporting._artifact_index import registry as artifact_registry
from emrys.reporting._run_report import computational as report_computational
from emrys.reporting._run_report import context as report_context
from emrys.reporting._run_report import publication, receipt, validation, view
from emrys.reporting._run_report import scientific_context as report_scientific_context
from emrys.reporting._run_report.models import (
    EVIDENCE_REPORT_SECTION_IDS,
    JINJA_VERSION,
    LOGOMAKER_VERSION,
    MATPLOTLIB_VERSION,
    PRIMARY_SCIENTIFIC_FIGURE_IDS,
    PRODUCER_VERSION,
    SCIENTIFIC_FIGURE_IDS,
    SCIENTIFIC_FIGURE_LABELS,
    SUPPORTING_SCIENTIFIC_FIGURE_IDS,
    ReportRenderError,
)
from emrys.reporting._run_summary import builder as run_summary_builder
from emrys.reporting._run_summary import publication as run_summary_publication
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]


def publish_run_summary(fixture: Any) -> Path:
    FIXTURE.publish_run_summary(fixture)
    return fixture.summary_json_path


@pytest.fixture(scope="module")
def computational_summary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return publish_run_summary(
        FIXTURE.build_fixture(tmp_path_factory.mktemp("report-v4") / "fixture")
    )


@pytest.fixture(scope="module")
def failed_summary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return publish_run_summary(
        FIXTURE.build_failed_fixture(
            tmp_path_factory.mktemp("report-v4-failed") / "fixture"
        )
    )


def arguments(
    summary: Path,
    output_root: Path,
    *,
    execute: bool = False,
    artifact_source_root: Path | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=(
            summary.parent.parent
            if artifact_source_root is None
            else artifact_source_root
        ),
        run_summary=summary,
        output_root=output_root,
        execute=execute,
    )


def output_paths(context: Any) -> tuple[Path, Path, Path, Path]:
    return (
        context.output_scientific_html,
        context.output_evidence_html,
        context.output_summary_tsv,
        context.output_receipt,
    )


def test_external_module_owns_one_bespoke_scientific_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_fixture = FIXTURE.ADAPTER_FIXTURE.build_fixture(
        tmp_path / "external-module"
    )
    builtin = analysis_module_v1()
    selected_outputs = builtin.tasks[0].outputs
    scientific_adapters = tuple(
        item.adapter for item in selected_outputs if item.kind != "validation_report"
    )
    validation_adapter = next(
        item.adapter for item in selected_outputs if item.kind == "validation_report"
    )
    render_contexts: list[analyses.AnalysisReportContextV1] = []

    def render_scientific_report(
        context: analyses.AnalysisReportContextV1,
    ) -> analyses.AnalysisScientificReportV1:
        render_contexts.append(context)
        boundary = "Computational association only."
        items = "".join(
            f"<li>{artifact.adapter}</li>" for artifact in context.artifacts
        )
        return analyses.AnalysisScientificReportV1(
            boundary,
            (
                "<!doctype html><html lang='en'><title>Collaborator report</title>"
                f"<main data-report-view='scientific' data-run-id='{context.run_id}'>"
                "<h1 id='bespoke-collaborator-report'>Collaborator differential "
                "analysis</h1>"
                f"<div class='state-banner'>{boundary}</div><ul>{items}</ul>"
                "</main></html>"
            ).encode(),
        )

    descriptor = replace(
        builtin,
        module_id="collaborator.differential",
        module_version="1.0.0",
        tasks=(
            analyses.AnalysisTaskV1(
                owner_key="collaborator.analysis.differential.v1",
                rule_name="run_collaborator_differential",
                step_id="09",
                stage_memory_mb="workflow",
                inputs=(),
                outputs=selected_outputs,
                plan=builtin.tasks[0].plan,
            ),
        ),
        render_scientific_report=render_scientific_report,
    )
    loaded = replace(
        analyses.load_analysis_module(analyses.BUILTIN_PAIRED_CMH_MODULE_ID),
        descriptor=descriptor,
        trust="external",
        distribution_name="collaborator-analysis",
        distribution_version="1.0.0",
        entry_point_value="collaborator_analysis:analysis_module_v1",
        implementation_sha256="e" * 64,
    )
    policy = {
        "schema_version": "emrys.analysis-module-policy.v1",
        "analysis_id": FIXTURE.ADAPTER_FIXTURE.PRIMARY_ANALYSIS_ID,
        "configuration": {},
        "module": analyses.module_identity_record(loaded),
    }
    policy_path = adapter_fixture.root / "analysis-policy.json"
    policy_path.write_bytes(orchestration_contracts.canonical_json_bytes(policy))
    policy_sha256 = orchestration_contracts.canonical_sha256(policy)
    selected_adapters = {item.adapter for item in selected_outputs}
    FIXTURE.ADAPTER_FIXTURE.write_tsv(
        adapter_fixture.inventory,
        FIXTURE.ADAPTER_FIXTURE.INVENTORY_HEADER,
        (
            row
            for row in adapter_fixture.inventory_rows
            if row["scope_type"] != "analysis" or row["adapter"] in selected_adapters
        ),
    )
    run_contract = json.loads(adapter_fixture.run_contract.read_text(encoding="utf-8"))
    run_contract["primary_analysis_policy_sha256"] = policy_sha256
    components = {
        key: value
        for key, value in run_contract.items()
        if key != "run_contract_sha256"
    }
    run_contract["run_contract_sha256"] = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(components)
    ).hexdigest()
    adapter_fixture.run_contract.write_bytes(
        orchestration_contracts.canonical_json_bytes(run_contract)
    )
    monkeypatch.setattr(
        artifact_registry.analyses,
        "load_analysis_module",
        lambda module_id: loaded,
    )
    profile = analyses.compose_profile(
        json.loads(
            (REPO_ROOT / "workflow/contracts/local_cmh_v2.json").read_text(
                encoding="utf-8"
            )
        ),
        descriptor,
    )
    indexed = artifact_context.prepare_context(
        argparse.Namespace(
            run_id=adapter_fixture.run_id,
            run_contract=adapter_fixture.run_contract,
            analysis_policy=policy_path,
            profile=profile,
            inventory=adapter_fixture.inventory,
            output_root=adapter_fixture.output_root,
        ),
        source_checkout=SourceCheckout(root=REPO_ROOT),
        artifact_source_root=ArtifactSourceRoot(root=adapter_fixture.root),
        identity_ops=artifact_context.ArtifactIdentityOps(
            matching_clean_checkout_head_commit=lambda **_kwargs: (
                artifact_core.get_git_commit(
                    source_root=REPO_ROOT,
                    sanitize_git_routing=True,
                )
            )
        ),
    )
    artifact_publication.publish_context(indexed)
    summarized = run_summary_builder.prepare_context(
        argparse.Namespace(
            run_id=adapter_fixture.run_id,
            artifact_receipt=adapter_fixture.receipt_path,
            analysis_policy=policy_path,
            output_root=adapter_fixture.output_root,
        ),
        source_checkout=SourceCheckout(root=REPO_ROOT),
        artifact_source_root=ArtifactSourceRoot(root=adapter_fixture.root),
    )
    assert summarized.document["schema_version"] == "3.0.0"
    assert summarized.document["analysis_policy"]["record"] == policy
    assert summarized.document["analysis_policy"]["sha256"] == policy_sha256
    run_summary_publication.publish_context(summarized)
    rendered = REPORT.prepare_report(
        arguments(
            summarized.paths.summary_json,
            tmp_path / "reports",
            execute=True,
            artifact_source_root=adapter_fixture.root,
        ),
        analysis_module=indexed.analysis_module,
    )
    assert rendered.analysis_module is indexed.analysis_module
    assert len(render_contexts) == 1
    report_input = render_contexts[0]
    assert report_input.run_summary["schema_version"] == "3.0.0"
    assert {artifact.adapter for artifact in report_input.artifacts} == set(
        scientific_adapters
    )
    scientific = rendered.scientific_html_bytes.decode("utf-8")
    evidence = rendered.evidence_html_bytes.decode("utf-8")
    assert "bespoke-collaborator-report" in scientific
    assert "Computational association only." in scientific
    assert all(adapter in scientific for adapter in scientific_adapters)
    assert validation_adapter not in scientific
    assert validation_adapter in evidence
    assert "interpretation_boundary" not in summarized.document
    assert "result_terminology" not in summarized.document
    assert "report" not in summarized.document["analysis_policy"]["record"]
    publication.publish_report(rendered, REPORT.default_publication_ops())
    published_receipt = receipt.read_receipt_tsv(rendered.output_receipt)
    assert published_receipt["schema_version"] == "5.0.0"
    assert published_receipt["input_run_summary"]["schema_version"] == "3.0.0"
    assert published_receipt["renderer"] == {
        "name": "collaborator.differential",
        "version": "1.0.0",
    }
    assert published_receipt["interpretation_boundary"] == (
        "Computational association only."
    )
    validated = transaction_validation.validate_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=adapter_fixture.root,
        run_summary=summarized.paths.summary_json,
        output_root=rendered.output_root,
        analysis_policy=policy_path,
        profile=profile,
        receipt_ops=transaction_validation.ReceiptValidationOps(
            matching_clean_checkout_head_commit=lambda **_kwargs: (
                artifact_core.get_git_commit(
                    source_root=REPO_ROOT,
                    sanitize_git_routing=True,
                )
            )
        ),
    )
    assert validated.receipt_path == rendered.output_receipt


def receipt_document(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    values = {row["report_receipt_json"] for row in rows}
    assert len(values) == 1
    return json.loads(values.pop())


def write_summary_copy(
    source: Path,
    root: Path,
    mutate: Any | None = None,
) -> Path:
    document = json.loads(source.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(document)
    run_id = document["run_id"]
    directory = root / run_id
    directory.mkdir(parents=True)
    path = directory / f"{run_id}.run_summary.json"
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


STEP09_REPORT_ADAPTERS = (
    "step09_validation_report_v1",
    "step09_cmh_all_sites_v1",
    "step09_cmh_significant_sites_v1",
    "step09_cmh_summary_v1",
    "step09_mutation_spectrum_tsv_v1",
)


def copied_step09_summary(
    source: Path,
    root: Path,
    *,
    mutate_sources: Any | None = None,
    mutate_document: Any | None = None,
) -> tuple[Path, dict[str, Path]]:
    document = json.loads(source.read_text(encoding="utf-8"))
    records = {
        artifact["adapter"]: artifact
        for artifact in document["artifacts"]
        if artifact["adapter"] in STEP09_REPORT_ADAPTERS
        and artifact["scope"]["scope_id"]
        == document["run_contract"]["primary_analysis_id"]
    }
    assert set(records) == set(STEP09_REPORT_ADAPTERS)
    source_dir = root / "step09"
    source_dir.mkdir(parents=True)
    paths: dict[str, Path] = {}
    for adapter, record in records.items():
        original = Path(record["source"]["path"])
        copied = source_dir / original.name
        copied.write_bytes(original.read_bytes())
        record["expectation"]["source_path"] = str(copied)
        record["source"]["path"] = str(copied)
        paths[adapter] = copied
    if mutate_sources is not None:
        mutate_sources(paths)
    for adapter, record in records.items():
        path = paths[adapter]
        payload = path.read_bytes()
        with path.open(encoding="utf-8", newline="") as stream:
            row_count = sum(1 for _row in csv.reader(stream, delimiter="\t")) - 1
        record["source"].update(
            {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "row_count": row_count,
            }
        )
        for metric in record["metrics"]:
            if metric["metric_id"] == "source_row_count":
                metric["value"] = row_count
    if mutate_document is not None:
        mutate_document(document, records)
    step10_artifact_ids = {
        artifact["artifact_id"]
        for artifact in document["artifacts"]
        if artifact["adapter"].startswith("step10_")
    }
    document["artifacts"] = [
        artifact
        for artifact in document["artifacts"]
        if artifact["artifact_id"] not in step10_artifact_ids
    ]
    document["expected_scopes"] = [
        scope
        for scope in document["expected_scopes"]
        if scope["scope"]["step_id"] != "10"
    ]
    document["qc_metrics"] = [
        metric
        for metric in document["qc_metrics"]
        if metric["source_artifact_id"] not in step10_artifact_ids
    ]
    removed_count = len(step10_artifact_ids)
    document["inventory"]["row_count"] -= removed_count
    document["computational_rollup"]["expected_artifact_count"] -= removed_count
    document["computational_rollup"]["complete_artifact_count"] -= removed_count
    run_id = document["run_id"]
    summary_dir = root / "summary" / run_id
    summary_dir.mkdir(parents=True)
    summary = summary_dir / f"{run_id}.run_summary.json"
    summary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary, paths


def rewrite_tsv(path: Path, mutate: Any) -> None:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        rows = list(reader)
    mutate(fieldnames, rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def test_step10_absence_and_partial_declaration_are_context_local_unavailability(
    computational_summary: Path,
) -> None:
    document = json.loads(computational_summary.read_text(encoding="utf-8"))
    without_step10 = {
        **document,
        "artifacts": [
            artifact
            for artifact in document["artifacts"]
            if not artifact["adapter"].startswith("step10_")
        ],
    }
    results, reason = report_scientific_context.admit_scientific_context_results(
        without_step10,
        source_root=computational_summary.parent.parent,
        computational_results=None,
    )
    assert results is None
    assert reason is not None and "predates" in reason

    partially_declared = {
        **without_step10,
        "artifacts": [
            *without_step10["artifacts"],
            next(
                artifact
                for artifact in document["artifacts"]
                if artifact["adapter"] == "step10_context_receipt_v1"
            ),
        ],
    }
    results, reason = report_scientific_context.admit_scientific_context_results(
        partially_declared,
        source_root=computational_summary.parent.parent,
        computational_results=None,
    )
    assert results is None
    assert reason is not None and "not declared" in reason


def test_present_step10_record_mismatch_fails_closed(
    computational_summary: Path,
) -> None:
    document = json.loads(computational_summary.read_text(encoding="utf-8"))
    record = next(
        artifact
        for artifact in document["artifacts"]
        if artifact["adapter"] == "step10_candidate_context_v1"
    )
    record["source"]["sha256"] = "0" * 64
    with pytest.raises(ReportRenderError, match="SHA-256 mismatch"):
        report_scientific_context.admit_scientific_context_results(
            document,
            source_root=computational_summary.parent.parent,
            computational_results=None,
        )


def test_historical_summary_discloses_step10_unavailability_in_candidate_evidence(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    copied, _paths = copied_step09_summary(
        computational_summary, tmp_path / "historical"
    )

    context = REPORT.prepare_report(arguments(copied, tmp_path / "reports"))

    assert context.scientific_context_results is None
    assert context.scientific_context_unavailable_reason is not None
    assert "sequence-context and motif-enrichment figures are unavailable" in (
        context.scientific_context_unavailable_reason
    )
    assert "Selected-candidate editing-rate and location evidence remains" in (
        context.scientific_context_unavailable_reason
    )
    assert tuple(figure.status for figure in context.scientific_figures) == (
        *("available" for _ in range(5)),
        *("unavailable" for _ in range(2)),
        "available",
    )
    assert context.candidate_display is not None
    assert all(
        candidate.motif.state == "step10_unavailable"
        for candidate in context.candidate_display.candidates
    )
    html = context.scientific_html_bytes.decode("utf-8")
    assert 'aria-label="Result files"' in html
    assert "Threshold-passing candidates" in html
    assert "Complete candidate table" in html
    assert "Candidate context" not in html


def test_step10_report_admission_calls_the_canonical_transaction_once(
    computational_summary: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = json.loads(computational_summary.read_text(encoding="utf-8"))
    original = (
        report_scientific_context.owner_context.validate_scientific_context_transaction
    )
    observed: list[Path] = []

    def validate_once(path: Path) -> Any:
        observed.append(path)
        return original(path)

    monkeypatch.setattr(
        report_scientific_context.owner_context,
        "validate_scientific_context_transaction",
        validate_once,
    )
    results, unavailable = report_scientific_context.admit_scientific_context_results(
        document,
        source_root=computational_summary.parent.parent,
        computational_results=None,
    )

    assert results is not None
    assert unavailable is None
    assert observed == [results.receipt.path]


def publish(context: Any, ops: REPORT.ReportPublicationOps | None = None) -> None:
    publication.publish_report(context, ops or REPORT.default_publication_ops())


def test_source_checkout_is_admitted_before_report_inputs(
    tmp_path: Path,
) -> None:
    invalid_checkout = tmp_path / "not-emrys"
    invalid_checkout.mkdir()
    with pytest.raises(ReportRenderError) as captured:
        REPORT.prepare_report(
            argparse.Namespace(
                source_checkout=invalid_checkout,
                artifact_source_root=tmp_path,
                run_summary=tmp_path / "missing.json",
                output_root=tmp_path / "reports",
                execute=False,
            )
        )
    assert "Source checkout project metadata is unavailable" in str(captured.value)
    assert "missing.json" not in str(captured.value)


def test_renderer_git_identity_uses_checkout_not_artifact_root(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    artifact_root = computational_summary.parent.parent.resolve(strict=True)
    assert artifact_root != REPO_ROOT
    observed: list[SourceCheckout] = []

    def matching_commit(**kwargs: Any) -> str:
        assert kwargs["source_checkout"] == SourceCheckout(root=REPO_ROOT)
        observed.append(kwargs["source_checkout"])
        return "a" * 40

    context = report_context.prepare_context(
        arguments(
            computational_summary,
            tmp_path / "reports",
            artifact_source_root=artifact_root,
        ),
        source_checkout=SourceCheckout(root=REPO_ROOT),
        artifact_source_root=ArtifactSourceRoot(root=artifact_root),
        identity_ops=report_context.ReportIdentityOps(
            matching_checkout_head_commit=matching_commit,
        ),
    )

    assert context.producer_git_commit == "a" * 40
    assert observed == [SourceCheckout(root=REPO_ROOT)]


def test_dry_run_is_side_effect_free(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "reports"
    context = REPORT.prepare_report(arguments(computational_summary, output_root))
    assert context.output_dir == output_root / context.summary["run_id"]
    assert not output_root.exists()


def test_success_publishes_two_html_views_summary_and_v4_receipt_last(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    links: list[Path] = []
    base = REPORT.default_publication_ops()

    def record_link(source: Path, target: Path) -> None:
        links.append(target)
        base.link(source, target)

    publish(context, replace(base, link=record_link))
    assert output_paths(context) == tuple(path for path in context.stable_paths)
    assert all(path.is_file() for path in output_paths(context))
    assert [path.name for path in links[-4:]] == [
        context.output_scientific_html.name,
        context.output_evidence_html.name,
        context.output_summary_tsv.name,
        context.output_receipt.name,
    ]
    assert not (
        context.output_dir / f"{context.summary['run_id']}.run_report.html"
    ).exists()
    assert not (
        context.output_dir / f"{context.summary['run_id']}.run_report.pdf"
    ).exists()
    document = receipt_document(context.output_receipt)
    assert document["schema_version"] == "4.0.0"
    assert document["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_emrys"
    )
    assert document["renderer"] == {"name": "Jinja2", "version": JINJA_VERSION}
    assert [item["kind"] for item in document["outputs"]] == [
        "scientific_html",
        "evidence_html",
        "run_summary_tsv",
    ]
    assert document["outputs"][0]["self_contained"] is True
    assert document["outputs"][1]["self_contained"] is True
    html_paths = (context.output_scientific_html, context.output_evidence_html)
    for descriptor, path in zip(document["outputs"][:2], html_paths, strict=True):
        assert descriptor["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert document["outputs"][0]["sha256"] != document["outputs"][1]["sha256"]
    assert document["analysis_execution_performed"] is False
    assert document["validation_claimed"] is False


def test_report_rejects_a_run_summary_without_the_computational_boundary(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    copied = write_summary_copy(
        computational_summary,
        tmp_path / "input",
        lambda document: document.pop("interpretation_boundary"),
    )

    with pytest.raises(ReportRenderError, match="failed validation"):
        REPORT.prepare_report(arguments(copied, tmp_path / "reports"))


def test_receipt_validation_reports_schema_and_semantic_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ReportRenderError, match="schema validation failed"):
        receipt.validate_receipt({})

    class NoSchemaErrors:
        def iter_errors(self, _document: object) -> tuple[()]:
            return ()

    monkeypatch.setattr(
        receipt.contracts,
        "schema_validator",
        lambda _name: NoSchemaErrors(),
    )

    def reject_semantics(_document: dict[str, Any]) -> None:
        raise receipt.contracts.ContractValidationError("synthetic semantic failure")

    monkeypatch.setattr(
        receipt.contracts,
        "validate_report_receipt_semantics",
        reject_semantics,
    )
    with pytest.raises(ReportRenderError, match="synthetic semantic failure"):
        receipt.validate_receipt({})


def test_summary_tsv_validation_rejects_shape_defects(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports")
    )
    path = tmp_path / "summary.tsv"

    path.write_text("wrong\n", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="unexpected header"):
        receipt.validate_summary_tsv(path, context)

    header = "\t".join(receipt.SUMMARY_HEADER) + "\n"
    path.write_text(header, encoding="utf-8")
    with pytest.raises(ReportRenderError, match="row count"):
        receipt.validate_summary_tsv(path, context)

    malformed_rows = "x\n" * len(context.summary["expected_scopes"])
    path.write_text(header + malformed_rows, encoding="utf-8")
    with pytest.raises(ReportRenderError, match="malformed row"):
        receipt.validate_summary_tsv(path, context)


def test_existing_receipt_reader_rejects_shape_and_json_defects(
    tmp_path: Path,
) -> None:
    path = tmp_path / "receipt.tsv"

    def write_rows(rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=receipt.RECEIPT_HEADER,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    path.write_text("wrong\n", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="v4 receipt header"):
        receipt.read_receipt_tsv(path)

    write_rows([])
    with pytest.raises(ReportRenderError, match="must contain output rows"):
        receipt.read_receipt_tsv(path)

    write_rows(
        [
            {"report_receipt_json": "{}"},
            {"report_receipt_json": "[]"},
        ]
    )
    with pytest.raises(ReportRenderError, match="disagree on canonical JSON"):
        receipt.read_receipt_tsv(path)

    write_rows([{"report_receipt_json": "not-json"}])
    with pytest.raises(ReportRenderError, match="JSON is invalid"):
        receipt.read_receipt_tsv(path)


def test_receipt_attributes_provenance_to_renderer_checkout(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    upstream_commit = "upstream-summary-commit"

    def replace_upstream_commit(document: dict[str, Any]) -> None:
        document["provenance"]["git_commit"] = upstream_commit

    copied = write_summary_copy(
        computational_summary,
        tmp_path / "input",
        replace_upstream_commit,
    )
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    publish(context)
    document = receipt_document(context.output_receipt)
    assert context.summary["provenance"]["git_commit"] == upstream_commit
    assert context.producer_git_commit != upstream_commit
    assert document["provenance"] == {
        "producer": "emrys.reporting.report",
        "producer_version": PRODUCER_VERSION,
        "git_commit": context.producer_git_commit,
        "created_at": context.summary["generated_at"],
    }


def test_failed_expected_scope_renders_from_valid_pipeline_summary(
    failed_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(failed_summary, tmp_path / "reports", execute=True)
    )
    failed_scopes = [
        item
        for item in context.summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    assert [item["scope"] for item in failed_scopes] == [
        {"step_id": "01", "scope_type": "sample", "scope_id": "SYNTH_A"}
    ]
    publish(context)
    content = context.output_evidence_html.read_text(encoding="utf-8")
    assert "Failed expected scopes" in content
    assert "01 sample SYNTH_A failed" in content


def test_identical_republication_is_byte_deterministic(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    arguments_value = arguments(
        computational_summary, tmp_path / "reports", execute=True
    )
    first_context = REPORT.prepare_report(arguments_value)
    publish(first_context)
    first = tuple(path.read_bytes() for path in output_paths(first_context))
    second_context = REPORT.prepare_report(arguments_value)
    publish(second_context)
    second = tuple(path.read_bytes() for path in output_paths(second_context))
    assert second == first


def test_jinja_is_strict_autoescaped_and_template_owns_markup(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    def add_untrusted(document: dict[str, Any]) -> None:
        document["warnings"].append(
            {
                "code": "untrusted_text",
                "message": '<script src="https://evil.invalid/x.js">bad</script>',
                "related_artifact_ids": [],
                "evidence": [],
            }
        )

    copied = write_summary_copy(
        computational_summary, tmp_path / "input", add_untrusted
    )
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    publish(context)
    content = context.output_evidence_html.read_text(encoding="utf-8")
    environment = validation.build_environment()
    assert environment.undefined is StrictUndefined
    assert environment.autoescape("run_report.html.j2") is True
    with pytest.raises(UndefinedError):
        environment.get_template("run_report.html.j2").render(view={}, css="")
    assert "&lt;script src=&#34;https://evil.invalid/x.js&#34;&gt;" in content
    assert "<script" not in content.lower()
    assert 'src="https://evil.invalid' not in content
    assert content.count('<style id="emrys-report-styles">') == 1


def test_template_rejects_additional_or_untrusted_safe_boundaries() -> None:
    source = (
        files("emrys.reporting")
        .joinpath("templates/run_report.html.j2")
        .read_text(encoding="utf-8")
    )
    validation.validate_template_source(source)
    with pytest.raises(ReportRenderError, match="may use \\|safe exactly once"):
        validation.validate_template_source(source + "\n{{ view.run_id|safe }}\n")
    with pytest.raises(ReportRenderError, match="may use \\|safe exactly once"):
        validation.validate_template_source(
            source.replace("{{ css | safe }}", "{{ view | safe }}")
        )


def test_scientific_print_styles_pin_static_nonoverflow_layout() -> None:
    source = (
        files("emrys.reporting")
        .joinpath("styles/run_report.css")
        .read_text(encoding="utf-8")
    )

    assert "@media print" in source
    assert "@page" in source
    assert "position: static" in source
    assert "background: #fff" in source
    assert "border: 2px solid #17202a" in source
    assert "color: #17202a" in source
    assert '[data-report-view="scientific"] > .report-disclaimer:last-child' in source
    assert "display: none" in source
    assert '[data-report-view="scientific"] .emrys-table-wrap' in source
    assert "overflow: visible" in source
    assert ".candidate-evidence-record {" in source
    assert "break-inside: auto" in source
    assert "break-inside: avoid-page" in source
    for section_id in (
        "#primary-scientific-figures-section",
        "#supporting-scientific-figures-section",
        "#figure-guide-section",
        "#methods-data-note-section",
    ):
        assert section_id in source
    assert "break-before: page" in source
    assert "max-height: 7.25in" in source
    assert "width: 100%" in source
    assert "page-break-before: always" in source
    assert ".candidate-pair-batch" in source
    assert "page-break-before: always" in source
    assert ".candidate-index-record" in source
    assert ".candidate-index-facts" in source
    assert ".figure-summary" in source
    assert "page-break-inside: avoid" in source
    assert ".scientific-figure-assets" in source
    assert "display: block" in source
    assert ".scientific-figure-image:last-child" in source


def test_two_html_views_separate_science_from_operational_evidence(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    publish(context)
    scientific = context.output_scientific_html.read_text(encoding="utf-8")
    evidence = context.output_evidence_html.read_text(encoding="utf-8")
    banner = "COMPUTATIONAL RESULTS — BIOLOGICAL VALIDATION IS OUTSIDE EMRYS."

    assert banner in scientific and banner in evidence
    assert 'data-report-view="scientific"' in scientific
    assert 'data-report-view="evidence"' in evidence
    run_id = context.summary["run_id"]
    destinations = (
        (
            "Scientific report",
            "What did the analysis find?",
            f"{run_id}.scientific_report.html",
        ),
        (
            "Evidence and provenance",
            "Why should the reader trust this result?",
            f"{run_id}.evidence_report.html#evidence-category",
        ),
        (
            "Operations",
            "How did execution proceed?",
            f"{run_id}.evidence_report.html#operations-category",
        ),
    )
    for content in (scientific, evidence):
        assert 'aria-label="Report purposes"' in content
        for label, question, href in destinations:
            assert f'href="{href}"><strong>{label}</strong>' in content
            assert f'<span class="candidate-status">{question}</span>' in content
    assert context.computational_results is not None
    assert context.scientific_context_results is not None
    result_destinations = (
        (
            "Threshold-passing candidates",
            "Ranked Step 09 result table",
            context.computational_results.significant_sites.path,
        ),
        (
            "Complete candidate table",
            "All tested Step 09 candidates",
            context.computational_results.all_sites.path,
        ),
        (
            "Candidate context",
            "Step 10 scientific context",
            context.scientific_context_results.candidate_context.path,
        ),
    )
    for content in (scientific, evidence):
        assert 'aria-label="Result files"' in content
        for label, description, target in result_destinations:
            href = Path(os.path.relpath(target, start=context.output_dir)).as_posix()
            assert f'href="{href}"><strong>{label}</strong>' in content
            assert f'<span class="candidate-status">{description}</span>' in content
            assert Path(os.path.normpath(context.output_dir / href)) == target
        assert 'href="file:' not in content
        assert 'href="http:' not in content
        assert 'href="https:' not in content
        assert 'href="/' not in content
    assert "emrys inspect run --run-root" not in scientific
    assert "Inspect this Run: emrys inspect run --run-root &lt;run-root&gt;" in evidence
    assert "CMH-ranked candidates" in scientific
    assert "FWD_like" in scientific
    assert 'id="computational_significant_sites"' not in scientific
    assert 'id="computational_all_sites"' not in scientific
    assert 'id="scientific-kpis"' in scientific
    for label in (
        "Samples",
        "Replicate pairs",
        "Successfully tested",
        "Significant up",
        "Significant down",
    ):
        assert label in scientific
    assert 'id="scientific-method-summary"' in scientific
    assert 'id="selected-candidate-index"' in scientific
    assert "Primary findings" in scientific
    assert "Supporting scientific analyses appendix" in scientific
    assert "Figure 1 — Candidate editing landscape" in scientific
    assert (
        "Figure 2 — Selected candidate editing rate, location, and nearby motifs"
        in scientific
    )
    assert "Figure 3 — Candidate location memberships" in scientific
    assert "Figure 4 — Registered PUM motif position and enrichment" in scientific
    assert "Figure S1 — Candidate mutation spectrum" in scientific
    assert "Figure S2 — Condition editing-rate concordance" in scientific
    assert "Figure S3 — Selected candidate per-sample profiles" in scientific
    assert (
        "Figure S4 — Edit-centered sequence context and registered PUM motif"
        in scientific
    )
    assert "Figure 8 —" not in scientific
    assert "1 of 1 significant candidate is shown" in scientific
    assert "1 of 1 significant candidate is displayed" in scientific
    assert "1 exact significant overlay" in scientific
    assert "1 exact significant overlays" not in scientific
    assert "threshold-passing (1 row) TSVs" in scientific
    assert "the admitted Step 10 display order" in scientific
    assert "step10_display_rank" not in scientific
    assert scientific.count('<article id="candidate-evidence-') == 1
    assert scientific.index('id="candidate-landscape-figure"') < scientific.index(
        'id="selected-context-track-figure"'
    )
    assert scientific.index('id="selected-context-track-figure"') < scientific.index(
        'id="candidate-evidence-1"'
    )
    assert scientific.index('id="candidate-evidence-1"') < scientific.index(
        'id="location-membership-figure"'
    )
    assert "Editing rate" in scientific
    assert "Location" in scientific
    assert "Nearby motifs" in scientific
    assert "candidate_1" in scientific
    assert "Selected exact sample QC" not in scientific
    assert "Attempt lineage" not in scientific
    assert "Artifact appendix" not in scientific
    assert "Tools and issues" not in scientific
    assert "Report provenance" not in scientific
    assert "<svg" not in scientific
    assert scientific.count("data:image/svg+xml;base64,") == sum(
        len(figure.assets) for figure in context.scientific_figures
    )
    assert tuple(figure.status for figure in context.scientific_figures) == (
        "available",
        "available",
        "available",
        "available",
        "available",
        "available",
        "unavailable",
        "available",
    )
    assert "unweighted means across manifest-defined replicates" in scientific
    assert "percentages therefore need not sum" in scientific
    assert "<details" not in scientific
    assert '<div class="emrys-table-wrap emrys-table-wrap-wide"' not in scientific
    assert scientific.count("figure-takeaway") == len(SCIENTIFIC_FIGURE_IDS)
    assert scientific.count('class="figure-guide-entry"') == len(SCIENTIFIC_FIGURE_IDS)
    assert tuple(
        sorted(
            SCIENTIFIC_FIGURE_IDS,
            key=lambda figure_id: scientific.index(f'id="{figure_id}"'),
        )
    ) == (*PRIMARY_SCIENTIFIC_FIGURE_IDS, *SUPPORTING_SCIENTIFIC_FIGURE_IDS)
    assert tuple(
        SCIENTIFIC_FIGURE_LABELS[figure_id]
        for figure_id in (
            *PRIMARY_SCIENTIFIC_FIGURE_IDS,
            *SUPPORTING_SCIENTIFIC_FIGURE_IDS,
        )
    ) == (
        "Figure 1",
        "Figure 2",
        "Figure 3",
        "Figure 4",
        "Figure S1",
        "Figure S2",
        "Figure S3",
        "Figure S4",
    )
    assert 'id="step09-source-records"' in evidence
    assert 'id="scientific-figure-provenance"' in evidence
    assert 'id="computational_significant_sites"' not in evidence
    assert 'id="computational_all_sites"' not in evidence
    assert "candidate_1" not in evidence
    assert "Attempt lineage" in evidence
    assert "EMRYS evidence and operations report" in evidence
    assert evidence.index('id="evidence-category"') < evidence.index(
        'id="operations-category"'
    )
    assert 'id="provenance-category"' not in evidence
    for section_id in EVIDENCE_REPORT_SECTION_IDS:
        assert evidence.count(f'id="{section_id}"') == 1
    assert "<details" in evidence
    assert "Artifact appendix" in evidence
    assert "Report provenance" in evidence
    assert "<svg" in evidence
    assert "data:image/svg+xml;base64," not in evidence
    assert f"Matplotlib {MATPLOTLIB_VERSION}" in evidence
    assert f"Logomaker {LOGOMAKER_VERSION}" in evidence
    assert "exact significant overlay" in evidence
    for table in context.computational_results.tables:
        assert str(table.path) not in scientific
        assert table.sha256 not in scientific
        assert str(table.path) in evidence
        assert table.sha256 in evidence
    assert context.scientific_context_results is not None
    for table in context.scientific_context_results.tables:
        assert str(table.path) not in scientific
        assert table.sha256 not in scientific
        assert str(table.path) in evidence
        assert table.sha256 in evidence
    for source in context.scientific_context_results.bound_inputs:
        assert str(source.path) not in scientific
        assert source.sha256 not in scientific
        assert str(source.path) in evidence
        assert source.sha256 in evidence
    for metadata_field in (
        "css_sha256",
        "run_summary_sha256",
        "template_sha256",
    ):
        assert context.render_metadata[metadata_field] not in scientific
        assert context.render_metadata[metadata_field] in evidence
    for content in (scientific, evidence):
        assert "selected biological strand" not in content
        assert "<script" not in content.lower()
        assert "http://" not in content and "https://" not in content

    validation.validate_rendered_html(
        context.output_scientific_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity={
            "data-report-view": "scientific",
            "data-run-id": context.summary["run_id"],
            "data-selected-candidate-count": "1",
        },
        expected_candidate_ids=("candidate_1",),
    )
    validation.validate_rendered_html(
        context.output_evidence_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity={
            "data-css-sha256": context.render_metadata["css_sha256"],
            "data-jinja-version": JINJA_VERSION,
            "data-report-view": "evidence",
            "data-renderer-version": context.render_metadata["renderer_version"],
            "data-run-id": context.summary["run_id"],
            "data-run-summary-sha256": context.render_metadata["run_summary_sha256"],
            "data-template-sha256": context.render_metadata["template_sha256"],
        },
    )
    candidate_in_evidence = tmp_path / "candidate-in-evidence.html"
    candidate_in_evidence.write_text(
        evidence.replace(
            "</main>",
            '<div class="candidate-index-block"></div></main>',
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ReportRenderError, match="selected-candidate presentation"):
        validation.validate_rendered_html(
            candidate_in_evidence,
            expected_banner=context.render_metadata["state_banner"],
            expected_identity={
                "data-css-sha256": context.render_metadata["css_sha256"],
                "data-jinja-version": JINJA_VERSION,
                "data-report-view": "evidence",
                "data-renderer-version": context.render_metadata["renderer_version"],
                "data-run-id": context.summary["run_id"],
                "data-run-summary-sha256": context.render_metadata[
                    "run_summary_sha256"
                ],
                "data-template-sha256": context.render_metadata["template_sha256"],
            },
        )
    missing_motif_group = tmp_path / "missing-motif-group.html"
    missing_motif_group.write_text(
        scientific.replace(' data-evidence-group="nearby-motifs"', "", 1),
        encoding="utf-8",
    )
    with pytest.raises(ReportRenderError, match="lacks Editing rate"):
        validation.validate_rendered_html(
            missing_motif_group,
            expected_banner=context.render_metadata["state_banner"],
            expected_identity={
                "data-report-view": "scientific",
                "data-run-id": context.summary["run_id"],
                "data-selected-candidate-count": "1",
            },
            expected_candidate_ids=("candidate_1",),
        )


def test_report_displays_print_first_selected_candidate_evidence(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    assert context.computational_unavailable_reason is None
    assert context.computational_results is not None
    assert context.computational_results.analysis_id == "synthetic_analysis"
    assert context.computational_results.sample_ids == (
        "SYNTH_A",
        "SYNTH_T1",
        "SYNTH_C2",
        "SYNTH_T2",
    )
    assert tuple(
        (
            pair.replicate,
            pair.control_sample_id,
            pair.treatment_sample_id,
        )
        for pair in context.computational_results.sample_manifest.pairs
    ) == (
        ("R1", "SYNTH_A", "SYNTH_T1"),
        ("R2", "SYNTH_C2", "SYNTH_T2"),
    )
    manifest_index = context.input_snapshot_labels.index("Step 09 sample manifest")
    assert context.input_snapshots[manifest_index] == (
        context.computational_results.sample_manifest.snapshot
    )
    assert context.scientific_context_results is not None
    assert context.input_snapshot_labels[-1] == (
        "scientific-context receipt-bound input 'motif_catalog'"
    )
    reference_recheck = next(
        recheck
        for recheck in context.input_rechecks
        if recheck[1] == "scientific-context receipt-bound input 'reference_fasta'"
    )
    assert reference_recheck[2] is False
    assert context.computational_results.all_sites.row_count == 4
    assert context.computational_results.significant_sites.row_count == 1
    assert context.computational_results.mutation_spectrum.row_count == 12
    assert context.computational_results.mutation_spectrum.displayed_row_count == 12
    assert context.computational_results.mutation_spectrum.truncated is False
    assert tuple(
        row[
            context.computational_results.mutation_spectrum.header.index(
                "mutation_type"
            )
        ]
        for row in context.computational_results.mutation_spectrum.display_rows
    ) == (
        "A>C",
        "A>G",
        "A>T",
        "C>A",
        "C>G",
        "C>T",
        "G>A",
        "G>C",
        "G>T",
        "T>A",
        "T>C",
        "T>G",
    )
    landscape = context.scientific_figures[0]
    assert "zero mean-depth threshold" in landscape.caption
    assert "cannot be represented on the logarithmic axis" in landscape.alt_text
    assert "zero mean_dp_threshold is outside the log axis" in landscape.mapping
    publish(context)
    content = context.output_scientific_html.read_text(encoding="utf-8")
    assert '<div id="scientific-category" ' in content
    assert "<details" not in content
    assert "COMPUTATIONAL RESULTS — NOT SCIENTIFICALLY ADJUDICATED." in content
    assert 'id="computational_significant_sites"' not in content
    assert 'id="computational_all_sites"' not in content
    assert 'id="selected-candidate-index"' in content
    assert 'class="candidate-index-list"' in content
    assert 'class="candidate-index-record"' in content
    assert '<table class="emrys-table candidate-index"' not in content
    assert '<th scope="col">Editing rate</th>' not in content
    assert 'id="candidate-evidence-1"' in content
    assert "candidate_1" in content
    assert "control mean" in content
    assert "11.00% (AF 0.11)" in content
    assert "treatment mean" in content
    assert "31.00% (AF 0.31)" in content
    assert "1:10" in content
    assert "GENE1" in content
    assert "PUM_UGUANA" in content
    assert "RNA UGUANA" in content
    assert "DNA TGTANA" in content
    assert "registered radius ±100 nt" in content
    assert "hits outside that panel remain listed here" in content
    assert "Admitted orientation policy" in content
    assert "Context orientation action" in content
    assert "Recorded transcripts (no isoform selected)" in content
    assert "AD 10 / DP 100" in content
    assert 'class="candidate-pair-batch"' in content
    assert "Manifest-paired sample evidence — candidate_1" in content
    assert "candidate_1 (continued)" not in content
    assert "not validated RNA-editing sites" in content
    evidence_view = view.build_evidence_view(
        context.summary,
        context.render_metadata,
        scientific_figures=context.scientific_figures,
        computational_results=context.computational_results,
        computational_unavailable_reason=context.computational_unavailable_reason,
        scientific_context_results=context.scientific_context_results,
        scientific_context_unavailable_reason=(
            context.scientific_context_unavailable_reason
        ),
    )
    assert tuple(category["id"] for category in evidence_view["categories"]) == (
        "overview-category",
        "evidence-category",
        "operations-category",
    )
    evidence_sections = tuple(
        section["id"] for section in evidence_view["categories"][1]["sections"]
    )
    operations_sections = tuple(
        section["id"] for section in evidence_view["categories"][2]["sections"]
    )
    assert evidence_sections == (
        "step09-sources-section",
        "qc-metrics-section",
        "artifact-appendix-section",
        "tools-issues-section",
        "report-provenance-section",
    )
    assert operations_sections == ("attempt-lineage-section",)
    source_section = next(
        section
        for category in evidence_view["categories"]
        for section in category["sections"]
        if section["id"] == "step09-sources-section"
    )
    source_table = source_section["blocks"][0]
    assert source_table["header"] == (
        "Role",
        "Artifact ID",
        "Source path",
        "SHA-256",
        "Bytes",
        "Rows",
    )
    assert tuple(row[0] for row in source_table["rows"]) == (
        "validation",
        "all_sites",
        "significant_sites",
        "summary",
        "mutation_spectrum",
        "sample_manifest",
    )
    context_source_table = source_section["blocks"][1]
    assert context_source_table["id"] == "step10-source-records"
    assert tuple(row[0] for row in context_source_table["rows"][:6]) == (
        "validation",
        "candidate_context",
        "motif_hits",
        "sequence_logo",
        "motif_statistics",
        "receipt",
    )
    assert tuple(row[0] for row in context_source_table["rows"][6:]) == (
        "step09_all_sites",
        "step09_significant_sites",
        "step09_summary",
        "reference_fasta",
        "reference_fai",
        "motif_catalog",
    )
    assert source_section["blocks"][2]["id"] == "step10-policy-record"


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("stale_bytes", "sample manifest SHA-256 mismatch"),
        ("run_contract", "differs from the immutable run contract"),
        ("sample_order", "order differs from the admitted result-table"),
        ("invalid_pairing", "pairing failed validation"),
    ),
)
def test_sample_manifest_admission_fails_closed(
    computational_summary: Path,
    tmp_path: Path,
    case: str,
    expected: str,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports")
    )
    assert context.computational_results is not None
    results = context.computational_results
    source = results.sample_manifest.path
    with source.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    if case == "sample_order":
        rows[0], rows[1] = rows[1], rows[0]
    elif case == "invalid_pairing":
        rows[-1]["replicate"] = "R1"
    manifest = tmp_path / f"{case}-samples.tsv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=header,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    recorded_hash = "0" * 64 if case == "stale_bytes" else digest
    run_contract_hash = "f" * 64 if case == "run_contract" else recorded_hash
    summary_row = list(results.summary.display_rows[0])
    summary_row[results.summary.header.index("sample_manifest_path")] = str(manifest)
    summary_row[results.summary.header.index("sample_manifest_sha256")] = recorded_hash
    summary_table = replace(results.summary, display_rows=(tuple(summary_row),))
    summary_document = {
        **context.summary,
        "run_contract": {
            **context.summary["run_contract"],
            "sample_manifest_sha256": run_contract_hash,
        },
    }

    with pytest.raises(ReportRenderError, match=expected):
        report_computational._admit_sample_manifest(
            summary_document,
            summary_table,
            results.sample_ids,
            source_root=tmp_path,
        )


@pytest.mark.parametrize(
    "artifact_id",
    (
        "analysis.synthetic.cmh_all_sites",
        "analysis.synthetic.mutation_spectrum_tsv",
    ),
)
def test_incomplete_step09_trio_is_disclosed_without_opening_candidate_rows(
    tmp_path: Path,
    artifact_id: str,
) -> None:
    fixture = FIXTURE.build_missing_fixture(
        tmp_path / "fixture",
        artifact_id=artifact_id,
    )
    summary = publish_run_summary(fixture)
    context = REPORT.prepare_report(
        arguments(summary, tmp_path / "reports", execute=True)
    )
    assert context.computational_results is None
    assert context.computational_unavailable_reason is not None
    assert "not complete" in context.computational_unavailable_reason
    publish(context)
    scientific = context.output_scientific_html.read_text(encoding="utf-8")
    evidence = context.output_evidence_html.read_text(encoding="utf-8")
    assert "no computational candidate rows were opened or displayed" in scientific
    assert 'id="computational_all_sites"' not in scientific
    assert "no computational candidate rows were opened or displayed" in evidence
    assert 'id="step09-source-records"' not in evidence
    if artifact_id.endswith("cmh_all_sites"):
        assert 'aria-label="Result files"' not in scientific
        assert 'aria-label="Result files"' not in evidence
    else:
        for content in (scientific, evidence):
            assert 'aria-label="Result files"' in content
            assert "Candidate context" in content
            assert "Threshold-passing candidates" not in content
            assert "Complete candidate table" not in content


def test_report_delegates_mutation_spectrum_reconciliation_to_step09(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    def mutate_sources(paths: dict[str, Path]) -> None:
        def corrupt(_header: tuple[str, ...], rows: list[dict[str, str]]) -> None:
            rows[0]["candidate_count"] = "999"

        rewrite_tsv(paths["step09_mutation_spectrum_tsv_v1"], corrupt)

    copied, _paths = copied_step09_summary(
        computational_summary,
        tmp_path / "input",
        mutate_sources=mutate_sources,
    )
    with pytest.raises(
        ReportRenderError,
        match="Primary Step 09 projection failed validation",
    ):
        REPORT.prepare_report(arguments(copied, tmp_path / "reports"))


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("sha256", "0" * 64, "SHA-256 mismatch"),
        ("size_bytes", 1, "size mismatch"),
        ("row_count", 99, "row-count mismatch"),
    ),
)
def test_step09_source_identity_mismatches_fail_closed(
    computational_summary: Path,
    tmp_path: Path,
    field: str,
    replacement: Any,
    message: str,
) -> None:
    def mutate_document(
        _document: dict[str, Any],
        records: dict[str, dict[str, Any]],
    ) -> None:
        record = records["step09_cmh_all_sites_v1"]
        record["source"][field] = replacement
        if field == "row_count":
            for metric in record["metrics"]:
                if metric["metric_id"] == "source_row_count":
                    metric["value"] = replacement

    copied, _paths = copied_step09_summary(
        computational_summary,
        tmp_path / "input",
        mutate_document=mutate_document,
    )
    with pytest.raises(ReportRenderError, match=message):
        REPORT.prepare_report(arguments(copied, tmp_path / "reports"))


def test_report_translates_canonical_step09_projection_rejection(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    def mutate_sources(paths: dict[str, Path]) -> None:
        def duplicate(_header: tuple[str, ...], rows: list[dict[str, str]]) -> None:
            rows[1]["candidate_id"] = rows[0]["candidate_id"]

        rewrite_tsv(paths["step09_cmh_all_sites_v1"], duplicate)

    copied, _paths = copied_step09_summary(
        computational_summary,
        tmp_path / "input",
        mutate_sources=mutate_sources,
    )
    with pytest.raises(
        ReportRenderError,
        match="Primary Step 09 projection failed validation",
    ):
        REPORT.prepare_report(arguments(copied, tmp_path / "reports"))


@pytest.mark.parametrize(
    ("corruption", "message"),
    (
        ("missing_row", "must contain exactly 7 check rows"),
        ("wrong_step_scope", "wrong step/scope"),
        ("ordered_check_swap", "wrong ordered check roster"),
        ("non_pass", "owner-validation report is not all-pass"),
    ),
)
def test_step09_owner_validation_must_be_exact_all_pass_before_rows_open(
    computational_summary: Path,
    tmp_path: Path,
    corruption: str,
    message: str,
) -> None:
    def mutate_sources(paths: dict[str, Path]) -> None:
        def corrupt_report(
            _header: tuple[str, ...], rows: list[dict[str, str]]
        ) -> None:
            if corruption == "missing_row":
                rows.pop()
            elif corruption == "wrong_step_scope":
                rows[0]["step_id"] = "08"
                rows[0]["scope_id"] = "wrong-analysis"
            elif corruption == "ordered_check_swap":
                rows[0]["check_id"], rows[1]["check_id"] = (
                    rows[1]["check_id"],
                    rows[0]["check_id"],
                )
            else:
                rows[0]["status"] = "fail"

        rewrite_tsv(paths["step09_validation_report_v1"], corrupt_report)

    copied, _paths = copied_step09_summary(
        computational_summary,
        tmp_path / "input",
        mutate_sources=mutate_sources,
    )
    with pytest.raises(ReportRenderError, match=message):
        REPORT.prepare_report(arguments(copied, tmp_path / "reports"))


@pytest.mark.parametrize(
    "adapter",
    ("step09_cmh_all_sites_v1", "step09_mutation_spectrum_tsv_v1"),
)
def test_step09_input_mutation_aborts_before_publication(
    computational_summary: Path,
    tmp_path: Path,
    adapter: str,
) -> None:
    copied, paths = copied_step09_summary(computational_summary, tmp_path / "input")
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    paths[adapter].write_bytes(paths[adapter].read_bytes() + b" ")
    with pytest.raises(ReportRenderError, match="changed during report"):
        publish(context)
    assert not any(path.exists() for path in output_paths(context))
    assert not context.lock_path.exists()


def test_step10_reference_identity_mutation_aborts_before_publication(
    tmp_path: Path,
) -> None:
    summary = publish_run_summary(FIXTURE.build_fixture(tmp_path / "fixture"))
    context = REPORT.prepare_report(
        arguments(summary, tmp_path / "reports", execute=True)
    )
    assert context.scientific_context_results is not None
    reference = next(
        source
        for source in context.scientific_context_results.bound_inputs
        if source.role == "reference_fasta"
    )
    payload = bytearray(reference.path.read_bytes())
    index = payload.index(ord("A"))
    payload[index] = ord("C")
    reference.path.write_bytes(payload)

    with pytest.raises(ReportRenderError, match="changed during report"):
        publish(context)
    assert not any(path.exists() for path in output_paths(context))
    assert not context.lock_path.exists()


def test_native_candidate_tables_are_not_rendered_as_truncated_wide_tables(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    def expand_sources(paths: dict[str, Path]) -> None:
        def expand_all(_header: tuple[str, ...], rows: list[dict[str, str]]) -> None:
            significant = dict(rows[0])
            nonsignificant = dict(rows[1])
            rows[:] = [significant]
            for index in range(1, 251):
                row = dict(nonsignificant)
                row["candidate_id"] = f"expanded_candidate_{index:03d}"
                rows.append(row)

        def update_summary(
            _header: tuple[str, ...], rows: list[dict[str, str]]
        ) -> None:
            rows[0].update(
                {
                    "candidate_count": "251",
                    "target_candidate_count": "251",
                    "successfully_tested_count": "251",
                    "effect_not_met_count": "250",
                }
            )

        def update_mutation_spectrum(
            _header: tuple[str, ...], rows: list[dict[str, str]]
        ) -> None:
            target = next(row for row in rows if row["mutation_type"] == "A>G")
            target.update(
                {
                    "candidate_count": "251",
                    "candidate_fraction": "1",
                    "successfully_tested_count": "251",
                    "significant_up_count": "1",
                    "significant_down_count": "0",
                }
            )

        rewrite_tsv(paths["step09_cmh_all_sites_v1"], expand_all)
        rewrite_tsv(paths["step09_cmh_summary_v1"], update_summary)
        rewrite_tsv(
            paths["step09_mutation_spectrum_tsv_v1"],
            update_mutation_spectrum,
        )

    copied, _paths = copied_step09_summary(
        computational_summary,
        tmp_path / "input",
        mutate_sources=expand_sources,
    )
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    assert context.computational_results is not None
    all_sites = context.computational_results.all_sites
    assert all_sites.row_count == 251
    assert all_sites.display_row_limit == 0
    assert all_sites.displayed_row_count == 0
    publish(context)
    document = receipt_document(context.output_receipt)
    assert document["truncations"] == []
    scientific = context.output_scientific_html.read_text(encoding="utf-8")
    assert "Displayed the first 250 of 251 rows" not in scientific
    assert 'id="computational_all_sites"' not in scientific
    assert 'id="computational_significant_sites"' not in scientific
    assert "Successfully tested" in scientific
    assert "251" in scientific


def test_explicit_input_and_canonical_name_are_required(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    wrong = tmp_path / "wrong.json"
    wrong.write_bytes(computational_summary.read_bytes())
    with pytest.raises(ReportRenderError, match="Canonical run-summary"):
        REPORT.prepare_report(arguments(wrong, tmp_path / "reports"))
    with pytest.raises(ReportRenderError, match="Could not inspect"):
        REPORT.prepare_report(
            arguments(tmp_path / "missing.json", tmp_path / "reports")
        )


def test_report_rejects_a_non_directory_output_root(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "not-a-directory"
    output_root.write_text("occupied\n", encoding="utf-8")

    with pytest.raises(ReportRenderError, match="non-symlink directory"):
        REPORT.prepare_report(arguments(computational_summary, output_root))


@pytest.mark.parametrize("suffix", ("run_report.html", "run_report.pdf"))
def test_retired_single_report_predecessors_require_fresh_output_root(
    computational_summary: Path,
    tmp_path: Path,
    suffix: str,
) -> None:
    run_id = json.loads(computational_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    (output_dir / f"{run_id}.{suffix}").write_text("retired", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="fresh output root"):
        REPORT.prepare_report(arguments(computational_summary, output_root))


def test_bare_v4_output_requires_fresh_output_root(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(computational_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    (output_dir / f"{run_id}.scientific_report.html").write_text(
        "bare",
        encoding="utf-8",
    )
    with pytest.raises(ReportRenderError, match="fresh output root"):
        REPORT.prepare_report(arguments(computational_summary, output_root))


def test_v3_receipt_requires_fresh_output_root(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(computational_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    v3 = json.loads(
        (
            REPO_ROOT / "tests/contracts/artifacts/fixtures/report_receipt_v3.json"
        ).read_text(encoding="utf-8")
    )
    (output_dir / f"{run_id}.report_outputs.tsv").write_bytes(
        receipt.receipt_tsv_bytes(v3)
    )
    with pytest.raises(ReportRenderError, match="active v4 contract"):
        REPORT.prepare_report(arguments(computational_summary, output_root))


def test_lock_collision_is_rejected_without_mutation(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(computational_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    lock = output_dir / f".{run_id}.report.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="lock already exists"):
        REPORT.prepare_report(arguments(computational_summary, output_root))
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_input_mutation_aborts_and_removes_owned_state(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    copied = write_summary_copy(computational_summary, tmp_path / "input")
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    copied.write_bytes(copied.read_bytes() + b" ")
    with pytest.raises(ReportRenderError, match="changed during report"):
        publish(context)
    assert not any(path.exists() for path in output_paths(context))
    assert not context.lock_path.exists()


def test_interrupted_lock_acquisition_cleans_owned_lock(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    base = REPORT.default_publication_ops()

    def interrupt(_descriptor: int, _payload: bytes) -> int:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        publish(context, replace(base, lock_write=interrupt))
    assert not context.lock_path.exists()
    assert not any(path.exists() for path in output_paths(context))


def test_post_backup_failure_rolls_back_exact_predecessor(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    args = arguments(computational_summary, tmp_path / "reports", execute=True)
    first = REPORT.prepare_report(args)
    publish(first)
    before = {path: path.read_bytes() for path in output_paths(first)}
    context = REPORT.prepare_report(args)
    base = REPORT.default_publication_ops()

    def fail_summary_link(source: Path, target: Path) -> None:
        if (
            target == context.output_summary_tsv
            and ".run-report." in source.parent.name
        ):
            raise OSError("synthetic post-backup failure")
        base.link(source, target)

    with pytest.raises(ReportRenderError, match="synthetic post-backup failure"):
        publish(context, replace(base, link=fail_summary_link))
    assert {path: path.read_bytes() for path in output_paths(context)} == before
    assert not context.lock_path.exists()
    assert not list(context.output_dir.glob("*.previous"))


def test_foreign_final_and_backup_are_preserved(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    empty_context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "foreign-final", execute=True)
    )
    empty_context.output_dir.mkdir(parents=True)
    empty_context.output_scientific_html.write_text(
        "foreign final\n",
        encoding="utf-8",
    )
    with pytest.raises(ReportRenderError, match="appeared after preflight"):
        publish(empty_context)
    assert (
        empty_context.output_scientific_html.read_text(encoding="utf-8")
        == "foreign final\n"
    )

    args = arguments(computational_summary, tmp_path / "foreign-backup", execute=True)
    initial = REPORT.prepare_report(args)
    publish(initial)
    context = REPORT.prepare_report(args)
    token = "fixed-foreign-token"
    backup = (
        context.output_dir / f".{context.output_scientific_html.name}.{token}.previous"
    )
    backup.write_text("foreign backup\n", encoding="utf-8")
    ops = replace(REPORT.default_publication_ops(), make_token=lambda: token)
    with pytest.raises(ReportRenderError, match="backup path unexpectedly exists"):
        publish(context, ops)
    assert backup.read_text(encoding="utf-8") == "foreign backup\n"
    assert all(path.is_file() for path in output_paths(context))


def test_incomplete_rollback_preserves_lock_stage_and_recovery(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    args = arguments(computational_summary, tmp_path / "reports", execute=True)
    initial = REPORT.prepare_report(args)
    publish(initial)
    context = REPORT.prepare_report(args)
    base = REPORT.default_publication_ops()

    def fail_publication_and_restore(source: Path, target: Path) -> None:
        if (
            ".run-report." in source.parent.name
            and target == context.output_scientific_html
        ):
            raise OSError("synthetic publication failure")
        if source.name.endswith(".previous"):
            raise OSError("synthetic rollback failure")
        base.link(source, target)

    with pytest.raises(ReportRenderError, match="rollback was incomplete"):
        publish(context, replace(base, link=fail_publication_and_restore))
    assert context.lock_path.exists()
    assert list(context.output_dir.glob("*.RECOVERY.txt"))
    assert list(context.output_dir.glob(".run-report.*.tmp"))


def test_post_commit_cleanup_failure_keeps_committed_outputs_and_evidence(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    base = REPORT.default_publication_ops()

    def fail_cleanup(
        _path: Path, _token: str, _identity: tuple[int, int] | None
    ) -> None:
        raise OSError("synthetic cleanup failure")

    with pytest.raises(ReportRenderError, match="cleanup failed"):
        publish(context, replace(base, remove_owned_stage=fail_cleanup))
    assert all(path.is_file() for path in output_paths(context))
    assert context.lock_path.exists()
    assert list(context.output_dir.glob("*.RECOVERY.txt"))


def test_final_byte_corruption_never_commits_a_false_receipt(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    base = REPORT.default_publication_ops()
    corrupted = False

    def corrupt_summary(path: Path) -> None:
        nonlocal corrupted
        if path == context.output_summary_tsv and not corrupted:
            payload = path.read_bytes()
            old = context.summary["run_id"].encode("utf-8")
            replacement = (b"X" if old[:1] != b"X" else b"Y") + old[1:]
            path.write_bytes(payload.replace(old, replacement, 1))
            corrupted = True
        base.fsync_file(path)

    with pytest.raises(ReportRenderError, match="rollback was incomplete"):
        publish(context, replace(base, fsync_file=corrupt_summary))
    assert not context.output_receipt.exists()
    assert context.lock_path.exists()
    assert list(context.output_dir.glob("*.RECOVERY.txt"))


def test_signal_restoration_failure_is_controlled_recovery(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    base = REPORT.default_publication_ops()

    def fail_restore(handlers: dict[int, Any]) -> None:
        base.restore_signal_handlers(handlers)
        raise OSError("synthetic signal restore failure")

    with pytest.raises(ReportRenderError, match="signal-handler restoration failed"):
        publish(context, replace(base, restore_signal_handlers=fail_restore))
    assert all(path.is_file() for path in output_paths(context))
    assert not context.lock_path.exists()
    assert list(context.output_dir.glob("*.RECOVERY.txt"))


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("run_id", "different-run"),
        ("kind", "bogus"),
        ("sha256", "0" * 64),
        ("self_contained", "false"),
    ),
)
def test_receipt_rows_must_match_canonical_json(
    computational_summary: Path,
    tmp_path: Path,
    column: str,
    replacement: str,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / column, execute=True)
    )
    publish(context)
    with context.output_receipt.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    rows[0][column] = replacement
    with context.output_receipt.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ReportRenderError, match="TSV columns differ"):
        receipt.read_receipt_tsv(context.output_receipt)


def test_summary_and_receipt_serializers_are_deterministic(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports")
    )
    assert receipt.summary_tsv_bytes(context) == receipt.summary_tsv_bytes(context)
    stage = tmp_path / "stage"
    stage.mkdir()
    scientific_html = stage / context.output_scientific_html.name
    evidence_html = stage / context.output_evidence_html.name
    summary = stage / context.output_summary_tsv.name
    scientific_html.write_bytes(context.scientific_html_bytes)
    evidence_html.write_bytes(context.evidence_html_bytes)
    summary.write_bytes(receipt.summary_tsv_bytes(context))
    document = receipt.receipt_document(
        context,
        (
            (
                "scientific-report-html",
                "scientific_html",
                scientific_html,
                context.output_scientific_html,
            ),
            (
                "evidence-report-html",
                "evidence_html",
                evidence_html,
                context.output_evidence_html,
            ),
            ("run-summary-tsv", "run_summary_tsv", summary, context.output_summary_tsv),
        ),
    )
    assert receipt.receipt_tsv_bytes(document) == receipt.receipt_tsv_bytes(
        json.loads(json.dumps(document))
    )
