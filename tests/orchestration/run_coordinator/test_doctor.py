"""Focused contracts for Project-aware Doctor diagnosis and repair."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import sys
from dataclasses import replace
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1
from emrys import reporting
from emrys.evidence.runtime_availability import inspector as runtime_inspector
from emrys.evidence.runtime_availability._probes import R_NAMESPACE_ROOT_OUTPUT_MARKER
from emrys.evidence.runtime_availability._profile_contract import CHOICE_IDS
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
)
from emrys.evidence.storage_inventory.qualification import QualifiedStorage
from emrys.libraries.application_logging import (
    ApplicationLogError,
    LogControls,
    helpers as log_helpers,
)
from emrys.orchestration.run_coordinator import doctor
from emrys.orchestration.run_coordinator.normalization import (
    ProjectAdmission,
    admit_project,
)
from tests.orchestration.run_coordinator import fixture


def _arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    doctor.configure_parser(parser)
    return parser.parse_args(argv)


def _project(tmp_path: Path) -> ProjectAdmission:
    root = tmp_path / "project"
    source = fixture.build(root)
    for name in ("logs", "runs", "runtime"):
        (root / name).mkdir(exist_ok=True)
    return admit_project(source, fixture.profile())


def _result(
    project: ProjectAdmission,
    *,
    ready: bool,
    inspection: RuntimeInspection | None = None,
) -> doctor.DoctorResult:
    return doctor.DoctorResult(
        project=project,
        analysis=project.select_analysis(),
        installed_package=doctor.admit_installed_package(),
        inspection=inspection,
        bindings=(),
        blockers=() if ready else ("runtime inventory is not admitted",),
        remediations=() if ready else ("Run `emrys doctor --repair`.",),
        storage_ready=True,
        runtime_ready=ready,
    )


def _patch_foundations(
    monkeypatch: pytest.MonkeyPatch,
    project: ProjectAdmission,
) -> QualifiedStorage:
    receipt = project.source_path.parent / "storage.tsv"
    receipt.write_bytes(b"qualified\n")
    qualified = QualifiedStorage(receipt, "b" * 64, "site-1")
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=project),
    )
    monkeypatch.setattr(
        doctor.storage_qualification,
        "admit_direct_requirement",
        lambda *_args, **_kwargs: qualified,
    )
    return qualified


def _check(
    check_id: str,
    check_type: str,
    target: str,
    *,
    resolved_path: Path | None = None,
) -> RuntimeObservation:
    return RuntimeObservation(
        check=RuntimeCheck(
            check_id=check_id,
            check_type=check_type,
            target=target,
            probe_args=(),
            expected=".*",
        ),
        status="pass",
        observed="1.0",
        detail="qualified",
        resolved_path=resolved_path,
    )


def _inspection(
    tmp_path: Path,
    observations: tuple[RuntimeObservation, ...] = (),
    *,
    profile: Path | None = None,
    profile_bytes: bytes = b"runtime profile\n",
) -> RuntimeInspection:
    return RuntimeInspection(
        profile_path=profile or tmp_path / "runtime.tsv",
        profile_sha256=hashlib.sha256(profile_bytes).hexdigest(),
        profile_bytes=profile_bytes,
        observations=observations,
    )


def _plan(project: ProjectAdmission) -> doctor._RepairPlan:
    managed = project.source_path.parent / "runtime/managed"
    return doctor._RepairPlan(
        project=project,
        analysis_name=project.select_analysis().name,
        installed_package=doctor.admit_installed_package(),
        storage=None,
        runtime=doctor._ManagedRuntimePlan(
            managed_root=managed,
            profile=project.source_path.parent / "runtime/runtime.tsv",
            pixi=Path("/managers/pixi"),
            pixi_sha256="c" * 64,
            profile_bytes=None,
            manifest_bytes=b'[workspace]\nname = "emrys"\n',
            lock_bytes=b"locked\n",
            r_settings_bytes=b"{}\n",
        ),
    )


def _runtime(plan: doctor._RepairPlan) -> doctor._ManagedRuntimePlan:
    assert plan.runtime is not None
    return plan.runtime


def _controls(project: ProjectAdmission) -> LogControls:
    return LogControls(
        False,
        project.source_path.parent / "logs/application",
        "default",
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _repair_log(
    project: ProjectAdmission, *, previous: Path | None = None
) -> tuple[Path, list[dict[str, Any]]]:
    (path,) = (
        path
        for path in (project.source_path.parent / "logs/application").glob(
            "**/emrys-doctor.jsonl"
        )
        if path != previous
    )
    return path, [json.loads(line) for line in path.read_text().splitlines()]


def test_runtime_identity_binds_executables_packages_and_storage(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "source"
    project_root.mkdir()
    library = tmp_path / "renv-library"
    package = library / "edgeR"
    package.mkdir(parents=True)
    (package / "DESCRIPTION").write_text(
        "Package: edgeR\nVersion: 4.0.0\n", encoding="utf-8"
    )
    observations = (
        _check("python", "tool_version", sys.executable),
        _check("snakemake", "tool_version", sys.executable),
        _check("renv_project", "path_visibility", str(project_root)),
        _check("renv_library", "path_visibility", str(library)),
        _check("r_edger", "r_namespace", "edgeR", resolved_path=package),
    )
    inspection = _inspection(tmp_path, observations)
    receipt = tmp_path / "storage.tsv"
    receipt.write_bytes(b"qualified\n")
    storage = doctor.storage_runtime_binding(
        QualifiedStorage(
            receipt, hashlib.sha256(receipt.read_bytes()).hexdigest(), "site-1"
        )
    )

    bindings = (*runtime_inspector.runtime_file_bindings(inspection), storage)
    identities = doctor.required_tool_identities(
        inspection,
        bindings=bindings,
        python_executable=Path(sys.executable),
    )

    by_name = {item["name"]: item for item in identities}
    assert set(by_name) == {
        "python",
        "renv_library",
        "renv_project",
        "r_edger",
        "runtime_profile",
        "snakemake",
        "storage_qualification",
    }
    assert by_name["python"]["sha256"] == by_name["snakemake"]["sha256"]
    assert by_name["r_edger"]["resolved_path"] == str(package)
    assert "identity_kind" not in by_name["r_edger"]
    assert by_name["storage_qualification"]["version"] == "site-1"
    assert (
        doctor.required_tool_identities(
            replace(
                inspection,
                observations=tuple(
                    replace(item, detail="version probe: elapsed_seconds=99.000")
                    for item in inspection.observations
                ),
            ),
            bindings=bindings,
            python_executable=Path(sys.executable),
        )
        == identities
    )


def test_selected_package_tree_dependency_is_composed_and_content_bound(
    tmp_path: Path,
) -> None:
    tool = tmp_path / "collaborator-tool"
    tool.write_bytes(b"tool\n")
    resource = tmp_path / "collaborator.dat"
    resource.write_bytes(b"resource\n")
    package = tmp_path / "collaborator-package"
    package.mkdir()
    (package / "model.dat").write_bytes(b"fixed model\n")
    renv_library = tmp_path / "renv-library"
    renv_library.mkdir()
    descriptor = replace(
        analysis_module_v1(),
        dependencies=(
            "python",
            analyses.AnalysisDependencyV1(
                "collaborator_tool", "executable", str(tool), ".*", ("--version",)
            ),
            analyses.AnalysisDependencyV1(
                "collaborator_r", "r_namespace", "Collaborator", ".*"
            ),
            analyses.AnalysisDependencyV1("collaborator_file", "file", str(resource)),
            analyses.AnalysisDependencyV1(
                "collaborator_assets",
                "package_tree",
                str(package),
                description="collaborator model assets",
            ),
        ),
    )
    rscript = tmp_path / "Rscript"
    additions, package_tree_ids, explicit_file_ids = doctor._module_dependency_checks(
        descriptor,
        (
            _check("python", "tool_version", sys.executable).check,
            _check("rscript", "tool_version", str(rscript)).check,
        ),
    )
    by_name = {check.check_id: check for check in additions}
    inspection = _inspection(
        tmp_path,
        (
            _check("renv_library", "path_visibility", str(renv_library)),
            RuntimeObservation(
                check=by_name["collaborator_assets"],
                status="pass",
                observed="readable",
                detail="qualified",
                resolved_path=package,
            ),
        ),
    )
    (binding,) = runtime_inspector.runtime_file_bindings(
        inspection,
        package_tree_ids=package_tree_ids,
    )

    assert tuple(check.check_id for check in additions) == (
        "collaborator_assets",
        "collaborator_file",
        "collaborator_r",
        "collaborator_tool",
    )
    assert by_name["collaborator_assets"].probe_args == ("directory_readable",)
    assert by_name["collaborator_file"].probe_args == ("file_readable",)
    assert by_name["collaborator_r"].probe_args == (str(rscript),)
    assert by_name["collaborator_tool"].check_type == "tool_version"
    assert package_tree_ids == {"collaborator_assets", "collaborator_r"}
    assert explicit_file_ids == {"collaborator_file", "collaborator_tool"}
    assert binding.identity_kind == "package_tree"
    assert (
        binding.sha256
        == runtime_inspector.installed_package_tree_identity(package).sha256
    )

    (file_binding,) = runtime_inspector.runtime_file_bindings(
        _inspection(
            tmp_path,
            (
                _check("renv_library", "path_visibility", str(renv_library)),
                _check("r_tool", "tool_version", str(tool)),
            ),
        ),
        explicit_file_ids=frozenset({"r_tool"}),
    )
    assert file_binding.identity_kind == "file"

    linked_tool = tmp_path / "linked-tool"
    linked_tool.symlink_to(tool)
    with pytest.raises(
        runtime_inspector.RuntimeInspectionError, match="canonical real file"
    ):
        runtime_inspector.runtime_file_bindings(
            _inspection(
                tmp_path,
                (
                    _check("renv_library", "path_visibility", str(renv_library)),
                    _check("r_tool", "tool_version", str(linked_tool)),
                ),
            ),
            explicit_file_ids=frozenset({"r_tool"}),
        )


def test_runtime_package_binding_rechecks_a_symlink_after_hashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = tmp_path / "renv-library"
    first = tmp_path / "edgeR-first"
    second = tmp_path / "edgeR-second"
    for package, version in ((first, "1.0"), (second, "2.0")):
        package.mkdir()
        (package / "DESCRIPTION").write_text(
            f"Package: edgeR\nVersion: {version}\n",
            encoding="utf-8",
        )
    library.mkdir()
    selected = library / "edgeR"
    selected.symlink_to(first, target_is_directory=True)
    real_identity = runtime_inspector.installed_package_tree_identity

    def retarget_after_hash(path: Path):
        identity = real_identity(path)
        selected.unlink()
        selected.symlink_to(second, target_is_directory=True)
        return identity

    monkeypatch.setattr(
        runtime_inspector,
        "installed_package_tree_identity",
        retarget_after_hash,
    )

    with pytest.raises(
        runtime_inspector.RuntimeInspectionError, match="package-tree root changed"
    ):
        runtime_inspector.runtime_file_bindings(
            _inspection(
                tmp_path,
                (
                    _check("renv_library", "path_visibility", str(library)),
                    _check(
                        "r_edger",
                        "r_namespace",
                        "edgeR",
                        resolved_path=first,
                    ),
                ),
            )
        )


def test_runtime_contract_allows_missing_but_refuses_symlinked_renv_library(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    real_library = tmp_path / "real-library"
    real_library.mkdir()
    linked_library = tmp_path / "linked-library"
    linked_library.symlink_to(real_library, target_is_directory=True)
    choices = {key: tmp_path / key for key in CHOICE_IDS}
    choices["renv_library"] = linked_library
    data = runtime_inspector.runtime_profile_bytes(choices)
    with pytest.raises(
        runtime_inspector.RuntimeInspectionError, match="canonical real directory"
    ):
        runtime_inspector.runtime_profile_checks(data, source)
    linked_library.unlink()
    runtime_inspector.runtime_profile_checks(data, source)


def test_absent_runtime_diagnosis_is_read_only_and_opens_no_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("diagnosis opened an application log"),
    )
    before = _snapshot(tmp_path)

    result = doctor.diagnose_project(project.source_path)

    assert not result.ready
    assert not result.runtime_ready
    assert result.inspection is None
    assert "runtime inventory is not admitted" in result.blockers[-1]
    assert (
        doctor.doctor_from_args(_arguments(["--project", str(project.source_path)]))
        == 1
    )
    output = capsys.readouterr().err
    assert "Runtime    NOT PREPARED" in output
    assert "Storage    PASS" in output
    assert "Execution  PASS" in output
    assert f"EXECUTION REQUIREMENT: {result.blockers[-1]}" in output
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("selection", (None, "named", "absolute"))
def test_doctor_selects_execution_profile_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    selection: str | None,
) -> None:
    from emrys.orchestration.run_coordinator import execution_profile

    project = _project(tmp_path)
    qualified = _patch_foundations(monkeypatch, project)
    monkeypatch.setattr(
        doctor.storage_qualification,
        "admit_final_qualification",
        lambda *_args: qualified,
    )
    selector = (
        str(tmp_path / "alternate.yaml") if selection == "absolute" else selection
    )
    path = execution_profile.project_execution_profile_path(
        project.source_path, selector
    )
    if selector is not None:
        path.write_bytes(execution_profile.project_default_profile_bytes("viking"))
    expected = execution_profile.load_execution_profile(path)
    observed: list[doctor.DoctorResult] = []
    diagnose = doctor.diagnose_project

    def inspect(*args: Any, **kwargs: Any) -> doctor.DoctorResult:
        result = diagnose(*args, **kwargs)
        observed.append(result)
        return result

    monkeypatch.setattr(doctor, "diagnose_project", inspect)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("diagnosis opened an application log"),
    )
    before = _snapshot(tmp_path)
    arguments = ["--project", str(project.source_path)]
    if selector is not None:
        arguments.extend(("--profile", selector))

    assert doctor.doctor_from_args(_arguments(arguments)) == 1

    (result,) = observed
    assert result.execution_profile == expected
    assert result.execution_ready and result.storage_ready
    assert expected.placement.kind == ("direct" if selection is None else "slurm")
    assert "Execution  PASS" in capsys.readouterr().err
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("selection", ("missing", "../escape", "invalid.yaml"))
def test_invalid_selected_execution_profile_does_not_fall_back_to_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    selection: str,
) -> None:
    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    before = _snapshot(tmp_path)

    assert (
        doctor.doctor_from_args(
            _arguments(["--project", str(project.source_path), "--profile", selection])
        )
        == 1
    )

    output = capsys.readouterr().err
    assert "Execution  NOT ADMITTED" in output
    assert "selected execution profile is not admitted" in output
    assert "Select a valid execution profile with --profile" in output
    assert (
        doctor.doctor_from_args(
            _arguments(
                [
                    "--project",
                    str(project.source_path),
                    "--profile",
                    selection,
                    "--repair",
                    "--execute",
                ]
            )
        )
        == 1
    )
    assert (
        "DOCTOR BLOCKED: Doctor preserves execution profiles; restore or select a valid profile with --profile"
        in capsys.readouterr().err
    )
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("state", ("malformed_default", "missing_explicit"))
def test_invalid_runtime_inventory_is_not_presented_as_initial_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    inventory = doctor.onboarding.runtime_profile_path(project.source_path)
    if state == "malformed_default":
        inventory.write_text("invalid inventory\n", encoding="utf-8")
    before = _snapshot(tmp_path)
    with pytest.raises(doctor.DoctorInputError):
        doctor.diagnose_project(
            project.source_path,
            runtime_inventory=inventory if state == "missing_explicit" else None,
        )
    assert _snapshot(tmp_path) == before


def test_existing_invalid_storage_evidence_is_not_assumed_to_be_fresh_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project(tmp_path)
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=project),
    )
    fasta = Path(
        str(project.select_analysis().workflow_inputs["reference"]["fasta"]["path"])
    )
    plan = doctor.storage_qualification.plan_direct_qualification(
        project.source_path.parent, fasta
    )
    plan.evidence_root.mkdir()
    plan.receipt_path.write_bytes(b"invalid existing receipt\n")
    before = _snapshot(tmp_path)
    result = doctor.diagnose_project(project.source_path)
    assert not result.storage_ready
    assert any(
        "Direct storage qualification receipt is not valid UTF-8 JSON" in blocker
        for blocker in result.blockers
    )
    doctor._print_result(result, False)
    output = capsys.readouterr().err
    assert "Storage    NOT QUALIFIED" in output
    assert "Storage    NOT PREPARED" not in output
    assert all(
        f"EXECUTION REQUIREMENT: {blocker}" in output for blocker in result.blockers
    )
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("state", ("missing", "malformed"))
def test_doctor_rejects_an_unusable_default_execution_profile_without_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
) -> None:
    project = _project(tmp_path)
    default = project.source_path.parent / "runtime/profiles/default.yaml"
    if state == "missing":
        default.unlink()
    else:
        default.write_text("not: [valid\n", encoding="utf-8")
    _patch_foundations(monkeypatch, project)
    before = _snapshot(tmp_path)

    result = doctor.diagnose_project(project.source_path)

    assert not result.ready
    assert not result.execution_ready
    assert "default execution profile is not admitted" in result.blockers[-1]
    with pytest.raises(doctor.DoctorRepairError, match="preserves execution profiles"):
        doctor._build_repair_plan(result)
    assert (
        doctor.doctor_from_args(
            _arguments(["--project", str(project.source_path), "--repair", "--execute"])
        )
        == 1
    )
    output = capsys.readouterr().err
    assert "Execution  NOT ADMITTED" in output
    assert "DOCTOR BLOCKED: Doctor preserves execution profiles" in output
    assert _snapshot(tmp_path) == before


def test_doctor_refuses_incompatible_reservation_before_planning_runtime_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from emrys.orchestration.run_coordinator.execution_profile import (
        project_default_profile_bytes,
    )

    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    profile = project.source_path.parent / "runtime/profiles/default.yaml"
    profile.write_bytes(
        project_default_profile_bytes("viking")
        .replace(b"cpus_per_task: node", b"cpus_per_task: 3")
        .replace(
            b"placement:",
            b'resources:\n  schema_version: emrys.local-pilot-resources.v1\n  stage_concurrency: {"01": 6}\n  step_threads: {"01": 2}\nplacement:',
        )
    )
    monkeypatch.setattr(
        doctor,
        "_manager",
        lambda *_args: pytest.fail(
            "invalid reservation reached runtime repair planning"
        ),
    )
    before = _snapshot(tmp_path)

    assert (
        doctor.doctor_from_args(
            _arguments(["--project", str(project.source_path), "--repair", "--execute"])
        )
        == 1
    )

    assert (
        "DOCTOR BLOCKED: Stage 01 concurrency x threads exceeds workflow cores: 6 x 2 > 3"
        in capsys.readouterr().err
    )
    assert _snapshot(tmp_path) == before


def test_doctor_derives_storage_requirement_from_the_default_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    requirements: list[str] = []
    monkeypatch.setattr(
        doctor,
        "load_execution_profile",
        lambda **_kwargs: SimpleNamespace(placement=SimpleNamespace(kind="slurm")),
    )

    qualified = _patch_foundations(monkeypatch, project)
    monkeypatch.setattr(
        doctor.storage_qualification,
        "admit_final_qualification",
        lambda *_args, **_kwargs: requirements.append("slurm") or qualified,
    )

    doctor.diagnose_project(project.source_path)

    assert requirements == ["slurm"]


def test_foundation_readiness_requires_reporter_only_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    monkeypatch.setattr(
        reporting,
        "admit_analysis_reporter",
        lambda _module_id: (_ for _ in ()).throw(
            reporting.ReportProviderError("not installed")
        ),
    )

    required = doctor.diagnose_project(
        project.source_path,
        require_reporter=True,
    )
    disabled = doctor.diagnose_project(
        project.source_path,
        require_reporter=False,
    )

    assert any("analysis reporter is not ready" in item for item in required.blockers)
    assert not any(
        "analysis reporter is not ready" in item for item in disabled.blockers
    )


@pytest.mark.parametrize("storage_ready", (False, True))
def test_runtime_diagnosis_preserves_combined_diagnostics_and_binding_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    storage_ready: bool,
) -> None:
    project = _project(tmp_path)
    qualified = _patch_foundations(monkeypatch, project)
    profile = doctor.onboarding.runtime_profile_path(project.source_path)
    choices = {key: tmp_path / key for key in CHOICE_IDS}
    choices["python"] = Path(sys.executable)
    profile.write_bytes(runtime_inspector.runtime_profile_bytes(choices))
    observations = (
        replace(
            _check("bash", "tool_version", "/bin/bash"),
            status="fail",
            observed="unavailable",
            detail="Executable was not found",
        ),
        replace(
            _check("python", "tool_version", sys.executable),
            detail='version probe: elapsed_seconds=0.125; loader "note"\n\x1b[31m',
        ),
        _check("renv_library", "path_visibility", str(tmp_path / "library")),
    )
    inspection = _inspection(tmp_path, observations, profile=profile)
    monkeypatch.setattr(
        doctor, "inspect_runtime_profile_bytes", lambda *_args, **_kwargs: inspection
    )
    runtime_remediation = (
        "Run `emrys doctor --repair` for an EMRYS-managed runtime, or repair "
        "and re-admit the selected site environment without editing runtime.tsv."
    )
    monkeypatch.setattr(
        doctor,
        "workspace_location_blockers",
        lambda *_args: (
            ["workspace diagnosis"],
            [runtime_remediation, runtime_remediation],
        ),
    )
    if not storage_ready:

        def unavailable_storage(*_args: object) -> None:
            raise doctor.storage_qualification.StorageQualificationError("unavailable")

        monkeypatch.setattr(
            doctor.storage_qualification,
            "admit_direct_requirement",
            unavailable_storage,
        )

    def unavailable_execution(**_kwargs: object) -> None:
        raise doctor.ExecutionProfileError("unavailable")

    monkeypatch.setattr(doctor, "load_execution_profile", unavailable_execution)
    before = _snapshot(tmp_path)

    result = doctor.diagnose_project(project.source_path, require_reporter=False)

    assert result.inspection is inspection
    assert (
        result.ready,
        result.storage_ready,
        result.runtime_ready,
        result.execution_ready,
    ) == (
        False,
        storage_ready,
        False,
        False,
    )
    assert result.blockers == (
        "workspace diagnosis",
        *(
            ("single-host storage is not qualified: unavailable",)
            if not storage_ready
            else ()
        ),
        "bash: fail (unavailable)",
        "default execution profile is not admitted: unavailable",
    )
    assert result.remediations == (
        runtime_remediation,
        *(
            ("Run `emrys doctor --repair` in the intended direct execution context.",)
            if not storage_ready
            else ()
        ),
        "Restore a valid Project-owned runtime/profiles/default.yaml; "
        "Doctor preserves operator execution policy.",
    )
    assert tuple(binding.check_id for binding in result.bindings) == (
        "python",
        *(("storage_qualification",) if storage_ready else ()),
    )
    assert result.bindings[0].path == Path(sys.executable)
    if storage_ready:
        assert result.bindings[-1] == doctor.storage_runtime_binding(qualified)
    assert _snapshot(tmp_path) == before
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("diagnosis opened an application log"),
    )
    for level in ("normal", "verbose"):
        assert (
            doctor.doctor_from_args(
                _arguments(
                    [
                        "--project",
                        str(project.source_path),
                        *(["--verbose"] if level == "verbose" else []),
                    ]
                )
            )
            == 1
        )
        output = capsys.readouterr().err
        assert "EXECUTION REQUIREMENT: bash: fail (unavailable)" in output
        assert "Runtime    CHECKS FAILED" in output
        assert "Runtime    NOT PREPARED" not in output
        assert f"Storage    {'PASS' if storage_ready else 'NOT QUALIFIED'}" in output
        assert "Execution  NOT ADMITTED" in output
        assert ('"expected": ".*"' in output) == (level != "normal")
        assert ("Executable was not found" in output) == (level != "normal")
        assert ("elapsed_seconds=0.125" in output) == (level != "normal")
        assert "\x1b[31m" not in output
        if level != "normal":
            prefix = "  'python': pass; "
            (packet,) = [
                line.removeprefix(prefix)
                for line in output.splitlines()
                if line.startswith(prefix)
            ]
            assert json.loads(packet) == {
                "observed": observations[1].observed,
                "detail": observations[1].detail,
            }
        assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("execute", "repair", "expected_status"),
    ((False, False, 1), (True, False, 2), (False, True, 1)),
)
@pytest.mark.parametrize(
    ("runtime_state", "operation", "runtime_work"),
    (
        (
            "verified",
            "verification",
            "Selected runtime passed current checks; no package-manager work is needed.",
        ),
        (
            "inventory_absent",
            "repair and verification",
            "Prepare a managed runtime inventory; package managers check any retained tools and caches.",
        ),
        (
            "inventory_retained",
            "repair and verification",
            "Check/update tools selected by the retained managed runtime inventory.",
        ),
    ),
)
def test_diagnosis_and_repair_preview_write_nothing_and_open_no_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    execute: bool,
    repair: bool,
    expected_status: int,
    runtime_state: str,
    operation: str,
    runtime_work: str,
) -> None:
    project = _project(tmp_path)
    result = _result(project, ready=False)
    plan = _plan(project)
    from emrys.orchestration.run_coordinator.execution_profile import (
        load_execution_profile,
    )

    plan = replace(plan, execution=load_execution_profile())
    runtime_required = runtime_state != "verified"
    if not runtime_required:
        plan = replace(plan, runtime=None)
        result = replace(
            result,
            runtime_ready=True,
            storage_ready=False,
            blockers=("storage is not qualified",),
        )
    else:
        runtime = _runtime(plan)
        cache = runtime.managed_root / "cache/pixi/retained-package"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"retained cache; usability not inferred\n")
        if runtime_state == "inventory_retained":
            plan = replace(
                plan, runtime=replace(runtime, profile_bytes=b"retained inventory\n")
            )
            runtime.profile.write_bytes(b"retained inventory\n")
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(doctor, "_build_repair_plan", lambda _result: plan)
    monkeypatch.setattr(
        doctor.sys,
        "stdin",
        SimpleNamespace(isatty=lambda: True, readline=lambda: "n\n"),
    )
    monkeypatch.setattr(doctor.sys.stderr, "isatty", lambda: True)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(
        doctor,
        "_execute_repair",
        lambda *_args, **_kwargs: pytest.fail("preview executed repair"),
    )
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("read-only path opened an application log"),
    )
    before = _snapshot(tmp_path)

    status = doctor.doctor_from_args(
        argparse.Namespace(
            project=project.source_path,
            analysis=None,
            verbose=False,
            log_root=None,
            repair=repair,
            execute=execute,
        )
    )

    assert status == expected_status
    assert _snapshot(tmp_path) == before
    output = capsys.readouterr()
    assert output.out == ""
    assert "Doctor invocation timing" not in output.err
    assert "Doctor phase timing" not in output.err
    assert ("Doctor elapsed:" in output.err) is repair
    if repair:
        assert f"EMRYS Doctor {operation} plan" in output.err
        assert "First Doctor setup can take 5–25 minutes." in output.err
        assert f"Runtime work: {runtime_work}" not in output.err
        assert "Package-manager output records" not in output.err
        assert "Execution placement: Direct" not in output.err
        assert "Workflow CPU ceiling:" not in output.err
        assert f"Apply this {operation} plan? [y/N]" in output.err
        assert f"{operation.capitalize()} preview complete" in output.err
        assert "Checks repeat because inputs" not in output.err
        assert "Checking/updating native tools and R" not in output.err
        assert "Checking/restoring R packages" not in output.err
        assert "Maintenance claim:" not in output.err


def test_invocation_timing_includes_confirmation_and_preserves_read_only_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project(tmp_path)
    result = _result(project, ready=False)
    elapsed = 10.0

    def diagnose(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        nonlocal elapsed
        elapsed += 1.25
        return result

    def readline() -> str:
        nonlocal elapsed
        elapsed += 7.5
        return "n\n"

    clock = SimpleNamespace(monotonic=lambda: elapsed)
    monkeypatch.setattr(doctor, "time", clock)
    monkeypatch.setattr(log_helpers, "time", clock)
    monkeypatch.setattr(doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(doctor, "_build_repair_plan", lambda _result: _plan(project))
    monkeypatch.setattr(
        doctor.sys, "stdin", SimpleNamespace(isatty=lambda: True, readline=readline)
    )
    monkeypatch.setattr(doctor.sys.stderr, "isatty", lambda: True)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("preview opened a log"),
    )
    before = _snapshot(tmp_path)
    assert (
        doctor.doctor_from_args(
            _arguments(
                [
                    "--project",
                    str(project.source_path),
                    "--repair",
                    "--verbose",
                ]
            )
        )
        == 1
    )
    output = capsys.readouterr().err
    assert (
        "Doctor phase timing (head/local): Inspecting the Project and runtime; complete; elapsed 1.250000s"
        in output
    )
    assert (
        "Doctor invocation timing (head/local, including operator confirmation time): elapsed 8.750000s; exit status 1"
        in output
    )
    assert (
        "Doctor elapsed: 8.750s including confirmation; slowest phase: "
        "Inspecting the Project and runtime (1.250s); exit 1" in output
    )
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "outcome",
    (
        "available",
        "failed",
        "cancelled",
        "unknown",
        "raises",
        "invalid",
        "no_identity",
        "interrupt",
    ),
)
def test_scheduler_timing_observation_is_optional_buffered_and_escaped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
) -> None:
    submission = doctor.slurm_submission.SlurmSubmission(
        argv=(),
        batch_script="",
        environment={},
        stdout_pattern=tmp_path / "maintenance-%j.out",
        stderr_pattern=tmp_path / "maintenance-%j.err",
        job_name="emrys-local-pilot",
    )
    timing = doctor._DoctorTiming()
    timing.detail = True
    elapsed = 0.0
    monkeypatch.setattr(log_helpers, "time", SimpleNamespace(monotonic=lambda: elapsed))
    queries = []
    interruption = KeyboardInterrupt("accounting interrupted")
    diagnostic = 'accounting "unavailable"\n\x1b[31m'
    state, exit_code = {
        "failed": ("FAILED", "7:0"),
        "cancelled": ("CANCELLED", "0:15"),
    }.get(outcome, ("COMPLETED", "0:0"))

    def observe(*args, **kwargs):
        nonlocal elapsed
        queries.append((args, kwargs))
        elapsed += 11.0
        if outcome == "interrupt":
            raise interruption
        if outcome == "raises":
            raise OSError(diagnostic)
        if outcome == "invalid":
            return None
        if outcome == "unknown":
            return doctor.scheduler_observation.unknown_observation(diagnostic)
        return {
            "state": state,
            "exit_code": exit_code,
            "terminal": True,
            "source": "sacct",
            "cluster": "fixture",
            "diagnostic": None,
            "timing_observed_at": "2026-09-15T12:00:00Z",
            "timing": {
                "submission_to_start_seconds": 120,
                "eligible_to_start_seconds": 90,
                "allocation_wall_seconds": 60,
            },
        }

    monkeypatch.setattr(doctor.scheduler_observation, "observe_job", observe)
    identity = None if outcome == "no_identity" else ("614999", "fixture")
    if outcome == "interrupt":
        with pytest.raises(KeyboardInterrupt) as caught:
            timing.observe_scheduler(submission, identity)
        assert caught.value is interruption
        assert timing.scheduler_timing is None
    else:
        timing.observe_scheduler(submission, identity)
    assert queries == (
        []
        if identity is None
        else [
            (
                (
                    "614999",
                    str(submission.stdout_pattern),
                    str(submission.stderr_pattern),
                    "fixture",
                ),
                {"job_name": submission.job_name, "include_timing": True},
            )
        ]
    )
    assert "Slurm accounting" not in capsys.readouterr().err
    records = []

    def record(name, message, **fields):
        records.append((name, fields))
        return True

    timing.flush(record)
    packet = [fields for name, fields in records if name == "doctor_scheduler_timing"]
    assert packet == ([] if outcome == "interrupt" else [timing.scheduler_timing])
    before = list(records)
    timing.flush(record)
    assert records == before
    timing.finish(16.0, 1)
    output = capsys.readouterr().err
    assert "elapsed 16.000000s; exit status 1" in output
    if outcome in {"available", "failed", "cancelled"}:
        assert (
            f"Slurm accounting observation: {state}; source: sacct; scheduler exit status: {exit_code}"
            in output
        )
        assert "eligible queue wait: 90s" in output
        assert "allocation wall time: 60s" in output
    elif outcome != "interrupt":
        assert (
            "Slurm accounting observation: UNKNOWN; source: unavailable; scheduler exit status: unavailable"
            in output
        )
        assert "eligible queue wait: unavailable" in output
        assert "allocation wall time: unavailable" in output
    else:
        assert "Slurm accounting" not in output
    if outcome in {"unknown", "raises"}:
        assert packet[0]["diagnostic"] == diagnostic
        assert r'accounting "unavailable"\n\x1b[31m' in output and "\x1b" not in output
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fault", ("none", "clock", "callback", "finish"))
@pytest.mark.parametrize("interrupted", (False, True))
def test_failed_diagnosis_timing_cannot_replace_error_or_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fault: str,
    interrupted: bool,
) -> None:
    calls: list[str] = []
    original = KeyboardInterrupt("diagnosis interrupted")
    source = tmp_path / "project.yaml"
    source.write_text("input: refused\n", encoding="utf-8")

    def diagnose(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        calls.append("diagnose")
        if interrupted:
            raise original
        raise doctor.DoctorInputError("input refused")

    def failed_telemetry(*_args: object) -> None:
        raise OSError("telemetry unavailable")

    monkeypatch.setattr(doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("failed diagnosis opened a log"),
    )
    if fault == "clock":
        clock = SimpleNamespace(monotonic=failed_telemetry)
        monkeypatch.setattr(doctor, "time", clock)
        monkeypatch.setattr(log_helpers, "time", clock)
    elif fault == "callback":
        monkeypatch.setattr(doctor._DoctorTiming, "observe", failed_telemetry)
    elif fault == "finish":
        monkeypatch.setattr(doctor._DoctorTiming, "finish", failed_telemetry)
    arguments = _arguments(["--project", str(source), "--verbose"])
    before = _snapshot(tmp_path)
    if interrupted:
        with pytest.raises(KeyboardInterrupt) as failure:
            doctor.doctor_from_args(arguments)
        assert failure.value is original
    else:
        assert doctor.doctor_from_args(arguments) == 2
    output = capsys.readouterr().err
    assert calls == ["diagnose"]
    assert _snapshot(tmp_path) == before
    if fault != "finish":
        assert "Doctor invocation timing" in output
        assert ("interrupted or failed" if interrupted else "exit status 2") in output
    if fault == "clock":
        assert "elapsed unavailable" in output


def test_diagnosis_resolves_shared_log_controls_without_opening_a_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    result = _result(project, ready=True)
    observed: list[dict[str, object]] = []
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(
        doctor,
        "resolve_log_controls",
        lambda **kwargs: observed.append(kwargs) or _controls(project),
    )
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("diagnosis opened an application log"),
    )

    status = doctor.doctor_from_args(
        argparse.Namespace(
            project=project.source_path,
            analysis=None,
            verbose=True,
            log_root=tmp_path / "selected-logs",
            repair=False,
            execute=False,
        )
    )

    assert status == 0
    assert observed[0]["verbose"] is True
    assert observed[0]["cli_root"] == tmp_path / "selected-logs"


def test_repair_refuses_a_site_owned_runtime_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    external = tmp_path / "site/bin/star"
    external.parent.mkdir(parents=True)
    external.write_bytes(b"tool\n")
    result = _result(
        project,
        ready=False,
        inspection=_inspection(
            tmp_path,
            (_check("star", "tool_version", str(external)),),
        ),
    )
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(doctor, "_manager", lambda name: Path(f"/manager/{name}"))
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: "d" * 64)
    before = _snapshot(tmp_path)

    with pytest.raises(doctor.DoctorRepairError, match="site- or user-owned"):
        doctor._build_repair_plan(result)

    assert _snapshot(tmp_path) == before


def test_managed_repair_accepts_missing_library_and_binds_base_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    profile = project.source_path.parent / "runtime/runtime.tsv"
    base_bytes = b"fixed managed profile\n"
    profile.write_bytes(base_bytes)
    tool = tmp_path / "collaborator-tool"
    tool.write_bytes(b"tool\n")
    python_check = _check("python", "tool_version", sys.executable)
    missing_library = project.source_path.parent / "runtime/managed/renv/library"
    renv_check = _check("renv_library", "path_visibility", str(missing_library))
    dependency_check = _check("collaborator_tool", "tool_version", str(tool))
    result = _result(
        project,
        ready=False,
        inspection=_inspection(
            tmp_path,
            (python_check, dependency_check),
            profile=profile,
            profile_bytes=b"fixed managed profile\nderived module check\n",
        ),
    )
    descriptor = replace(
        result.analysis.module.descriptor,
        dependencies=(
            analyses.AnalysisDependencyV1(
                "collaborator_tool",
                "executable",
                str(tool),
                ".*",
                ("--version",),
            ),
        ),
    )
    result = replace(
        result,
        analysis=replace(
            result.analysis,
            module=replace(result.analysis.module, descriptor=descriptor),
        ),
    )
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(doctor, "_manager", lambda name: Path(f"/manager/{name}"))
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: "d" * 64)
    monkeypatch.setattr(
        doctor,
        "load_runtime_profile_contract",
        lambda _path, _root: (base_bytes, (python_check.check, renv_check.check)),
    )

    plan = doctor._build_repair_plan(result)

    assert plan.runtime is not None
    assert plan.runtime.profile_bytes == base_bytes
    assert not missing_library.exists()


def test_retained_maintenance_claim_blocks_repair_but_not_verification_planning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    claim = project.source_path.parent / "runtime/maintenance.lock"
    claim.write_bytes(b"interrupted owner\n")
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        doctor, "_manager", lambda _name: pytest.fail("existing claim admitted manager")
    )
    before = _snapshot(tmp_path)
    with pytest.raises(doctor.DoctorRepairError, match="claim already exists"):
        doctor._build_repair_plan(_result(project, ready=False))
    plan = doctor._build_repair_plan(_result(project, ready=True))
    assert plan.runtime is None
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("check_id", ("collaborator_tool", "snakemake"))
def test_managed_repair_refuses_external_dependency_installation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_id: str,
) -> None:
    project = _project(tmp_path)
    missing = replace(
        _check(check_id, "tool_version", str(tmp_path / "tool")),
        status="fail",
        observed="missing",
    )
    result = _result(
        project,
        ready=False,
        inspection=_inspection(tmp_path, (missing,)),
    )
    descriptor = replace(
        result.analysis.module.descriptor,
        dependencies=(
            analyses.AnalysisDependencyV1(
                "collaborator_tool",
                "executable",
                str(tmp_path / "tool"),
                ".*",
                ("--version",),
            ),
        ),
    )
    result = replace(
        result,
        analysis=replace(
            result.analysis,
            module=replace(result.analysis.module, descriptor=descriptor),
        ),
    )

    with pytest.raises(doctor.DoctorRepairError, match="package manager"):
        doctor._build_repair_plan(result)

    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(doctor, "_manager", lambda name: Path(f"/manager/{name}"))
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: "d" * 64)

    bootstrap = doctor._build_repair_plan(replace(result, inspection=None))

    assert bootstrap.runtime is not None
    assert bootstrap.runtime.profile_bytes is None


def test_storage_only_repair_preserves_ready_site_runtime_and_skips_managers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from emrys.evidence.storage_inventory import qualification

    project = _project(tmp_path)
    profile = project.source_path.parent / "runtime/runtime.tsv"
    profile.write_bytes(b"site runtime\n")
    inspection = _inspection(
        tmp_path, profile=profile, profile_bytes=profile.read_bytes()
    )
    blocked = doctor.DoctorResult(
        project=project,
        analysis=project.select_analysis(),
        installed_package=doctor.admit_installed_package(),
        inspection=inspection,
        bindings=(),
        blockers=("single-host storage is not qualified",),
        remediations=("Run `emrys doctor --repair`.",),
        storage_ready=False,
        runtime_ready=True,
    )
    monkeypatch.setattr(
        doctor,
        "_manager",
        lambda _name: pytest.fail("storage-only repair admitted a package manager"),
    )
    monkeypatch.setattr(
        qualification,
        "_mount_identity",
        lambda path: {
            "mount_point": path.anchor,
            "filesystem_type": "test",
            "filesystem_source": "test",
        },
    )

    plan = doctor._build_repair_plan(blocked)

    assert plan.runtime is None
    assert plan.storage is not None
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    monkeypatch.setattr(
        doctor,
        "_repair_actions",
        lambda _plan: pytest.fail("storage-only repair planned a manager action"),
    )
    ready = replace(
        blocked,
        blockers=(),
        remediations=(),
        storage_ready=True,
    )

    def diagnose(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        assert profile.read_bytes() == b"site runtime\n"
        qualification.admit_direct_qualification(
            project.source_path.parent,
            Path(
                str(
                    project.select_analysis().workflow_inputs["reference"]["fasta"][
                        "path"
                    ]
                )
            ),
        )
        return ready

    monkeypatch.setattr(doctor, "diagnose_project", diagnose)

    assert doctor._execute_repair(plan, controls=_controls(project)) is ready
    assert not (project.source_path.parent / "runtime/maintenance.lock").exists()
    assert profile.read_bytes() == b"site runtime\n"
    assert records[0] == "opened"
    assert "terminal" in records
    _log_path, events = _repair_log(project)
    output = capsys.readouterr().err
    assert "Runtime work:" not in output
    started = next(
        item["fields"] for item in events if item["event"] == "repair_started"
    )
    assert (
        started["runtime_work"]
        == "Selected runtime passed current checks; no package-manager work is needed."
    )
    assert "package_output" not in started
    assert [
        (item["event"], item["message"])
        for item in events
        if item["phase"] == "terminal"
    ] == [("repair_requalified", "Project verification completed.")]


def test_repair_refuses_redirected_pixi_state(tmp_path: Path) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    runtime.managed_root.mkdir()
    external = tmp_path / "external-pixi"
    external.mkdir()
    (runtime.managed_root / ".pixi").symlink_to(external, target_is_directory=True)

    with pytest.raises(doctor.DoctorRepairError, match="Pixi state is not owned"):
        doctor._admit_managed_root(runtime)

    assert not (runtime.managed_root / "pixi.toml").exists()


def test_repair_isolates_and_refuses_pixi_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    runtime.managed_root.mkdir()
    config = runtime.managed_root / ".pixi/config.toml"
    config.parent.mkdir()
    config.write_text('detached-environments = "/tmp/external"\n', encoding="utf-8")

    with pytest.raises(doctor.DoctorRepairError, match="Pixi configuration"):
        doctor._admit_managed_root(runtime)

    config.unlink()
    monkeypatch.setenv("PIXI_HOME", "/tmp/external")
    monkeypatch.setenv("PIXI_CACHE_DETACHED_ENVIRONMENTS_DIR", "/tmp/external")
    pixi_environments = [
        environment
        for _label, argv, environment in doctor._repair_actions(plan)
        if Path(argv[0]).name == "pixi"
    ]
    assert pixi_environments
    assert all(
        environment["PIXI_NO_CONFIG"] == "1" for environment in pixi_environments
    )
    assert all(
        environment["PIXI_DISABLE_NETFS_REDIRECT"] == "1"
        for environment in pixi_environments
    )
    assert all("PIXI_HOME" not in environment for environment in pixi_environments)
    assert all(
        "PIXI_CACHE_DETACHED_ENVIRONMENTS_DIR" not in environment
        for environment in pixi_environments
    )
    assert pixi_environments[-1]["RENV_PROJECT"] == str(runtime.managed_root)
    assert pixi_environments[-1]["R_PROFILE_USER"] == str(
        plan.installed_package.root / ".Rprofile"
    )


def _patch_logging(
    monkeypatch: pytest.MonkeyPatch,
    plan: doctor._RepairPlan,
    records: list[str],
) -> None:
    monkeypatch.setattr(
        doctor,
        "_readmit_repair_plan",
        lambda _plan, **_kwargs: None,
    )

    real_open_log = doctor.open_attempt_log

    def observe(method: Any, name: str, **kwargs: object) -> object:
        records.append(name)
        return method(**kwargs)

    def open_log(**kwargs: Any) -> Any:
        if plan.runtime is not None:
            assert not plan.runtime.managed_root.exists(), (
                "repair mutated before opening its log"
            )
        if plan.storage is not None:
            assert not plan.storage.receipt_path.exists(), (
                "repair mutated before opening its log"
            )
        attempt = real_open_log(**kwargs)
        records.append("opened")
        for method, name in (
            ("terminal", "terminal"),
            ("fail", "failed"),
            ("interrupt_best_effort", "interrupted"),
            ("close", "closed"),
        ):
            monkeypatch.setattr(
                attempt, method, partial(observe, getattr(attempt, method), name)
            )
        return attempt

    monkeypatch.setattr(doctor, "open_attempt_log", open_log)


@pytest.mark.parametrize("log_error", (None, OSError))
@pytest.mark.parametrize("failed_readmission", (False, True))
def test_phase_timing_uses_only_open_maintenance_log_and_never_controls_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    log_error: type[Exception] | None,
    failed_readmission: bool,
) -> None:
    project = _project(tmp_path)
    plan = replace(_plan(project), runtime=None)
    inspection = _inspection(
        tmp_path, (_check("python", "tool_version", sys.executable),)
    )
    ready = _result(project, ready=True, inspection=inspection)
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    open_log = doctor.open_attempt_log
    log_attempts: list[str] = []

    def open_observed(**kwargs: Any) -> Any:
        attempt = open_log(**kwargs)
        write = attempt._write_record

        def record(entry: Any, **kwargs: Any) -> None:
            if entry.emrys_event == "doctor_phase_timing":
                log_attempts.append(entry.emrys_fields["phase_name"].value)
                if log_error is not None:
                    raise log_error("timing log unavailable")
            write(entry, **kwargs)

        monkeypatch.setattr(attempt, "_write_record", record)
        return attempt

    def readmit(*_args: object, **_kwargs: object) -> None:
        if failed_readmission:
            raise doctor.DoctorRepairError("readmission refused")

    monkeypatch.setattr(doctor, "open_attempt_log", open_observed)
    monkeypatch.setattr(doctor, "_readmit_repair_plan", readmit)
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: ready)
    timing = doctor._DoctorTiming()
    timing.observe("Inspecting the Project and runtime", 0.125, "complete")
    timing.observe_runtime(inspection, phase="diagnosis")
    assert records == [] and log_attempts == []
    if failed_readmission:
        with pytest.raises(doctor.DoctorRepairError, match="readmission refused"):
            doctor._execute_repair(plan, controls=_controls(project), timing=timing)
    else:
        assert (
            doctor._execute_repair(plan, controls=_controls(project), timing=timing)
            is ready
        )
    log_path, events = _repair_log(project)
    assert records[0] == "opened" and records[-1] == "closed"
    terminal = "failed" if failed_readmission else "terminal"
    assert (terminal in records) == (log_error is not OSError)
    expected_phases = [
        "Inspecting the Project and runtime",
        "Verifying the approved plan inputs",
        *([] if failed_readmission else ["Checking Project readiness"]),
    ]
    assert log_attempts == (
        expected_phases if log_error is None else expected_phases[:1]
    )
    assert timing.flushed
    before = log_path.read_bytes()
    timing.observe("after close", 0.5, "complete")
    timing.flush(lambda *_args, **_kwargs: pytest.fail("timing flush retried"))
    assert log_path.read_bytes() == before
    observations = [
        item["fields"] for item in events if item["event"] == "doctor_phase_timing"
    ]
    if log_error is not None:
        assert observations == []
    else:
        assert observations[0] == {
            "execution_context": "head/local",
            "phase_name": "Inspecting the Project and runtime",
            "elapsed_seconds": 0.125,
            "outcome": "complete",
        }
        assert observations[-1]["outcome"] == (
            "interrupted or failed" if failed_readmission else "complete"
        )
    assert [
        item["phase"] for item in events if item["event"] == "runtime_check_passed"
    ] == (
        []
        if log_error is not None
        else ["diagnosis", *([] if failed_readmission else ["project_readiness"])]
    )


@pytest.mark.parametrize("interrupted", (False, True))
def test_pass_observation_failure_does_not_replace_readiness_or_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupted: bool
) -> None:
    project = _project(tmp_path)
    result = _result(
        project,
        ready=True,
        inspection=_inspection(
            tmp_path, (_check("python", "tool_version", sys.executable),)
        ),
    )
    original = KeyboardInterrupt("probe observation interrupted")

    def fail_packet(*_args: object) -> dict[str, object]:
        raise original if interrupted else OSError("probe observation unavailable")

    monkeypatch.setattr(doctor, "_runtime_observation_fields", fail_packet)
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("diagnosis opened a log"),
    )
    arguments = _arguments(["--project", str(project.source_path)])
    before = _snapshot(tmp_path)
    if interrupted:
        with pytest.raises(KeyboardInterrupt) as failure:
            doctor.doctor_from_args(arguments)
        assert failure.value is original
    else:
        assert doctor.doctor_from_args(arguments) == 0
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("changed", ("profile", "package", "settings"))
def test_repair_readmission_rejects_changed_package_or_appeared_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=plan.project),
    )
    monkeypatch.setattr(
        doctor,
        "_file_sha256",
        lambda _path: runtime.pixi_sha256,
    )
    if changed == "profile":
        runtime.profile.write_bytes(b"unapproved\n")
    elif changed == "package":
        plan = replace(
            plan,
            installed_package=replace(plan.installed_package, content_sha256="0" * 64),
        )
    else:
        settings = runtime.managed_root / "renv/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_bytes(b"changed\n")

    with pytest.raises(
        doctor.DoctorRepairError,
        match="appeared after repair confirmation|changed before execution|settings changed",
    ):
        doctor._readmit_repair_plan(plan, before_storage=changed != "settings")


def test_repair_readmission_rejects_a_redirected_runtime_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    external = tmp_path / "external-runtime"
    external.mkdir()
    default_profile = runtime.managed_root.parent / "profiles/default.yaml"
    default_profile.unlink()
    default_profile.parent.rmdir()
    runtime.managed_root.parent.rmdir()
    runtime.managed_root.parent.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=plan.project),
    )

    with pytest.raises(doctor.DoctorRepairError, match="changed before execution"):
        doctor._readmit_repair_plan(plan, before_storage=True)

    assert not (external / "managed").exists()


@pytest.mark.parametrize(
    "timing_fault", (None, "write", "interrupt", "probe_write", "probe_interrupt")
)
@pytest.mark.parametrize("retained_inventory", (False, True))
def test_repair_delegates_to_managers_admits_profile_logs_and_requalifies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    timing_fault: str | None,
    retained_inventory: bool,
) -> None:
    from emrys.evidence.storage_inventory import qualification
    from emrys.libraries.application_logging import storage as log_storage

    project = _project(tmp_path)
    monkeypatch.setattr(
        qualification,
        "_mount_identity",
        lambda path: {
            "mount_point": path.anchor,
            "filesystem_type": "test",
            "filesystem_source": "test",
        },
    )
    plan = replace(
        _plan(project),
        storage=qualification.plan_direct_qualification(
            project.source_path.parent,
            Path(
                str(
                    project.select_analysis().workflow_inputs["reference"]["fasta"][
                        "path"
                    ]
                )
            ),
        ),
    )
    runtime = _runtime(plan)
    if retained_inventory:
        runtime = replace(runtime, profile_bytes=b"admitted runtime\n")
        plan = replace(plan, runtime=runtime)
        runtime.profile.write_bytes(runtime.profile_bytes)
    original_profile = runtime.profile.stat() if retained_inventory else None
    records: list[str] = []
    commands: list[tuple[str, ...]] = []
    _patch_logging(monkeypatch, plan, records)
    real_subprocess_run = doctor.subprocess.run

    def run_manager(argv: tuple[str, ...], **_kwargs: object) -> Any:
        if Path(argv[0]) == Path(sys.executable):
            return real_subprocess_run(argv, **_kwargs)
        assert (
            (runtime.managed_root.parent / "maintenance.lock")
            .read_bytes()
            .startswith(b"emrys-doctor:")
        )
        commands.append(tuple(argv))
        environment = _kwargs["env"]
        temporary = Path(environment["TMPDIR"])
        assert temporary.parent == runtime.managed_root / "cache" and temporary.is_dir()
        assert environment["NO_COLOR"] == "1"
        _kwargs["stdout"].write(b"package-manager output\n")
        if Path(argv[0]).name == "pixi" and "install" in argv:
            jar = (
                runtime.managed_root
                / ".pixi/envs/native/share/picard-slim-3.1.1-0/picard.jar"
            )
            jar.parent.mkdir(parents=True)
            jar.write_bytes(b"jar\n")
            rscript = runtime.managed_root / ".pixi/envs/r/bin/Rscript"
            rscript.parent.mkdir(parents=True)
            rscript.write_bytes(b"rscript\n")
        if "run" in argv:
            renv = (
                runtime.managed_root
                / "renv/library/R-4.6/x86_64-pc-linux-gnu/renv/DESCRIPTION"
            )
            renv.parent.mkdir(parents=True)
            renv.write_bytes(b"Package: renv\nVersion: 1.2.3\n")
        return SimpleNamespace(returncode=0)

    candidate = _inspection(
        tmp_path,
        (_check("python", "tool_version", sys.executable),),
        profile=runtime.profile,
        profile_bytes=b"admitted runtime\n",
    )
    discovery_calls: list[dict[str, object]] = []

    def discover(**kwargs: object) -> RuntimeInspection:
        discovery_calls.append(kwargs)
        return candidate

    final = _result(project, ready=True, inspection=candidate)
    requalified: list[Path] = []

    def diagnose(path: Path, **_kwargs: object) -> doctor.DoctorResult:
        assert runtime.profile.read_bytes() == candidate.profile_bytes
        requalified.append(path)
        return final

    monkeypatch.setattr(doctor.subprocess, "run", run_manager)
    monkeypatch.setattr(doctor.onboarding, "discover_runtime_profile", discover)
    monkeypatch.setattr(doctor, "diagnose_project", diagnose)
    write = log_storage._write
    timing_writes: list[str] = []
    timing_boundaries: list[tuple[int, tuple[Path, ...], bool]] = []
    probe_boundaries: list[tuple[int, tuple[Path, ...], bool]] = []
    original = KeyboardInterrupt("timing write interrupted")

    def write_observed(descriptor: int, payload: bytes) -> int:
        document = json.loads(payload)
        if document["event"] == "doctor_phase_timing":
            timing_writes.append(document["fields"]["phase_name"])
            timing_boundaries.append(
                (
                    len(commands),
                    tuple(requalified),
                    (runtime.managed_root.parent / "maintenance.lock").exists(),
                )
            )
            if timing_fault == "write":
                raise OSError(errno.ENOSPC, "timing write full")
            if timing_fault == "interrupt":
                raise original
        if document["event"] == "runtime_check_passed":
            probe_boundaries.append(
                (
                    len(commands),
                    tuple(requalified),
                    (runtime.managed_root.parent / "maintenance.lock").exists(),
                )
            )
            if timing_fault == "probe_write":
                raise OSError(errno.ENOSPC, "probe observation write full")
            if timing_fault == "probe_interrupt":
                raise original
        return write(descriptor, payload)

    monkeypatch.setattr(log_storage, "_write", write_observed)
    timing = doctor._DoctorTiming()
    if timing_fault in {"interrupt", "probe_interrupt"}:
        with pytest.raises(KeyboardInterrupt) as failure:
            doctor._execute_repair(plan, controls=_controls(project), timing=timing)
        assert failure.value is original
    else:
        assert (
            doctor._execute_repair(plan, controls=_controls(project), timing=timing)
            is final
        )

    assert timing.flushed
    assert not (runtime.managed_root.parent / "maintenance.lock").exists()
    assert [Path(argv[0]).name for argv in commands] == ["pixi", "pixi"]
    assert "install" in commands[0]
    assert "run" in commands[1] and "--environment" in commands[1]
    assert commands[1][-1].endswith("resources/runtime/restore_r_environment.R")
    assert discovery_calls[0]["environment"]["EMRYS_RENV_LIBRARY"].endswith(
        "R-4.6/x86_64-pc-linux-gnu"
    )
    assert discovery_calls[0]["project"] == project.source_path
    assert requalified == [project.source_path]
    assert plan.storage is not None
    qualification.admit_direct_qualification(
        plan.storage.workspace,
        plan.storage.reference_fasta,
    )
    assert runtime.profile.read_bytes() == b"admitted runtime\n"
    if original_profile is not None:
        assert runtime.profile.stat().st_ino == original_profile.st_ino
    assert records[0] == "opened"
    assert ("terminal" in records) == (timing_fault is None)
    assert ("interrupted" in records) == (
        timing_fault in {"interrupt", "probe_interrupt"}
    )
    assert records[-1] == "closed"
    assert not list((runtime.managed_root / "cache").glob("repair-*"))
    output = capsys.readouterr().err
    summary = (
        "Check/update tools selected by the retained managed runtime inventory."
        if retained_inventory
        else "Prepare a managed runtime inventory; package managers check any retained tools and caches."
    )
    assert f"Runtime work: {summary}" not in output
    assert "Package-manager output records" not in output
    assert "Checking/updating native tools and R" in output
    assert "Checking/restoring R packages" in output
    _log_path, events = _repair_log(project)
    started = next(
        item["fields"] for item in events if item["event"] == "repair_started"
    )
    assert started["runtime_work"].startswith(summary)
    assert started["package_output"] == str(_log_path.parent / "package-output.log")
    phases = [
        "Verifying the approved plan inputs",
        "Qualifying single-host storage",
        "Checking/updating native tools and R",
        "Checking/restoring R packages",
        "Discovering and verifying the installed runtime",
        "Checking Project readiness",
    ]
    phase_fault = timing_fault in {"write", "interrupt"}
    assert timing_writes == (phases[:1] if phase_fault else phases)
    assert timing_boundaries == [(2, (project.source_path,), False)] * len(
        timing_writes
    )
    assert [
        item["fields"]["phase_name"]
        for item in events
        if item["event"] == "doctor_phase_timing"
    ] == ([] if phase_fault else phases)
    assert probe_boundaries == [(2, (project.source_path,), False)] * (
        0 if phase_fault else 2 if timing_fault is None else 1
    )
    assert [
        item["phase"] for item in events if item["event"] == "runtime_check_passed"
    ] == (["runtime_discovery", "project_readiness"] if timing_fault is None else [])
    assert [
        (item["event"], item["message"])
        for item in events
        if item["phase"] == "terminal"
    ] == (
        [("repair_requalified", "Project repair and verification completed.")]
        if timing_fault is None
        else []
    )
    if timing_fault in {"interrupt", "probe_interrupt"}:
        assert events[-1]["event"] == "attempt_interrupted"
    assert (
        next(
            project.source_path.parent.glob("logs/application/**/package-output.log")
        ).read_bytes()
        == b"package-manager output\n" * 2
    )


@pytest.mark.parametrize("failed_check", ("star", "r_variant_annotation"))
def test_repair_retains_failed_candidate_probe_after_managers_succeed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failed_check: str,
) -> None:
    project = _project(tmp_path)
    _patch_foundations(monkeypatch, project)
    managed = project.source_path.parent / "runtime/managed"
    native = managed / ".pixi/envs/native/bin"
    library = managed / "renv/library/R-4.6/x86_64-pc-linux-gnu"
    pixi = tmp_path / "pixi"
    pixi.write_bytes(b"synthetic package manager\n")
    pixi.chmod(0o755)
    monkeypatch.setattr(doctor, "_manager", lambda _name: pixi)
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    namespaces = {
        item.target: item.expected.removeprefix("^")
        .removesuffix("$")
        .replace("[.]", ".")
        for item in runtime_inspector.load_runtime_policy()
        if item.check_type == "r_namespace"
    }
    versions = {
        "bash": "GNU bash, version 5.2",
        "STAR": "2.7.11b",
        "samtools": "samtools 1.19.2",
        "java": 'openjdk version "17.0.1"',
        "gatk": "The Genome Analysis Toolkit (GATK) v4.6.1.0",
        "bcftools": "bcftools 1.21",
        "infer_experiment.py": "infer_experiment.py 5.0.4",
        "gunzip": "gzip 1.12",
        "Rscript": "Rscript (R) version 4.6.1",
    }
    observed = 'loader: "libmissing.so" could not be loaded'
    commands: list[tuple[str, ...]] = []
    real_subprocess_run = doctor.subprocess.run

    def run(argv: list[str] | tuple[str, ...], **kwargs: Any) -> Any:
        executable = Path(argv[0])
        if executable == Path("/bin/sh"):
            assert tuple(argv) == ("/bin/sh", "-c", "command -v java")
            return real_subprocess_run(argv, **kwargs)
        if executable == pixi:
            commands.append(tuple(argv))
            kwargs["stdout"].write(b"package-manager succeeded\n")
            if "install" in argv:
                for command in doctor.onboarding.PATH_TOOL_COMMANDS.values():
                    path = native / command
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"synthetic native executable\n")
                    path.chmod(0o755)
                rscript = managed / ".pixi/envs/r/bin/Rscript"
                rscript.parent.mkdir(parents=True)
                rscript.write_bytes(b"synthetic R executable\n")
                rscript.chmod(0o755)
                jar = managed / ".pixi/envs/native/share/picard-slim-3.1.1-0/picard.jar"
                jar.parent.mkdir(parents=True)
                jar.write_bytes(b"synthetic jar\n")
            else:
                for name in ("renv", *namespaces):
                    package = library / name
                    package.mkdir(parents=True)
                    (package / "DESCRIPTION").write_text(f"Package: {name}\n")
            return SimpleNamespace(returncode=0)
        code = 0
        if executable == Path(sys.executable):
            output = (
                hashlib.sha256(kwargs["input"]).hexdigest()
                if kwargs.get("input") is not None
                else "9.25.1"
                if "snakemake" in argv
                else "Python 3.14.0"
            )
        elif executable.name == "Rscript" and "-e" in argv:
            package = argv[-2]
            output = (
                namespaces[package]
                + R_NAMESPACE_ROOT_OUTPUT_MARKER
                + str(library / package).encode().hex()
            )
            if (
                failed_check == "r_variant_annotation"
                and package == "VariantAnnotation"
            ):
                code, output = 42, observed
        elif "-jar" in argv:
            code, output = 1, "Version:3.1.1"
        else:
            output = versions[executable.name]
            if failed_check == "star" and executable.name == "STAR":
                code, output = 7, observed
        return SimpleNamespace(returncode=code, stdout=output.encode())

    monkeypatch.setattr(doctor.subprocess, "run", run)
    status = doctor.doctor_from_args(
        _arguments(["--project", str(project.source_path), "--repair", "--execute"])
    )

    assert status == 1
    assert len(commands) == 2 and "install" in commands[0] and "run" in commands[1]
    assert not (managed.parent / "runtime.tsv").exists()
    log_path, records = _repair_log(project)
    (failure,) = [item for item in records if item["event"] == "runtime_check_failed"]
    assert failure["phase"] == "runtime_discovery"
    fields = failure["fields"]
    assert fields["check_id"] == failed_check
    assert fields["target"] == (
        str(native / "STAR") if failed_check == "star" else "VariantAnnotation"
    )
    assert fields["status"] == "fail"
    assert fields["observed"] == observed
    assert (
        "exit_status=" + ("7" if failed_check == "star" else "42") in fields["detail"]
    )
    assert fields["expected"] == next(
        item.expected
        for item in runtime_inspector.load_runtime_policy()
        if item.check_id == failed_check
    )
    assert fields["host"] == doctor.platform.node()
    assert fields["inventory"] == str(managed.parent / "runtime.tsv")
    assert len(fields["inventory_sha256"]) == 64
    passes = [item for item in records if item["event"] == "runtime_check_passed"]
    assert passes and all(item["phase"] == "runtime_discovery" for item in passes)
    passed = {item["fields"]["check_id"]: item["fields"] for item in passes}
    assert failed_check not in passed
    assert "version probe: elapsed_seconds=" in passed["python"]["detail"]
    assert not any(item["event"] == "runtime_profile_admitted" for item in records)
    output = capsys.readouterr().err
    assert str(log_path) in output
    assert "REPAIR AND VERIFICATION FAILED:" in output


def test_repair_refuses_a_discovered_executable_symlink_outside_managed_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    runtime = _runtime(plan)
    external = tmp_path / "site/bin/STAR"
    external.parent.mkdir(parents=True)
    external.write_bytes(b"site tool\n")
    external.chmod(0o755)
    linked = runtime.managed_root / "bin/STAR"
    candidate = _inspection(
        tmp_path,
        (_check("star", "tool_version", str(linked)),),
        profile=runtime.profile,
        profile_bytes=b"escaped runtime\n",
    )
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)

    def discover(**_kwargs: object) -> RuntimeInspection:
        linked.parent.mkdir(parents=True)
        linked.symlink_to(external)
        return candidate

    monkeypatch.setattr(doctor, "_readmit_repair_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        doctor,
        "_admit_managed_root",
        lambda plan: (plan.managed_root / "cache").mkdir(parents=True),
    )
    monkeypatch.setattr(doctor, "_repair_actions", lambda _plan: ())
    monkeypatch.setattr(doctor, "_managed_discovery_environment", lambda _plan: {})
    monkeypatch.setattr(
        doctor.onboarding,
        "discover_runtime_profile",
        discover,
    )
    monkeypatch.setattr(
        doctor.onboarding,
        "publish_runtime_profile",
        lambda _candidate: pytest.fail("escaped runtime profile was published"),
    )

    with pytest.raises(doctor.DoctorRepairError, match="escaped"):
        doctor._execute_repair(plan, controls=_controls(project))

    assert not runtime.profile.exists()
    assert "failed" in records


@pytest.mark.parametrize(
    ("failure", "expected_record"),
    (("exit", "failed"), ("interrupt", "interrupted")),
)
def test_repair_records_manager_failure_or_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    expected_record: str,
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    runtime = _runtime(plan)
    records: list[str] = []
    real_open_log = doctor.open_attempt_log
    _patch_logging(monkeypatch, plan, records)
    manager_calls = 0

    def fail_manager(*_args: object, **_kwargs: object) -> Any:
        nonlocal manager_calls
        manager_calls += 1
        if failure == "interrupt":
            raise KeyboardInterrupt
        return SimpleNamespace(returncode=9)

    monkeypatch.setattr(doctor.subprocess, "run", fail_manager)

    expected = KeyboardInterrupt if failure == "interrupt" else doctor.DoctorRepairError
    with pytest.raises(expected):
        doctor._execute_repair(plan, controls=_controls(project))

    assert expected_record in records
    assert "terminal" not in records
    assert records[-1] == "closed"
    assert not runtime.profile.exists()
    claim = runtime.managed_root.parent / "maintenance.lock"
    retained = claim.read_bytes()
    assert retained.startswith(b"emrys-doctor:")
    monkeypatch.setattr(doctor, "open_attempt_log", real_open_log)
    with pytest.raises(doctor.DoctorRepairError, match="lock already exists"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert claim.read_bytes() == retained
    assert manager_calls == 1


def test_repair_records_failed_final_requalification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    candidate_bytes = b"admitted runtime\n"
    base = _plan(project)
    runtime = replace(_runtime(base), profile_bytes=candidate_bytes)
    plan = replace(base, runtime=runtime)
    runtime.profile.write_bytes(candidate_bytes)
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    monkeypatch.setattr(
        doctor,
        "_admit_managed_root",
        lambda plan: (plan.managed_root / "cache").mkdir(parents=True),
    )
    monkeypatch.setattr(doctor, "_repair_actions", lambda _plan: ())
    monkeypatch.setattr(doctor, "_managed_discovery_environment", lambda _plan: {})
    monkeypatch.setattr(
        doctor.onboarding,
        "discover_runtime_profile",
        lambda **_kwargs: _inspection(
            tmp_path,
            profile=runtime.profile,
            profile_bytes=candidate_bytes,
        ),
    )
    monkeypatch.setattr(
        doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: _result(project, ready=False),
    )

    with pytest.raises(doctor.DoctorRepairError, match="remained not ready"):
        doctor._execute_repair(plan, controls=_controls(project))

    assert "failed" in records
    assert "terminal" not in records
    assert records[-1] == "closed"
    assert (runtime.managed_root.parent / "maintenance.lock").exists()


def test_log_open_failure_prevents_the_first_repair_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    runtime = _runtime(plan)
    monkeypatch.setattr(
        doctor,
        "open_attempt_log",
        lambda **_kwargs: (_ for _ in ()).throw(
            ApplicationLogError("unavailable", stage="open", path=None)
        ),
    )

    with pytest.raises(doctor.DoctorRepairError, match="before mutation"):
        doctor._execute_repair(plan, controls=_controls(project))

    assert not runtime.managed_root.exists()
    assert not (runtime.managed_root.parent / "maintenance.lock").exists()


@pytest.mark.parametrize("parent_state", ("missing", "symlink"))
def test_repair_claim_refuses_unadmitted_runtime_parent_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, parent_state: str
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    parent = _runtime(plan).managed_root.parent
    saved = parent.with_name("saved-runtime")
    parent.rename(saved)
    if parent_state == "symlink":
        parent.symlink_to(saved, target_is_directory=True)
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    with pytest.raises(doctor.DoctorRepairError, match="runtime directory"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert not (saved / "maintenance.lock").exists()
    assert not (saved / "managed").exists()
    assert records == ["opened", "failed", "closed"]


def test_repair_success_cannot_release_a_replaced_maintenance_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    runtime = _runtime(plan)
    claim = runtime.managed_root.parent / "maintenance.lock"
    ready = _result(project, ready=True)
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    monkeypatch.setattr(doctor, "_repair_actions", lambda _plan: ())
    monkeypatch.setattr(doctor, "_managed_discovery_environment", lambda _plan: {})
    monkeypatch.setattr(
        doctor.onboarding,
        "discover_runtime_profile",
        lambda **_kwargs: _inspection(tmp_path, profile=runtime.profile),
    )

    def replace_claim(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        claim.rename(claim.with_suffix(".retained"))
        claim.write_bytes(b"another owner\n")
        return ready

    monkeypatch.setattr(doctor, "diagnose_project", replace_claim)
    with pytest.raises(doctor.DoctorRepairError, match="identity or content changed"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert claim.read_bytes() == b"another owner\n"
    assert records == ["opened", "failed", "closed"]


def test_failed_maintenance_claim_acquisition_retains_partial_before_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from emrys.libraries import exclusive_publication

    project = _project(tmp_path)
    plan = _plan(project)
    claim = _runtime(plan).managed_root.parent / "maintenance.lock"

    def fail_write(_descriptor: int, _payload: bytes) -> int:
        raise OSError("claim write failed")

    monkeypatch.setattr(exclusive_publication, "_write_durable", fail_write)
    monkeypatch.setattr(
        doctor,
        "_readmit_repair_plan",
        lambda *_args, **_kwargs: pytest.fail("failed acquisition applied repair"),
    )
    with pytest.raises(doctor.DoctorRepairError, match="claim write failed"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert claim.read_bytes() == b""
    assert not _runtime(plan).managed_root.exists()


def test_default_slurm_qualification_hides_submission_record_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "project/project.yaml"
    source.parent.mkdir()
    fasta = source.parent / "reference.fa"
    fasta.write_bytes(b">chr1\nA\n")
    plan = SimpleNamespace(
        project=SimpleNamespace(source_path=source),
        analysis_name="primary",
        execution=SimpleNamespace(source_path=tmp_path / "profile.yaml"),
        compute=False,
    )
    result = SimpleNamespace(
        analysis=SimpleNamespace(
            workflow_inputs={"reference": {"fasta": {"path": str(fasta)}}}
        )
    )
    submission = SimpleNamespace(
        stdout_pattern=tmp_path / "job-%j.out",
        stderr_pattern=tmp_path / "job-%j.err",
        job_name="emrys-fixture",
    )
    monkeypatch.setattr(doctor, "_qualification_binding", lambda _result: "binding")
    monkeypatch.setattr(
        doctor.slurm_submission, "plan_submission", lambda *_args, **_kwargs: submission
    )

    def reject(_submission: object, **kwargs: object) -> str:
        assert kwargs["show_details"] is False
        raise doctor.slurm_submission.SlurmSubmissionError("fixture rejection")

    monkeypatch.setattr(doctor.slurm_submission, "submit", reject)
    controls = LogControls(False, tmp_path / "logs", "default")
    attempt = SimpleNamespace(path=tmp_path / "logs/doctor.jsonl")
    with pytest.raises(
        doctor.slurm_submission.SlurmSubmissionError, match="fixture rejection"
    ):
        doctor._qualify_slurm(plan, result, attempt, controls)


@pytest.mark.parametrize(
    ("failure", "selection", "timing_outcome"),
    (
        (None, None, "available"),
        (None, "named", "available"),
        (None, "absolute", "available"),
        (None, None, "unknown"),
        (None, None, "raises"),
        ("scheduler", None, "available"),
        ("scheduler", None, "failed"),
        ("scheduler", None, "cancelled"),
        ("scheduler", None, "unknown"),
        ("scheduler", None, "raises"),
        ("scheduler_unconfirmed", None, "available"),
        ("scheduler_interrupt", None, "available"),
        ("runtime", None, "available"),
        ("startup", None, "available"),
        ("head_runtime", None, "available"),
        ("profile", None, "available"),
        ("finalize", None, "available"),
        ("execution_before", "named", "available"),
        ("execution_after", "absolute", "available"),
        ("execution_final", "named", "available"),
        ("head_final_error", None, "available"),
        ("head_final_io", None, "available"),
        ("final_project", None, "available"),
        ("final_package", None, "available"),
        ("final_inventory", None, "available"),
    ),
)
def test_head_doctor_qualifies_slurm_with_one_log_and_preserves_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str | None,
    selection: str | None,
    timing_outcome: str,
) -> None:
    from emrys.orchestration.run_coordinator import execution_profile, slurm_submission
    from tests.evidence.storage_inventory.test_storage_inventory import (
        synthetic_mount_identity,
    )

    project = _project(tmp_path)
    selector = (
        str(tmp_path / "alternate.yaml") if selection == "absolute" else selection
    )
    profile_path = execution_profile.project_execution_profile_path(
        project.source_path, selector
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_bytes(execution_profile.project_default_profile_bytes("viking"))
    execution = execution_profile.load_execution_profile(profile_path)
    inspection = _inspection(
        tmp_path, (_check("python", "tool_version", sys.executable),)
    )
    ready = replace(
        _result(project, ready=True, inspection=inspection), execution_profile=execution
    )
    fasta = Path(str(ready.analysis.workflow_inputs["reference"]["fasta"]["path"]))
    qualification = doctor.storage_qualification
    monkeypatch.setattr(qualification, "_mount_identity", synthetic_mount_identity)
    from emrys.orchestration.run_coordinator.resource_policy import AllocationCapacity

    monkeypatch.setattr(
        doctor, "observe_allocation", lambda: AllocationCapacity(256, 524288, "slurm")
    )
    state = {"compute": False, "probes": 0, "jobs": 0, "finalized": False}
    elapsed = 10.0
    clock = SimpleNamespace(monotonic=lambda: elapsed)
    monkeypatch.setattr(doctor, "time", clock)
    monkeypatch.setattr(log_helpers, "time", clock)
    failed_probe = replace(
        _check("star", "tool_version", str(tmp_path / "STAR")),
        status="fail",
        observed='loader: "missing"\nsecond line',
        detail="Version probe failed; exit_status=7; expected_exit_status=0",
    )
    if failure == "startup":
        failed_probe = replace(
            _check("snakemake", "tool_version", sys.executable),
            status="fail",
            observed="No username set in the environment",
            detail="Snakemake startup failed; exit_status=1; expected_exit_status=0",
        )
    run_compute = qualification._run_compute
    qualify_head = qualification.qualify_head
    selected_sources: list[object] = []
    submissions = []
    timing_queries = []

    def assert_timing_not_flushed() -> None:
        path = submissions[-1].stdout_pattern.parent / "emrys-doctor.jsonl"
        assert all(
            json.loads(line)["event"] != "doctor_scheduler_timing"
            for line in path.read_text().splitlines()
        )

    def finalize(*args: Path) -> QualifiedStorage:
        assert_timing_not_flushed()
        if failure == "finalize" and state["jobs"] == 1:
            raise KeyboardInterrupt
        if failure == "head_final_error":
            retained = next(
                (
                    project.source_path.parent.parent / qualification.EVIDENCE_DIRECTORY
                ).glob("*.compute.json")
            )
            probe_root = Path(
                json.loads(retained.read_text())["roots"][0]["probe_directory"]
            )
            (probe_root / "visible.bin").write_bytes(b"changed retained probe\n")
        qualified = qualify_head(*args)
        state["finalized"] = True
        if failure == "execution_final":
            profile_path.write_bytes(profile_path.read_bytes() + b"\n")
        return qualified

    unlink = Path.unlink

    def fail_cleanup(path: Path, *args: Any, **kwargs: Any) -> None:
        if (
            failure == "head_final_io"
            and not state["compute"]
            and path.name == "fsync-source.bin"
        ):
            raise OSError('head cleanup "denied"\n\x1b[31m')
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_cleanup)

    def probe(*args: Path) -> Path:
        state["probes"] += 1
        return run_compute(*args)

    def diagnose(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        selected_sources.append(_kwargs.get("execution_profile"))
        selected = execution_profile.load_execution_profile(
            execution_profile.project_execution_profile_path(
                project.source_path, _kwargs.get("execution_profile")
            )
        )
        if failure != "execution_final":
            assert selected == execution
        try:
            qualification.admit_final_qualification(project.source_path.parent, fasta)
        except qualification.StorageQualificationError:
            result = replace(
                ready, storage_ready=False, blockers=("storage is not site-qualified",)
            )
        else:
            result = ready
        if (state["compute"] and failure in {"runtime", "startup"}) or (
            not state["compute"] and state["jobs"] and failure == "head_runtime"
        ):
            result = replace(
                result,
                runtime_ready=False,
                inspection=replace(inspection, observations=(failed_probe,)),
            )
        if state["compute"] and failure == "profile":
            result = replace(
                result, inspection=replace(inspection, profile_sha256="f" * 64)
            )
        if state["finalized"]:
            if failure == "final_project":
                result = replace(
                    result,
                    project=replace(project, source_bytes=project.source_bytes + b"\n"),
                )
            elif failure == "final_package":
                result = replace(
                    result,
                    installed_package=replace(
                        ready.installed_package, content_sha256="d" * 64
                    ),
                )
            elif failure == "final_inventory":
                result = replace(
                    result, inspection=replace(inspection, profile_sha256="d" * 64)
                )
        return replace(result, execution_profile=selected)

    monkeypatch.setattr(qualification, "_run_compute", probe)
    monkeypatch.setattr(qualification, "qualify_head", finalize)
    monkeypatch.setattr(doctor, "diagnose_project", diagnose)
    arguments = _arguments(
        ["--project", str(project.source_path), "--repair", "--execute", "--verbose"]
        + (["--profile", selector] if selector is not None else [])
    )
    records: list[str] = []
    readmit = doctor._readmit_repair_plan
    _patch_logging(
        monkeypatch,
        doctor._build_repair_plan(diagnose(execution_profile=selector)),
        records,
    )
    selected_sources.clear()
    monkeypatch.setattr(doctor, "_readmit_repair_plan", readmit)
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=project),
    )
    if failure == "execution_before":
        open_log = doctor.open_attempt_log

        def drift_after_plan(**kwargs: Any) -> Any:
            attempt = open_log(**kwargs)
            profile_path.write_bytes(profile_path.read_bytes() + b"\n")
            return attempt

        monkeypatch.setattr(doctor, "open_attempt_log", drift_after_plan)
    plan_submission = slurm_submission.plan_submission
    delegate_argv: list[str] = []

    def plan_selected(*args: Any, **kwargs: Any) -> Any:
        delegate_argv[:] = kwargs["emrys_argv"]
        assert delegate_argv[delegate_argv.index("--profile") + 1] == str(profile_path)
        submission = plan_submission(*args, **kwargs)
        submissions.append(submission)
        return submission

    monkeypatch.setattr(slurm_submission, "plan_submission", plan_selected)

    def submit(submission: object, **kwargs: Any) -> str:
        nonlocal elapsed
        assert kwargs["wait"] is True
        assert kwargs["show_details"] is True
        assert kwargs["record_path"].name == "slurm-submit.stdout"
        state["jobs"] += 1
        elapsed += 5.0
        if failure == "scheduler_unconfirmed":
            raise slurm_submission.SlurmSubmissionError(
                "submission identity unavailable"
            )
        kwargs["on_submitted"]("614999", "fixture")
        assert "--compute" in submission.batch_script
        if failure == "scheduler_interrupt":
            raise KeyboardInterrupt
        if failure == "scheduler":
            raise slurm_submission.SlurmSubmissionError("sbatch failed with exit 1")
        with monkeypatch.context() as compute:
            compute.setenv("SLURM_JOB_ID", "614999")
            compute.setenv(
                slurm_submission.DELEGATE_MARKER_ENV, slurm_submission.DELEGATE_MARKER
            )
            compute.setenv(
                slurm_submission.PROFILE_SHA256_ENV, execution.binding_sha256
            )
            compute.setenv(slurm_submission.SUBMIT_UID_ENV, str(doctor.os.getuid()))
            compute_args = _arguments(
                delegate_argv[delegate_argv.index("doctor") + 1 :]
            )
            state["compute"] = True
            try:
                status = doctor.doctor_from_args(compute_args)
            finally:
                state["compute"] = False
        if status:
            raise slurm_submission.SlurmSubmissionError("compute qualification failed")
        if failure == "execution_after":
            profile_path.write_bytes(profile_path.read_bytes() + b"\n")
        return "614999"

    observe_job = doctor.scheduler_observation.observe_job
    scheduler_state, scheduler_exit = {
        "failed": ("FAILED", "7:0"),
        "cancelled": ("CANCELLED", "0:15"),
    }.get(timing_outcome, ("COMPLETED", "0:0"))
    accounting_queries = []

    def accounting_query(argv, **kwargs):
        accounting_queries.append(argv)
        submission = submissions[-1]
        assert argv[0] == "sacct" and "--clusters=fixture" in argv
        assert kwargs["environment"]["TZ"] == "UTC0"
        values = (
            "614999",
            str(doctor.os.getuid()),
            f"CANCELLED by {doctor.os.getuid()}"
            if scheduler_state == "CANCELLED"
            else scheduler_state,
            "fixture",
            str(submission.stdout_pattern).replace("%j", "614999"),
            str(submission.stderr_pattern).replace("%j", "614999"),
            scheduler_exit,
            submission.job_name,
            "2026-09-15T12:00:00Z",
            "2026-09-15T12:00:30Z",
            "2026-09-15T12:02:00Z",
            "2026-09-15T12:03:00Z",
            "60",
            "0",
            "00:00:00",
        )
        return ("|".join(values) + "\n").encode()

    monkeypatch.setattr(doctor.scheduler_observation, "command_bytes", accounting_query)

    def observe_timing(job_id, stdout, stderr, cluster, **kwargs):
        nonlocal elapsed
        assert not state["compute"]
        submission = submissions[-1]
        assert (job_id, stdout, stderr, cluster, kwargs) == (
            "614999",
            str(submission.stdout_pattern),
            str(submission.stderr_pattern),
            "fixture",
            {"job_name": submission.job_name, "include_timing": True},
        )
        timing_queries.append(job_id)
        assert_timing_not_flushed()
        elapsed += 11.0
        if timing_outcome == "raises":
            raise OSError('accounting "unavailable"\n\x1b[31m')
        if timing_outcome == "unknown":
            return doctor.scheduler_observation.unknown_observation(
                'accounting "unavailable"\n\x1b[31m'
            )
        return observe_job(job_id, stdout, stderr, cluster, **kwargs)

    monkeypatch.setattr(slurm_submission, "submit", submit)
    monkeypatch.setattr(doctor.scheduler_observation, "observe_job", observe_timing)
    expected_status = (
        0
        if failure is None
        else 130
        if failure in {"finalize", "scheduler_interrupt"}
        else 1
    )
    assert doctor.doctor_from_args(arguments) == expected_status
    assert records.count("opened") == 1
    output = capsys.readouterr().err
    log_path, events = _repair_log(project)
    timing_events = [
        item["fields"] for item in events if item["event"] == "doctor_phase_timing"
    ]
    assert timing_events[0]["phase_name"] == "Inspecting the Project and runtime"
    assert all(item["execution_context"] == "head/local" for item in timing_events)
    assert all(
        isinstance(item["elapsed_seconds"], float) and item["elapsed_seconds"] >= 0
        for item in timing_events
    )
    waits = [
        item
        for item in timing_events
        if item["phase_name"] == "Slurm submission-to-return wait"
    ]
    assert len(waits) == (1 if state["jobs"] else 0)
    if waits:
        assert waits[0]["elapsed_seconds"] == 5.0
    queried = state["jobs"] and failure not in {
        "scheduler_unconfirmed",
        "scheduler_interrupt",
    }
    assert timing_queries == (["614999"] if queried else [])
    assert len(accounting_queries) == (
        1 if queried and timing_outcome in {"available", "failed", "cancelled"} else 0
    )
    timing_reads = [
        item
        for item in timing_events
        if item["phase_name"] == "Reading recorded Slurm timing"
    ]
    assert [item["elapsed_seconds"] for item in timing_reads] == (
        [11.0] if queried else []
    )
    scheduler_events = [
        item for item in events if item["event"] == "doctor_scheduler_timing"
    ]
    assert len(scheduler_events) == (
        1 if state["jobs"] and failure != "scheduler_interrupt" else 0
    )
    if scheduler_events:
        observation = scheduler_events[0]
        assert observation["console_detail"] == "durable_only"
        assert events.index(observation) < len(events) - 1
        assert observation["fields"]["scheduler_job_id"] == (
            None if failure == "scheduler_unconfirmed" else "614999"
        )
        if queried and timing_outcome in {"available", "failed", "cancelled"}:
            assert observation["fields"]["timing"]["eligible_to_start_seconds"] == 90
            assert observation["fields"]["state"] == scheduler_state
            assert observation["fields"]["exit_code"] == scheduler_exit
            assert (
                f"Slurm accounting observation: {scheduler_state}; source: sacct; scheduler exit status: {scheduler_exit}"
                in output
            )
            assert "eligible queue wait: 90s" in output
        else:
            assert (
                "Slurm accounting observation: UNKNOWN; source: unavailable; scheduler exit status: unavailable"
                in output
            )
            assert "eligible queue wait: unavailable" in output
        if queried and timing_outcome in {"unknown", "raises"}:
            assert (
                'accounting "unavailable"\n\x1b[31m'
                == observation["fields"]["diagnostic"]
            )
            assert (
                r'accounting "unavailable"\n\x1b[31m' in output and "\x1b" not in output
            )
    if failure in {"scheduler", "scheduler_unconfirmed", "scheduler_interrupt"}:
        assert waits[0]["outcome"] == "interrupted or failed"
        assert not state["finalized"]
        assert "repair_requalified" not in {item["event"] for item in events}
        if failure == "scheduler":
            assert "sbatch failed with exit 1" in output
            assert str(log_path) in output and state["jobs"] == 1
        elif failure == "scheduler_interrupt":
            assert "Slurm accounting observation" not in output
    if failure is None:
        assert waits[0]["outcome"] == "complete"
        assert "Doctor invocation timing (delegated compute," in output
        passed = [item for item in events if item["event"] == "runtime_check_passed"]
        assert [item["phase"] for item in passed] == [
            "diagnosis",
            "project_readiness",
            "head_requalification",
            "head_final_readiness",
        ]
        for item in passed:
            assert item["fields"] == {
                "check_id": "python",
                "target": sys.executable,
                "status": "pass",
                "expected": ".*",
                "observed": "1.0",
                "detail": "qualified",
                "host": doctor.platform.node(),
                "inventory": str(inspection.profile_path),
                "inventory_sha256": inspection.profile_sha256,
                "execution_context": "head/local",
            }
    assert "Doctor invocation timing (head/local," in output
    assert "Waiting for Slurm runtime and storage checks" not in output
    assert "EMRYS Doctor verification plan" in output
    assert all(line in output for line in execution.submission_summary())
    assert "Checking/updating native tools and R" not in output
    if failure is None:
        assert [
            (item["event"], item["message"])
            for item in events
            if item["phase"] == "terminal"
        ] == [("repair_requalified", "Project verification completed.")]
    elif failure in {"finalize", "scheduler_interrupt"}:
        assert "Verification interrupted;" in output
    else:
        assert "VERIFICATION FAILED:" in output
    if failure in {"execution_before", "execution_after"}:
        assert "Doctor plan changed before execution" in output
        assert state["jobs"] == (0 if failure == "execution_before" else 1)
        with pytest.raises(qualification.StorageQualificationError):
            qualification.admit_final_qualification(project.source_path.parent, fasta)
    if failure == "execution_final":
        assert "Execution profile changed during head finalization" in output
        assert str(log_path) in output
        assert state["jobs"] == 1
        changed = execution_profile.load_execution_profile(profile_path)
        assert changed.sha256 == execution.sha256
        assert changed.binding_sha256 != execution.binding_sha256
        assert "repair_requalified" not in {item["event"] for item in events}
        qualification.admit_final_qualification(project.source_path.parent, fasta)
    if failure in {"head_final_error", "head_final_io"}:
        assert "Head storage finalization failed after Slurm job 614999:" in output
        assert str(log_path) in output
        assert state["jobs"] == 1
        assert "repair_requalified" not in {item["event"] for item in events}
        if failure == "head_final_error":
            assert "Retained visible-file hash differs:" in output
        else:
            assert r'head cleanup "denied"\n\x1b[31m' in output
            assert "\x1b[31m" not in output
    if failure in {"final_project", "final_package", "final_inventory"}:
        assert "Project, package, or runtime changed during head finalization" in output
        assert len(selected_sources) == 5
        assert state["jobs"] == 1
        assert "repair_requalified" not in {item["event"] for item in events}
    if failure is None:
        assert len(selected_sources) == 5
        assert selected_sources[0] == selector
        assert all(Path(str(source)) == profile_path for source in selected_sources[1:])
    if failure in {"runtime", "startup", "head_runtime"}:
        diagnostics = [
            item for item in events if item["event"] == "runtime_check_failed"
        ]
        assert str(log_path) in output
        if failure in {"runtime", "startup"}:
            assert diagnostics == []
            prefix = "Runtime check failed (compute_runtime): "
            (payload,) = [
                line.removeprefix(prefix)
                for line in output.splitlines()
                if line.startswith(prefix)
            ]
            fields = json.loads(payload)
            if failure == "runtime":
                assert r"\n" in payload
        else:
            (diagnostic,) = diagnostics
            assert diagnostic["phase"] == "head_requalification"
            fields = diagnostic["fields"]
        assert fields["check_id"] == failed_probe.check.check_id
        assert fields["target"] == failed_probe.check.target
        assert fields["status"] == failed_probe.status
        assert fields["expected"] == failed_probe.check.expected
        assert fields["observed"] == failed_probe.observed
        assert fields["detail"] == failed_probe.detail
        assert fields["host"] == doctor.platform.node()
        assert fields["inventory"] == str(inspection.profile_path)
        assert fields["inventory_sha256"] == inspection.profile_sha256
    if failure in {None, "finalize"}:
        compute = next(
            (project.source_path.parent.parent / qualification.EVIDENCE_DIRECTORY).glob(
                "*.compute.json"
            )
        )
        original = compute.read_bytes()
        if failure == "finalize":
            assert "interrupted" in records
        else:
            assert diagnose(execution_profile=profile_path).ready
        assert doctor.doctor_from_args(arguments) == 0
        assert state["jobs"] == 2 and state["probes"] == 1
        assert compute.read_bytes() == original
        qualification.admit_final_qualification(project.source_path.parent, fasta)
        repeated_output = capsys.readouterr().err
        assert "EMRYS is ready." in repeated_output
        assert "EMRYS Doctor verification plan" in repeated_output
        assert "Checking/updating native tools and R" not in repeated_output
        _repeated_log_path, repeated_events = _repair_log(project, previous=log_path)
        assert [
            (item["event"], item["message"])
            for item in repeated_events
            if item["phase"] == "terminal"
        ] == [("repair_requalified", "Project verification completed.")]
        assert records.count("opened") == 2
    else:
        assert state["probes"] == (
            1
            if failure
            in {
                "head_runtime",
                "execution_after",
                "execution_final",
                "head_final_error",
                "head_final_io",
                "final_project",
                "final_package",
                "final_inventory",
            }
            else 0
        )
        assert (
            "interrupted" if failure == "scheduler_interrupt" else "failed"
        ) in records
        if failure in {
            "execution_final",
            "head_final_io",
            "final_project",
            "final_package",
            "final_inventory",
        }:
            qualification.admit_final_qualification(project.source_path.parent, fasta)
        else:
            with pytest.raises(qualification.StorageQualificationError):
                qualification.admit_final_qualification(
                    project.source_path.parent, fasta
                )


def test_malformed_project_is_a_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project(tmp_path)
    monkeypatch.setattr(
        doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            doctor.DoctorInputError("malformed Project")
        ),
    )

    status = doctor.doctor_from_args(
        argparse.Namespace(
            project=project.source_path,
            analysis=None,
            verbose=False,
            log_root=None,
            repair=False,
            execute=False,
        )
    )

    assert status == 2
    assert "malformed Project" in capsys.readouterr().err


@pytest.mark.parametrize("inventory", ("missing", "damaged"))
def test_malformed_shared_seal_refuses_repair_without_an_admissible_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inventory: str,
) -> None:
    project = _project(tmp_path)
    runtime = project.source_path.parent / "runtime"
    seal = runtime / "shared.json"
    seal.write_bytes(b"even malformed seal evidence must be preserved\n")
    if inventory == "damaged":
        (runtime / "runtime.tsv").write_bytes(b"damaged inventory\n")
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        doctor,
        "_manager",
        lambda _name: pytest.fail("sealed donor admitted a package manager"),
    )
    before = _snapshot(tmp_path)
    with pytest.raises(
        doctor.DoctorRepairError, match="re-admit the shared runtime seal"
    ):
        doctor._build_repair_plan(_result(project, ready=False))
    assert _snapshot(tmp_path) == before


def test_repair_plan_predating_seal_refuses_before_managed_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    seal = project.source_path.parent / "runtime/shared.json"
    seal.write_bytes(b"immutable seal\n")
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    with pytest.raises(doctor.DoctorRepairError, match="seal appeared"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert seal.read_bytes() == b"immutable seal\n"
    assert not _runtime(plan).managed_root.exists()
    assert not (seal.parent / "maintenance.lock").exists()
    assert records == ["opened", "failed", "closed"]


def test_valid_shared_owner_plans_a_fresh_generation_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    runtime = project.source_path.parent / "runtime"
    seal = runtime / "shared.json"
    seal.write_bytes(b"retained seal\n")
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(doctor, "_manager", lambda _name: Path("/manager/pixi"))
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: "d" * 64)
    monkeypatch.setattr(
        doctor,
        "admit_runtime_seal_bytes",
        lambda path, _data: SimpleNamespace(
            path=path,
            managed_root=runtime / "managed",
        ),
    )
    before = _snapshot(tmp_path)

    plan = doctor._build_repair_plan(_result(project, ready=False))

    assert plan.runtime is not None
    assert plan.runtime.source_seal == seal
    assert plan.runtime.source_seal_bytes == seal.read_bytes()
    assert plan.runtime.replacement_seal is not None
    assert plan.runtime.replacement_seal.parent.parent == runtime / "generations"
    assert plan.runtime.managed_root == plan.runtime.replacement_seal.parent / "managed"
    assert _snapshot(tmp_path) == before


def test_dependent_project_requires_the_source_projects_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    profile = project.source_path.parent / "runtime/runtime.tsv"
    source = tmp_path / "source"
    source.mkdir()
    source_project = source / "project.yaml"
    source_project.write_bytes(b"source Project identity\n")
    profile_bytes = runtime_inspector.shared_runtime_profile_bytes(
        source / "runtime/shared.json",
        b"source seal\n",
        Path(sys.executable),
    )
    profile.write_bytes(profile_bytes)
    inspection = _inspection(
        tmp_path,
        profile=profile,
        profile_bytes=profile_bytes,
    )
    monkeypatch.setattr(
        doctor,
        "load_runtime_profile_contract",
        lambda *_args: (profile_bytes, ()),
    )
    monkeypatch.setattr(doctor.platform, "system", lambda: "Linux")
    monkeypatch.setattr(doctor.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        doctor, "_manager", lambda _name: pytest.fail("dependent admitted repair")
    )

    with pytest.raises(doctor.DoctorRepairError) as failure:
        doctor._build_repair_plan(_result(project, ready=False, inspection=inspection))

    assert str(source_project) in str(failure.value)
    assert "--replace --execute" in str(failure.value)


def test_shared_owner_repair_publishes_replacement_without_changing_old_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    base = _plan(project)
    runtime_root = project.source_path.parent / "runtime"
    generation = runtime_root / "generations" / ("a" * 32)
    old_profile = b"old shared selection\n"
    old_seal = runtime_root / "shared.json"
    old_seal.write_bytes(b"old sealed generation\n")
    runtime = replace(
        _runtime(base),
        managed_root=generation / "managed",
        profile_bytes=old_profile,
        source_seal=old_seal,
        source_seal_bytes=old_seal.read_bytes(),
        replacement_seal=generation / "shared.json",
    )
    runtime.profile.write_bytes(old_profile)
    plan = replace(base, runtime=runtime)
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: runtime.pixi_sha256)
    monkeypatch.setattr(
        doctor,
        "admit_runtime_seal_bytes",
        lambda path, _data: SimpleNamespace(path=path),
    )
    monkeypatch.setattr(doctor, "_repair_actions", lambda _plan: ())
    monkeypatch.setattr(doctor, "_managed_discovery_environment", lambda _plan: {})
    direct = _inspection(
        tmp_path,
        (_check("python", "tool_version", sys.executable),),
        profile=runtime.profile,
        profile_bytes=b"new direct inventory\n",
    )
    monkeypatch.setattr(
        doctor.onboarding, "discover_runtime_profile", lambda **_kwargs: direct
    )
    monkeypatch.setattr(
        doctor, "runtime_seal_bytes", lambda _candidate, _path: b"new seal\n"
    )
    replacement_profile = b"new shared selection\n"
    monkeypatch.setattr(
        doctor,
        "shared_runtime_profile_bytes",
        lambda *_args: replacement_profile,
    )
    library = generation / "managed/renv/library"
    monkeypatch.setattr(
        doctor,
        "runtime_profile_checks",
        lambda *_args: (
            RuntimeCheck("renv_library", "path_visibility", str(library), (), ".*"),
        ),
    )
    selected = replace(
        direct,
        profile_bytes=replacement_profile,
        profile_sha256=hashlib.sha256(replacement_profile).hexdigest(),
    )
    monkeypatch.setattr(
        doctor, "inspect_runtime_profile_bytes", lambda *_args, **_kwargs: selected
    )
    monkeypatch.setattr(doctor, "runtime_file_bindings", lambda *_args, **_kwargs: ())
    final = _result(project, ready=True, inspection=selected)

    def diagnose(*_args: object, **_kwargs: object) -> doctor.DoctorResult:
        assert runtime.profile.read_bytes() == replacement_profile
        return final

    monkeypatch.setattr(doctor, "diagnose_project", diagnose)

    assert doctor._execute_repair(plan, controls=_controls(project)) is final
    assert old_seal.read_bytes() == b"old sealed generation\n"
    assert runtime.replacement_seal.read_bytes() == b"new seal\n"
    assert runtime.profile.read_bytes() == replacement_profile
    assert not (runtime_root / "maintenance.lock").exists()
    assert records == ["opened", "terminal", "closed"]


def test_repair_readmission_rechecks_seal_while_holding_its_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    plan = _plan(project)
    runtime = project.source_path.parent / "runtime"
    acquire = doctor.acquire_lock
    original_readmission = doctor._readmit_repair_plan
    records: list[str] = []
    _patch_logging(monkeypatch, plan, records)
    monkeypatch.setattr(doctor, "_readmit_repair_plan", original_readmission)

    def seal_after_acquisition(path, payload, error_type, **kwargs):
        owned = acquire(path, payload, error_type, **kwargs)
        (runtime / "shared.json").write_bytes(b"seal appeared after preview\n")
        return owned

    monkeypatch.setattr(doctor, "acquire_lock", seal_after_acquisition)
    with pytest.raises(doctor.DoctorRepairError, match="seal appeared"):
        doctor._execute_repair(plan, controls=_controls(project))
    assert (runtime / "maintenance.lock").exists()
    assert not _runtime(plan).managed_root.exists()
    assert records == ["opened", "failed", "closed"]
