"""Focused contract and real-render tests for report-exports-v1."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "render_run_report.py"
HTML_CORE_RUNNER = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "report_html_v1"
    / "run_html_core.py"
)
BUNDLE_SCRIPT = REPO_ROOT / "scripts" / "render_run_report_bundle.py"
FIXTURE_BUILDER = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "artifact_run_summary_v1"
    / "build_fixture.py"
)
RUN_SUMMARY_SCRIPT = REPO_ROOT / "scripts" / "build_run_summary.py"
FIXED_EPOCH = "1700000000"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FIXTURE = load_module("norad_report_exports_fixture", FIXTURE_BUILDER)
BUNDLE = load_module("norad_report_exports_bundle", BUNDLE_SCRIPT)


def publish_summary(fixture: Any) -> Path:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    result = subprocess.run(
        [
            sys.executable,
            str(RUN_SUMMARY_SCRIPT),
            *fixture.command_args(execute=True),
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return fixture.summary_json_path


@pytest.fixture(scope="module")
def incomplete_summary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    fixture = FIXTURE.build_fixture(
        tmp_path_factory.mktemp("report-exports") / "fixture"
    )
    return publish_summary(fixture)


@pytest.fixture(scope="module")
def exploratory_approved_summary(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path_factory.mktemp("report-exports-exploratory") / "fixture",
        science_status="science_review_complete_exploratory",
        roles=("candidate_selection",),
        display_limits={"candidate_selection": 1},
    )
    return publish_summary(fixture)


def fake_quarto(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "quarto"
    path.write_text(
        f"""#!{sys.executable}
import sys
if sys.argv[1:] == ["--version"]:
    print("1.9.38")
    raise SystemExit(0)
if sys.argv[1:] == ["pandoc", "--version"]:
    print("pandoc 3.8.3")
    raise SystemExit(0)
raise SystemExit(97)
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def arguments(
    summary: Path,
    output_root: Path,
    quarto: Path,
    *,
    formats: str = "all",
    execute: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_summary=summary,
        output_root=output_root,
        quarto_bin=quarto,
        formats=formats,
        execute=execute,
    )


def test_default_format_is_all() -> None:
    parsed = BUNDLE.parse_arguments(
        [
            "--run-summary",
            "/explicit/run/run.run_summary.json",
            "--output-root",
            "/explicit/reports",
            "--quarto-bin",
            "/explicit/quarto",
        ]
    )
    assert parsed.formats == "all"


@pytest.mark.parametrize(
    ("formats", "requested"),
    [
        ("html", ("html",)),
        ("pdf", ("pdf",)),
        ("all", ("html", "pdf")),
    ],
)
def test_prepare_context_maps_formats_and_is_side_effect_free(
    incomplete_summary: Path,
    tmp_path: Path,
    formats: str,
    requested: tuple[str, ...],
) -> None:
    output_root = tmp_path / formats / "reports"
    context = BUNDLE.prepare_context(
        arguments(
            incomplete_summary,
            output_root,
            fake_quarto(tmp_path / formats / "fake"),
            formats=formats,
        )
    )
    assert context.requested_formats == requested
    assert not output_root.exists()


def test_summary_tsv_projection_is_deterministic_and_scope_complete(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = BUNDLE.prepare_context(
        arguments(
            incomplete_summary,
            tmp_path / "reports",
            fake_quarto(tmp_path / "fake"),
        )
    )
    first = BUNDLE._summary_tsv_bytes(context)
    second = BUNDLE._summary_tsv_bytes(context)
    rows = list(csv.reader(first.decode("utf-8").splitlines(), delimiter="\t"))
    assert first == second
    assert tuple(rows[0]) == BUNDLE.SUMMARY_HEADER
    assert len(rows) - 1 == len(context.html.summary["expected_scopes"])
    assert all(row[0] == context.html.summary["run_id"] for row in rows[1:])


def test_pdf_source_has_exact_banner_order_and_no_analysis_code(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = BUNDLE.prepare_context(
        arguments(
            incomplete_summary,
            tmp_path / "reports",
            fake_quarto(tmp_path / "fake"),
        )
    )
    source = BUNDLE._pdf_body(context).decode("utf-8")
    banner = BUNDLE.html_report.SCIENCE_BANNERS["evidence_incomplete"]
    assert banner in source
    positions = [source.index(marker) for marker in BUNDLE.PDF_SECTION_MARKERS]
    assert positions == sorted(positions)
    assert "CMH-ranked candidates" in source
    assert "step_09_cmh_editing_site_calling" not in source
    assert "Rscript" not in source


def test_partial_existing_bundle_is_rejected(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(incomplete_summary.read_text(encoding="utf-8"))["run_id"]
    output_dir = tmp_path / "reports" / run_id
    output_dir.mkdir(parents=True)
    (output_dir / f"{run_id}.run_summary.tsv").write_text(
        "partial\n",
        encoding="utf-8",
    )
    with pytest.raises(BUNDLE.html_report.ReportRenderError, match="incomplete"):
        BUNDLE.prepare_context(
            arguments(
                incomplete_summary,
                tmp_path / "reports",
                fake_quarto(tmp_path / "fake"),
            )
        )


def test_receipt_projection_round_trips_valid_schema(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = BUNDLE.prepare_context(
        arguments(
            incomplete_summary,
            tmp_path / "reports",
            fake_quarto(tmp_path / "fake"),
            formats="html",
        )
    )
    stage = tmp_path / "stage"
    stage.mkdir()
    staged_html = stage / context.html.output_html.name
    staged_html.write_text("<!doctype html><html></html>\n", encoding="utf-8")
    staged_tsv = stage / context.output_summary_tsv.name
    staged_tsv.write_bytes(BUNDLE._summary_tsv_bytes(context))
    document = BUNDLE._receipt_document(
        context,
        (
            ("run-report-html", "html", staged_html, context.html.output_html, None),
            (
                "run-summary-tsv",
                "run_summary_tsv",
                staged_tsv,
                context.output_summary_tsv,
                None,
            ),
        ),
    )
    receipt = stage / context.output_receipt.name
    receipt.write_bytes(BUNDLE._receipt_tsv_bytes(document))
    assert BUNDLE._read_receipt_tsv(receipt) == document
    assert document["analysis_execution_performed"] is False
    assert document["validation_claimed"] is False


def _real_quarto() -> Path:
    value = os.environ.get("QUARTO_BIN")
    if not value:
        pytest.skip("Set QUARTO_BIN for real report-export validation")
    path = Path(value).resolve()
    if not path.is_file():
        pytest.skip(f"QUARTO_BIN is unavailable: {path}")
    return path


@pytest.mark.skipif(
    os.environ.get("NORAD_REQUIRE_QUARTO") != "1",
    reason="set NORAD_REQUIRE_QUARTO=1 for real HTML/PDF export validation",
)
def test_real_all_bundle_is_valid_receipt_last_and_deterministic(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto = _real_quarto()
    output_root = tmp_path / "reports"
    command = [
        sys.executable,
        str(SCRIPT),
        "--run-summary",
        str(incomplete_summary),
        "--output-root",
        str(output_root),
        "--quarto-bin",
        str(quarto),
        "--formats",
        "all",
        "--execute",
    ]
    legacy_command = [
        sys.executable,
        str(HTML_CORE_RUNNER),
        "--run-summary",
        str(incomplete_summary),
        "--output-root",
        str(output_root),
        "--quarto-bin",
        str(quarto),
        "--formats",
        "html",
        "--execute",
    ]
    legacy = subprocess.run(
        legacy_command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert legacy.returncode == 0, legacy.stdout + legacy.stderr
    run_id = json.loads(incomplete_summary.read_text(encoding="utf-8"))["run_id"]
    output_dir = output_root / run_id
    legacy_html = output_dir / f"{run_id}.run_report.html"
    assert legacy_html.is_file()
    assert not (output_dir / f"{run_id}.report_outputs.tsv").exists()

    first = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    paths = {
        "html": output_dir / f"{run_id}.run_report.html",
        "pdf": output_dir / f"{run_id}.run_report.pdf",
        "summary": output_dir / f"{run_id}.run_summary.tsv",
        "receipt": output_dir / f"{run_id}.report_outputs.tsv",
    }
    assert all(path.is_file() for path in paths.values())
    before = {name: path.read_bytes() for name, path in paths.items()}
    document = BUNDLE._read_receipt_tsv(paths["receipt"])
    assert document["requested_formats"] == ["html", "pdf"]
    assert [item["kind"] for item in document["outputs"]] == [
        "html",
        "pdf",
        "run_summary_tsv",
    ]
    reader = PdfReader(paths["pdf"], strict=True)
    banner = BUNDLE.html_report.SCIENCE_BANNERS["evidence_incomplete"]
    assert reader.pages
    assert all(
        " ".join(banner.split()) in " ".join((page.extract_text() or "").split())
        for page in reader.pages
    )

    second = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert before == {name: path.read_bytes() for name, path in paths.items()}


@pytest.mark.skipif(
    os.environ.get("NORAD_REQUIRE_QUARTO") != "1",
    reason="set NORAD_REQUIRE_QUARTO=1 for validation-report propagation",
)
@pytest.mark.parametrize(
    ("artifact_id", "step_id", "scope_label"),
    [
        ("ref.star_index.validation", "00a", "reference novogene_ref"),
        ("ref.bed12.validation", "00b", "reference novogene_ref"),
        ("ref.sidecars.validation", "00c", "reference novogene_ref"),
        ("sample.SYNTH_A.star_validation", "01", "sample SYNTH_A"),
        ("sample.SYNTH_A.canonical_validation", "02", "sample SYNTH_A"),
        ("sample.SYNTH_A.bam_qc_validation", "02b", "sample SYNTH_A"),
        ("sample.SYNTH_A.strand_validation", "03", "sample SYNTH_A"),
        ("sample.SYNTH_A.markdup_validation", "04", "sample SYNTH_A"),
        ("sample.SYNTH_A.split_validation", "05", "sample SYNTH_A"),
        ("sample.SYNTH_A.orientation_validation", "06", "sample SYNTH_A"),
        ("cohort.synthetic.p1.validation", "07", "cohort_partition synthetic_cohort__p1"),
    ],
)
def test_failed_validation_reaches_summary_html_and_pdf(
    tmp_path: Path,
    artifact_id: str,
    step_id: str,
    scope_label: str,
) -> None:
    adapter_fixture = FIXTURE.ADAPTER_FIXTURE.build_fixture(
        tmp_path / "adapter",
        run_id=f"step{step_id}_validation_run",
    )
    validation = adapter_fixture.source_for(artifact_id)
    validation.write_text(
        validation.read_text(encoding="utf-8").replace(
            "\tpass\tfixture\tfixture\tsynthetic passing validation",
            "\tfail\tmismatch\tfixture\tsynthetic failed validation",
            1,
        ),
        encoding="utf-8",
    )
    FIXTURE.publish_adapter_fixture(adapter_fixture)
    fixture = FIXTURE.RunSummaryFixture(
        root=tmp_path,
        run_id=adapter_fixture.run_id,
        artifact_receipt=adapter_fixture.receipt_path,
        output_root=adapter_fixture.output_root,
        adapter_fixture=adapter_fixture,
    )
    summary = publish_summary(fixture)
    document = json.loads(summary.read_text(encoding="utf-8"))
    validation_artifact = next(
        item
        for item in document["artifacts"]
        if item["artifact_id"] == artifact_id
    )
    assert validation_artifact["completion_status"] == "failed"

    output_root = tmp_path / "reports"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-summary",
            str(summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(_real_quarto()),
            "--formats",
            "all",
            "--execute",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report_dir = output_root / adapter_fixture.run_id
    html = (
        report_dir / f"{adapter_fixture.run_id}.run_report.html"
    ).read_text(encoding="utf-8")
    pdf = report_dir / f"{adapter_fixture.run_id}.run_report.pdf"
    pdf_text = " ".join(
        (page.extract_text() or "")
        for page in PdfReader(pdf, strict=True).pages
    )
    assert artifact_id in html
    assert "failed" in html
    assert f"{step_id} {scope_label} failed" in " ".join(pdf_text.split())


@pytest.mark.skipif(
    os.environ.get("NORAD_REQUIRE_QUARTO") != "1",
    reason="set NORAD_REQUIRE_QUARTO=1 for real rollback validation",
)
def test_bundle_failure_restores_valid_html_only_predecessor(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto = _real_quarto()
    output_root = tmp_path / "reports"
    legacy = subprocess.run(
        [
            sys.executable,
            str(HTML_CORE_RUNNER),
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--formats",
            "html",
            "--execute",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert legacy.returncode == 0, legacy.stdout + legacy.stderr
    context = BUNDLE.prepare_context(
        arguments(
            incomplete_summary,
            output_root,
            quarto,
            formats="all",
            execute=True,
        )
    )
    prior = context.html.output_html.read_bytes()
    original_link = BUNDLE.os.link

    def fail_summary_publication(
        source: str | os.PathLike[str],
        destination: str | os.PathLike[str],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if Path(destination) == context.output_summary_tsv:
            raise OSError("injected summary publication failure")
        original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(BUNDLE.os, "link", fail_summary_publication)
    with pytest.raises(
        BUNDLE.html_report.ReportRenderError,
        match="injected summary publication failure",
    ):
        BUNDLE.publish_bundle(context)
    assert context.html.output_html.read_bytes() == prior
    assert not context.output_pdf.exists()
    assert not context.output_summary_tsv.exists()
    assert not context.output_receipt.exists()
    assert not context.html.lock_path.exists()
    assert not list(context.html.output_dir.glob("*.previous"))


@pytest.mark.skipif(
    os.environ.get("NORAD_REQUIRE_QUARTO") != "1",
    reason="set NORAD_REQUIRE_QUARTO=1 for real exploratory PDF validation",
)
def test_real_pdf_only_preserves_exploratory_banner_and_truncation(
    exploratory_approved_summary: Path,
    tmp_path: Path,
) -> None:
    quarto = _real_quarto()
    output_root = tmp_path / "reports"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-summary",
            str(exploratory_approved_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--formats",
            "pdf",
            "--execute",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    run_id = json.loads(
        exploratory_approved_summary.read_text(encoding="utf-8")
    )["run_id"]
    output_dir = output_root / run_id
    pdf = output_dir / f"{run_id}.run_report.pdf"
    receipt = output_dir / f"{run_id}.report_outputs.tsv"
    summary_tsv = output_dir / f"{run_id}.run_summary.tsv"
    assert pdf.is_file() and receipt.is_file() and summary_tsv.is_file()
    assert not (output_dir / f"{run_id}.run_report.html").exists()
    document = BUNDLE._read_receipt_tsv(receipt)
    assert document["requested_formats"] == ["pdf"]
    assert [item["kind"] for item in document["outputs"]] == [
        "pdf",
        "run_summary_tsv",
    ]
    assert len(document["truncations"]) == 1
    truncation = document["truncations"][0]
    assert truncation["table_id"] == "synthetic_candidate_selection"
    assert truncation["report_section"] == "cmh-ranked-candidates"
    assert truncation["full_row_count"] > 1
    assert truncation["displayed_row_count"] == 1
    assert len(truncation["full_table_sha256"]) == 64
    banner = BUNDLE.html_report.SCIENCE_BANNERS[
        "science_review_complete_exploratory"
    ]
    reader = PdfReader(pdf, strict=True)
    texts = [page.extract_text() or "" for page in reader.pages]
    assert all(
        " ".join(banner.split()) in " ".join(text.split()) for text in texts
    )
    assert "CMH-ranked candidates" in "\n".join(texts)
