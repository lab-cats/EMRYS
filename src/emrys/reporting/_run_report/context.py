"""Generic admission and invocation for one two-view report transaction."""

from __future__ import annotations

import argparse
import copy
import importlib.metadata
import os
import re
import shlex
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from emrys import analyses
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.reporting import (
    AnalysisReportArtifactV1,
    AnalysisReportContextV1,
    AnalysisReportInputV1,
    AnalysisScientificReportV1,
    admit_analysis_reporter,
)
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_python_package_identity,
)
from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    SourceCheckoutError,
    matching_checkout_head_commit,
)

from .inputs import (
    _assert_input_recheck,
    _assert_snapshot,
    _explicit_path,
    _fail,
    _load_run_summary,
    _read_snapshot_bytes,
    _reject_symlink_components,
    _snapshot_regular,
)
from .models import (
    CSS_RESOURCE,
    HISTORICAL_REPORT_RECEIPT_SCHEMA_VERSION,
    HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION,
    JINJA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    REPORT_RECEIPT_SCHEMA_VERSION,
    RUN_SUMMARY_SCHEMA_VERSION,
    TEMPLATE_RESOURCE,
    FileSnapshot,
    ReportContext,
)
from .receipt import read_receipt_tsv
from .validation import render_html
from .view import build_evidence_view


@dataclass(frozen=True, slots=True)
class ReportIdentityOps:
    """Explicit source-provenance observation for focused tests."""

    matching_checkout_head_commit: Callable[..., str | None]


DEFAULT_REPORT_IDENTITY_OPS = ReportIdentityOps(
    matching_checkout_head_commit=matching_checkout_head_commit,
)


def _resource_snapshot(resource: str, label: str) -> FileSnapshot:
    return _snapshot_regular(
        Path(str(files("emrys.reporting").joinpath(resource))),
        label,
    )


def _core_renderer_sha256() -> str:
    try:
        package = installed_python_package_identity(Path(str(files("emrys.reporting"))))
    except (InstalledPackageIdentityError, OSError, TypeError) as exc:
        _fail(f"Could not identify the installed core reporting package: {exc}")
    return package.sha256


def _admit_analysis_policy(
    arguments: argparse.Namespace,
    summary: Mapping[str, object],
) -> tuple[Path | None, FileSnapshot | None, dict[str, object] | None]:
    value = getattr(arguments, "analysis_policy", None)
    version = str(summary["schema_version"])
    if value is None:
        if version == RUN_SUMMARY_SCHEMA_VERSION:
            _fail("Modular report publication requires an explicit analysis policy")
        return None, None, None
    path = _explicit_path(Path(value), "primary analysis policy")
    snapshot = _snapshot_regular(path, "primary analysis policy")
    payload = _read_snapshot_bytes(snapshot, "primary analysis policy")
    try:
        policy = orchestration_contracts.load_json_object_bytes(
            payload, "primary analysis policy"
        )
        if orchestration_contracts.canonical_json_bytes(policy) != payload:
            _fail("Primary analysis policy must use canonical JSON bytes")
        orchestration_contracts.validate_record("policy", policy)
    except orchestration_contracts.ContractValidationError as exc:
        _fail(f"Primary analysis policy is invalid: {exc}")
    contract = summary["run_contract"]
    if (
        snapshot.sha256 != contract["primary_analysis_policy_sha256"]
        or policy["analysis_id"] != contract["primary_analysis_id"]
    ):
        _fail("Primary analysis policy differs from the immutable run contract")
    modular = policy["schema_version"] == "emrys.analysis-module-policy.v1"
    if version == RUN_SUMMARY_SCHEMA_VERSION:
        binding = summary["analysis_policy"]
        if (
            not modular
            or binding != {
                "path": str(snapshot.path),
                "sha256": snapshot.sha256,
                "size_bytes": snapshot.size_bytes,
            }
        ):
            _fail("Modular run summary does not bind its exact analysis policy")
    elif modular:
        _fail("Run-summary v2 requires the built-in paired-CMH analysis policy")
    return snapshot.path, snapshot, policy


def _inspect_command(source_root: Path, output_root: Path) -> str:
    if output_root not in {
        source_root / "results" / "reports",
        source_root / "products" / "report",
    }:
        return "emrys inspect <RUN>"
    return shlex.join(
        ("emrys", "inspect", source_root.name, "--project", str(source_root.parent.parent / "project.yaml"))
    )


def expected_html_identity(
    context: ReportContext,
    report_view: Literal["scientific", "evidence"],
) -> dict[str, str]:
    identity = {
        "data-report-view": report_view,
        "data-run-id": context.summary["run_id"],
    }
    if report_view == "evidence":
        metadata = context.render_metadata
        identity.update(
            {
                "data-css-sha256": metadata["css_sha256"],
                "data-jinja-version": metadata["jinja_version"],
                "data-renderer-version": metadata["renderer_version"],
                "data-run-summary-sha256": metadata["run_summary_sha256"],
                "data-template-sha256": metadata["template_sha256"],
            }
        )
    return identity


def _admit_analysis_artifacts(
    summary: Mapping[str, object],
    module: analyses.LoadedAnalysisModuleV1,
    *,
    analysis_id: str,
    source_root: Path,
) -> tuple[tuple[AnalysisReportArtifactV1, ...], tuple[FileSnapshot, ...]]:
    declared = {
        artifact.adapter: (task.step_id, artifact)
        for task in module.descriptor.tasks
        for artifact in task.outputs
    }
    report_artifacts = []
    snapshots = []
    admitted_adapters: set[str] = set()
    for record in summary["artifacts"]:
        adapter = record["adapter"]
        if adapter not in declared:
            continue
        step_id, artifact = declared[adapter]
        scope = record["scope"]
        if (
            scope["step_id"] != step_id
            or scope["scope_type"] != "analysis"
            or scope["scope_id"] != analysis_id
        ):
            _fail(f"Analysis artifact has the wrong Step or scope: {adapter!r}")
        source = record["source"]
        admitted_status = (
            record["expectation"]["required"] is True
            and record["availability_status"] == "present"
            and record["completion_status"] == "complete"
        )
        if source is None or not admitted_status:
            continue
        expected_media_type = analyses.ANALYSIS_ARTIFACT_MEDIA_TYPES[artifact.kind]
        if adapter in admitted_adapters:
            _fail(f"Run summary repeats analysis artifact adapter: {adapter!r}")
        declared_path = Path(source["path"])
        path = (
            declared_path
            if declared_path.is_absolute()
            else source_root / declared_path
        )
        snapshot = _snapshot_regular(
            path,
            f"analysis artifact {record['artifact_id']!r}",
        )
        if (
            snapshot.sha256 != source["sha256"]
            or snapshot.size_bytes != source["size_bytes"]
            or source["media_type"] != expected_media_type
        ):
            _fail(
                "Analysis artifact differs from the admitted run summary: "
                f"{record['artifact_id']}"
            )
        admitted_adapters.add(adapter)
        snapshots.append(snapshot)
        report_artifacts.append(
            AnalysisReportArtifactV1(
                adapter=adapter,
                artifact_id=record["artifact_id"],
                path=snapshot.path,
                sha256=snapshot.sha256,
                size_bytes=snapshot.size_bytes,
                row_count=source["row_count"],
                kind=artifact.kind,
                media_type=expected_media_type,
            )
        )
    return tuple(report_artifacts), tuple(snapshots)


def _render_scientific_report(
    summary: dict[str, object],
    *,
    source_root: Path,
    output_dir: Path,
    analysis_policy: Mapping[str, object] | None,
) -> tuple[
    analyses.LoadedAnalysisModuleV1,
    Mapping[str, str],
    AnalysisScientificReportV1,
    tuple[AnalysisReportArtifactV1, ...],
    tuple[tuple[FileSnapshot, str, bool], ...],
]:
    policy = analysis_policy or {"schema_version": "emrys.analysis-policy.v1"}
    analysis_id = str(summary["run_contract"]["primary_analysis_id"])
    try:
        module = analyses.readmit_analysis_module(policy)
    except analyses.AnalysisModuleLoadError as exc:
        _fail(str(exc))
    reporter = admit_analysis_reporter(module.descriptor.module_id)
    report_artifacts, snapshots = _admit_analysis_artifacts(
        summary,
        module,
        analysis_id=analysis_id,
        source_root=source_root,
    )
    try:
        rendered = reporter.provider(
            AnalysisReportContextV1(
                run_id=summary["run_id"],
                analysis_id=analysis_id,
                module_id=module.descriptor.module_id,
                output_dir=output_dir,
                artifact_source_root=source_root,
                run_summary=copy.deepcopy(summary),
                artifacts=report_artifacts,
            )
        )
    except Exception as exc:
        _fail(f"Analysis scientific reporter failed: {exc}")
    if (
        not isinstance(rendered, AnalysisScientificReportV1)
        or not isinstance(rendered.html_bytes, bytes)
        or not rendered.html_bytes
        or not isinstance(rendered.interpretation_boundary, str)
        or rendered.interpretation_boundary.strip() != rendered.interpretation_boundary
        or not rendered.interpretation_boundary
        or any(
            len(item) != 2 or any(not isinstance(value, str) for value in item)
            for item in rendered.renderer_details
        )
        or any(
            len(row) != 8 or any(not isinstance(value, str) for value in row)
            for row in rendered.figure_evidence
        )
    ):
        _fail("Analysis reporter returned an invalid scientific report")
    returned_paths: set[Path] = set()
    returned_rechecks = []
    for item in rendered.inputs:
        if (
            not isinstance(item, AnalysisReportInputV1)
            or not item.label
            or not isinstance(item.path, Path)
            or not re.fullmatch(r"[0-9a-f]{64}", item.sha256)
            or not isinstance(item.rehash_content, bool)
        ):
            _fail("Analysis reporter returned an invalid input identity")
        path = item.path.absolute()
        if path in returned_paths:
            _fail(f"Analysis reporter returned a duplicate input: {path}")
        snapshot = _snapshot_regular(path, item.label)
        if snapshot.sha256 != item.sha256:
            _fail(f"Analysis reporter input changed while rendering: {path}")
        returned_paths.add(path)
        returned_rechecks.append((snapshot, item.label, item.rehash_content))
    returned_paths = {item[0].path for item in returned_rechecks}
    preadmitted = tuple(
        (snapshot, f"analysis artifact {snapshot.path.name!r}", True)
        for snapshot in snapshots
        if snapshot.path not in returned_paths
    )
    return (
        module,
        {
            "module_id": module.descriptor.module_id,
            "distribution_name": reporter.distribution_name,
            "distribution_version": reporter.distribution_version,
            "package": reporter.entry_point_value.partition(":")[0],
            "entry_point": reporter.entry_point_value,
            "content_sha256": reporter.package.sha256,
        },
        rendered,
        report_artifacts,
        (*preadmitted, *returned_rechecks),
    )


def _validate_output_root(output_root: Path, output_dir: Path) -> None:
    for path, label in (
        (output_root, "Report output root"),
        (output_dir, "Report output directory"),
    ):
        if os.path.lexists(path):
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                _fail(f"{label} must be a non-symlink directory: {path}")


def _existing_outputs(
    output_dir: Path,
    stable_paths: tuple[Path, ...],
    retired_paths: tuple[Path, ...],
    expected_receipt_version: str,
) -> dict[Path, FileSnapshot]:
    present = [
        path for path in (*stable_paths, *retired_paths) if os.path.lexists(path)
    ]
    if not present:
        return {}
    receipt_path = stable_paths[-1]
    if any(path in present for path in retired_paths) or not os.path.lexists(
        receipt_path
    ):
        _fail(
            "Existing report outputs are incomplete or retired; preserve them "
            "and use a fresh output root"
        )
    document = read_receipt_tsv(receipt_path)
    if document["schema_version"] != expected_receipt_version:
        _fail(
            "Existing report evidence uses another schema version and cannot "
            "be rewritten by this publisher"
        )
    snapshots: dict[Path, FileSnapshot] = {}
    for output in document["outputs"]:
        path = Path(output["path"])
        if path.parent != output_dir:
            _fail("Existing report receipt output is outside its run directory")
        snapshot = _snapshot_regular(path, f"existing {output['kind']} output")
        if (
            snapshot.sha256 != output["sha256"]
            or snapshot.size_bytes != output["size_bytes"]
        ):
            _fail(f"Existing report output does not match its receipt: {path}")
        snapshots[path] = snapshot
    snapshots[receipt_path] = _snapshot_regular(
        receipt_path,
        "existing report receipt",
    )
    if set(present) != set(snapshots):
        _fail("Existing report outputs differ from their receipt")
    return snapshots


def _result_links(
    artifacts: tuple[AnalysisReportArtifactV1, ...],
    output_dir: Path,
) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "label": f"Analysis artifact: {artifact.artifact_id}",
            "description": "Admitted analysis artifact",
            "href": quote(
                Path(os.path.relpath(artifact.path, start=output_dir)).as_posix(),
                safe="/._-",
            ),
        }
        for artifact in artifacts
        if artifact.kind != "validation_report"
    )


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
    identity_ops: ReportIdentityOps = DEFAULT_REPORT_IDENTITY_OPS,
) -> ReportContext:
    source_root = artifact_source_root.root
    run_summary_path = _explicit_path(arguments.run_summary, "run-summary path")
    run_summary_snapshot = _snapshot_regular(run_summary_path, "run-summary document")
    summary = _load_run_summary(run_summary_path, source_root=source_root)
    _assert_snapshot(run_summary_snapshot, "run-summary document")
    run_id = summary["run_id"]
    if (
        run_summary_path.name != f"{run_id}.run_summary.json"
        or run_summary_path.parent.name != run_id
    ):
        _fail("Canonical run-summary input must use <run-id>/<run-id>.run_summary.json")
    analysis_policy_path, analysis_policy_snapshot, analysis_policy = (
        _admit_analysis_policy(arguments, summary)
    )
    receipt_version = (
        REPORT_RECEIPT_SCHEMA_VERSION
        if summary["schema_version"] == RUN_SUMMARY_SCHEMA_VERSION
        else HISTORICAL_REPORT_RECEIPT_SCHEMA_VERSION
    )
    try:
        producer_git_commit = (
            identity_ops.matching_checkout_head_commit(
                source_checkout=source_checkout,
                package_root=Path(__file__).resolve().parents[2],
            )
            or "local_build"
        )
    except SourceCheckoutError as exc:
        _fail(str(exc))
    if importlib.metadata.version("Jinja2") != JINJA_VERSION:
        _fail(f"Installed Jinja2 version must match {JINJA_VERSION}")
    template_snapshot = _resource_snapshot(TEMPLATE_RESOURCE, "report Jinja template")
    css_snapshot = _resource_snapshot(CSS_RESOURCE, "report CSS resource")
    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_scientific_html = output_dir / f"{run_id}.scientific_report.html"
    output_evidence_html = output_dir / f"{run_id}.evidence_report.html"
    output_summary_tsv = output_dir / f"{run_id}.run_summary.tsv"
    output_receipt = output_dir / f"{run_id}.report_outputs.tsv"
    stable_paths = (
        output_scientific_html,
        output_evidence_html,
        output_summary_tsv,
        output_receipt,
    )
    retired_paths = (
        output_dir / f"{run_id}.run_report.html",
        output_dir / f"{run_id}.run_report.pdf",
    )
    lock_path = output_dir / f".{run_id}.report.lock"
    for path in (output_dir, *stable_paths, *retired_paths, lock_path):
        _reject_symlink_components(path, "report publication path")
    _validate_output_root(output_root, output_dir)
    if os.path.lexists(lock_path):
        _fail(f"Report publication lock already exists: {lock_path}")
    previous = _existing_outputs(
        output_dir,
        stable_paths,
        retired_paths,
        receipt_version,
    )
    (
        admitted_module,
        reporter,
        scientific_report,
        report_artifacts,
        report_input_rechecks,
    ) = _render_scientific_report(
        summary,
        source_root=source_root,
        output_dir=output_dir,
        analysis_policy=analysis_policy,
    )
    try:
        css = css_snapshot.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read report CSS resource: {exc}")
    metadata = {
        "css_path": f"emrys.reporting/{CSS_RESOURCE}",
        "css_sha256": css_snapshot.sha256,
        "jinja_version": JINJA_VERSION,
        "producer_git_commit": producer_git_commit,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "renderer_package_sha256": _core_renderer_sha256(),
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
        "state_banner": scientific_report.interpretation_boundary,
        "source_checkout": str(source_checkout.root),
        "artifact_source_root": str(artifact_source_root.root),
        "template_path": f"emrys.reporting/{TEMPLATE_RESOURCE}",
        "template_sha256": template_snapshot.sha256,
    }
    if summary["schema_version"] == HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION:
        renderer_details = dict(scientific_report.renderer_details)
        metadata.update(
            {
                "figure_renderer_version": renderer_details[
                    "Figure renderer"
                ].removeprefix("Matplotlib "),
                "logo_renderer_version": renderer_details[
                    "Logo renderer"
                ].removeprefix("Logomaker "),
                "figure_policy_version": renderer_details[
                    "Figure policy version"
                ],
            }
        )
    evidence_html_bytes = render_html(
        build_evidence_view(
            summary,
            metadata,
            banner=scientific_report.interpretation_boundary,
            result_links=_result_links(report_artifacts, output_dir),
            inspect_command=_inspect_command(source_root, output_root),
            analysis_policy=analysis_policy,
            renderer_details=scientific_report.renderer_details,
            figure_evidence=scientific_report.figure_evidence,
            report_inputs=tuple(
                (
                    item.label,
                    str(item.path),
                    item.sha256,
                    "content hash" if item.rehash_content else "file identity",
                )
                for item in scientific_report.inputs
                if item.path not in {artifact.path for artifact in report_artifacts}
            ),
        ),
        css,
    )
    context = ReportContext(
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        producer_git_commit=producer_git_commit,
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        analysis_policy_path=analysis_policy_path,
        analysis_policy_snapshot=analysis_policy_snapshot,
        analysis_policy=analysis_policy,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_scientific_html=output_scientific_html,
        output_evidence_html=output_evidence_html,
        output_summary_tsv=output_summary_tsv,
        output_receipt=output_receipt,
        lock_path=lock_path,
        stable_paths=stable_paths,
        previous_snapshots=previous,
        render_metadata=metadata,
        scientific_html_bytes=scientific_report.html_bytes,
        evidence_html_bytes=evidence_html_bytes,
        analysis_module=admitted_module,
        scientific_renderer=reporter,
        report_receipt_schema_version=receipt_version,
        report_input_rechecks=report_input_rechecks,
        interpretation_boundary=(
            str(summary["interpretation_boundary"])
            if summary["schema_version"] == HISTORICAL_RUN_SUMMARY_SCHEMA_VERSION
            else scientific_report.interpretation_boundary
        ),
    )
    for recheck in context.input_rechecks:
        _assert_input_recheck(*recheck)
    return context
