"""Behavior, security, receipt, and recovery tests for two-view reporting."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from importlib.resources import files
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jinja2 import StrictUndefined, UndefinedError

from norad.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    controlled_python_argv,
)
from norad.reporting import report as REPORT
from norad.reporting._run_report import context as report_context
from norad.reporting._run_report import publication, receipt, validation, view
from norad.reporting._run_report.models import JINJA_VERSION, ReportRenderError
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"


def publish_run_summary(fixture: Any) -> Path:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    result = subprocess.run(
        [
            *controlled_python_argv(sys.executable, "-m", "norad"),
            "build",
            "run-summary",
            *fixture.command_args(execute=True),
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
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


def publish(context: Any, ops: REPORT.ReportPublicationOps | None = None) -> None:
    publication.publish_report(context, ops or REPORT.default_publication_ops())


def test_grouped_help_exposes_only_direct_html_contract(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            *controlled_python_argv(sys.executable, "-m", "norad"),
            "build",
            "report",
            "--help",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    missing = subprocess.run(
        [
            *controlled_python_argv(sys.executable, "-m", "norad"),
            "build",
            "report",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage: norad build report" in result.stdout
    assert "--source-checkout" in result.stdout
    assert "--artifact-source-root" in result.stdout
    assert "--run-summary" in result.stdout
    assert "--output-root" in result.stdout
    assert "--execute" in result.stdout
    assert "--formats" not in result.stdout
    assert "--quarto-bin" not in result.stdout
    assert missing.returncode == 2
    assert "required" in missing.stderr


def test_source_checkout_is_admitted_before_report_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_checkout = tmp_path / "not-norad"
    invalid_checkout.mkdir()
    result = REPORT.build_from_args(
        argparse.Namespace(
            source_checkout=invalid_checkout,
            artifact_source_root=tmp_path,
            run_summary=tmp_path / "missing.json",
            output_root=tmp_path / "reports",
            execute=False,
        )
    )
    captured = capsys.readouterr()
    assert result == 1
    assert "Source checkout project metadata is unavailable" in captured.err
    assert "missing.json" not in captured.err


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
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "reports"
    result = REPORT.build_from_args(arguments(computational_summary, output_root))
    captured = capsys.readouterr()
    assert result == 0
    assert "Dry-run only" in captured.out
    assert not captured.err
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
    assert not (context.output_dir / f"{context.summary['run_id']}.run_report.html").exists()
    assert not (context.output_dir / f"{context.summary['run_id']}.run_report.pdf").exists()
    document = receipt_document(context.output_receipt)
    assert document["schema_version"] == "4.0.0"
    assert document["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_norad"
    )
    assert document["renderer"] == {"name": "Jinja2", "version": JINJA_VERSION}
    assert [item["kind"] for item in document["outputs"]] == [
        "scientific_html",
        "evidence_html",
        "run_summary_tsv",
    ]
    assert document["outputs"][0]["self_contained"] is True
    assert document["outputs"][1]["self_contained"] is True
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
        "producer": "norad.reporting.report",
        "producer_version": "4.0.0",
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
    assert content.count('<style id="norad-report-styles">') == 1


def test_template_rejects_additional_or_untrusted_safe_boundaries() -> None:
    source = (
        files("norad.reporting")
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
    banner = "COMPUTATIONAL RESULTS — BIOLOGICAL VALIDATION IS OUTSIDE NORAD."

    assert banner in scientific and banner in evidence
    assert 'data-report-view="scientific"' in scientific
    assert 'data-report-view="evidence"' in evidence
    assert "CMH-ranked candidates" in scientific
    assert "FWD_like" in scientific
    assert 'id="computational_significant_sites"' in scientific
    assert 'id="computational_all_sites"' in scientific
    assert "candidate_1" in scientific
    assert "Selected exact sample QC" in scientific
    assert "Attempt lineage" not in scientific
    assert "Artifact appendix" not in scientific
    assert "Tools and issues" not in scientific
    assert "Report provenance" not in scientific
    assert "<svg" not in scientific
    assert 'id="step09-source-records"' in evidence
    assert 'id="computational_significant_sites"' not in evidence
    assert 'id="computational_all_sites"' not in evidence
    assert "candidate_1" not in evidence
    assert "Attempt lineage" in evidence
    assert "Artifact appendix" in evidence
    assert "Report provenance" in evidence
    assert "<svg" in evidence
    assert context.computational_results is not None
    for table in context.computational_results.tables:
        assert str(table.path) not in scientific
        assert table.sha256 not in scientific
        assert str(table.path) in evidence
        assert table.sha256 in evidence
    for metadata_field in (
        "css_sha256",
        "run_summary_sha256",
        "template_sha256",
    ):
        assert context.render_metadata[metadata_field] not in scientific
        assert context.render_metadata[metadata_field] in evidence
    for content in (scientific, evidence):
        assert "biological strand" not in content
        assert "<script" not in content.lower()
        assert "http://" not in content and "https://" not in content

    validation.validate_rendered_html(
        context.output_scientific_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity={
            "data-report-view": "scientific",
            "data-run-id": context.summary["run_id"],
        },
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


def test_report_displays_exact_step09_results_and_key_qc(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(computational_summary, tmp_path / "reports", execute=True)
    )
    assert context.computational_unavailable_reason is None
    assert context.computational_results is not None
    assert context.computational_results.analysis_id == "synthetic_analysis"
    assert context.computational_results.sample_ids == ("SYNTH_A",)
    assert context.computational_results.all_sites.row_count == 4
    assert context.computational_results.significant_sites.row_count == 1
    publish(context)
    content = context.output_scientific_html.read_text(encoding="utf-8")
    assert (
        '<details id="scientific-category" '
        'class="report-category" name="norad-report-categories" open>'
    ) in content
    assert "COMPUTATIONAL RESULTS — NOT SCIENTIFICALLY ADJUDICATED." in content
    assert 'id="computational_significant_sites"' in content
    assert 'id="computational_all_sites"' in content
    assert "candidate_1" in content
    assert "DP__SYNTH_A" in content
    assert "Mapped reads" in content
    assert "0.97" in content
    assert "not validated RNA-editing sites" in content
    evidence_view = view.build_evidence_view(
        context.summary,
        context.render_metadata,
        computational_results=context.computational_results,
        computational_unavailable_reason=context.computational_unavailable_reason,
    )
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
    )


def test_incomplete_step09_trio_is_disclosed_without_opening_candidate_rows(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_missing_fixture(
        tmp_path / "fixture",
        artifact_id="analysis.synthetic.cmh_all_sites",
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


def test_step09_input_mutation_aborts_before_publication(
    computational_summary: Path,
    tmp_path: Path,
) -> None:
    copied, paths = copied_step09_summary(computational_summary, tmp_path / "input")
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    paths["step09_cmh_all_sites_v1"].write_bytes(
        paths["step09_cmh_all_sites_v1"].read_bytes() + b" "
    )
    with pytest.raises(ReportRenderError, match="changed during report"):
        publish(context)
    assert not any(path.exists() for path in output_paths(context))
    assert not context.lock_path.exists()


def test_computational_all_sites_limit_and_truncation_are_receipted(
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

        rewrite_tsv(paths["step09_cmh_all_sites_v1"], expand_all)
        rewrite_tsv(paths["step09_cmh_summary_v1"], update_summary)

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
    assert all_sites.displayed_row_count == 250
    assert all_sites.truncated is True
    publish(context)
    document = receipt_document(context.output_receipt)
    assert document["truncations"][0] == {
        "table_id": "computational_all_sites",
        "report_section": "computational-results-section",
        "full_table_path": str(all_sites.path),
        "full_table_sha256": all_sites.sha256,
        "full_row_count": 251,
        "displayed_row_count": 250,
    }
    assert "Displayed the first 250 of 251 rows" in (
        context.output_scientific_html.read_text(encoding="utf-8")
    )


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
            REPO_ROOT
            / "tests/contracts/artifacts/fixtures/report_receipt_v3.json"
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
        context.output_dir
        / f".{context.output_scientific_html.name}.{token}.previous"
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
