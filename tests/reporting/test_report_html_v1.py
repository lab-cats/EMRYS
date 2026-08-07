"""Focused model, security, transaction, and real-render tests for HTML reports."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTING_ROOT = REPO_ROOT / "src" / "norad" / "reporting"
RENDER_SCRIPT = REPORTING_ROOT / "render_run_report.py"
SCRIPT = (
    REPO_ROOT
    / "tests"
    / "reporting"
    / "fixtures"
    / "report_html_v1"
    / "run_html_core.py"
)
RUN_SUMMARY_SCRIPT = REPORTING_ROOT / "build_run_summary.py"
FIXTURE_BUILDER = (
    REPO_ROOT
    / "tests"
    / "reporting"
    / "fixtures"
    / "artifact_run_summary_v1"
    / "build_fixture.py"
)
APPROVED_TABLE_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "reporting"
    / "fixtures"
    / "report_html_v1"
    / "approved_candidates.tsv"
)
FIXED_EPOCH = "1700000000"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FIXTURE = load_module("norad_report_html_fixture_builder", FIXTURE_BUILDER)
RENDER = load_module("norad_report_html_renderer", RENDER_SCRIPT)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publish_run_summary(fixture: Any) -> Path:
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
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not publish report fixture:\n{result.stdout}\n{result.stderr}"
        )
    return fixture.summary_json_path


@pytest.fixture(scope="module")
def incomplete_summary(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    root = tmp_path_factory.mktemp("report-html-incomplete")
    fixture = FIXTURE.build_fixture(root / "fixture")
    return publish_run_summary(fixture)


@pytest.fixture(scope="module")
def exploratory_summary(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    root = tmp_path_factory.mktemp("report-html-exploratory")
    fixture = FIXTURE.build_explicit_science_fixture(
        root / "fixture",
        science_status="science_review_complete_exploratory",
    )
    return publish_run_summary(fixture)


def read_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_summary_copy(
    document: Mapping[str, Any],
    root: Path,
    *,
    raw_bytes: bytes | None = None,
) -> Path:
    run_id = str(document["run_id"])
    output_dir = root / run_id
    output_dir.mkdir(parents=True)
    path = output_dir / f"{run_id}.run_summary.json"
    path.write_bytes(
        raw_bytes if raw_bytes is not None else canonical_json_bytes(document)
    )
    return path


def attach_fixture_approval_provenance(
    document: dict[str, Any],
    root: Path,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    approval_count = len(document["approved_report_tables"])
    manifest = root / "fixture_report_table_approvals.tsv"
    manifest.write_text(
        "table_id\n"
        + "".join(
            f"{record['table_id']}\n"
            for record in document["approved_report_tables"]
        ),
        encoding="utf-8",
    )
    document["parameters"]["report_table_approvals"] = {
        "path": str(manifest),
        "sha256": sha256_file(manifest),
        "size_bytes": manifest.stat().st_size,
        "row_count": approval_count,
        "media_type": "text/tab-separated-values",
    }


def build_fake_quarto(
    root: Path,
    *,
    version: str = RENDER.QUARTO_VERSION,
    mode: str = "success",
    mutation_path: Path | None = None,
    environment_log: Path | None = None,
    child_ready: Path | None = None,
    child_sentinel: Path | None = None,
) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    executable = root / "quarto"
    log = root / "quarto.log"
    executable.write_text(
        """#!__PYTHON__
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path

log = Path(__LOG__)
with log.open("a", encoding="utf-8") as stream:
    stream.write("\\t".join(sys.argv[1:]) + "\\n")
environment_log = __ENVIRONMENT_LOG__
if environment_log is not None:
    names = (
        "BASH_ENV",
        "ENV",
        "HOME",
        "PANDOC_DATA_DIR",
        "QUARTO_DENO",
        "QUARTO_PANDOC",
        "QUARTO_PROFILE",
        "QUARTO_PYTHON",
        "PATH",
    )
    with Path(environment_log).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({name: os.environ.get(name) for name in names}, sort_keys=True) + "\\n")
if sys.argv[1:] == ["--version"]:
    print(__VERSION__)
    raise SystemExit(0)
if len(sys.argv) < 2 or sys.argv[1] != "render":
    raise SystemExit(97)
mode = __MODE__
if mode == "fail":
    print("synthetic Quarto failure", file=sys.stderr)
    raise SystemExit(42)
if mode == "mutate_input":
    mutation_path = Path(__MUTATION_PATH__)
    mutation_path.write_bytes(mutation_path.read_bytes() + b" ")
if mode == "spawn_child":
    child_code = (
        "import time\\n"
        "from pathlib import Path\\n"
        "time.sleep(1.0)\\n"
        "Path(" + repr(__CHILD_SENTINEL__) + ").write_text('survived', encoding='utf-8')\\n"
    )
    subprocess.Popen([sys.executable, "-c", child_code])
    Path(__CHILD_READY__).write_text("ready", encoding="utf-8")
    time.sleep(60)
output_name = sys.argv[sys.argv.index("--output") + 1]
output = Path.cwd() / output_name
if mode == "omit":
    raise SystemExit(0)
if mode == "empty":
    output.write_bytes(b"")
    raise SystemExit(0)
qmd = (Path.cwd() / sys.argv[2]).read_text(encoding="utf-8")
parts = qmd.split("---", 2)
body = parts[2] if len(parts) == 3 else qmd
if mode == "external":
    body += '<script src="https://cdn.invalid/a.js"></script>'
if mode == "malformed":
    output.write_text("<html>", encoding="utf-8")
    raise SystemExit(0)
payload = (
    "<!DOCTYPE html><html lang=\\"en\\"><head>"
    "<meta charset=\\"utf-8\\"><title>NORAD consolidated run report</title>"
    "<style>body{color:#17202a}</style>"
    "</head><body>" + body + "</body></html>\\n"
)
output.write_text(payload, encoding="utf-8")
"""
        .replace("__PYTHON__", str(Path(sys.executable).resolve()))
        .replace("__LOG__", repr(str(log)))
        .replace("__ENVIRONMENT_LOG__", repr(
            str(environment_log) if environment_log is not None else None
        ))
        .replace("__VERSION__", repr(version))
        .replace("__MODE__", repr(mode))
        .replace(
            "__MUTATION_PATH__",
            repr(str(mutation_path) if mutation_path is not None else ""),
        )
        .replace(
            "__CHILD_READY__",
            repr(str(child_ready) if child_ready is not None else ""),
        )
        .replace(
            "__CHILD_SENTINEL__",
            repr(str(child_sentinel) if child_sentinel is not None else ""),
        ),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable, log


def run_renderer(
    *,
    summary: Path,
    output_root: Path,
    quarto: Path,
    execute: bool = False,
    extra_env: Mapping[str, str] | None = None,
    cwd: Path = REPO_ROOT,
    arguments: Sequence[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if extra_env:
        environment.update(extra_env)
    cli = (
        list(arguments)
        if arguments is not None
        else [
            "--run-summary",
            str(summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--formats",
            "html",
            *(["--execute"] if execute else []),
        ]
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), *cli],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def make_approved_summary(
    source_summary: Path,
    root: Path,
    *,
    display_row_limit: int | None,
    role: str = "candidate_selection",
) -> Path:
    document = read_summary(source_summary)
    artifact = next(
        item
        for item in document["artifacts"]
        if item["artifact_id"] == "cohort.synthetic.step08_sites"
    )
    relative_path = str(APPROVED_TABLE_FIXTURE.relative_to(REPO_ROOT))
    source = {
        "path": relative_path,
        "sha256": sha256_file(APPROVED_TABLE_FIXTURE),
        "size_bytes": APPROVED_TABLE_FIXTURE.stat().st_size,
        "row_count": 2,
        "media_type": "text/tab-separated-values",
    }
    artifact["expectation"]["source_path"] = relative_path
    artifact["source"] = source
    for metric in artifact["metrics"]:
        if metric["metric_id"] == "source_row_count":
            metric["value"] = 2
    document["approved_report_tables"] = [
        {
            "table_id": "synthetic_candidates",
            "artifact_id": artifact["artifact_id"],
            "role": role,
            "title": "Synthetic CMH-ranked candidates",
            "path": relative_path,
            "sha256": source["sha256"],
            "row_count": 2,
            "display_row_limit": display_row_limit,
            "approval": {
                "status": "approved",
                "policy_version": "synthetic_report_policy_v1",
                "approved_by": "scientific_owner",
                "approved_at": "2023-11-14T22:13:20Z",
            },
        }
    ]
    attach_fixture_approval_provenance(document, root)
    return write_summary_copy(document, root)


def expected_output(output_root: Path, summary: Path) -> Path:
    run_id = read_summary(summary)["run_id"]
    return output_root / run_id / f"{run_id}.run_report.html"


def test_help_and_dry_run_are_explicit_and_side_effect_free(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, log = build_fake_quarto(tmp_path)
    output_root = tmp_path / "reports"
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    result = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=quarto,
    )

    assert help_result.returncode == 0
    for option in (
        "--run-summary",
        "--output-root",
        "--quarto-bin",
        "--formats",
        "--execute",
    ):
        assert option in help_result.stdout
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert not output_root.exists()
    assert log.read_text(encoding="utf-8").splitlines() == ["--version"]


def test_execute_invokes_only_quarto_and_publishes_exact_html(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, log = build_fake_quarto(tmp_path)
    output_root = tmp_path / "reports"
    result = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )

    assert result.returncode == 0, result.stderr
    output = expected_output(output_root, incomplete_summary)
    assert output.is_file()
    content = output.read_text(encoding="utf-8")
    assert RENDER.SCIENCE_BANNERS["evidence_incomplete"] in content
    assert RENDER.CANDIDATE_TERMINOLOGY in content
    assert "<main id=\"norad-report\"" in content
    assert f'data-run-id="{read_summary(incomplete_summary)["run_id"]}"' in content
    assert f'data-renderer-version="{RENDER.PRODUCER_VERSION}"' in content
    assert f'data-quarto-version="{RENDER.QUARTO_VERSION}"' in content
    assert "Static report renderer provenance" in content
    assert sha256_file(incomplete_summary) in content
    assert sha256_file(RENDER.QMD_TEMPLATE) in content
    assert sha256_file(RENDER.CSS_TEMPLATE) in content
    calls = log.read_text(encoding="utf-8").splitlines()
    assert calls[0] == "--version"
    assert calls[1].startswith("render\t")
    assert "\t--no-execute" in calls[1]
    assert not any(
        engine in "\n".join(calls).lower()
        for engine in (
            "star",
            "samtools",
            "picard",
            "gatk",
            "bcftools",
            "rscript",
            "mantelhaen",
            "restore_quarto",
        )
    )
    assert not any(
        child.name.endswith("_files") for child in output.parent.iterdir()
    )
    assert not any(
        child.name.startswith(".run-report.") for child in output.parent.iterdir()
    )


def test_static_qmd_is_deterministic_escaped_and_complete(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    document = read_summary(incomplete_summary)
    sentinel = (
        '<script>alert("x")</script> jupyter: knitr: '
        "{{NORAD_REPORT_BODY}} url(https://visible.example) `ticks` & Unicode Ω"
    )
    document["limitations"][0]["description"] = sentinel
    summary = write_summary_copy(document, tmp_path / "copy")
    loaded = RENDER._load_run_summary(summary)

    first = RENDER.build_qmd_bytes(loaded, ())
    second = RENDER.build_qmd_bytes(loaded, ())
    text = first.decode("utf-8")

    assert first == second
    assert "<script>alert" not in text
    assert "&lt;script&gt;alert" in text
    assert "jupyter:" in text
    assert "{{NORAD_REPORT_BODY}}" in text
    assert "url(https://visible.example)" in text
    assert "&#96;ticks&#96;" in text
    assert "&amp;" in text
    assert "Unicode Ω" in text
    assert "```{" not in text
    assert RENDER.CANDIDATE_TERMINOLOGY in text
    assert "Report generation is not evidence" in text


def test_qmd_template_rejects_filters_and_other_unapproved_frontmatter() -> None:
    template = RENDER.QMD_TEMPLATE.read_text(encoding="utf-8")
    malicious = template.replace(
        "execute:\n",
        "filters:\n  - /tmp/undeclared-filter.lua\nexecute:\n",
        1,
    )
    with pytest.raises(
        RENDER.ReportRenderError,
        match="closed static HTML allowlist",
    ):
        RENDER.validate_qmd_template(malicious)


def test_render_subprocess_environment_is_closed_and_deterministic(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    environment_log = tmp_path / "environment.jsonl"
    quarto, _ = build_fake_quarto(
        tmp_path / "fake",
        environment_log=environment_log,
    )
    result = run_renderer(
        summary=incomplete_summary,
        output_root=tmp_path / "reports",
        quarto=quarto,
        execute=True,
        extra_env={
            "BASH_ENV": "/tmp/hostile-bash-env",
            "ENV": "/tmp/hostile-shell-env",
            "PANDOC_DATA_DIR": "/tmp/hostile-pandoc-data",
            "QUARTO_DENO": "/tmp/hostile-deno",
            "QUARTO_PANDOC": "/tmp/hostile-pandoc",
            "QUARTO_PROFILE": "hostile",
            "QUARTO_PYTHON": "/tmp/hostile-python",
        },
    )

    assert result.returncode == 0, result.stderr
    records = [
        json.loads(line)
        for line in environment_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 2
    for record in records:
        assert record["PATH"] == RENDER.SAFE_RENDER_PATH
        for name, value in record.items():
            if name != "PATH":
                assert value is None


def test_renderer_signal_terminates_complete_quarto_process_group(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    child_ready = tmp_path / "child-ready"
    child_sentinel = tmp_path / "child-survived"
    quarto, _ = build_fake_quarto(
        tmp_path / "fake",
        mode="spawn_child",
        child_ready=child_ready,
        child_sentinel=child_sentinel,
    )
    output_root = tmp_path / "reports"
    process = subprocess.Popen(
        [
            sys.executable,
            str(SCRIPT),
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not child_ready.exists() and time.monotonic() < deadline:
            if process.poll() is not None:
                break
            time.sleep(0.05)
        assert child_ready.is_file()
        process.send_signal(signal.SIGTERM)
        standard_output, standard_error = process.communicate(timeout=15)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    assert process.returncode == 1, standard_output + standard_error
    assert "interrupted by signal SIGTERM" in standard_error
    time.sleep(1.2)
    assert not child_sentinel.exists()
    assert not output_root.exists()


def test_exploratory_summary_preserves_science_metadata_and_banner(
    exploratory_summary: Path,
) -> None:
    document = RENDER._load_run_summary(exploratory_summary)
    qmd = RENDER.build_qmd_bytes(document, ()).decode("utf-8")

    assert RENDER.SCIENCE_BANNERS[
        "science_review_complete_exploratory"
    ] in qmd
    for expected in (
        "Scientific-review metadata",
        "Scientific-review policy versions",
        "Preregistered selection and sensitivity rules",
        "Orientation status",
        "background",
        "matched_dna",
        "orthogonal_evidence",
        "Rerun required",
        "Explicit scientific evidence records",
    ):
        assert expected in qmd
    assert "BIOLOGICALLY VALIDATED" in qmd
    assert "biological_interpretation_ready" not in qmd


def test_artifact_metrics_and_missing_failed_states_remain_visible(
    incomplete_summary: Path,
) -> None:
    document = RENDER._load_run_summary(incomplete_summary)
    qmd = RENDER.build_qmd_bytes(document, ()).decode("utf-8")

    assert "Canonical artifact-level QC metrics" in qmd
    assert "source_row_count" in qmd
    assert "sample_count" in qmd
    for state in ("missing", "incomplete", "failed", "externally_unavailable"):
        if any(
            artifact["availability_status"] == state
            or artifact["completion_status"] == state
            for artifact in document["artifacts"]
        ):
            assert state.replace("_", " ") in qmd or state in qmd
    assert "State reason" in qmd
    assert "Warning detail" in qmd


@pytest.mark.parametrize("display_limit", [0, 1, 2, None])
def test_approved_table_limits_paths_hashes_and_escaping(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    display_limit: int | None,
) -> None:
    summary = make_approved_summary(
        incomplete_summary,
        tmp_path / f"limit-{display_limit}",
        display_row_limit=display_limit,
    )
    monkeypatch.chdir(tmp_path)
    document = RENDER._load_run_summary(summary)
    tables = tuple(
        RENDER._read_approved_table(record)
        for record in document["approved_report_tables"]
    )
    qmd = RENDER.build_qmd_bytes(document, tables).decode("utf-8")

    table = tables[0]
    assert table.path == APPROVED_TABLE_FIXTURE
    assert table.row_count == 2
    assert table.approved_by == "scientific_owner"
    assert str(APPROVED_TABLE_FIXTURE) in qmd
    assert table.sha256 in qmd
    assert "synthetic_report_policy_v1" in qmd
    if display_limit == 0:
        assert "Displayed 0 of 2 rows" in qmd
        assert "candidate_001" not in qmd
    elif display_limit == 1:
        assert "Displayed 1 of 2 rows" in qmd
        assert table.display_rows[0][1] == "FWD_like"
        assert all("REV_like" not in cell for cell in table.display_rows[0])
    else:
        assert [row[1] for row in table.display_rows] == [
            "FWD_like",
            "REV_like",
        ]
        assert ">+<" in qmd and ">-<" in qmd
        assert "<script>alert" not in qmd
        assert "&lt;script&gt;alert" in qmd
        assert "Displayed 2 of 2 rows" not in qmd


def test_wide_tables_are_scoped_to_a_keyboard_scroll_region() -> None:
    rendered = RENDER._table(
        table_id="wide-table",
        caption="Wide approved evidence",
        header=tuple(f"column_{index}" for index in range(7)),
        rows=(tuple(f"value_{index}" for index in range(7)),),
    )
    assert 'class="norad-table-wrap norad-table-wrap-wide"' in rendered
    assert 'tabindex="0" role="region"' in rendered
    assert 'aria-label="Wide approved evidence"' in rendered


def test_builder_approved_tables_render_end_to_end(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "producer",
        science_status="science_review_complete_exploratory",
        display_limits={
            "candidate_selection": 1,
            "candidate_adjudication": 1,
        },
    )
    summary = publish_run_summary(fixture)
    untouched = summary.read_bytes()
    document = read_summary(summary)
    quarto, _log = build_fake_quarto(tmp_path / "quarto")
    output_root = tmp_path / "reports"

    result = run_renderer(
        summary=summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )

    assert result.returncode == 0, result.stderr
    assert summary.read_bytes() == untouched
    output = expected_output(output_root, summary)
    rendered = output.read_text(encoding="utf-8")
    assert (
        "EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED."
        in rendered
    )
    assert "CMH-ranked candidates: approved selection summary" in rendered
    assert "CMH-ranked candidates: approved adjudication summary" in rendered
    for approval in document["approved_report_tables"]:
        assert approval["path"] in rendered
        assert approval["sha256"] in rendered
    assert (
        str(fixture.report_table_approvals)
        in json.dumps(document["parameters"], sort_keys=True)
    )


def test_unknown_approved_role_is_never_silently_omitted(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    summary = make_approved_summary(
        incomplete_summary,
        tmp_path / "unknown",
        display_row_limit=1,
        role="future_table_role",
    )
    document = RENDER._load_run_summary(summary)
    tables = tuple(
        RENDER._read_approved_table(record)
        for record in document["approved_report_tables"]
    )
    qmd = RENDER.build_qmd_bytes(document, tables).decode("utf-8")
    assert "Other explicitly approved report tables" in qmd
    assert "Synthetic CMH-ranked candidates" in qmd


def test_candidate_role_uses_controlled_nonvalidating_caption(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    summary = make_approved_summary(
        incomplete_summary,
        tmp_path / "candidate-caption",
        display_row_limit=1,
        role="candidate_selection",
    )
    document = read_summary(summary)
    document["approved_report_tables"][0]["title"] = (
        "Validated editing sites and confirmed biology"
    )
    summary = write_summary_copy(document, tmp_path / "candidate-caption-copy")
    loaded = RENDER._load_run_summary(summary)
    tables = tuple(
        RENDER._read_approved_table(record)
        for record in loaded["approved_report_tables"]
    )
    qmd = RENDER.build_qmd_bytes(loaded, tables).decode("utf-8")

    assert "CMH-ranked candidates: approved selection summary" in qmd
    assert "Validated editing sites" not in qmd
    assert "confirmed biology" not in qmd


def test_header_only_approved_candidate_table_is_rendered_as_zero_rows(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    document = read_summary(incomplete_summary)
    table_path = tmp_path / "header-only-candidates.tsv"
    table_path.write_text(
        "candidate_id\torientation\tannotation_strand\n",
        encoding="utf-8",
    )
    artifact = next(
        item
        for item in document["artifacts"]
        if item["artifact_id"] == "cohort.synthetic.step08_sites"
    )
    source = {
        "path": str(table_path),
        "sha256": sha256_file(table_path),
        "size_bytes": table_path.stat().st_size,
        "row_count": 0,
        "media_type": "text/tab-separated-values",
    }
    artifact["expectation"]["source_path"] = str(table_path)
    artifact["source"] = source
    document["approved_report_tables"] = [
        {
            "table_id": "header_only_candidates",
            "artifact_id": artifact["artifact_id"],
            "role": "candidate_selection",
            "title": "Ignored candidate caption",
            "path": str(table_path),
            "sha256": source["sha256"],
            "row_count": 0,
            "display_row_limit": None,
            "approval": {
                "status": "approved",
                "policy_version": "fixture_v1",
                "approved_by": "scientific_owner",
                "approved_at": "2023-11-14T22:13:20Z",
            },
        }
    ]
    attach_fixture_approval_provenance(
        document,
        tmp_path / "approval-provenance",
    )
    summary = write_summary_copy(document, tmp_path / "summary")
    loaded = RENDER._load_run_summary(summary)
    tables = tuple(
        RENDER._read_approved_table(record)
        for record in loaded["approved_report_tables"]
    )
    qmd = RENDER.build_qmd_bytes(loaded, tables).decode("utf-8")

    assert tables[0].row_count == 0
    assert tables[0].displayed_row_count == 0
    assert "No rows are available." in qmd
    assert "CMH-ranked candidates: approved selection summary" in qmd


def test_mutated_approved_table_hash_and_row_shape_fail_closed(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    document = read_summary(incomplete_summary)
    table_copy = tmp_path / "table.tsv"
    shutil.copyfile(APPROVED_TABLE_FIXTURE, table_copy)
    artifact = next(
        item
        for item in document["artifacts"]
        if item["artifact_id"] == "cohort.synthetic.step08_sites"
    )
    source = {
        "path": str(table_copy),
        "sha256": sha256_file(table_copy),
        "size_bytes": table_copy.stat().st_size,
        "row_count": 2,
        "media_type": "text/tab-separated-values",
    }
    artifact["expectation"]["source_path"] = str(table_copy)
    artifact["source"] = source
    document["approved_report_tables"] = [
        {
            "table_id": "mutated",
            "artifact_id": artifact["artifact_id"],
            "role": "candidate_selection",
            "title": "Mutated table",
            "path": str(table_copy),
            "sha256": source["sha256"],
            "row_count": 2,
            "display_row_limit": None,
            "approval": {
                "status": "approved",
                "policy_version": "fixture_v1",
                "approved_by": "owner",
                "approved_at": "2023-11-14T22:13:20Z",
            },
        }
    ]
    attach_fixture_approval_provenance(
        document,
        tmp_path / "approval-provenance",
    )
    summary = write_summary_copy(document, tmp_path / "summary")
    loaded = RENDER._load_run_summary(summary)

    table_copy.write_text("a\tb\n1\n", encoding="utf-8")
    with pytest.raises(RENDER.ReportRenderError, match="SHA-256 mismatch"):
        RENDER._read_approved_table(loaded["approved_report_tables"][0])

    mutated_sha = sha256_file(table_copy)
    loaded["approved_report_tables"][0]["sha256"] = mutated_sha
    loaded["approved_report_tables"][0]["row_count"] = 1
    with pytest.raises(RENDER.ReportRenderError, match="has 1 fields"):
        RENDER._read_approved_table(loaded["approved_report_tables"][0])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda document: document.update(
                {"schema_version": "999.0.0"}
            ),
            "failed validation",
        ),
        (
            lambda document: document.update(
                {
                    "science_status": "biological_interpretation_ready",
                    "scientific_review": {
                        **document["scientific_review"],
                        "overall_status": "biological_interpretation_ready",
                    },
                }
            ),
            "failed validation",
        ),
        (
            lambda document: document["expected_scopes"].append(
                copy.deepcopy(document["expected_scopes"][0])
            ),
            "duplicate expected scope",
        ),
    ],
)
def test_schema_version_reserved_state_and_duplicate_ids_are_rejected(
    incomplete_summary: Path,
    tmp_path: Path,
    mutation: Any,
    message: str,
) -> None:
    document = read_summary(incomplete_summary)
    mutation(document)
    path = write_summary_copy(document, tmp_path / "bad")
    with pytest.raises(RENDER.ReportRenderError, match=message):
        RENDER._load_run_summary(path)


def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    document = read_summary(incomplete_summary)
    payload = canonical_json_bytes(document).decode("utf-8")
    duplicate = payload.replace(
        '"run_id": "synthetic_run",',
        '"run_id": "synthetic_run",\n  "run_id": "synthetic_run",',
        1,
    ).encode("utf-8")
    duplicate_path = write_summary_copy(
        document,
        tmp_path / "duplicate",
        raw_bytes=duplicate,
    )
    with pytest.raises(RENDER.ReportRenderError, match="Duplicate JSON"):
        RENDER._load_run_summary(duplicate_path)

    nonfinite = payload.replace(
        '"summary_state": "complete",',
        '"summary_state": "complete",\n  "not_a_number": NaN,',
        1,
    ).encode("utf-8")
    nonfinite_path = write_summary_copy(
        document,
        tmp_path / "nonfinite",
        raw_bytes=nonfinite,
    )
    with pytest.raises(RENDER.ReportRenderError, match="Non-standard JSON"):
        RENDER._load_run_summary(nonfinite_path)


def test_canonical_input_name_and_quarto_version_are_required(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "good")
    wrong_quarto, _ = build_fake_quarto(tmp_path / "wrong", version="1.9.37")
    document = read_summary(incomplete_summary)
    wrong_name_dir = tmp_path / "wrong-name"
    wrong_name_dir.mkdir()
    wrong_name = wrong_name_dir / "summary.json"
    wrong_name.write_bytes(canonical_json_bytes(document))

    bad_name = run_renderer(
        summary=wrong_name,
        output_root=tmp_path / "reports-a",
        quarto=quarto,
    )
    bad_version = run_renderer(
        summary=incomplete_summary,
        output_root=tmp_path / "reports-b",
        quarto=wrong_quarto,
    )
    assert bad_name.returncode != 0
    assert "Canonical run-summary input" in bad_name.stderr
    assert bad_version.returncode != 0
    assert "expected exactly" in bad_version.stderr
    assert not (tmp_path / "reports-a").exists()
    assert not (tmp_path / "reports-b").exists()


def test_unrelated_files_are_ignored_and_invocation_is_cwd_independent(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path)
    unrelated = tmp_path / "unrelated.tsv"
    unrelated.write_text("must\tremain\nunchanged\ttrue\n", encoding="utf-8")
    before = unrelated.read_bytes()
    result = run_renderer(
        summary=incomplete_summary,
        output_root=tmp_path / "reports",
        quarto=quarto,
        execute=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert unrelated.read_bytes() == before
    assert expected_output(tmp_path / "reports", incomplete_summary).is_file()


def test_lock_failure_and_render_failure_preserve_prior_report(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path)
    output_root = tmp_path / "reports"
    first = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )
    assert first.returncode == 0, first.stderr
    output = expected_output(output_root, incomplete_summary)
    prior = output.read_bytes()
    lock = output.parent / ".synthetic_run.report-html.lock"
    lock.write_text("foreign lock\n", encoding="utf-8")

    locked = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )
    assert locked.returncode != 0
    assert lock.read_text(encoding="utf-8") == "foreign lock\n"
    assert output.read_bytes() == prior
    lock.unlink()

    external_quarto, _ = build_fake_quarto(
        tmp_path / "external",
        mode="external",
    )
    failed = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=external_quarto,
        execute=True,
    )
    assert failed.returncode != 0
    assert "non-embedded active resources" in failed.stderr
    assert output.read_bytes() == prior
    assert not any(
        child.name.startswith(".run-report.") or child.name.endswith(".previous")
        for child in output.parent.iterdir()
    )


def test_interrupt_immediately_after_backup_rename_restores_prior_report(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    first_context = RENDER.prepare_context(arguments)
    RENDER.publish_report(first_context)
    prior = first_context.output_html.read_bytes()
    second_context = RENDER.prepare_context(arguments)
    original_link = RENDER.os.link
    interrupted = False

    def interrupt_after_backup(
        source: Path,
        destination: Path,
        *,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal interrupted
        original_link(
            source,
            destination,
            follow_symlinks=follow_symlinks,
        )
        if (
            Path(source) == second_context.output_html
            and Path(destination).name.endswith(".previous")
        ):
            interrupted = True
            raise KeyboardInterrupt("synthetic post-backup interrupt")

    monkeypatch.setattr(RENDER.os, "link", interrupt_after_backup)
    with pytest.raises(
        KeyboardInterrupt,
        match="synthetic post-backup interrupt",
    ):
        RENDER.publish_report(second_context)

    assert interrupted
    assert second_context.output_html.read_bytes() == prior
    assert not second_context.lock_path.exists()
    assert not any(
        child.name.endswith((".previous", ".RECOVERY.txt"))
        or child.name.startswith(".run-report.")
        for child in second_context.output_dir.iterdir()
    )


def test_interrupt_during_lock_acquisition_cleans_lock_and_restores_handlers(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    context = RENDER.prepare_context(arguments)
    original_write = RENDER.os.write
    original_handlers = {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    interrupted = False

    def interrupt_after_lock_write(descriptor: int, payload: bytes) -> int:
        nonlocal interrupted
        written = original_write(descriptor, payload)
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt("synthetic lock-acquisition interrupt")
        return written

    monkeypatch.setattr(RENDER.os, "write", interrupt_after_lock_write)
    with pytest.raises(
        KeyboardInterrupt,
        match="synthetic lock-acquisition interrupt",
    ):
        RENDER.publish_report(context)

    assert interrupted
    assert not context.lock_path.exists()
    assert not output_root.exists()
    for signum, handler in original_handlers.items():
        assert signal.getsignal(signum) == handler


def test_signal_handlers_remain_installed_through_lock_release(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(tmp_path / "reports"),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    context = RENDER.prepare_context(arguments)
    original_handler = signal.getsignal(signal.SIGTERM)
    original_release = RENDER._release_lock
    observed_custom_handler = False

    def inspect_release(ownership: Any) -> None:
        nonlocal observed_custom_handler
        observed_custom_handler = (
            signal.getsignal(signal.SIGTERM) != original_handler
        )
        original_release(ownership)

    monkeypatch.setattr(RENDER, "_release_lock", inspect_release)
    RENDER.publish_report(context)

    assert observed_custom_handler
    assert signal.getsignal(signal.SIGTERM) == original_handler
    assert not context.lock_path.exists()


def test_foreign_replacement_during_rollback_retains_lock_and_recovery(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    context = RENDER.prepare_context(arguments)
    original_validate = RENDER.validate_rendered_html

    def replace_final_then_fail(
        path: Path,
        *,
        expected_banner: str | None,
        expected_identity: Mapping[str, str] | None = None,
    ) -> None:
        if Path(path) == context.output_html:
            Path(path).write_text(
                "<!doctype html><html lang=\"en\"><body>foreign</body></html>",
                encoding="utf-8",
            )
            raise RENDER.ReportRenderError(
                "synthetic post-publication validation failure"
            )
        original_validate(
            path,
            expected_banner=expected_banner,
            expected_identity=expected_identity,
        )

    monkeypatch.setattr(
        RENDER,
        "validate_rendered_html",
        replace_final_then_fail,
    )
    with pytest.raises(
        RENDER.ReportRenderError,
        match="rollback was incomplete",
    ):
        RENDER.publish_report(context)

    assert context.output_html.read_text(encoding="utf-8").endswith(
        "foreign</body></html>"
    )
    assert context.lock_path.is_file()
    assert any(
        child.name.endswith(".RECOVERY.txt")
        for child in context.output_dir.iterdir()
    )
    assert any(
        child.name.startswith(".run-report.")
        for child in context.output_dir.iterdir()
    )


def test_late_foreign_final_is_never_clobbered(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    context = RENDER.prepare_context(arguments)
    original_link = RENDER.os.link
    foreign = b"late foreign final\n"
    injected = False

    def inject_foreign_final(
        source: Path,
        destination: Path,
        *,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal injected
        if Path(destination) == context.output_html and not injected:
            context.output_html.write_bytes(foreign)
            injected = True
        original_link(
            source,
            destination,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(RENDER.os, "link", inject_foreign_final)
    with pytest.raises(
        RENDER.ReportRenderError,
        match="rollback was incomplete",
    ):
        RENDER.publish_report(context)

    assert injected
    assert context.output_html.read_bytes() == foreign
    assert context.lock_path.is_file()
    assert any(
        child.name.endswith(".RECOVERY.txt")
        for child in context.output_dir.iterdir()
    )


def test_late_foreign_backup_is_never_clobbered(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    first_context = RENDER.prepare_context(arguments)
    RENDER.publish_report(first_context)
    prior = first_context.output_html.read_bytes()
    context = RENDER.prepare_context(arguments)
    original_link = RENDER.os.link
    foreign = b"late foreign backup\n"
    foreign_backup: Path | None = None

    def inject_foreign_backup(
        source: Path,
        destination: Path,
        *,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal foreign_backup
        destination_path = Path(destination)
        if (
            destination_path.name.endswith(".previous")
            and foreign_backup is None
        ):
            destination_path.write_bytes(foreign)
            foreign_backup = destination_path
        original_link(
            source,
            destination,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(RENDER.os, "link", inject_foreign_backup)
    with pytest.raises(
        RENDER.ReportRenderError,
        match="rollback was incomplete",
    ):
        RENDER.publish_report(context)

    assert context.output_html.read_bytes() == prior
    assert foreign_backup is not None
    assert foreign_backup.read_bytes() == foreign
    assert context.lock_path.is_file()
    assert any(
        child.name.endswith(".RECOVERY.txt")
        for child in context.output_dir.iterdir()
    )


def test_post_commit_backup_cleanup_failure_preserves_new_report_and_lock(
    incomplete_summary: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path / "fake")
    output_root = tmp_path / "reports"
    arguments = RENDER.parse_arguments(
        [
            "--run-summary",
            str(incomplete_summary),
            "--output-root",
            str(output_root),
            "--quarto-bin",
            str(quarto),
            "--execute",
        ]
    )
    first_context = RENDER.prepare_context(arguments)
    RENDER.publish_report(first_context)
    second_context = RENDER.prepare_context(arguments)
    original_sync = RENDER._fsync_directory
    output_sync_count = 0

    def fail_post_commit_backup_sync(path: Path) -> None:
        nonlocal output_sync_count
        if Path(path) == second_context.output_dir:
            output_sync_count += 1
            if output_sync_count == 4:
                raise OSError("synthetic post-commit backup cleanup failure")
        original_sync(path)

    monkeypatch.setattr(RENDER, "_fsync_directory", fail_post_commit_backup_sync)
    with pytest.raises(
        RENDER.ReportRenderError,
        match="cleanup failed",
    ):
        RENDER.publish_report(second_context)

    RENDER.validate_rendered_html(
        second_context.output_html,
        expected_banner=RENDER.SCIENCE_BANNERS[
            second_context.summary["science_status"]
        ],
        expected_identity=RENDER._expected_html_identity(second_context),
    )
    assert second_context.lock_path.is_file()
    assert any(
        child.name.endswith(".RECOVERY.txt")
        for child in second_context.output_dir.iterdir()
    )


@pytest.mark.parametrize("mode", ["fail", "omit", "empty", "malformed"])
def test_first_publication_failures_leave_no_transaction_residue(
    incomplete_summary: Path,
    tmp_path: Path,
    mode: str,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path, mode=mode)
    output_root = tmp_path / "reports"
    result = run_renderer(
        summary=incomplete_summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )
    assert result.returncode != 0
    assert not expected_output(output_root, incomplete_summary).exists()
    assert not output_root.exists()


def test_input_mutation_during_render_fails_closed(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    document = read_summary(incomplete_summary)
    summary = write_summary_copy(document, tmp_path / "summary")
    quarto, _ = build_fake_quarto(
        tmp_path / "fake",
        mode="mutate_input",
        mutation_path=summary,
    )
    output_root = tmp_path / "reports"
    result = run_renderer(
        summary=summary,
        output_root=output_root,
        quarto=quarto,
        execute=True,
    )
    assert result.returncode != 0
    assert "changed during report rendering" in result.stderr
    assert not expected_output(output_root, summary).exists()


def minimal_valid_html(extra: str = "") -> str:
    banner = RENDER.SCIENCE_BANNERS["evidence_incomplete"]
    return f"""<!DOCTYPE html>
<html lang="en"><head><title>Report</title><style>body{{color:#17202a}}</style></head><body>
<main><h1>Report</h1>
<div class="state-banner">{banner}</div>
<table class="norad-table"><caption>Data</caption>
<thead><tr><th scope="col">Field</th></tr></thead><tbody><tr><td>x</td></tr></tbody>
</table>
<svg role="img" aria-labelledby="t d"><title id="t">Figure</title><desc id="d">Description</desc></svg>
{extra}
</main></body></html>
"""


@pytest.mark.parametrize(
    "resource",
    [
        "<script>window.undeclared = true;</script>",
        '<script src="https://cdn.invalid/a.js"></script>',
        '<link rel="stylesheet" href="relative.css">',
        '<img src="relative.png" alt="image">',
        '<img srcset="data:image/png;base64,AAAA 1x, https://x.invalid/a.png 2x" alt="image">',
        '<iframe src="data:text/html,embedded"></iframe>',
        '<object data="data:text/plain,x"></object>',
        '<embed src="data:text/plain,x">',
        '<base href="https://example.invalid/">',
        '<meta http-equiv="refresh" content="0;url=https://example.invalid">',
        '<style>@import "https://cdn.invalid/a.css";</style>',
        '<div style="background:url(relative.png)">x</div>',
    ],
)
def test_self_contained_validator_rejects_active_resources(
    tmp_path: Path,
    resource: str,
) -> None:
    path = tmp_path / "report.html"
    path.write_text(minimal_valid_html(resource), encoding="utf-8")
    with pytest.raises(RENDER.ReportRenderError):
        RENDER.validate_rendered_html(
            path,
            expected_banner=RENDER.SCIENCE_BANNERS["evidence_incomplete"],
        )


def test_self_contained_validator_allows_visible_urls_and_data_images(
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.html"
    path.write_text(
        minimal_valid_html(
            "<p>Visible url(https://example.invalid) text is inert.</p>"
            '<img src="data:image/png;base64,AAAA" alt="Synthetic pixel">'
        ),
        encoding="utf-8",
    )
    RENDER.validate_rendered_html(
        path,
        expected_banner=RENDER.SCIENCE_BANNERS["evidence_incomplete"],
    )


def test_fixed_input_fake_rerenders_are_byte_deterministic(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto, _ = build_fake_quarto(tmp_path)
    roots = (tmp_path / "reports-a", tmp_path / "reports-b")
    outputs = []
    for root in roots:
        result = run_renderer(
            summary=incomplete_summary,
            output_root=root,
            quarto=quarto,
            execute=True,
        )
        assert result.returncode == 0, result.stderr
        outputs.append(expected_output(root, incomplete_summary))
    assert outputs[0].read_bytes() == outputs[1].read_bytes()


@pytest.mark.report_runtime
def test_real_pinned_quarto_rerender_is_self_contained_and_deterministic(
    incomplete_summary: Path,
    tmp_path: Path,
) -> None:
    quarto_value = os.environ.get("QUARTO_BIN")
    required = os.environ.get("NORAD_REQUIRE_QUARTO") == "1"
    if not quarto_value:
        if required:
            pytest.fail("NORAD_REQUIRE_QUARTO=1 but QUARTO_BIN is unset")
        pytest.skip("real pinned Quarto is not required for the normal pytest gate")
    quarto = Path(quarto_value)
    if not quarto.is_file():
        if required:
            pytest.fail(f"required Quarto executable is absent: {quarto}")
        pytest.skip("real pinned Quarto is unavailable")

    outputs = []
    bash_env_sentinel = tmp_path / "hostile-bash-env-ran"
    bash_env = tmp_path / "hostile-bash-env.sh"
    bash_env.write_text(
        f"#!/bin/sh\nprintf unsafe > {shlex.quote(str(bash_env_sentinel))}\n",
        encoding="utf-8",
    )
    for name in ("a", "b"):
        output_root = tmp_path / f"real-{name}"
        result = run_renderer(
            summary=incomplete_summary,
            output_root=output_root,
            quarto=quarto,
            execute=True,
            extra_env={
                "BASH_ENV": str(bash_env),
                "QUARTO_PROFILE": "undeclared-profile",
                "QUARTO_PANDOC": "/tmp/undeclared-pandoc",
            },
        )
        assert result.returncode == 0, result.stderr
        output = expected_output(output_root, incomplete_summary)
        RENDER.validate_rendered_html(
            output,
            expected_banner=RENDER.SCIENCE_BANNERS["evidence_incomplete"],
        )
        outputs.append(output)
    assert not bash_env_sentinel.exists()
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
