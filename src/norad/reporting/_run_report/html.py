"""Render one canonical NORAD run summary as a static report bundle.

The command is explicit-input-only and dry-run-first. It validates one
``norad.run_summary`` v1.1 document and may read only the TSVs explicitly
authorized by that document's ``approved_report_tables`` records. It never
discovers pipeline outputs, executes analysis code, installs software, or
promotes computational or scientific status.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.contracts.artifacts import validate_artifact_contracts as _contracts
from norad.reporting import _signals

from . import html_projection as _projection
from . import html_validation as _validation
from . import inputs as _inputs
from . import models as _models

ACTIVE_RESOURCE_ATTRIBUTES = _models.ACTIVE_RESOURCE_ATTRIBUTES
BODY_MARKER = _models.BODY_MARKER
CANDIDATE_TERMINOLOGY = _models.CANDIDATE_TERMINOLOGY
CSS_MARKER = _models.CSS_MARKER
CSS_RESOURCE_RE = _models.CSS_RESOURCE_RE
CSS_TEMPLATE = _models.CSS_TEMPLATE
EXECUTABLE_QMD_RE = _models.EXECUTABLE_QMD_RE
EXPECTED_QMD_BODY = _models.EXPECTED_QMD_BODY
EXPECTED_QMD_FRONTMATTER = _models.EXPECTED_QMD_FRONTMATTER
PRODUCER = _models.PRODUCER
PRODUCER_VERSION = _models.PRODUCER_VERSION
QMD_TEMPLATE = _models.QMD_TEMPLATE
QUARTO_VERSION = _models.QUARTO_VERSION
REMOTE_URI_RE = _models.REMOTE_URI_RE
REPORT_SECTION_IDS = _models.REPORT_SECTION_IDS
RUN_SUMMARY_SCHEMA_VERSION = _models.RUN_SUMMARY_SCHEMA_VERSION
SAFE_RENDER_PATH = _models.SAFE_RENDER_PATH
SCIENCE_BANNERS = _models.SCIENCE_BANNERS
ApprovedTable = _models.ApprovedTable
FileSnapshot = _models.FileSnapshot
LockOwnership = _models.LockOwnership
RenderContext = _models.RenderContext
ReportRenderError = _models.ReportRenderError
contracts = _contracts

_artifact_overview = _projection._artifact_overview
_category = _projection._category
_empty = _projection._empty
_escape = _projection._escape
_failed_scope_summary = _projection._failed_scope_summary
_fallback_render_metadata = _projection._fallback_render_metadata
_key_value_table = _projection._key_value_table
_render_approved_table = _projection._render_approved_table
_render_artifact_appendix = _projection._render_artifact_appendix
_render_attempt_lineage = _projection._render_attempt_lineage
_render_decisions = _projection._render_decisions
_render_evidence_categories = _projection._render_evidence_categories
_render_evidence_index = _projection._render_evidence_index
_render_input_artifacts = _projection._render_input_artifacts
_render_issues = _projection._render_issues
_render_json_block = _projection._render_json_block
_render_limitations = _projection._render_limitations
_render_qc_metrics = _projection._render_qc_metrics
_render_report_provenance = _projection._render_report_provenance
_render_rerun_implications = _projection._render_rerun_implications
_render_run_identity = _projection._render_run_identity
_render_science_methods = _projection._render_science_methods
_render_scope_matrix = _projection._render_scope_matrix
_render_status_panels = _projection._render_status_panels
_render_table_inventory = _projection._render_table_inventory
_render_tools = _projection._render_tools
_scientific_record = _projection._scientific_record
_section = _projection._section
_status = _projection._status
_status_class = _projection._status_class
_table = _projection._table
_tables_for_roles = _projection._tables_for_roles
build_report_body = _projection.build_report_body
_assert_snapshot = _inputs._assert_snapshot
_explicit_path = _inputs._explicit_path
_fail = _inputs._fail
_load_run_summary = _inputs._load_run_summary
_read_approved_table = _inputs._read_approved_table
_reject_symlink_components = _inputs._reject_symlink_components
_resolve_contract_file = _inputs._resolve_contract_file
_snapshot_regular = _inputs._snapshot_regular
ReportHTMLInspector = _validation.ReportHTMLInspector
_validate_css_resources = _validation._validate_css_resources
build_qmd_bytes = _validation.build_qmd_bytes
validate_qmd_template = _validation.validate_qmd_template
validate_rendered_html = _validation.validate_rendered_html


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one validated NORAD run-summary JSON as a static, "
            "self-contained HTML report. Dry-run is the default."
        )
    )
    parser.add_argument(
        "--run-summary",
        required=True,
        type=Path,
        help="Explicit canonical <run-id>.run_summary.json input.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--quarto-bin",
        required=True,
        type=Path,
        help=f"Explicit Quarto {QUARTO_VERSION} executable.",
    )
    parser.add_argument(
        "--formats",
        choices=("html", "pdf", "all"),
        default="all",
        help=(
            "Presentation format. The default all publishes HTML and PDF; "
            "every mode also publishes a deterministic summary TSV and "
            "receipt."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the validated HTML report. Omit for dry-run.",
    )
    return parser.parse_args(argv)


















def _sanitized_tool_environment() -> dict[str, str]:
    """Return the small ambient environment allowed for pinned report tools."""

    return {
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PATH": SAFE_RENDER_PATH,
        "TMPDIR": "/tmp",
        "TZ": "UTC",
    }


def _quarto_version(path: Path) -> str:
    try:
        result = subprocess.run(
            [str(path), "--version"],
            env=_sanitized_tool_environment(),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _fail(f"Could not execute {path} --version: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        _fail(f"Quarto version check failed: {detail}")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if lines != [QUARTO_VERSION]:
        _fail(
            f"Quarto reported {result.stdout.strip()!r}; expected exactly "
            f"{QUARTO_VERSION!r}"
        )
    return lines[0]












def _expected_html_identity(context: RenderContext) -> dict[str, str]:
    metadata = context.render_metadata
    return {
        "data-css-sha256": metadata["css_template_sha256"],
        "data-qmd-sha256": metadata["qmd_template_sha256"],
        "data-quarto-version": metadata["quarto_version"],
        "data-renderer-version": metadata["renderer_version"],
        "data-run-id": context.summary["run_id"],
        "data-run-summary-sha256": metadata["run_summary_sha256"],
    }


def prepare_context(arguments: argparse.Namespace) -> RenderContext:
    run_summary_path = _explicit_path(
        arguments.run_summary,
        "run-summary path",
    )
    run_summary_snapshot = _snapshot_regular(
        run_summary_path,
        "run-summary document",
    )
    summary = _load_run_summary(run_summary_path)
    _assert_snapshot(run_summary_snapshot, "run-summary document")
    run_id = summary["run_id"]
    expected_name = f"{run_id}.run_summary.json"
    if run_summary_path.name != expected_name or run_summary_path.parent.name != run_id:
        _fail(
            "Canonical run-summary input must use "
            f"<run-id>/{expected_name}; observed {run_summary_path}"
        )

    tables = tuple(
        _read_approved_table(record) for record in summary["approved_report_tables"]
    )
    template_snapshot = _snapshot_regular(
        QMD_TEMPLATE,
        "report QMD template",
    )
    css_snapshot = _snapshot_regular(
        CSS_TEMPLATE,
        "report CSS template",
    )
    quarto_path = _explicit_path(arguments.quarto_bin, "Quarto executable")
    quarto_snapshot = _snapshot_regular(
        quarto_path,
        "Quarto executable",
        executable=True,
    )
    _quarto_version(quarto_path)
    _assert_snapshot(quarto_snapshot, "Quarto executable")

    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_html = output_dir / f"{run_id}.run_report.html"
    lock_path = output_dir / f".{run_id}.report-html.lock"
    for path, label in (
        (output_dir, "report output directory"),
        (output_html, "report HTML output"),
        (lock_path, "report lock"),
    ):
        _reject_symlink_components(path, label)

    if os.path.lexists(output_root):
        metadata = output_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output root must be a non-symlink directory when it "
                f"exists: {output_root}"
            )
    if os.path.lexists(output_dir):
        metadata = output_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output directory must be a non-symlink directory when "
                f"it exists: {output_dir}"
            )
    previous_output_snapshot: FileSnapshot | None = None
    if os.path.lexists(output_html):
        metadata = output_html.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail(
                "Existing report output must be a regular non-symlink file: "
                f"{output_html}"
            )
        previous_output_snapshot = _snapshot_regular(
            output_html,
            "existing report output",
        )
        validate_rendered_html(
            output_html,
            expected_banner=None,
        )
        _assert_snapshot(
            previous_output_snapshot,
            "existing report output",
        )
    if os.path.lexists(lock_path):
        _fail(f"Report render lock already exists: {lock_path}")

    template_bytes = template_snapshot.path.read_bytes()
    css_bytes = css_snapshot.path.read_bytes()
    try:
        css_text = css_bytes.decode("utf-8")
    except UnicodeError as exc:
        _fail(f"Report CSS template is not UTF-8: {exc}")
    _validate_css_resources(css_text, "Report CSS template")
    render_metadata = {
        "css_template_path": str(css_snapshot.path),
        "css_template_sha256": css_snapshot.sha256,
        "qmd_template_path": str(template_snapshot.path),
        "qmd_template_sha256": template_snapshot.sha256,
        "quarto_path": str(quarto_snapshot.path),
        "quarto_sha256": quarto_snapshot.sha256,
        "quarto_version": QUARTO_VERSION,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
    }
    qmd_bytes = build_qmd_bytes(
        summary,
        tables,
        template_bytes=template_bytes,
        css_bytes=css_bytes,
        render_metadata=render_metadata,
    )
    for snapshot, label in (
        (run_summary_snapshot, "run-summary document"),
        (template_snapshot, "report QMD template"),
        (css_snapshot, "report CSS template"),
        (quarto_snapshot, "Quarto executable"),
    ):
        _assert_snapshot(snapshot, label)
    return RenderContext(
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        tables=tables,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        quarto_path=quarto_path,
        quarto_snapshot=quarto_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_html=output_html,
        lock_path=lock_path,
        previous_output_snapshot=previous_output_snapshot,
        render_metadata=render_metadata,
        qmd_bytes=qmd_bytes,
        execute=arguments.execute,
    )


def _create_directories(path: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while not os.path.lexists(current):
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent
    if os.path.lexists(current):
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(f"Report output ancestor is not a non-symlink directory: {current}")
    created: list[Path] = []
    try:
        for directory in reversed(missing):
            os.mkdir(directory, 0o755)
            created.append(directory)
    except OSError as exc:
        for directory in reversed(created):
            with contextlib.suppress(OSError):
                directory.rmdir()
        _fail(f"Could not create report output directory {path}: {exc}")
    _reject_symlink_components(path, "report output directory")
    return created


def _remove_empty_created_directories(created: Sequence[Path]) -> None:
    for directory in reversed(created):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            break


def _lock_payload(context: RenderContext, token: str) -> str:
    return (
        "owner\tNORAD_REPORT_HTML\n"
        f"pid\t{os.getpid()}\n"
        f"token\t{token}\n"
        f"run_id\t{context.summary['run_id']}\n"
        f"run_summary_sha256\t{context.run_summary_snapshot.sha256}\n"
    )


def _acquire_lock(context: RenderContext, token: str) -> LockOwnership:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(context.lock_path, flags, 0o600)
    except FileExistsError:
        _fail(f"Report render lock already exists: {context.lock_path}")
    except OSError as exc:
        _fail(f"Could not create report render lock {context.lock_path}: {exc}")
    metadata: os.stat_result | None = None
    try:
        metadata = os.fstat(descriptor)
        payload = _lock_payload(context, token).encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    except BaseException as original_exc:
        if metadata is None:
            try:
                metadata = os.fstat(descriptor)
            except OSError:
                metadata = None
        os.close(descriptor)
        try:
            if metadata is None:
                raise ReportRenderError("Could not capture owned report-lock identity")
            current = context.lock_path.lstat()
            if current.st_dev != metadata.st_dev or current.st_ino != metadata.st_ino:
                raise ReportRenderError(
                    "Report lock changed identity during interrupted "
                    f"acquisition: {context.lock_path}"
                )
            context.lock_path.unlink()
        except (OSError, ReportRenderError) as cleanup_exc:
            raise ReportRenderError(
                "Report lock acquisition was interrupted and owned cleanup "
                f"could not be proved: {cleanup_exc}"
            ) from original_exc
        raise
    os.close(descriptor)
    assert metadata is not None
    return LockOwnership(
        path=context.lock_path,
        token=token,
        device=metadata.st_dev,
        inode=metadata.st_ino,
    )


def _release_lock(ownership: LockOwnership) -> None:
    snapshot = _snapshot_regular(ownership.path, "owned report render lock")
    try:
        payload = ownership.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read owned report render lock: {exc}")
    if (
        snapshot.device != ownership.device
        or snapshot.inode != ownership.inode
        or f"token\t{ownership.token}\n" not in payload
    ):
        _fail(
            "Report render lock identity or ownership changed; refusing "
            f"cleanup: {ownership.path}"
        )
    ownership.path.unlink()


def _install_publication_signal_handlers() -> dict[int, Any]:
    return _signals.install(ReportRenderError, "Report", "report publication")


_restore_signal_handlers = _signals.restore


def _snapshot_at(snapshot: FileSnapshot, path: Path) -> FileSnapshot:
    return FileSnapshot(
        path=path,
        sha256=snapshot.sha256,
        device=snapshot.device,
        inode=snapshot.inode,
        size_bytes=snapshot.size_bytes,
        mtime_ns=snapshot.mtime_ns,
        ctime_ns=snapshot.ctime_ns,
    )


def _capture_moved_snapshot(
    path: Path,
    expected: FileSnapshot,
    label: str,
) -> FileSnapshot:
    current = _snapshot_regular(path, label)
    stable_identity = (
        current.device,
        current.inode,
        current.size_bytes,
        current.mtime_ns,
        current.sha256,
    )
    expected_identity = (
        expected.device,
        expected.inode,
        expected.size_bytes,
        expected.mtime_ns,
        expected.sha256,
    )
    if stable_identity != expected_identity:
        _fail(f"{label} changed identity or content during publication: {path}")
    return current


def _assert_predecessor(context: RenderContext) -> None:
    previous = context.previous_output_snapshot
    if previous is None:
        if os.path.lexists(context.output_html):
            _fail(
                "Report output appeared after initial validation; prepare a "
                f"fresh render context: {context.output_html}"
            )
        return
    _assert_snapshot(previous, "existing report output")
    validate_rendered_html(
        context.output_html,
        expected_banner=None,
    )
    _assert_snapshot(previous, "existing report output")


def _write_recovery_marker(path: Path, message: str) -> None:
    with contextlib.suppress(OSError, ReportRenderError):
        _write_owned_file(path, message.encode("utf-8"))


def _write_owned_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_owned_stage(
    path: Path,
    token: str,
    identity: tuple[int, int] | None,
) -> None:
    if not os.path.lexists(path):
        return
    metadata = path.lstat()
    if (
        token not in path.name
        or identity is None
        or (metadata.st_dev, metadata.st_ino) != identity
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(f"Refusing to remove unverified report staging path: {path}")
    shutil.rmtree(path)


def _recheck_inputs(context: RenderContext) -> None:
    labels = (
        "run-summary document",
        "report QMD template",
        "report CSS template",
        "Quarto executable",
        *(f"approved report table {table.table_id!r}" for table in context.tables),
    )
    for snapshot, label in zip(context.input_snapshots, labels):
        _assert_snapshot(snapshot, label)


def _source_date_epoch(summary: Mapping[str, Any]) -> str:
    value = summary["generated_at"]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # schema validation should make this unreachable
        _fail(f"Could not derive fixed report time from generated_at: {exc}")
    return str(int(parsed.timestamp()))


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Stop the complete Quarto process group and reap its direct process."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        if process.poll() is None:
            process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def _run_quarto_process(
    command: Sequence[str],
    stage: Path,
    environment: Mapping[str, str],
    fail: Callable[[str], NoReturn],
) -> tuple[int, str, str]:
    """Own the shared timeout and process-group lifecycle for Quarto renders."""
    print("Quarto render command:")
    print(f"  {shlex.join(command)}")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=stage,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process)
            fail(f"Quarto render exceeded the 300-second timeout: {exc}")
    except OSError as exc:
        if process is not None:
            _terminate_process_group(process)
        fail(f"Could not execute Quarto render: {exc}")
    except BaseException:
        if process is not None:
            _terminate_process_group(process)
        raise
    assert process is not None and process.returncode is not None
    if stdout.strip():
        print(stdout.rstrip())
    return process.returncode, stdout, stderr


def _render_with_quarto(
    context: RenderContext,
    stage: Path,
) -> Path:
    run_id = context.summary["run_id"]
    qmd_path = stage / f"{run_id}.run_report.qmd"
    output_name = f"{run_id}.run_report.html"
    output_path = stage / output_name
    project_path = stage / "_quarto.yml"
    _write_owned_file(qmd_path, context.qmd_bytes)
    project_bytes = (
        f"project:\n  type: default\n  render:\n    - {qmd_path.name}\n"
    ).encode()
    _write_owned_file(project_path, project_bytes)
    command = [
        str(context.quarto_path),
        "render",
        qmd_path.name,
        "--to",
        "html",
        "--output",
        output_name,
        "--no-execute",
    ]
    environment = _sanitized_tool_environment()
    environment["SOURCE_DATE_EPOCH"] = _source_date_epoch(context.summary)
    environment["DENO_DIR"] = str(stage / ".deno")
    runtime_tmp = stage / ".runtime-tmp"
    runtime_tmp.mkdir(mode=0o700)
    environment["TMPDIR"] = str(runtime_tmp)
    returncode, standard_output, standard_error = _run_quarto_process(
        command, stage, environment, _fail
    )
    if returncode != 0:
        detail = standard_error.strip() or standard_output.strip()
        _fail(f"Quarto render failed with exit {returncode}: {detail}")
    if standard_error.strip():
        print(standard_error.rstrip(), file=sys.stderr)
    for child in stage.iterdir():
        if child.is_dir() and child.name.endswith("_files"):
            _fail(
                "Quarto created a sidecar resource directory despite the "
                f"self-contained contract: {child}"
            )
    validate_rendered_html(
        output_path,
        expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
        expected_identity=_expected_html_identity(context),
    )
    return output_path


def publish_report(context: RenderContext) -> None:
    created = _create_directories(context.output_dir)
    output_dir_metadata = context.output_dir.lstat()
    output_dir_identity = (
        output_dir_metadata.st_dev,
        output_dir_metadata.st_ino,
    )
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.output_dir / f".run-report.{token}.tmp"
    backup = context.output_dir / f".{context.output_html.name}.{token}.previous"
    recovery = (
        context.output_dir
        / f".{context.summary['run_id']}.report-html.{token}.RECOVERY.txt"
    )
    ownership: LockOwnership | None = None
    previous_signal_handlers: dict[int, Any] | None = None
    backed_up = False
    published = False
    committed = False
    recovery_required = False
    output_identity_lost = False
    stage_identity: tuple[int, int] | None = None
    rendered_snapshot: FileSnapshot | None = None
    backup_snapshot: FileSnapshot | None = None
    published_snapshot: FileSnapshot | None = None

    def assert_output_dir_identity() -> None:
        if not os.path.lexists(context.output_dir):
            _fail(
                "Report output directory disappeared during publication: "
                f"{context.output_dir}"
            )
        metadata = context.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != output_dir_identity
        ):
            _fail(
                "Report output directory changed identity during publication: "
                f"{context.output_dir}"
            )

    try:
        previous_signal_handlers = _install_publication_signal_handlers()
        ownership = _acquire_lock(context, token)
        assert_output_dir_identity()
        _assert_predecessor(context)
        os.mkdir(stage, 0o700)
        stage_metadata = stage.lstat()
        stage_identity = (stage_metadata.st_dev, stage_metadata.st_ino)
        _recheck_inputs(context)
        rendered = _render_with_quarto(context, stage)
        rendered_snapshot = _snapshot_regular(
            rendered,
            "validated staged HTML report",
        )
        _fsync_file(rendered)
        _recheck_inputs(context)
        assert_output_dir_identity()
        _assert_predecessor(context)
        if os.path.lexists(backup):
            _fail(f"Report backup path unexpectedly exists: {backup}")
        if context.previous_output_snapshot is not None:
            backed_up = True
            os.link(
                context.output_html,
                backup,
                follow_symlinks=False,
            )
            backup_snapshot = _capture_moved_snapshot(
                backup,
                context.previous_output_snapshot,
                "backed-up prior HTML report",
            )
            _fsync_directory(context.output_dir)
            _capture_moved_snapshot(
                context.output_html,
                context.previous_output_snapshot,
                "existing report output",
            )
            context.output_html.unlink()
            _fsync_directory(context.output_dir)
        published = True
        os.link(
            rendered,
            context.output_html,
            follow_symlinks=False,
        )
        published_snapshot = _capture_moved_snapshot(
            context.output_html,
            rendered_snapshot,
            "newly published HTML report",
        )
        _fsync_file(context.output_html)
        _fsync_directory(context.output_dir)
        validate_rendered_html(
            context.output_html,
            expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
            expected_identity=_expected_html_identity(context),
        )
        _recheck_inputs(context)
        assert_output_dir_identity()
        committed = True
    except BaseException as original_exc:
        if committed:
            if isinstance(original_exc, ReportRenderError):
                raise
            if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise ReportRenderError(str(original_exc)) from original_exc
        rollback_errors: list[str] = []

        try:
            assert_output_dir_identity()
        except ReportRenderError as identity_exc:
            output_identity_lost = True
            recovery_required = True
            raise ReportRenderError(
                f"{original_exc}\nReport output directory identity changed "
                "during publication; path-based rollback was skipped to avoid "
                "modifying a replacement directory. Preserve the owned lock "
                f"and recovery state: {identity_exc}"
            ) from original_exc

        def rollback(label: str, operation: Any) -> None:
            nonlocal output_identity_lost
            try:
                assert_output_dir_identity()
            except ReportRenderError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")
                return
            try:
                operation()
                assert_output_dir_identity()
            except BaseException as rollback_exc:
                rollback_errors.append(f"{label}: {rollback_exc}")

        def remove_new_report() -> None:
            if not os.path.lexists(context.output_html):
                return
            if published_snapshot is None:
                if rendered_snapshot is None:
                    _fail(
                        "A final report exists but no owned staged report "
                        "snapshot was captured"
                    )
                _capture_moved_snapshot(
                    context.output_html,
                    rendered_snapshot,
                    "owned newly published HTML report",
                )
            else:
                _assert_snapshot(
                    published_snapshot,
                    "owned newly published HTML report",
                )
            context.output_html.unlink()

        def restore_prior_report() -> None:
            previous = context.previous_output_snapshot
            if previous is None:
                _fail("No prior report was declared for rollback")
            if os.path.lexists(backup):
                if backup_snapshot is None:
                    backup_snapshot_local = _capture_moved_snapshot(
                        backup,
                        previous,
                        "owned prior-report backup",
                    )
                else:
                    _assert_snapshot(
                        backup_snapshot,
                        "owned prior-report backup",
                    )
                    backup_snapshot_local = backup_snapshot
                if os.path.lexists(context.output_html):
                    _capture_moved_snapshot(
                        context.output_html,
                        previous,
                        "prior HTML report that remained during backup",
                    )
                    backup.unlink()
                    return
                os.link(
                    backup,
                    context.output_html,
                    follow_symlinks=False,
                )
                _capture_moved_snapshot(
                    context.output_html,
                    backup_snapshot_local,
                    "restored prior HTML report",
                )
                backup.unlink()
                return
            if os.path.lexists(context.output_html):
                _capture_moved_snapshot(
                    context.output_html,
                    previous,
                    "prior HTML report that remained in place",
                )
                return
            _fail(
                "Neither the validated prior report nor its owned backup "
                f"remains: {context.output_html}"
            )

        if published:
            rollback("remove owned new report", remove_new_report)
        if context.previous_output_snapshot is not None and backed_up:
            if not rollback_errors:
                rollback("restore validated prior report", restore_prior_report)
        elif context.previous_output_snapshot is not None:
            rollback(
                "verify prior report remained in place",
                restore_prior_report,
            )
        elif os.path.lexists(context.output_html):
            rollback(
                "remove unexpected first-publication output",
                remove_new_report,
            )
        if not rollback_errors:
            rollback(
                "durability-sync report rollback",
                lambda: _fsync_directory(context.output_dir),
            )
        if rollback_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML rollback was incomplete.\n"
                    f"Original error: {original_exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication failed and rollback was incomplete. "
                "Preserve the owned lock and recovery state under "
                f"{context.output_dir}. Rollback errors: " + "; ".join(rollback_errors)
            ) from original_exc
        backed_up = False
        published = False
        if isinstance(original_exc, ReportRenderError):
            raise
        if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise ReportRenderError(str(original_exc)) from original_exc
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required and not output_identity_lost:
            try:
                assert_output_dir_identity()
                _remove_owned_stage(stage, token, stage_identity)
            except Exception as exc:
                cleanup_errors.append(f"owned stage cleanup failed: {exc}")
            if not cleanup_errors and os.path.lexists(backup):
                try:
                    if not committed or backup_snapshot is None:
                        _fail("Unexpected report backup remains after rollback")
                    _assert_snapshot(
                        backup_snapshot,
                        "owned committed report backup",
                    )
                    backup.unlink()
                    _fsync_directory(context.output_dir)
                except Exception as exc:
                    cleanup_errors.append(f"owned backup cleanup failed: {exc}")
        if (
            ownership is not None
            and not recovery_required
            and not output_identity_lost
            and not cleanup_errors
        ):
            try:
                _release_lock(ownership)
            except Exception as exc:
                cleanup_errors.append(f"owned lock cleanup failed: {exc}")
        if previous_signal_handlers is not None:
            try:
                _restore_signal_handlers(previous_signal_handlers)
            except BaseException as exc:
                cleanup_errors.append(f"signal-handler restoration failed: {exc}")
        if cleanup_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML publication cleanup was incomplete.\n"
                    f"Active error: {active}\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication cleanup failed; preserve the owned lock "
                f"and recovery state under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active
        if (
            active is not None
            and not recovery_required
            and not os.path.lexists(context.output_html)
        ):
            _remove_empty_created_directories(created)


def print_plan(context: RenderContext) -> None:
    mode = "execute" if context.execute else "dry-run"
    print("NORAD static run-report plan:")
    print(f"  Mode: {mode}")
    print(f"  Run ID: {context.summary['run_id']}")
    print(f"  Run summary: {context.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.run_summary_snapshot.sha256}")
    print(f"  Science status: {context.summary['science_status']}")
    print(f"  State banner: {SCIENCE_BANNERS[context.summary['science_status']]}")
    print(f"  Approved report tables: {len(context.tables)}")
    for table in context.tables:
        print(
            f"    {table.table_id}: {table.path} "
            f"(rows={table.row_count}, display={table.displayed_row_count}, "
            f"sha256={table.sha256})"
        )
    print(f"  Quarto: {context.quarto_path}")
    print(f"  Quarto version: {QUARTO_VERSION}")
    print(f"  QMD template: {context.template_snapshot.path}")
    print(f"  CSS template: {context.css_snapshot.path}")
    print(f"  HTML output: {context.output_html}")
    print(
        "  Report meaning: rendering does not establish computational or "
        "scientific validation."
    )


def html_core_main(argv: Sequence[str] | None = None) -> int:
    """Run the established HTML core used by the bundle coordinator."""

    try:
        arguments = parse_arguments(argv)
        if arguments.formats != "html":
            _fail("The internal HTML core accepts only --formats html")
        context = prepare_context(arguments)
        print_plan(context)
        if context.execute:
            publish_report(context)
            print(f"Published self-contained HTML report: {context.output_html}")
        else:
            print(
                "Dry-run only. Add --execute to publish the HTML report; no "
                "output, lock, or scratch path was created."
            )
        return 0
    except ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the owner-private HTML-only entry point."""

    return html_core_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
