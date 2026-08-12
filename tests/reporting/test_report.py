"""Behavior, security, receipt, and recovery tests for direct HTML reporting."""

from __future__ import annotations

import argparse
import csv
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

from norad.reporting import report as REPORT
from norad.reporting._run_report import publication, receipt, validation
from norad.reporting._run_report.models import JINJA_VERSION, ReportRenderError
from tests.reporting.fixtures.artifact_run_summary_v1 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"


def publish_run_summary(fixture: Any) -> Path:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
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
def incomplete_summary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return publish_run_summary(
        FIXTURE.build_fixture(tmp_path_factory.mktemp("report-v2") / "fixture")
    )


@pytest.fixture(scope="module")
def exploratory_summary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path_factory.mktemp("report-v2-exploratory") / "fixture",
        science_status="science_review_complete_exploratory",
        roles=("candidate_selection",),
        display_limits={"candidate_selection": 1},
    )
    return publish_run_summary(fixture)


def arguments(
    summary: Path, output_root: Path, *, execute: bool = False
) -> argparse.Namespace:
    return argparse.Namespace(
        run_summary=summary,
        output_root=output_root,
        execute=execute,
    )


def output_paths(context: Any) -> tuple[Path, Path, Path]:
    return context.output_html, context.output_summary_tsv, context.output_receipt


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


def publish(context: Any, ops: REPORT.ReportPublicationOps | None = None) -> None:
    publication.publish_report(context, ops or REPORT.default_publication_ops())


def test_grouped_help_exposes_only_direct_html_contract(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-m", "norad", "build", "report", "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    missing = subprocess.run(
        [sys.executable, "-I", "-m", "norad", "build", "report"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage: norad build report" in result.stdout
    assert "--run-summary" in result.stdout
    assert "--output-root" in result.stdout
    assert "--execute" in result.stdout
    assert "--formats" not in result.stdout
    assert "--quarto-bin" not in result.stdout
    assert missing.returncode == 2
    assert "required" in missing.stderr


def test_dry_run_is_side_effect_free(
    incomplete_summary: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "reports"
    result = REPORT.build_from_args(arguments(incomplete_summary, output_root))
    captured = capsys.readouterr()
    assert result == 0
    assert "Dry-run only" in captured.out
    assert not captured.err
    assert not output_root.exists()


def test_success_publishes_html_summary_and_v2_receipt_last(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "reports", execute=True)
    )
    links: list[Path] = []
    base = REPORT.default_publication_ops()

    def record_link(source: Path, target: Path) -> None:
        links.append(target)
        base.link(source, target)

    publish(context, replace(base, link=record_link))
    assert output_paths(context) == tuple(path for path in context.stable_paths)
    assert all(path.is_file() for path in output_paths(context))
    assert [path.name for path in links[-3:]] == [
        context.output_html.name,
        context.output_summary_tsv.name,
        context.output_receipt.name,
    ]
    assert not context.output_html.with_suffix(".pdf").exists()
    document = receipt_document(context.output_receipt)
    assert document["schema_version"] == "2.0.0"
    assert document["renderer"] == {"name": "Jinja2", "version": JINJA_VERSION}
    assert [item["kind"] for item in document["outputs"]] == [
        "html",
        "run_summary_tsv",
    ]
    assert document["outputs"][0]["self_contained"] is True
    assert document["analysis_execution_performed"] is False
    assert document["validation_claimed"] is False


def test_identical_republication_is_byte_deterministic(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    arguments_value = arguments(incomplete_summary, tmp_path / "reports", execute=True)
    first_context = REPORT.prepare_report(arguments_value)
    publish(first_context)
    first = tuple(path.read_bytes() for path in output_paths(first_context))
    second_context = REPORT.prepare_report(arguments_value)
    publish(second_context)
    second = tuple(path.read_bytes() for path in output_paths(second_context))
    assert second == first


def test_jinja_is_strict_autoescaped_and_template_owns_markup(
    incomplete_summary: Path,
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

    copied = write_summary_copy(incomplete_summary, tmp_path / "input", add_untrusted)
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    publish(context)
    content = context.output_html.read_text(encoding="utf-8")
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


def test_semantic_html_preserves_banner_sections_and_terminology(
    exploratory_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(exploratory_summary, tmp_path / "reports", execute=True)
    )
    publish(context)
    content = context.output_html.read_text(encoding="utf-8")
    assert "EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED." in content
    assert "CMH-ranked candidates" in content
    assert "FWD_like" in content
    assert "biological strand" not in content
    assert "<script" not in content.lower()
    assert "http://" not in content and "https://" not in content
    validation.validate_rendered_html(
        context.output_html,
        expected_banner=context.render_metadata["state_banner"],
        expected_identity={
            "data-css-sha256": context.render_metadata["css_sha256"],
            "data-jinja-version": JINJA_VERSION,
            "data-renderer-version": context.render_metadata["renderer_version"],
            "data-run-id": context.summary["run_id"],
            "data-run-summary-sha256": context.render_metadata["run_summary_sha256"],
            "data-template-sha256": context.render_metadata["template_sha256"],
        },
    )


def test_approved_table_limit_and_truncation_are_disclosed(
    exploratory_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(exploratory_summary, tmp_path / "reports", execute=True)
    )
    assert len(context.tables) == 1
    assert context.tables[0].displayed_row_count == 1
    assert context.tables[0].truncated is True
    publish(context)
    document = receipt_document(context.output_receipt)
    assert document["truncations"] == [
        {
            "table_id": context.tables[0].table_id,
            "report_section": "cmh-ranked-candidates",
            "full_table_path": str(context.tables[0].path),
            "full_table_sha256": context.tables[0].sha256,
            "full_row_count": context.tables[0].row_count,
            "displayed_row_count": 1,
        }
    ]
    assert "Displayed 1 of" in context.output_html.read_text(encoding="utf-8")


def test_explicit_input_and_canonical_name_are_required(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    wrong = tmp_path / "wrong.json"
    wrong.write_bytes(incomplete_summary.read_bytes())
    with pytest.raises(ReportRenderError, match="Canonical run-summary"):
        REPORT.prepare_report(arguments(wrong, tmp_path / "reports"))
    with pytest.raises(ReportRenderError, match="Could not inspect"):
        REPORT.prepare_report(
            arguments(tmp_path / "missing.json", tmp_path / "reports")
        )


def test_v1_and_bare_html_predecessors_require_fresh_output_root(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(incomplete_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    (output_dir / f"{run_id}.run_report.html").write_text("legacy", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="fresh output root"):
        REPORT.prepare_report(arguments(incomplete_summary, output_root))
    (output_dir / f"{run_id}.report_outputs.tsv").write_text(
        "schema_name\tschema_version\trequested_formats\n",
        encoding="utf-8",
    )
    with pytest.raises(ReportRenderError, match="fresh output root"):
        REPORT.prepare_report(arguments(incomplete_summary, output_root))


def test_lock_collision_is_rejected_without_mutation(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    run_id = json.loads(incomplete_summary.read_text(encoding="utf-8"))["run_id"]
    output_root = tmp_path / "reports"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True)
    lock = output_dir / f".{run_id}.report.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="lock already exists"):
        REPORT.prepare_report(arguments(incomplete_summary, output_root))
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_input_mutation_aborts_and_removes_owned_state(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    copied = write_summary_copy(incomplete_summary, tmp_path / "input")
    context = REPORT.prepare_report(
        arguments(copied, tmp_path / "reports", execute=True)
    )
    copied.write_bytes(copied.read_bytes() + b" ")
    with pytest.raises(ReportRenderError, match="changed during report"):
        publish(context)
    assert not any(path.exists() for path in output_paths(context))
    assert not context.lock_path.exists()


def test_interrupted_lock_acquisition_cleans_owned_lock(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "reports", execute=True)
    )
    base = REPORT.default_publication_ops()

    def interrupt(_descriptor: int, _payload: bytes) -> int:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        publish(context, replace(base, lock_write=interrupt))
    assert not context.lock_path.exists()
    assert not any(path.exists() for path in output_paths(context))


def test_post_backup_failure_rolls_back_exact_predecessor(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    args = arguments(incomplete_summary, tmp_path / "reports", execute=True)
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
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    empty_context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "foreign-final", execute=True)
    )
    empty_context.output_dir.mkdir(parents=True)
    empty_context.output_html.write_text("foreign final\n", encoding="utf-8")
    with pytest.raises(ReportRenderError, match="appeared after preflight"):
        publish(empty_context)
    assert empty_context.output_html.read_text(encoding="utf-8") == "foreign final\n"

    args = arguments(incomplete_summary, tmp_path / "foreign-backup", execute=True)
    initial = REPORT.prepare_report(args)
    publish(initial)
    context = REPORT.prepare_report(args)
    token = "fixed-foreign-token"
    backup = context.output_dir / f".{context.output_html.name}.{token}.previous"
    backup.write_text("foreign backup\n", encoding="utf-8")
    ops = replace(REPORT.default_publication_ops(), make_token=lambda: token)
    with pytest.raises(ReportRenderError, match="backup path unexpectedly exists"):
        publish(context, ops)
    assert backup.read_text(encoding="utf-8") == "foreign backup\n"
    assert all(path.is_file() for path in output_paths(context))


def test_incomplete_rollback_preserves_lock_stage_and_recovery(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    args = arguments(incomplete_summary, tmp_path / "reports", execute=True)
    initial = REPORT.prepare_report(args)
    publish(initial)
    context = REPORT.prepare_report(args)
    base = REPORT.default_publication_ops()

    def fail_publication_and_restore(source: Path, target: Path) -> None:
        if ".run-report." in source.parent.name and target == context.output_html:
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
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "reports", execute=True)
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
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "reports", execute=True)
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
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / "reports", execute=True)
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
    incomplete_summary: Path,
    tmp_path: Path,
    column: str,
    replacement: str,
) -> None:
    context = REPORT.prepare_report(
        arguments(incomplete_summary, tmp_path / column, execute=True)
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
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    context = REPORT.prepare_report(arguments(incomplete_summary, tmp_path / "reports"))
    assert receipt.summary_tsv_bytes(context) == receipt.summary_tsv_bytes(context)
    stage = tmp_path / "stage"
    stage.mkdir()
    html = stage / context.output_html.name
    summary = stage / context.output_summary_tsv.name
    html.write_bytes(context.html_bytes)
    summary.write_bytes(receipt.summary_tsv_bytes(context))
    document = receipt.receipt_document(
        context,
        (
            ("run-report-html", "html", html, context.output_html),
            ("run-summary-tsv", "run_summary_tsv", summary, context.output_summary_tsv),
        ),
    )
    assert receipt.receipt_tsv_bytes(document) == receipt.receipt_tsv_bytes(
        json.loads(json.dumps(document))
    )
