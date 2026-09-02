"""Public, report-only contracts and the EMRYS reporting implementation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, TypeAlias

from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    InstalledProviderV1,
    admit_installed_provider,
)
from emrys.reporting._files import FileSnapshot as ReportInputSnapshot

ANALYSIS_REPORTER_ENTRY_POINT_GROUP = "emrys.analysis_reporters"
JsonObject: TypeAlias = Mapping[str, object]


class AnalysisReportArtifactV1(NamedTuple):
    """One exact analysis artifact admitted for report-only use."""

    adapter: str
    artifact_id: str
    path: Path
    sha256: str
    size_bytes: int
    row_count: int | None
    kind: str
    media_type: str


class AnalysisReportInputV1(NamedTuple):
    """One report-provider input returned to the receipt-last recheck roster."""

    label: str
    path: Path
    sha256: str
    rehash_content: bool = True


class AnalysisReportContextV1(NamedTuple):
    """Copy-isolated report-time input supplied to an analysis reporter."""

    run_id: str
    analysis_id: str
    module_id: str
    output_dir: Path
    artifact_source_root: Path
    run_summary: JsonObject
    artifacts: tuple[AnalysisReportArtifactV1, ...]


class AnalysisScientificReportV1(NamedTuple):
    """One bespoke scientific view and its explicit interpretation boundary."""

    interpretation_boundary: str
    html_bytes: bytes
    inputs: tuple[AnalysisReportInputV1, ...] = ()
    renderer_details: tuple[tuple[str, str], ...] = ()
    figure_evidence: tuple[tuple[str, ...], ...] = ()


ScientificReporterV1: TypeAlias = Callable[
    [AnalysisReportContextV1], AnalysisScientificReportV1
]


class ReportProviderError(RuntimeError):
    """A scientific report provider rejected its admitted inputs or output."""


def admit_analysis_reporter(module_id: str) -> InstalledProviderV1:
    """Admit the one installed reporter registered for an analysis module."""

    try:
        return admit_installed_provider(
            ANALYSIS_REPORTER_ENTRY_POINT_GROUP,
            module_id,
            label="Analysis reporter",
        )
    except InstalledPackageIdentityError as exc:
        raise ReportProviderError(str(exc)) from exc


def fail_report_provider(message: str) -> NoReturn:
    raise ReportProviderError(message)


def admit_report_input(path: Path, label: str) -> ReportInputSnapshot:
    """Securely snapshot one report-only provider input."""

    from emrys.reporting._run_report.inputs import _snapshot_regular

    return _snapshot_regular(path, label)


def recheck_report_input(snapshot: ReportInputSnapshot, label: str) -> None:
    """Recheck an admitted provider input while constructing its scientific view."""

    from emrys.reporting._run_report.inputs import _assert_snapshot

    _assert_snapshot(snapshot, label)


def resolve_report_input(value: str, label: str, *, source_root: Path) -> Path:
    """Resolve one contract path through the reporting admission boundary."""

    from emrys.reporting._run_report.inputs import _resolve_contract_file

    return _resolve_contract_file(value, label, source_root=source_root)


def reporting_resource_path(resource: str) -> Path:
    """Return one installed core reporting resource for report-time support."""

    return Path(str(files("emrys.reporting").joinpath(resource)))


def render_report_view(view: Mapping[str, Any], css: str) -> bytes:
    """Render one provider-owned view through the installed core template."""

    from emrys.reporting._run_report.validation import render_html

    return render_html(view, css)
