"""Focused contracts for Project-aware Doctor diagnosis and repair."""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from emrys import reporting
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
)
from emrys.evidence.storage_inventory.qualification import QualifiedStorage
from emrys.libraries.application_logging import (
    ApplicationLogError,
    LogControls,
    LogLevel,
)
from emrys.orchestration.local_pilot import doctor
from emrys.orchestration.local_pilot.normalization import (
    ProjectAdmission,
    admit_project,
)
from tests.orchestration.local_pilot import fixture


def _project(tmp_path: Path) -> ProjectAdmission:
    root = tmp_path / "project"
    source = fixture.build(root)
    for name in ("logs", "runs", "runtime"):
        (root / name).mkdir()
    return admit_project(source, fixture.profile())


def _result(
    project: ProjectAdmission,
    *,
    ready: bool,
    inspection: RuntimeInspection | None = None,
) -> doctor.DoctorResult:
    source_root = project.source_path.parent / "source"
    source_root.mkdir(exist_ok=True)
    return doctor.DoctorResult(
        project=project,
        analysis=project.select_analysis(),
        source_root=source_root,
        source_commit="a" * 40,
        inspection=inspection,
        bindings=(),
        blockers=() if ready else ("runtime profile is not admitted",),
        remediations=() if ready else ("Run `emrys doctor --repair`.",),
        storage_ready=True,
        runtime_ready=ready,
    )


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
            runtime_context="local",
            required=True,
            target=target,
            probe_args=(),
            expected=".*",
            description=check_id,
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
        runtime_context="local",
        observations=observations,
        rendered_bytes=b"rendered\n",
    )


def _plan(project: ProjectAdmission) -> doctor._RepairPlan:
    managed = project.source_path.parent / "runtime/managed"
    return doctor._RepairPlan(
        project=project,
        analysis_name=project.select_analysis().name,
        source_root=project.source_path.parent / "source",
        source_commit="a" * 40,
        storage=None,
        runtime=doctor._ManagedRuntimePlan(
            source_root=project.source_path.parent / "source",
            managed_root=managed,
            profile=project.source_path.parent / "runtime/runtime.tsv",
            uv=Path("/managers/uv"),
            pixi=Path("/managers/pixi"),
            uv_sha256="b" * 64,
            pixi_sha256="c" * 64,
            profile_bytes=None,
            manifest_bytes=b'[workspace]\nname = "emrys"\n',
            lock_bytes=b"locked\n",
        ),
    )


def _runtime(plan: doctor._RepairPlan) -> doctor._ManagedRuntimePlan:
    assert plan.runtime is not None
    return plan.runtime


def _controls(project: ProjectAdmission) -> LogControls:
    return LogControls(
        LogLevel.NORMAL,
        project.source_path.parent / "logs/application",
        "default",
        "default",
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


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

    bindings = (*doctor.runtime_file_bindings(inspection), storage)
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
    assert by_name["storage_qualification"]["version"] == "site-1"


def test_runtime_contract_refuses_a_symlinked_renv_library(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    real_library = tmp_path / "real-library"
    real_library.mkdir()
    linked_library = tmp_path / "linked-library"
    linked_library.symlink_to(real_library, target_is_directory=True)
    _data, policy = doctor.load_runtime_profile_contract(
        doctor.onboarding.runtime_policy_path()
    )
    targets = {
        "python": "/python",
        "snakemake": "/python",
        "sha256_python": "/python",
        "java": "/java",
        "picard": "/java",
        "picard_jar": "/picard.jar",
        "rscript": "/Rscript",
        "renv_project": str(source),
        "renv_library": str(linked_library),
    }
    checks = tuple(
        replace(
            check,
            target=targets.get(check.check_id, check.target),
            probe_args=(
                doctor.controlled_python_argv(
                    "/python", "-m", "snakemake", "--version"
                )[1:]
                if check.check_id == "snakemake"
                else ("python_hashlib",)
                if check.check_id == "sha256_python"
                else ("-jar", "/picard.jar", "MarkDuplicates", "--version")
                if check.check_id == "picard"
                else ("/Rscript",)
                if check.check_type == "r_namespace"
                else check.probe_args
            ),
        )
        for check in policy
    )

    with pytest.raises(doctor.DoctorInputError, match="canonical real directory"):
        doctor.validate_runtime_profile_contract(checks, source)


def test_absent_runtime_diagnosis_is_read_only_and_opens_no_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    storage_receipt = tmp_path / "storage.tsv"
    storage_receipt.write_bytes(b"qualified\n")
    storage = doctor.storage_runtime_binding(
        QualifiedStorage(storage_receipt, "b" * 64, "site-1")
    )
    foundations = doctor.DoctorResult(
        project=project,
        analysis=project.select_analysis(),
        source_root=project.source_path.parent / "source",
        source_commit="a" * 40,
        inspection=None,
        bindings=(storage,),
        blockers=(),
        remediations=(),
        storage_ready=True,
        runtime_ready=False,
    )
    monkeypatch.setattr(
        doctor, "_inspect_foundations", lambda *_args, **_kwargs: foundations
    )
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
    assert "runtime profile is not admitted" in result.blockers[-1]
    assert _snapshot(tmp_path) == before


def test_foundation_readiness_requires_reporter_only_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(tmp_path)
    receipt = tmp_path / "storage.tsv"
    receipt.write_bytes(b"qualified\n")
    qualified = QualifiedStorage(receipt, "b" * 64, "site-1")
    monkeypatch.setattr(
        doctor,
        "inspect_source_checkout",
        lambda **_kwargs: SimpleNamespace(commit="a" * 40),
    )
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
    monkeypatch.setattr(
        reporting,
        "admit_analysis_reporter",
        lambda _module_id: (_ for _ in ()).throw(
            reporting.ReportProviderError("not installed")
        ),
    )

    required = doctor._inspect_foundations(
        project.source_path,
        project.source_path.parent,
        require_reporter=True,
    )
    disabled = doctor._inspect_foundations(
        project.source_path,
        project.source_path.parent,
        require_reporter=False,
    )

    assert any("analysis reporter is not ready" in item for item in required.blockers)
    assert not any(
        "analysis reporter is not ready" in item for item in disabled.blockers
    )


@pytest.mark.parametrize(
    ("execute", "repair", "expected_status"),
    ((False, False, 1), (True, False, 2), (False, True, 1)),
)
def test_diagnosis_and_repair_preview_write_nothing_and_open_no_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    execute: bool,
    repair: bool,
    expected_status: int,
) -> None:
    project = _project(tmp_path)
    result = _result(project, ready=False)
    plan = _plan(project)
    monkeypatch.setattr(doctor, "diagnose_project", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(doctor, "_build_repair_plan", lambda _result: plan)
    monkeypatch.setattr(doctor, "_confirm_repair", lambda: False)
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
            log_level=None,
            log_root=None,
            repair=repair,
            execute=execute,
        )
    )

    assert status == expected_status
    assert _snapshot(tmp_path) == before
    assert capsys.readouterr().out == ""


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
            log_level="verbose",
            log_root=tmp_path / "selected-logs",
            repair=False,
            execute=False,
        )
    )

    assert status == 0
    assert observed[0]["cli_level"] == "verbose"
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
    (result.source_root / ".venv").mkdir()
    monkeypatch.setattr(doctor.sys, "prefix", str(result.source_root / ".venv"))
    monkeypatch.setattr(doctor, "_manager", lambda name: Path(f"/manager/{name}"))
    monkeypatch.setattr(doctor, "_file_sha256", lambda _path: "d" * 64)
    before = _snapshot(tmp_path)

    with pytest.raises(doctor.DoctorRepairError, match="site- or user-owned"):
        doctor._build_repair_plan(result)

    assert _snapshot(tmp_path) == before


def test_storage_only_repair_preserves_ready_site_runtime_and_skips_managers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
        source_root=project.source_path.parent / "source",
        source_commit="a" * 40,
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
    assert profile.read_bytes() == b"site runtime\n"
    assert records[0] == "opened"
    assert "terminal" in records


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
        for argv, environment in doctor._repair_actions(plan)
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


class _Logger:
    def __init__(self, records: list[str]) -> None:
        self.records = records

    def info(self, _message: str, *, extra: object) -> None:
        assert extra is not None
        self.records.append("info")


class _Attempt:
    def __init__(self, records: list[str]) -> None:
        self.records = records

    def logger(self, **_kwargs: object) -> _Logger:
        return _Logger(self.records)

    def terminal(self, **_kwargs: object) -> bool:
        self.records.append("terminal")
        return True

    def fail(self, **_kwargs: object) -> bool:
        self.records.append("failed")
        return True

    def interrupt_best_effort(self, **_kwargs: object) -> bool:
        self.records.append("interrupted")
        return True

    def close(self) -> None:
        self.records.append("closed")


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

    def open_log(**_kwargs: object) -> _Attempt:
        if plan.runtime is not None:
            assert not plan.runtime.managed_root.exists(), (
                "repair mutated before opening its log"
            )
        if plan.storage is not None:
            assert not plan.storage.receipt_path.exists(), (
                "repair mutated before opening its log"
            )
        records.append("opened")
        return _Attempt(records)

    monkeypatch.setattr(doctor, "open_attempt_log", open_log)


def test_repair_readmission_rejects_a_profile_that_appeared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    monkeypatch.setattr(
        doctor,
        "inspect_source_checkout",
        lambda **_kwargs: SimpleNamespace(commit=plan.source_commit),
    )
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=plan.project),
    )
    monkeypatch.setattr(
        doctor,
        "_file_sha256",
        lambda path: runtime.uv_sha256 if path == runtime.uv else runtime.pixi_sha256,
    )
    runtime.profile.write_bytes(b"unapproved\n")

    with pytest.raises(
        doctor.DoctorRepairError, match="appeared after repair confirmation"
    ):
        doctor._readmit_repair_plan(plan, before_storage=True)


def test_repair_readmission_rejects_a_redirected_runtime_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(_project(tmp_path))
    runtime = _runtime(plan)
    external = tmp_path / "external-runtime"
    external.mkdir()
    runtime.managed_root.parent.rmdir()
    runtime.managed_root.parent.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(
        doctor,
        "inspect_source_checkout",
        lambda **_kwargs: SimpleNamespace(commit=plan.source_commit),
    )
    monkeypatch.setattr(
        doctor.onboarding,
        "validate_project",
        lambda *_args, **_kwargs: SimpleNamespace(project=plan.project),
    )

    with pytest.raises(doctor.DoctorRepairError, match="changed before execution"):
        doctor._readmit_repair_plan(plan, before_storage=True)

    assert not (external / "managed").exists()


def test_repair_delegates_to_managers_admits_profile_logs_and_requalifies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.evidence.storage_inventory import qualification

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
    records: list[str] = []
    commands: list[tuple[str, ...]] = []
    _patch_logging(monkeypatch, plan, records)
    real_subprocess_run = doctor.subprocess.run

    def run_manager(argv: tuple[str, ...], **_kwargs: object) -> Any:
        if Path(argv[0]) == Path(sys.executable):
            return real_subprocess_run(argv, **_kwargs)
        commands.append(tuple(argv))
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

    observed = doctor._execute_repair(plan, controls=_controls(project))

    assert observed is final
    assert [Path(argv[0]).name for argv in commands] == ["uv", "pixi", "pixi"]
    assert "sync" in commands[0] and "install" in commands[1]
    assert "run" in commands[2] and "--environment" in commands[2]
    assert commands[2][-1].endswith("scripts/restore_r_environment.R")
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
    assert records[0] == "opened"
    assert "terminal" in records
    assert records[-1] == "closed"


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
    _patch_logging(monkeypatch, plan, records)

    def fail_manager(*_args: object, **_kwargs: object) -> Any:
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
    monkeypatch.setattr(doctor, "_admit_managed_root", lambda _plan: None)
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
            log_level=None,
            log_root=None,
            repair=False,
            execute=False,
        )
    )

    assert status == 2
    assert "malformed Project" in capsys.readouterr().err
