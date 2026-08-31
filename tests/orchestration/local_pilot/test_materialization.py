"""Direct contracts for the fixed production local-pilot materializer."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
import threading
import zlib
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    PROCESSING_STEP_IDS,
    build_analysis_revision,
)
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.contracts.scientific_evidence import step08
from emrys.evidence.runtime_availability import inspector as runtime_inspector
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
    load_runtime_profile_contract,
)
from emrys.libraries import source_authority
from emrys.libraries.source_authority import controlled_python_argv
from emrys.libraries.application_logging import (
    ApplicationLogError,
    LogControls,
    LogLevel,
)
from emrys.libraries.application_logging.storage import (
    ApplicationLogFile,
    ApplicationLogStorageError,
)
from emrys.orchestration.local_pilot import (
    control,
    doctor,
    inspection,
    lifecycle,
    materialization,
    onboarding,
    reporting_operation,
    task,
)
from emrys.orchestration.local_pilot.materialization import (
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    publish_attempt,
)
from emrys.orchestration.local_pilot.normalization import (
    _historical_execution_v1,
    admit_project,
)
from emrys.orchestration.local_pilot.execution_profile import load_execution_profile
from emrys.orchestration.local_pilot.resource_policy import (
    AllocationCapacity,
    resolve_resource_policy,
)
from emrys.orchestration.local_pilot.run_implementation import (
    backend_semantics_identity,
    implementation_identity,
)
from tests.orchestration.local_pilot.fixture import build, build_legacy
from tests.orchestration.local_pilot.fixtures.b5_doubles import with_owner_doubles

REPO_ROOT = Path(__file__).resolve().parents[3]
_POLICY_BYTES, POLICY_CHECKS = load_runtime_profile_contract(
    onboarding.runtime_policy_path()
)
RUNTIME_CHECKS = tuple((check.check_id, check.check_type) for check in POLICY_CHECKS)
R_PACKAGES = tuple(
    (check.check_id, check.target)
    for check in POLICY_CHECKS
    if check.check_type == "r_namespace"
)


class _InputStream:
    def __init__(self, response, before_read=lambda: None, *, terminal=True) -> None:
        self.response = response
        self.before_read = before_read
        self.terminal = terminal

    def isatty(self) -> bool:
        return self.terminal

    def readline(self) -> str:
        self.before_read()
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


class _TerminalOutput:
    def __init__(self, stream) -> None:
        self.stream = stream

    def isatty(self) -> bool:
        return True

    def write(self, value: str) -> int:
        return self.stream.write(value)

    def flush(self) -> None:
        self.stream.flush()


def _readiness(
    tmp_path: Path,
    *,
    source_root: Path = REPO_ROOT,
    source_commit: str = "a" * 40,
    workflow_cores: int = 1,
    stage_concurrency: dict[str, int] | None = None,
    step_threads: dict[str, int] | None = None,
    legacy: bool = False,
    replicate_count: int = 2,
    sample_ids: list[str] | None = None,
) -> tuple[doctor.DoctorResult, object, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    workspace = tmp_path / "project"
    workspace.mkdir()
    request = (
        build_legacy(workspace)
        if legacy
        else build(workspace, replicate_count=replicate_count)
    )
    if sample_ids is not None:
        definition = yaml.safe_load(request.read_text(encoding="utf-8"))
        definition["analyses"]["primary"]["sample_ids"] = sample_ids
        request.write_text(
            yaml.safe_dump(definition, sort_keys=False),
            encoding="utf-8",
        )
    execution_profile_path = request.parent / "emrys.execution.yaml"
    profile_document = yaml.safe_load(
        execution_profile_path.read_text(encoding="utf-8")
    )
    resource_document = profile_document["resources"]
    resource_document["workflow_cores"] = workflow_cores
    resource_document["workflow_memory_mb"] = max(1024, workflow_cores * 1024)
    resource_document["stage_concurrency"] = {
        step_id: (1 if stage_concurrency is None else stage_concurrency.get(step_id, 1))
        for step_id in ("01", "02", "02b", "03", "04", "05", "06", "07")
    }
    resource_document["step_threads"] = (
        {"00a": 1, "01": 1, "02": 1, "06": 1, "08": 1}
        if step_threads is None
        else step_threads
    )
    profile_document["resources"] = resource_document
    execution_profile_path.write_text(
        yaml.safe_dump(profile_document, sort_keys=False),
        encoding="utf-8",
    )
    project = admit_project(
        request,
        source_root / "workflow/contracts/local_cmh_v2.json",
        allow_legacy=legacy,
    )
    analysis = project.select_analysis()
    resources = resolve_resource_policy(
        load_execution_profile(
            request,
            config_path=execution_profile_path,
        ).resource_policy,
        AllocationCapacity(
            cores=workflow_cores,
            memory_mb=max(1024, workflow_cores * 1024),
            source="test allocation",
        ),
    )
    runtime = workspace / "runtime/runtime.tsv"
    runtime.parent.mkdir(mode=0o700)
    runtime_bytes = b"fixed test runtime profile\n"
    runtime.write_bytes(runtime_bytes)
    tool = tmp_path / "tool"
    tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool.chmod(0o755)
    jar = tmp_path / "picard.jar"
    jar.write_bytes(b"jar\n")
    renv_library = tmp_path / "renv-library"
    renv_library.mkdir(exist_ok=True)
    installed_renv = renv_library / "renv"
    installed_renv.mkdir(exist_ok=True)
    (installed_renv / "DESCRIPTION").write_text(
        "Package: renv\nVersion: 1.2.3\n", encoding="utf-8"
    )
    for _check_id, package in R_PACKAGES:
        package_root = renv_library / package
        package_root.mkdir()
        (package_root / "DESCRIPTION").write_text(
            f"Package: {package}\nVersion: 1.0.0\n", encoding="utf-8"
        )
    observations: list[RuntimeObservation] = []
    rscript = str(tool)
    for check_id, check_type in RUNTIME_CHECKS:
        if check_id in {"python", "sha256_python"}:
            target = sys.executable
        elif check_id == "snakemake":
            target = sys.executable
        elif check_id == "picard_jar":
            target = str(jar)
        elif check_id == "renv_project":
            target = str(source_root)
        elif check_id == "renv_library":
            target = str(renv_library)
        elif check_type == "r_namespace":
            target = next(package for key, package in R_PACKAGES if key == check_id)
        else:
            target = str(tool)
        if check_id == "picard":
            probe_args = ("-jar", str(jar), "MarkDuplicates", "--version")
        elif check_id == "picard_jar":
            probe_args = ("file_readable",)
        elif check_id == "renv_project":
            probe_args = ("directory_readable",)
        elif check_id == "renv_library":
            probe_args = ("directory_readable",)
        elif check_id == "snakemake":
            probe_args = controlled_python_argv(
                sys.executable, "-m", "snakemake", "--version"
            )[1:]
        elif check_id == "sha256_python":
            probe_args = ("python_hashlib",)
        elif check_type == "r_namespace":
            probe_args = (rscript,)
        else:
            probe_args = ("--version",)
        observations.append(
            RuntimeObservation(
                check=RuntimeCheck(
                    check_id=check_id,
                    check_type=check_type,
                    runtime_context="local",
                    required=True,
                    target=target,
                    probe_args=probe_args,
                    expected="expected",
                    description=check_id,
                ),
                status="pass",
                observed=(
                    "9.25.1" if check_id == "snakemake" else f"observed-{check_id}"
                ),
                detail="test runtime",
                resolved_path=(
                    (renv_library / target).resolve(strict=True)
                    if check_type == "r_namespace"
                    else None
                ),
            )
        )
    runtime_inspection = RuntimeInspection(
        profile_path=runtime,
        profile_sha256=hashlib.sha256(runtime_bytes).hexdigest(),
        profile_bytes=runtime_bytes,
        runtime_context="local",
        observations=tuple(observations),
        rendered_bytes=b"test runtime report\n",
    )
    storage_receipt = tmp_path / "storage.qualified.json"
    storage_bytes = b"fixed storage qualification receipt\n"
    storage_receipt.write_bytes(storage_bytes)
    storage_binding = doctor.RuntimeBinding(
        check_id="storage_qualification",
        path=storage_receipt,
        resolved_path=storage_receipt.resolve(strict=True),
        sha256=hashlib.sha256(storage_bytes).hexdigest(),
        observed="b" * 64,
    )
    bindings = (*doctor.runtime_file_bindings(runtime_inspection), storage_binding)
    readiness = doctor.DoctorResult(
        project=project,
        analysis=analysis,
        source_root=source_root,
        source_commit=source_commit,
        inspection=runtime_inspection,
        bindings=bindings,
        blockers=(),
        remediations=(),
    )
    return readiness, resources, request, workspace


def _run_candidate(readiness, resources, *, through: str = "analysis"):
    stopping = (
        None
        if through == "analysis"
        else materialization.processing_stopping_owner_keys(readiness.analysis.profile)
    )
    return build_run_candidate(
        readiness.analysis,
        readiness,
        resources.declaration,
        scientific_stopping_owner_keys=stopping,
    )


def _plan(
    tmp_path: Path,
    *,
    step_threads: dict[str, int] | None = None,
    workflow_cores: int = 1,
    stage_concurrency: dict[str, int] | None = None,
    legacy: bool = False,
    through: str = "analysis",
):
    readiness, resources, _request, workspace = _readiness(
        tmp_path,
        workflow_cores=workflow_cores,
        stage_concurrency=stage_concurrency,
        step_threads=step_threads,
        legacy=legacy,
    )
    return build_attempt_plan(
        _run_candidate(readiness, resources, through=through),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )


def _freeze_attempt_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    token: str = "1" * 32,
    minute: int = 0,
    host: str = "test-host",
    process_id: int = 123,
) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 12, 20, minute, tzinfo=tz or UTC)

    monkeypatch.setattr(materialization, "datetime", FixedDateTime)
    monkeypatch.setattr(
        materialization.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex=token),
    )
    monkeypatch.setattr(materialization.socket, "gethostname", lambda: host)
    monkeypatch.setattr(materialization.os, "getpid", lambda: process_id)


def _after_plan(plan, *, minutes: int = 0) -> datetime:
    created = datetime.fromisoformat(
        str(plan.attempt_record["created_at"]).replace("Z", "+00:00")
    )
    return created + timedelta(minutes=minutes)


def _patch_run_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    execute_plan,
    transform_plan,
):
    readiness, resources, project_path, workspace = _readiness(tmp_path)
    arguments = argparse.Namespace(
        project=project_path,
        execution_profile=project_path.parent / "emrys.execution.yaml",
        log_level=None,
        log_root=None,
        execute=False,
    )
    real_build = control.build_attempt_plan
    plans = []

    def diagnose(*_args, **kwargs):
        assert kwargs == {
            "storage_requirement": "direct",
            "analysis_name": None,
        }
        return readiness

    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        diagnose,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: resources.allocation,
    )
    _patch_lifecycle_execution(monkeypatch, lambda: plans[-1], execute_plan)

    def build(*args, **kwargs):
        plan = transform_plan(real_build(*args, **kwargs))
        plans.append(plan)
        return plan

    monkeypatch.setattr(
        control,
        "build_attempt_plan",
        build,
    )
    return arguments, workspace


def _patch_lifecycle_execution(
    monkeypatch: pytest.MonkeyPatch,
    plan_source,
    execute,
) -> None:
    monkeypatch.setattr(control, "admit_run", lambda *_args, **_kwargs: None)

    def run(_preparation, _publish, *, ops, initial_runtime_inspection=None):
        plan = plan_source() if callable(plan_source) else plan_source
        return execute(plan, ops.observe_application_event, initial_runtime_inspection)

    monkeypatch.setattr(control.lifecycle, "run_materialized_attempt", run)


def _dispatch_records(plan) -> list[dict[str, object]]:
    return [json.loads(item.data) for item in plan.new_dispatch_files]


def _workflow_config(plan) -> dict[str, object]:
    return json.loads(
        next(item.data for item in plan.attempt_files if item.path == plan.config_path)
    )


def test_control_readiness_failure_preserves_doctor_remediation(
    tmp_path: Path,
) -> None:
    readiness, *_rest = _readiness(tmp_path)
    blocked = replace(
        readiness,
        blockers=("runtime is unavailable",),
        remediations=("load the admitted site module",),
    )

    with pytest.raises(control.ControlError, match="load the admitted site module"):
        control._require_ready(blocked)


def test_owner_doubles_preserve_immutable_run_toolchain(tmp_path: Path) -> None:
    plan = _plan(tmp_path)

    doubled = with_owner_doubles(plan)

    assert (
        replace(
            doubled,
            attempt_record_bytes=plan.attempt_record_bytes,
            attempt_files=plan.attempt_files,
            new_dispatch_files=plan.new_dispatch_files,
        )
        == plan
    )
    attempt = doubled.attempt_record
    assert attempt["execution_mode"] == "local-science-tools"
    original_attempt = plan.attempt_record
    assert doubled.config_path == plan.config_path
    attempt["workflow_config"] = original_attempt["workflow_config"]
    assert attempt == original_attempt

    original_files = {item.path: item.data for item in plan.attempt_files}
    doubled_files = {item.path: item.data for item in doubled.attempt_files}
    dispatch_paths = {item.path for item in plan.new_dispatch_files}
    assert doubled_files.keys() == original_files.keys()
    assert {item.path for item in doubled.new_dispatch_files} == dispatch_paths
    for path in dispatch_paths:
        original = json.loads(original_files[path])
        replacement = json.loads(doubled_files[path])
        replacement["producer_argv"] = original["producer_argv"]
        replacement["validator_argv"] = original["validator_argv"]
        assert replacement == original

    original_config = json.loads(original_files[plan.config_path])
    doubled_config = json.loads(doubled_files[plan.config_path])
    for machine_key, scopes in doubled_config["dispatch_paths"].items():
        for scope_id, doubled_reference in scopes.items():
            original_reference = original_config["dispatch_paths"][machine_key][
                scope_id
            ]
            assert doubled_reference["path"] == original_reference["path"]
            doubled_reference["sha256"] = original_reference["sha256"]
    assert doubled_config == original_config
    assert all(
        doubled_files[path] == data
        for path, data in original_files.items()
        if path not in dispatch_paths and path != plan.config_path
    )

    assert all(
        "--payload-base64" in record[field]
        for record in _dispatch_records(doubled)
        for field in ("producer_argv", "validator_argv")
    )


def test_owner_doubles_use_successor_scopes_inside_reporting_payloads(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    doubled = with_owner_doubles(plan)
    payloads: dict[Path, bytes] = {}
    for record in _dispatch_records(doubled):
        argv = record["producer_argv"]
        encoded = argv[argv.index("--payload-base64") + 1]
        manifest = json.loads(zlib.decompress(base64.b64decode(encoded, validate=True)))
        payloads.update(
            {
                Path(output["path"]): base64.b64decode(output["data_base64"])
                for output in manifest["producer"]
            }
        )
    analysis = plan.run.analysis.revision

    def one(suffix: str) -> bytes:
        matches = [
            data for path, data in payloads.items() if path.name.endswith(suffix)
        ]
        assert len(matches) == 1
        return matches[0]

    cohort_id = analysis.scope_id("cohort").encode()
    analysis_id = analysis.scope_id("analysis").encode()
    assert cohort_id in one(".step08_summary.tsv")
    assert cohort_id in one(".cmh_summary.tsv")
    assert analysis_id in one(".cmh_summary.tsv")
    assert analysis_id in one(".context_receipt.tsv")


def test_plan_is_no_write_and_projects_exact_public_owner_roster(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)

    assert not (plan.workspace / "runs").exists()
    assert not (plan.workspace / "logs").exists()
    assert plan.lifecycle_request.operation == "execute"
    assert json.loads(plan.lifecycle_request.attempt_record_bytes) == plan.attempt_record
    assert (
        plan.attempt_record["executor"]
        == plan.run.execution_plan.record["identity"]["backend"]["backend"]
    )
    assert plan.dispatch_count == 35
    records = _dispatch_records(plan)
    assert len(records) == 35
    assert len({record["machine_key"] for record in records}) == 14
    assert all("--execute" in record["producer_argv"] for record in records)
    assert all("--execute" in record["validator_argv"] for record in records)

    produced_paths = [
        Path(item["path"]) for record in records for item in record["outputs"]
    ] + [Path(record["validation_report_path"]) for record in records]
    run_produced_paths = [
        path for path in produced_paths if path.is_relative_to(plan.run_root)
    ]
    assert all(
        path.is_relative_to(plan.run_root / "products" / "native")
        or path.is_relative_to(plan.run_root / "results" / "editing")
        or path.is_relative_to(plan.run_root / "results" / "scientific_context")
        for path in run_produced_paths
    )
    assert {
        path.relative_to(plan.run_root / "results").parts[0]
        for path in run_produced_paths
        if path.is_relative_to(plan.run_root / "results")
    } == {"editing", "scientific_context"}

    def producer_argument(record: dict[str, object], option: str) -> Path:
        argv = record["producer_argv"]
        return Path(argv[argv.index(option) + 1])

    def artifact_path(record: dict[str, object], suffix: str) -> Path:
        return next(
            Path(item["path"])
            for field in ("inputs", "outputs")
            for item in record[field]
            if str(item["path"]).endswith(suffix)
        )

    def assert_root(
        record: dict[str, object], option: str, suffix: str, parent_index: int
    ) -> None:
        assert (
            producer_argument(record, option)
            == artifact_path(record, suffix).parents[parent_index]
        )

    step06 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1"
    )
    step06_prefix = controlled_python_argv(
        sys.executable,
        "-m",
        "emrys.stages.mechanical_orientation.producer",
    )
    producer_argv = tuple(step06["producer_argv"])
    assert any(
        producer_argv[index : index + len(step06_prefix)] == step06_prefix
        for index in range(len(producer_argv) - len(step06_prefix) + 1)
    )
    assert "step_06_split_bam_by_read_orientation.sh" not in " ".join(
        step06["producer_argv"]
    )
    assert_root(step06, "--output-dir", ".FWD_like.bam", 0)
    assert_root(step06, "--qc-dir", ".orientation_counts.tsv", 0)

    step07 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.stage.generate_partitioned_cohort_mpileup_VCFs.v1"
    )
    assert (
        step07["validator_argv"][step07["validator_argv"].index("--scope-id") + 1]
        == step07["scope"]["scope_id"]
    )
    assert Path(step07["validation_report_path"]).name == (
        f"{step07['scope']['scope_id']}.validation.tsv"
    )
    step07_prefix = controlled_python_argv(
        sys.executable,
        "-m",
        "emrys.stages.partitioned_cohort_mpileup.producer",
    )
    producer_argv = tuple(step07["producer_argv"])
    assert any(
        producer_argv[index : index + len(step07_prefix)] == step07_prefix
        for index in range(len(producer_argv) - len(step07_prefix) + 1)
    )
    assert "step_07_bcftools_mpileup_by_chrom_and_strand.sh" not in " ".join(
        step07["producer_argv"]
    )
    assert_root(step07, "--orientation-root", ".FWD_like.bam", 1)
    assert_root(step07, "--output-root", ".FWD_like.mpileup.vcf", 2)
    assert not any("--unlock" in record["producer_argv"] for record in records)
    assert not {
        "--unlock",
        "--forceall",
        "--rerun-incomplete",
        "--cleanup-metadata",
    }.intersection(plan.attempt_record["snakemake_argv"])
    step00a = next(
        record
        for record in records
        if record["machine_key"] == "emrys.stage.construct_STAR_index.v1"
    )
    assert "--genome-sa-index-nbases" in step00a["producer_argv"]
    assert "--expected-genome-sa-index-nbases" in step00a["validator_argv"]
    step00b = next(
        record
        for record in records
        if record["machine_key"] == "emrys.stage.convert_GTF_to_BED12.v1"
    )
    assert (
        step00b["producer_argv"][step00b["producer_argv"].index("--run-token") + 1]
        == step00b["owner_run_token"]
    )
    step01 = next(
        record
        for record in records
        if record["machine_key"] == "emrys.stage.align_RNA_reads_with_STAR.v1"
    )
    assert "--gunzip-bin" in step01["producer_argv"]
    assert step01["producer_argv"][
        step01["producer_argv"].index("--gunzip-bin") + 1
    ] == str(tmp_path / "tool")
    step08 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.stage.preprocess_and_annotate_cohort_candidates.v1"
    )
    producer = step08["producer_argv"]
    assert producer[:4] == [
        str(tmp_path / "tool"),
        "-c",
        (
            'export EMRYS_RUN_TOKEN="$1" EMRYS_SHA256_PYTHON="$2" '
            'EMRYS_REQUIRE_BOUND_SHA256=1; shift 2; exec "$@"'
        ),
        "emrys-owner",
    ]
    assert producer[4] == step08["owner_run_token"]
    assert producer[5] == sys.executable
    r_bootstrap = next(item for item in producer if "EMRYS_LOCAL_PILOT_R" in item)
    assert "R_LIBS*|R_PROFILE*|R_ENVIRON*|RENV_*|R_DEFAULT_PACKAGES" in r_bootstrap
    assert "EMRYS_USE_RENV" in r_bootstrap
    assert "RENV_PATHS_LIBRARY" in r_bootstrap
    assert "R_DEFAULT_PACKAGES" in r_bootstrap
    assert "--no-environ" not in producer
    assert str(tmp_path / "renv-library") in producer
    assert_root(step08, "--step07-root", ".FWD_like.mpileup.vcf", 2)
    assert_root(step08, "--output-root", ".step08_sites.tsv", 1)
    assert_root(step08, "--qc-root", ".step08_summary.tsv", 0)
    step09 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1"
    )
    step09_prefix = controlled_python_argv(
        sys.executable,
        "-m",
        "emrys.analyses.paired_cmh_candidate_ranking.producer",
    )
    producer_argv = tuple(step09["producer_argv"])
    assert any(
        producer_argv[index : index + len(step09_prefix)] == step09_prefix
        for index in range(len(producer_argv) - len(step09_prefix) + 1)
    )
    assert (
        next(item for item in producer_argv if "EMRYS_LOCAL_PILOT_R" in item)
        == r_bootstrap
    )
    assert "step_09_cmh_editing_site_calling.sh" not in " ".join(
        step09["producer_argv"]
    )
    assert_root(step09, "--step08-root", ".step08_sites.tsv", 1)
    assert_root(step09, "--output-root", ".cmh_all_sites.tsv", 1)
    step10 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.analysis.project_candidate_scientific_context.v1"
    )
    assert "scientific_context_projection.sh" in " ".join(step10["producer_argv"])
    assert "--motif-catalog" in step10["producer_argv"]
    assert "scientific-context-projection" in step10["validator_argv"]
    assert_root(step10, "--output-root", ".candidate_context.tsv", 1)
    assert len(step10["inputs"]) == 6
    assert len(step10["outputs"]) == 5
    assert plan.attempt_record["execution_mode"] == "local-science-tools"
    assert [item["name"] for item in plan.attempt_record["required_tools"]] == sorted(
        item["name"] for item in plan.attempt_record["required_tools"]
    )
    storage_identities = [
        item
        for item in plan.attempt_record["required_tools"]
        if item["name"] == "storage_qualification"
    ]
    assert storage_identities == [
        {
            "name": "storage_qualification",
            "version": "b" * 64,
            "path": str(tmp_path / "storage.qualified.json"),
            "resolved_path": str(
                (tmp_path / "storage.qualified.json").resolve(strict=True)
            ),
            "sha256": hashlib.sha256(
                b"fixed storage qualification receipt\n"
            ).hexdigest(),
        }
    ]
    assert all(
        set(item) == {"name", "version", "path", "resolved_path", "sha256"}
        for item in plan.attempt_record["required_tools"]
    )


def test_processing_plan_is_a_distinct_closed_31_task_run(tmp_path: Path) -> None:
    readiness, resources, _project, workspace = _readiness(tmp_path)
    full = _run_candidate(readiness, resources)
    processing = _run_candidate(readiness, resources, through="processing")
    plan = build_attempt_plan(
        processing,
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    owners = {
        str(item["machine_key"]): str(item["step_id"])
        for item in readiness.analysis.profile["owner_tasks"]
    }
    records = _dispatch_records(plan)

    assert processing.run_id != full.run_id
    assert (
        processing.analysis.revision.canonical_bytes
        == full.analysis.revision.canonical_bytes
    )
    assert processing.execution_plan.record["identity"][
        "scientific_stopping_owner_keys"
    ] == list(
        materialization.processing_stopping_owner_keys(readiness.analysis.profile)
    )
    assert plan.dispatch_count == len(records) == 31
    assert {owners[str(record["machine_key"])] for record in records} == set(
        PROCESSING_STEP_IDS
    )
    assert len({record["machine_key"] for record in records}) == 10
    assert not any(
        Path(output["path"]).is_relative_to(plan.run_root / "results")
        for record in records
        for output in record["outputs"]
    )


def test_subset_plan_materializes_one_bound_analysis_sample_manifest(
    tmp_path: Path,
) -> None:
    readiness, resources, _project_path, workspace = _readiness(
        tmp_path,
        replicate_count=3,
        sample_ids=["PUM1_3", "EV_2", "PUM1_2", "EV_3"],
    )
    plan = build_attempt_plan(
        _run_candidate(readiness, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )

    manifest = (
        plan.run_root
        / "contract"
        / "workflow-inputs"
        / plan.workflow_attempt_id
        / "samples.tsv"
    )
    selected_bytes = readiness.analysis.selected_sample_manifest_bytes
    assert selected_bytes is not None
    assert (
        {item.path: item.data for item in plan.attempt_files}[manifest]
        == selected_bytes
    )
    manifest_binding = {
        "path": str(manifest),
        "size_bytes": len(selected_bytes),
        "sha256": hashlib.sha256(selected_bytes).hexdigest(),
    }
    owners = {
        str(item["machine_key"]): str(item["step_id"])
        for item in readiness.analysis.profile["owner_tasks"]
    }
    records = _dispatch_records(plan)
    downstream = [
        record
        for record in records
        if owners[str(record["machine_key"])] in {"07", "08", "09"}
    ]
    assert downstream
    for record in downstream:
        assert str(manifest) in record["producer_argv"]
        assert str(manifest) in record["validator_argv"]
        assert any(
            all(item[key] == value for key, value in manifest_binding.items())
            for item in record["inputs"]
        )
    assert {
        str(record["scope"]["scope_id"])
        for record in records
        if record["scope"]["scope_type"] == "sample"
    } == {"EV_2", "PUM1_2", "EV_3", "PUM1_3"}

    processing = build_attempt_plan(
        _run_candidate(readiness, resources, through="processing"),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    assert not any(
        "workflow-inputs" in item.path.parts for item in processing.attempt_files
    )


@pytest.mark.parametrize(
    ("through", "message"),
    [
        ("analysis", "must stop at the exact Step 06 boundary"),
        ("processing", "requires valid, complete, successful Step 00-06 evidence"),
    ],
)
def test_processing_source_requires_an_exact_successful_processing_run(
    tmp_path: Path,
    through: str,
    message: str,
) -> None:
    plan = _plan(tmp_path, through=through)
    admit_run(plan, ops=lifecycle.default_lifecycle_ops())

    with pytest.raises(inspection.InspectionError, match=message):
        inspection.admit_processing_source(plan.run_root)


def test_processing_source_rejects_every_incompatible_target_dimension(
    tmp_path: Path,
) -> None:
    readiness, resources, _project, workspace = _readiness(tmp_path)
    source_run = _run_candidate(readiness, resources, through="processing")
    binding = {
        "source_run_id": source_run.run_id,
        "workflow_attempt_id": "workflow-20260831T120000Z-" + "1" * 32,
        "attempt_receipt_sha256": "2" * 64,
    }
    target = build_run_candidate(
        readiness.analysis,
        readiness,
        resources.declaration,
        processing_source=binding,
    )
    identity = target.analysis.revision.record["identity"]
    source_samples = [dict(row) for row in identity["samples"]]
    for condition in ("EV", "PUM1"):
        row = next(item for item in source_samples if item["condition"] == condition)
        source_samples.append(
            {**row, "sample_id": f"{condition}_3", "replicate": "3"}
        )
    source_analysis = build_analysis_revision(
        samples=source_samples,
        partitions=identity["partitions"],
        reference=identity["reference"],
        scientific_policy=identity["scientific_policy"],
    )
    source = inspection.ProcessingSourceAdmission(
        root=workspace / "runs" / source_run.run_id,
        state=SimpleNamespace(
            authority=SimpleNamespace(
                analysis_revision=source_analysis,
                execution_plan=source_run.execution_plan,
            )
        ),
        binding=binding,
        artifact_snapshots=(),
    )
    inspection.validate_processing_source(
        source,
        target_analysis=target.analysis.revision,
        target_plan=target.execution_plan,
    )

    samples = [dict(row) for row in identity["samples"]]
    samples[0]["r1_fastq_sha256"] = "3" * 64
    sample_changed = build_analysis_revision(
        samples=samples,
        partitions=identity["partitions"],
        reference=identity["reference"],
        scientific_policy=identity["scientific_policy"],
    )
    reference_changed = build_analysis_revision(
        samples=identity["samples"],
        partitions=identity["partitions"],
        reference={**identity["reference"], "fasta_sha256": "4" * 64},
        scientific_policy=identity["scientific_policy"],
    )
    different_binding = {**binding, "attempt_receipt_sha256": "5" * 64}
    binding_changed = build_run_candidate(
        readiness.analysis,
        readiness,
        resources.declaration,
        processing_source=different_binding,
    )
    resources_changed = build_run_candidate(
        readiness.analysis,
        readiness,
        replace(
            resources.declaration,
            workflow_cores=resources.declaration.workflow_cores + 1,
        ),
        processing_source=binding,
    )

    for analysis, plan, message in (
        (reference_changed, target.execution_plan, "reference identities differ"),
        (sample_changed, target.execution_plan, "not an exact subset"),
        (
            target.analysis.revision,
            binding_changed.execution_plan,
            "binds a different processing source",
        ),
        (
            target.analysis.revision,
            resources_changed.execution_plan,
            "execution semantics differ",
        ),
    ):
        with pytest.raises(inspection.InspectionError, match=message):
            inspection.validate_processing_source(
                source,
                target_analysis=analysis,
                target_plan=plan,
            )


def test_downstream_plan_rejects_an_unbound_reused_input(tmp_path: Path) -> None:
    readiness, resources, _project, workspace = _readiness(tmp_path)
    source_run_id = _run_candidate(
        readiness,
        resources,
        through="processing",
    ).run_id
    binding = {
        "source_run_id": source_run_id,
        "workflow_attempt_id": "workflow-20260831T120000Z-" + "1" * 32,
        "attempt_receipt_sha256": "2" * 64,
    }
    target = build_run_candidate(
        readiness.analysis,
        readiness,
        resources.declaration,
        processing_source=binding,
    )
    source = inspection.ProcessingSourceAdmission(
        root=workspace / "runs" / source_run_id,
        state=SimpleNamespace(),
        binding=binding,
        artifact_snapshots=(),
    )

    with pytest.raises(
        MaterializationError,
        match="Reused processing input lacks an admitted source snapshot",
    ):
        build_attempt_plan(
            target,
            readiness,
            workspace,
            resources=resources,
            operation="execute",
            processing_source=source,
        )


def _runtime_admission_fixture(
    plan: materialization.AttemptPlan,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[lifecycle.LifecycleRequest, doctor.RuntimeBinding]:
    ops = lifecycle.default_lifecycle_ops()
    admit_run(plan, ops=ops)
    request = plan.lifecycle_request
    publish_attempt(plan, ops=ops)
    monkeypatch.setattr(
        source_authority,
        "inspect_source_checkout",
        lambda **_kwargs: SimpleNamespace(
            root=plan.readiness.source_root,
            commit=plan.readiness.source_commit,
            clean=True,
        ),
    )
    monkeypatch.setattr(
        doctor,
        "validate_runtime_profile_contract",
        lambda _checks, _source_root: None,
    )
    return request, next(
        binding
        for binding in plan.readiness.bindings
        if binding.check_id == "storage_qualification"
    )


def test_runtime_admission_reuses_initial_inspection_then_reprobes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    request, storage = _runtime_admission_fixture(plan, monkeypatch)
    probes: list[Path] = []

    def inspect(_data, path, _context, **_kwargs):
        probes.append(path)
        return plan.readiness.inspection

    monkeypatch.setattr(runtime_inspector, "inspect_runtime_profile_bytes", inspect)

    lifecycle._admit_runtime_context(
        plan.attempt_record,
        request,
        storage,
        plan.readiness.inspection,
    )
    assert probes == []

    lifecycle._admit_runtime_context(plan.attempt_record, request, storage, None)
    runtime_profile = next(
        item
        for item in plan.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert probes == [Path(str(runtime_profile["path"]))]
    profile_path = Path(str(runtime_profile["resolved_path"]))
    profile_path.write_bytes(profile_path.read_bytes() + b"drift\n")
    monkeypatch.setattr(
        runtime_inspector,
        "inspect_runtime_profile_bytes",
        lambda *_args, **_kwargs: pytest.fail("drift reached external probes"),
    )

    with pytest.raises(lifecycle.LifecycleError, match="digest differs"):
        lifecycle._admit_runtime_context(
            plan.attempt_record,
            request,
            storage,
            plan.readiness.inspection,
        )


def test_attempt_plan_preserves_reporting_materialization(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    source = {**plan.run.analysis.workflow_inputs, "run_id": plan.run.run_id}
    reporting = build_reporting_bundle(
        source,
        plan.run.analysis.profile,
        plan.run.analysis.revision,
    )
    projection_data = {
        "reference_contract": reporting.reference_contract_bytes,
        "primary_analysis_policy": reporting.primary_analysis_policy_bytes,
        "reporting_run_contract": reporting.reporting_run_contract_bytes,
        "artifact_inventory": reporting.artifact_inventory_bytes,
    }
    planned_files = {
        item.path: item.data for item in (*plan.fixed_files, *plan.attempt_files)
    }
    config = _workflow_config(plan)

    for name in reporting.projection_references:
        reference = config[f"{name}_path"]
        path = plan.run_root / str(reference["path"])
        assert planned_files[path] == projection_data[name]
        assert config[f"{name}_path"] == reference
    assert plan.run_root / "contract/normalized.json" not in planned_files
    assert plan.execution_path == plan.run_root / "contract/run.json"
    assert (
        plan.attempt_record["execution_contract_sha256"]
        == plan.run.run_binding.record_sha256
    )
    assert {
        plan.run_root / "products" / "artifact-summary",
        plan.run_root / "results" / "reports",
    } <= set(plan.directories)


@pytest.mark.parametrize(
    ("through", "sample_ids"),
    (
        ("analysis", None),
        ("processing", None),
        ("analysis", ["EV_2", "PUM1_2", "EV_3", "PUM1_3"]),
    ),
    ids=("analysis", "processing", "subset-analysis"),
)
def test_direct_and_slurm_share_plan_when_resources_resolve_equally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    through: str,
    sample_ids: list[str] | None,
) -> None:
    readiness, resources, _request, workspace = _readiness(
        tmp_path,
        replicate_count=3 if sample_ids is not None else 2,
        sample_ids=sample_ids,
    )
    direct_run = _run_candidate(readiness, resources, through=through)
    scheduled_resources = resolve_resource_policy(
        resources.policy,
        AllocationCapacity(
            cores=2,
            memory_mb=2048,
            source="Slurm allocation",
            slurm_job_id="700123",
        ),
    )
    assert resources.effective_document() == scheduled_resources.effective_document()
    scheduled_run = _run_candidate(
        readiness,
        scheduled_resources,
        through=through,
    )

    assert (
        direct_run.analysis.revision.canonical_bytes,
        direct_run.execution_plan.canonical_bytes,
        direct_run.run_binding.canonical_bytes,
    ) == (
        scheduled_run.analysis.revision.canonical_bytes,
        scheduled_run.execution_plan.canonical_bytes,
        scheduled_run.run_binding.canonical_bytes,
    )

    _freeze_attempt_identity(
        monkeypatch,
        token="3" * 32,
        host="parity-host",
        process_id=456,
    )
    attempt_context = {"operation": "execute"}
    direct_plan = build_attempt_plan(
        direct_run,
        readiness,
        workspace,
        resources=resources,
        **attempt_context,
    )
    scheduled_plan = build_attempt_plan(
        scheduled_run,
        readiness,
        workspace,
        resources=scheduled_resources,
        **attempt_context,
    )

    assert direct_plan.fixed_files == scheduled_plan.fixed_files
    assert direct_plan.directories == scheduled_plan.directories
    assert tuple(
        item
        for item in direct_plan.attempt_files
        if item.path != direct_plan.config_path
    ) == tuple(
        item
        for item in scheduled_plan.attempt_files
        if item.path != scheduled_plan.config_path
    )

    direct_config = _workflow_config(direct_plan)
    scheduled_config = _workflow_config(scheduled_plan)
    direct_allocation = direct_config["resource_policy"].pop("allocation")
    scheduled_allocation = scheduled_config["resource_policy"].pop("allocation")
    assert direct_config == scheduled_config
    assert direct_allocation == {
        "cores": resources.allocation.cores,
        "memory_mb": resources.allocation.memory_mb,
        "source": "test allocation",
        "slurm_job_id": None,
    }
    assert scheduled_allocation == {
        "cores": 2,
        "memory_mb": 2048,
        "source": "Slurm allocation",
        "slurm_job_id": "700123",
    }

    direct_attempt = direct_plan.attempt_record
    scheduled_attempt = scheduled_plan.attempt_record
    assert (
        direct_attempt["workflow_config"]["sha256"]
        != scheduled_attempt["workflow_config"]["sha256"]
    )
    direct_attempt["workflow_config"].pop("sha256")
    scheduled_attempt["workflow_config"].pop("sha256")
    assert direct_attempt == scheduled_attempt

    reporting_policy = replace(
        resources.policy,
        reporting_memory_mb=tuple(
            (kind, 512) for kind, _memory in resources.policy.reporting_memory_mb
        ),
    )
    reporting_changed = resolve_resource_policy(
        reporting_policy,
        resources.allocation,
    )
    assert (
        _run_candidate(readiness, reporting_changed, through=through).run_id
        == direct_run.run_id
    )

    computational_change = replace(resources.declaration, workflow_cores=2)
    stopping = (
        None
        if through == "analysis"
        else materialization.processing_stopping_owner_keys(readiness.analysis.profile)
    )
    assert (
        build_run_candidate(
            readiness.analysis,
            readiness,
            computational_change,
            scientific_stopping_owner_keys=stopping,
        ).run_id
        != direct_run.run_id
    )
    tool_changed = replace(
        readiness,
        bindings=tuple(
            replace(binding, sha256="c" * 64) if binding.check_id == "star" else binding
            for binding in readiness.bindings
        ),
    )
    assert (
        build_run_candidate(
            readiness.analysis,
            tool_changed,
            resources.declaration,
            scientific_stopping_owner_keys=stopping,
        ).run_id
        != direct_run.run_id
    )


def test_attempt_plan_records_placement_without_making_it_run_compatibility(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readiness, resources, _request, workspace = _readiness(tmp_path)
    run = _run_candidate(readiness, resources)
    context = {
        "resources": resources,
        "operation": "execute",
    }
    _freeze_attempt_identity(
        monkeypatch,
        token="4" * 32,
        host="placement-host",
        process_id=456,
    )
    direct_placement = {
        "kind": "direct",
        "source": {"path": "/profiles/direct.yaml", "sha256": "a" * 64},
        "effective_sha256": "b" * 64,
        "request": {"kind": "direct"},
        "scheduler_job_id": None,
    }
    slurm_placement = {
        "kind": "slurm",
        "source": {"path": "/profiles/site.yaml", "sha256": "c" * 64},
        "effective_sha256": "d" * 64,
        "request": {
            "kind": "slurm",
            "account": "research",
            "partition": "compute",
            "qos": None,
            "cpus_per_task": 8,
            "memory_mb": None,
            "time": "02:00:00",
            "exclusive": True,
            "nodelist": None,
            "scratch_parent": "/scratch",
            "modules": {"mode": "none", "init": "", "load": []},
        },
        "scheduler_job_id": "700123",
    }

    historical = build_attempt_plan(run, readiness, workspace, **context)
    direct = build_attempt_plan(
        run,
        readiness,
        workspace,
        placement=direct_placement,
        **context,
    )
    scheduled = build_attempt_plan(
        run,
        readiness,
        workspace,
        placement=slurm_placement,
        **context,
    )

    assert "placement" not in historical.attempt_record
    assert direct.attempt_record["placement"] == direct_placement
    assert scheduled.attempt_record["placement"] == slurm_placement
    compatibility = inspection.attempt_fields(True)
    assert "placement" not in compatibility
    assert set(inspection.attempt_fields(False)) == {
        *compatibility,
        "source_checkout",
        "required_tools",
    }
    assert {field: direct.attempt_record[field] for field in compatibility} == {
        field: scheduled.attempt_record[field] for field in compatibility
    }


def test_run_identity_excludes_attempt_reporting_and_cli_adapter_code(
    tmp_path: Path,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    baseline = _run_candidate(readiness, resources)
    baseline_backend = backend_semantics_identity(checkout)

    report_renderer = checkout / "src/emrys/reporting/report.py"
    report_renderer.write_bytes(
        report_renderer.read_bytes() + b"\n# reporting-only change\n"
    )
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    resource_policy = (
        checkout / "src/emrys/orchestration/local_pilot/resource_policy.py"
    )
    resource_policy.write_bytes(resource_policy.read_bytes() + b"\n# policy change\n")
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    snakefile = checkout / "workflow/Snakefile"
    snakefile_bytes = snakefile.read_bytes()
    snakefile.write_bytes(snakefile_bytes + b"\n# adapter change\n")
    assert backend_semantics_identity(checkout) != baseline_backend
    assert _run_candidate(readiness, resources).run_id != baseline.run_id
    snakefile.write_bytes(snakefile_bytes)

    cli_adapter = checkout / "src/emrys/__main__.py"
    cli_adapter.write_bytes(cli_adapter.read_bytes() + b"\n# CLI adapter change\n")
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    reporting_materializer = (
        checkout / "src/emrys/orchestration/local_pilot/reporting_boundary.py"
    )
    reporting_materializer.write_bytes(
        reporting_materializer.read_bytes() + b"\n# reporting materialization change\n"
    )
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    reporting_projection = checkout / "src/emrys/contracts/orchestration/projection.py"
    reporting_projection.write_bytes(
        reporting_projection.read_bytes() + b"\n# reporting projection change\n"
    )
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    materializer = checkout / "src/emrys/orchestration/local_pilot/materialization.py"
    materializer.write_bytes(materializer.read_bytes() + b"\n# dispatch change\n")
    assert _run_candidate(readiness, resources).run_id != baseline.run_id


@pytest.mark.parametrize(
    "relative",
    (
        "src/emrys/orchestration/local_pilot/_inspection_admission.py",
        "src/emrys/orchestration/local_pilot/_inspection_attempts.py",
        "src/emrys/orchestration/local_pilot/_inspection_evidence.py",
        "src/emrys/orchestration/local_pilot/all_pass.py",
        "src/emrys/contracts/orchestration/artifact_inventory.py",
        "src/emrys/contracts/schemas/orchestration/v2/attempt_receipt.schema.json",
    ),
)
def test_run_identity_binds_semantic_admission_code(
    tmp_path: Path,
    relative: str,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    baseline_implementation = implementation_identity(checkout)
    baseline = _run_candidate(readiness, resources)

    admission = checkout / relative
    admission.write_bytes(admission.read_bytes() + b"\n# admission change\n")

    assert implementation_identity(checkout) != baseline_implementation
    assert _run_candidate(readiness, resources).run_id != baseline.run_id


def test_implementation_identity_closes_direct_scientific_dependencies(
    tmp_path: Path,
) -> None:
    checkout, _ = _clean_checkout(tmp_path)
    baseline = implementation_identity(checkout)
    dependencies = (
        ".Rprofile",
        "src/emrys/libraries/argument_parsing.sh",
        "src/emrys/libraries/executable_resolution.sh",
        "src/emrys/libraries/file_checks.sh",
        "src/emrys/libraries/gatk_invocation.sh",
        "src/emrys/libraries/input_contract.R",
        "src/emrys/libraries/signal_traps.sh",
        "src/emrys/analyses/scientific_context_projection/resources/pum_motifs_v1.tsv",
    )

    for relative in dependencies:
        path = checkout / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n# identity sensitivity\n")
        assert implementation_identity(checkout) != baseline, relative
        path.write_bytes(original)

    assert implementation_identity(checkout) == baseline


@pytest.mark.parametrize(
    ("relative", "error"),
    (
        (
            "src/emrys/orchestration/local_pilot/materialization.py",
            "implementation content",
        ),
        ("src/emrys/orchestration/local_pilot/all_pass.py", "implementation content"),
        (
            "src/emrys/contracts/orchestration/artifact_inventory.py",
            "implementation content",
        ),
        ("workflow/Snakefile", "backend semantics"),
    ),
)
def test_lifecycle_refuses_run_bound_implementation_drift_before_attempt(
    tmp_path: Path,
    relative: str,
    error: str,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, resources, _request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    plan = build_attempt_plan(
        _run_candidate(readiness, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    base = lifecycle.default_lifecycle_ops()
    ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: pytest.fail("workflow must not start"),
        host_name=lambda: plan.attempt_record["host"],
        process_id=lambda: plan.attempt_record["process_id"],
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    admit_run(plan, ops=ops)
    implementation = checkout / relative
    implementation.write_bytes(implementation.read_bytes() + b"\n# Run-bound drift\n")

    with pytest.raises(lifecycle.LifecycleError, match=error):
        lifecycle.run_materialized_attempt(
            plan.lifecycle_request,
            lambda: publish_attempt(plan, ops=ops),
            ops=ops,
        )

    assert not (plan.run_root / "attempts" / plan.workflow_attempt_id).exists()


def test_plan_passes_threads_only_to_thread_capable_tools(tmp_path: Path) -> None:
    allocation = {"00a": 1, "01": 2, "02": 3, "06": 4, "08": 2}
    plan = _plan(tmp_path, workflow_cores=4, step_threads=allocation)
    records = _dispatch_records(plan)
    threaded_owners = {
        "emrys.stage.construct_STAR_index.v1",
        "emrys.stage.align_RNA_reads_with_STAR.v1",
        "emrys.stage.construct_canonical_BAM.v1",
        "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1",
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
    }

    assert dict(plan.resources.step_threads) == allocation
    owner_steps = {
        "emrys.stage.construct_STAR_index.v1": "00a",
        "emrys.stage.align_RNA_reads_with_STAR.v1": "01",
        "emrys.stage.construct_canonical_BAM.v1": "02",
        "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1": "06",
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1": "08",
    }
    for record in records:
        producer = record["producer_argv"]
        if record["machine_key"] in threaded_owners:
            step_id = owner_steps[record["machine_key"]]
            assert producer[producer.index("--threads") + 1] == str(allocation[step_id])
        else:
            assert "--threads" not in producer


def test_plan_records_stage_specific_concurrency(tmp_path: Path) -> None:
    plan = _plan(
        tmp_path,
        workflow_cores=4,
        stage_concurrency={"01": 2, "02": 1, "06": 2},
        step_threads={"00a": 4, "01": 2, "02": 2, "06": 2, "08": 4},
    )
    argv = plan.attempt_record["snakemake_argv"]
    config = _workflow_config(plan)

    assert plan.resources.workflow_cores == 4
    assert dict(plan.resources.stage_concurrency)["01"] == 2
    assert dict(plan.resources.stage_concurrency)["02"] == 1
    assert dict(plan.resources.stage_concurrency)["06"] == 2
    assert plan.attempt_record["cores"] == 4
    assert argv[argv.index("--cores") + 1] == "4"
    resource_args = argv[argv.index("--resources") + 1 : argv.index("--nocolor")]
    assert "stage_01_slots=2" in resource_args
    assert "stage_02_slots=1" in resource_args
    assert "stage_06_slots=2" in resource_args
    effective = config["resource_policy"]["effective"]
    assert effective["step_threads"] == {
        "00a": 4,
        "01": 2,
        "02": 2,
        "06": 2,
        "08": 4,
    }
    assert effective["stage_concurrency"]["01"] == 2


def test_r_owner_bootstrap_clears_hostile_selectors_and_exports_exact_library(
    tmp_path: Path,
) -> None:
    library = tmp_path / "renv-library"
    library.mkdir()
    hostile_path = tmp_path / "hostile-path"
    hostile_path.mkdir()
    probe = tmp_path / "probe.sh"
    probe.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'RENV_PATHS_LIBRARY=%s\\n' \"$RENV_PATHS_LIBRARY\"\n"
        "printf 'R_LIBS=%s\\n' \"$R_LIBS\"\n"
        "printf 'R_DEFAULT_PACKAGES=%s\\n' \"$R_DEFAULT_PACKAGES\"\n"
        "printf 'R_PROFILE_USER=%s\\n' \"$R_PROFILE_USER\"\n"
        "if [[ ${RENV_PATHS_CACHE+x} || ${R_LIBS_CUSTOM+x} ]]; then exit 91; fi\n",
        encoding="utf-8",
    )
    command = materialization._r_owner_command(
        "/bin/bash",
        REPO_ROOT,
        library,
        ("/bin/bash", str(probe)),
    )
    assert command[-2:] == ("/bin/bash", str(probe))
    completed = subprocess.run(
        command,
        env={
            **os.environ,
            "PATH": str(hostile_path),
            "RENV_PATHS_CACHE": "/hostile/cache",
            "R_LIBS_CUSTOM": "/hostile/library",
            "R_PROFILE_SITE": "/hostile/profile",
            "R_ENVIRON_USER": "/hostile/environ",
            "R_DEFAULT_PACKAGES": "hostilePackage",
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    observed = dict(
        line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line
    )
    assert "RENV_PATHS_CACHE" not in observed
    assert "R_LIBS_CUSTOM" not in observed
    assert observed["RENV_PATHS_LIBRARY"] == str(library)
    assert observed["R_LIBS"] == str(library)
    assert observed["R_DEFAULT_PACKAGES"] == "NULL"
    assert observed["R_PROFILE_USER"] == str(REPO_ROOT / ".Rprofile")


def test_every_projected_owner_command_is_accepted_by_public_help(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    commands = {
        tuple(command)
        for record in _dispatch_records(plan)
        for command in (record["producer_argv"], record["validator_argv"])
    }

    for command in commands:
        help_command = tuple(
            "--help" if item == "--execute" else item for item in command
        )
        result = subprocess.run(
            help_command,
            cwd=REPO_ROOT,
            env={**os.environ, "XDG_CACHE_HOME": str(tmp_path / "cache")},
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, " ".join(command) + "\n" + result.stderr


def test_run_authority_is_committed_last_and_is_inspectable_without_an_attempt(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()
    published: list[Path] = []

    def observe_publication(path: Path, data: bytes) -> None:
        base.publish_bytes(path, data)
        published.append(path)

    admit_run(plan, ops=replace(base, publish_bytes=observe_publication))

    assert [path.name for path in published] == [
        "analysis.json",
        "execution-plan.json",
        "run.json",
    ]
    assert not (plan.run_root / "attempts" / plan.workflow_attempt_id).exists()
    observed = inspection.inspect_run(plan.run_root)
    assert (
        observed.integrity,
        observed.attempt_outcome,
        observed.results_status,
        observed.reporting_status,
        observed.recovery_available,
    ) == ("valid", "not_started", "incomplete", "incomplete", False)
    assert observed.authority is not None
    assert observed.run_id == plan.run.run_id
    assert observed.latest_attempt is None

    arguments = argparse.Namespace(run_root=plan.run_root, detail="normal")
    assert control.inspect_from_args(arguments) == 0
    normal = capsys.readouterr().out
    assert normal.count(f"Run ID: {plan.run.run_id}") == 1
    assert "Analysis ID:" not in normal
    assert "Execution Plan ID:" not in normal
    assert "Run root:" not in normal

    arguments.detail = "verbose"
    assert control.inspect_from_args(arguments) == 0
    verbose = capsys.readouterr().out
    assert f"Analysis ID: {plan.run.analysis.revision.analysis_revision_id}" in verbose
    assert f"Execution Plan ID: {plan.run.execution_plan.execution_plan_id}" in verbose
    assert "Attempt ID: none" in verbose

    blocked = replace(
        observed,
        tasks=(_status_task("02b", "blocked"),),
        results_blockers=("blocked task",),
    )
    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: blocked)
    assert control.inspect_from_args(arguments) == 0
    blocked_output = capsys.readouterr().out
    assert "QC evidence: blocked" in blocked_output
    assert "Verified tasks: 0/1" in blocked_output

    arguments.detail = "debug"
    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: observed)
    assert control.inspect_from_args(arguments) == 0
    debug = capsys.readouterr().out
    assert "Run authority records:" in debug
    assert f"path={plan.run_root / 'contract/execution-plan.json'}" in debug
    assert f"SHA-256={plan.run.execution_plan.record_sha256}" in debug
    assert "Effective plan: backend=local; engine=snakemake" in debug
    assert "Attempt receipt:" not in debug
    assert "Engine command:" not in debug

    historical = replace(
        observed,
        run_root=Path("/tmp/historical\x1b[31m-run"),
        authority=None,
    )
    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: historical)
    arguments.detail = "verbose"
    assert control.inspect_from_args(arguments) == 0
    historical_output = capsys.readouterr().out
    assert "Identity model: historical execution.v1" in historical_output
    assert "Analysis ID:" not in historical_output
    assert "Execution Plan ID:" not in historical_output
    assert "\x1b" not in historical_output
    assert r"\x1b" in historical_output

    arguments.detail = "debug"
    assert control.inspect_from_args(arguments) == 0
    historical_debug = capsys.readouterr().out
    assert "Historical authority record:" in historical_debug
    assert "Run authority records:" not in historical_debug
    assert "contract/execution-plan.json" not in historical_debug

    monkeypatch.setattr(
        control.inspection,
        "inspect_run",
        lambda _root: (_ for _ in ()).throw(
            inspection.InspectionError("invalid /tmp/run\x1b[31m-root")
        ),
    )
    assert control.inspect_from_args(arguments) == 2
    unsafe_error = capsys.readouterr().err
    assert "\x1b" not in unsafe_error
    assert r"\x1b" in unsafe_error

    with pytest.raises(MaterializationError, match="inspect or resume"):
        materialization.validate_run_destination(plan.run_root)
    materialization.validate_run_destination(plan.run_root, candidate=plan.run)


def test_attempt_refuses_incomplete_run_authority_before_mutex_or_materialization(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    ops = lifecycle.default_lifecycle_ops()
    admit_run(plan, ops=ops)
    (plan.run_root / "contract" / "run.json").unlink()

    def unexpected_materialization() -> None:
        raise AssertionError("materialization must remain unreachable")

    with pytest.raises(lifecycle.LifecycleError, match="successor Run"):
        lifecycle.run_materialized_attempt(
            plan.lifecycle_request,
            unexpected_materialization,
            ops=ops,
        )

    assert not (plan.run_root / "locks" / "run.lock").exists()


def test_pre_binding_failure_quarantines_only_uncommitted_run_residue(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()

    def fail_on_plan(path: Path, data: bytes) -> None:
        if path.name == "execution-plan.json":
            raise OSError("injected execution-plan publication failure")
        base.publish_bytes(path, data)

    with pytest.raises(OSError, match="execution-plan publication failure"):
        admit_run(plan, ops=replace(base, publish_bytes=fail_on_plan))

    assert not plan.run_root.exists()
    quarantines = tuple(plan.run_root.parent.glob(f"{plan.run.run_id}.uncommitted-*"))
    assert len(quarantines) == 1
    assert (quarantines[0] / "contract" / "analysis.json").is_file()
    assert not (quarantines[0] / "contract" / "run.json").exists()


def test_post_binding_interruption_completes_the_exact_pristine_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()

    def interrupt_after_binding(path: Path, data: bytes) -> None:
        base.publish_bytes(path, data)
        if path.name == "run.json":
            raise OSError("injected interruption after Run binding")

    with pytest.raises(OSError, match="after Run binding"):
        admit_run(plan, ops=replace(base, publish_bytes=interrupt_after_binding))

    authority_paths = tuple(
        plan.run_root / "contract" / name
        for name in ("analysis.json", "execution-plan.json", "run.json")
    )
    before = tuple(
        (path.read_bytes(), path.stat().st_mtime_ns) for path in authority_paths
    )

    admit_run(plan, ops=base)

    after = tuple(
        (path.read_bytes(), path.stat().st_mtime_ns) for path in authority_paths
    )
    assert after == before
    observed = inspection.inspect_run(plan.run_root)
    assert observed.integrity == "valid"
    assert observed.attempt_outcome == "not_started"
    assert all(
        (plan.run_root / name).is_dir() for name in ("attempts", "locks", "state")
    )
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: plan.readiness,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: plan.resources.allocation,
    )
    replanned = control._plan_run(
        plan.run.analysis.source_path,
        execution_profile=load_execution_profile(
            plan.run.analysis.source_path,
            config_path=plan.run.analysis.source_path.parent / "emrys.execution.yaml",
        ),
    )
    assert (
        replanned.run.run_binding.canonical_bytes
        == plan.run.run_binding.canonical_bytes
    )


def test_post_binding_failure_retains_truthful_run_authority(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()

    def obstruct_post_binding_namespace(path: Path, data: bytes) -> None:
        base.publish_bytes(path, data)
        if path.name == "run.json":
            (plan.run_root / "attempts").write_bytes(b"obstruction\n")

    with pytest.raises(MaterializationError, match="Run namespace is not a real"):
        admit_run(
            plan, ops=replace(base, publish_bytes=obstruct_post_binding_namespace)
        )

    authority = inspection.admit_successor_run(plan.run_root)
    assert authority is not None
    assert authority.run_binding.run_id == plan.run.run_id
    assert tuple(plan.run_root.parent.glob(f"{plan.run.run_id}.uncommitted-*")) == ()
    assert inspection.inspect_run(plan.run_root).integrity == "blocked"


def test_locked_publication_terminalizes_failure_and_refuses_repeat(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()
    ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: _after_plan(plan),
        host_name=lambda: plan.attempt_record["host"],
        process_id=lambda: plan.attempt_record["process_id"],
        process_is_alive=lambda _pid: False,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )

    admit_run(plan, ops=ops)
    outcome = lifecycle.run_materialized_attempt(
        plan.lifecycle_request,
        lambda: publish_attempt(plan, ops=ops),
        ops=ops,
    )

    assert outcome.receipt["status"] == "failed"
    assert outcome.receipt["snakemake_exit_code"] == 9
    assert outcome.released_lock_path.is_file()
    assert not (plan.run_root / "locks/run.lock").exists()
    assert len(list((plan.run_root / "contract/dispatch").rglob("*.json"))) == 35
    with pytest.raises(MaterializationError, match="inspect or resume"):
        admit_run(plan, ops=ops)


def _failed_run(plan):
    ops = replace(
        lifecycle.default_lifecycle_ops(),
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: _after_plan(plan),
        host_name=lambda: plan.attempt_record["host"],
        process_id=lambda: plan.attempt_record["process_id"],
        process_is_alive=lambda _pid: False,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    if isinstance(plan.run, materialization.HistoricalRun):
        for item in plan.fixed_files:
            item.path.parent.mkdir(parents=True, exist_ok=True)
            item.path.write_bytes(item.data)
        for name in ("attempts", "locks", "state"):
            (plan.run_root / name).mkdir()
    else:
        admit_run(plan, ops=ops)
    outcome = lifecycle.run_materialized_attempt(
        plan.lifecycle_request,
        lambda: publish_attempt(plan, ops=ops),
        ops=ops,
    )
    assert outcome.receipt["status"] == "failed"
    observed = inspection.inspect_run(plan.run_root)
    assert observed.recovery_available, observed.blockers
    return observed


def _patch_resume_control(
    monkeypatch: pytest.MonkeyPatch,
    observed,
    readiness,
    resources,
    selected,
) -> None:
    def inspect_readiness(
        _project: Path,
        _workspace: Path,
        runtime_profile: Path,
        **_kwargs: object,
    ) -> doctor.DoctorResult:
        legacy = (
            yaml.safe_load(readiness.analysis.source_bytes)["schema_version"]
            == "emrys.request.v3"
        )
        assert _kwargs == {
            "storage_requirement": "direct",
            "analysis_name": None if legacy else readiness.analysis.evidence_label,
            "expected_analysis_revision": (
                None
                if observed.authority is None
                else observed.authority.analysis_revision
            ),
            "allow_legacy": legacy,
        }
        selected.append(runtime_profile)
        return readiness

    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: observed)
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        inspect_readiness,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: resources.allocation,
    )


def test_legacy_resume_reuses_predecessor_retained_runtime_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readiness, resources, request, workspace = _readiness(
        tmp_path,
        legacy=True,
    )
    analysis = readiness.analysis
    symbolic_policy = replace(
        resources.policy,
        declaration=replace(
            resources.declaration,
            workflow_memory_mb="allocation",
        ),
    )
    resources = resolve_resource_policy(
        symbolic_policy,
        AllocationCapacity(cores=1, memory_mb=16_384, source="first allocation"),
    )
    legacy, legacy_bytes = _historical_execution_v1(analysis)
    first = build_attempt_plan(
        materialization.HistoricalRun(
            analysis=analysis,
            run_id=str(legacy["run_id"]),
            execution_projection_bytes=legacy_bytes,
        ),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    observed = _failed_run(first)
    assert observed.authority is None
    retained = next(
        Path(str(item["path"]))
        for item in first.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "label: first label",
            "label: renamed label",
        ),
        encoding="utf-8",
    )
    renamed_project = admit_project(
        request,
        REPO_ROOT / "workflow/contracts/local_cmh_v2.json",
        allow_legacy=True,
    )
    onboarding.runtime_profile_path(analysis.source_path).unlink()
    fallback_readiness = replace(
        readiness,
        project=renamed_project,
        analysis=renamed_project.select_analysis(),
        inspection=replace(readiness.inspection, profile_path=retained),
    )
    selected: list[Path] = []
    _patch_resume_control(
        monkeypatch,
        observed,
        fallback_readiness,
        resolve_resource_policy(
            symbolic_policy,
            AllocationCapacity(cores=1, memory_mb=8_192, source="resume allocation"),
        ),
        selected,
    )
    second = control._plan_resume(
        first.run_root,
        execution_profile=load_execution_profile(request),
        profile_resources_explicit=False,
    )

    assert selected == [retained]
    assert second.attempt_record["request_label"] == "renamed label"
    assert second.resources.workflow_memory_mb == 8_192
    assert (
        second.attempt_record["required_tools"]
        == first.attempt_record["required_tools"]
    )
    assert not {
        retained,
        second.run_root
        / "contract/runtime-profiles"
        / f"{second.workflow_attempt_id}.tsv",
    } & {item.path for item in second.attempt_files}


@pytest.mark.parametrize("legacy", (False, True))
@pytest.mark.parametrize("through", ("analysis", "processing"))
def test_successor_resume_snapshots_current_runtime_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    legacy: bool,
    through: str,
) -> None:
    first = _plan(tmp_path, legacy=legacy, through=through)
    observed = _failed_run(first)
    assert observed.authority is not None
    retained = next(
        Path(str(item["path"]))
        for item in first.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    onboarding.runtime_profile_path(first.run.analysis.source_path).unlink()
    fallback_readiness = replace(
        first.readiness,
        inspection=replace(first.readiness.inspection, profile_path=retained),
    )
    selected: list[Path] = []
    _patch_resume_control(
        monkeypatch,
        observed,
        fallback_readiness,
        first.resources,
        selected,
    )
    second = control._plan_resume(
        first.run_root,
        execution_profile=load_execution_profile(first.run.analysis.source_path),
        profile_resources_explicit=False,
    )

    new_profile = next(
        Path(str(item["path"]))
        for item in second.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert selected == [retained]
    assert new_profile != retained
    assert new_profile == (
        second.run_root
        / "contract/runtime-profiles"
        / f"{second.workflow_attempt_id}.tsv"
    )
    assert [item.data for item in second.attempt_files if item.path == new_profile] == [
        first.readiness.inspection.profile_bytes
    ]
    assert (
        second.run.execution_plan.canonical_bytes
        == first.run.execution_plan.canonical_bytes
    )


def test_project_v1_predecessor_does_not_enable_request_v3_resume(
    tmp_path: Path,
) -> None:
    first = _plan(tmp_path / "current")
    _failed_run(first)
    legacy = build_legacy(tmp_path / "legacy")
    first.run.analysis.source_path.write_bytes(legacy.read_bytes())

    with pytest.raises(
        control.ControlError,
        match="emrys.request.v3 is historical",
    ):
        control._plan_resume(
            first.run_root,
            execution_profile=load_execution_profile(first.run.analysis.source_path),
            profile_resources_explicit=False,
        )


def test_successor_resume_allows_relocated_checkout_and_new_runtime_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_source = tmp_path / "first-source"
    second_source = tmp_path / "second-source"
    first_source.mkdir()
    second_source.mkdir()
    checkout_one, commit_one = _clean_checkout(first_source)
    checkout_two, commit_two = _clean_checkout(second_source)
    readiness_one, resources, _request, workspace = _readiness(
        tmp_path / "first-case",
        source_root=checkout_one,
        source_commit=commit_one,
    )
    readiness_two, _unused_resources, _request_two, _workspace_two = _readiness(
        tmp_path / "second-case",
        source_root=checkout_two,
        source_commit=commit_two,
    )
    runtime_bytes = b"different admitted runtime profile\n"
    readiness_two.inspection.profile_path.write_bytes(runtime_bytes)
    runtime_sha256 = hashlib.sha256(runtime_bytes).hexdigest()
    readiness_two = replace(
        readiness_two,
        project=readiness_one.project,
        analysis=readiness_one.analysis,
        inspection=replace(
            readiness_two.inspection,
            profile_sha256=runtime_sha256,
            profile_bytes=runtime_bytes,
        ),
    )
    symbolic_policy = replace(
        resources.policy,
        declaration=replace(
            resources.declaration,
            workflow_memory_mb="allocation",
        ),
        reporting_memory_mb=tuple(
            (kind, "workflow") for kind, _memory in resources.policy.reporting_memory_mb
        ),
    )
    first_resources = resolve_resource_policy(
        symbolic_policy,
        AllocationCapacity(
            cores=1,
            memory_mb=32_768,
            source="first test allocation",
        ),
    )

    run_one = _run_candidate(readiness_one, first_resources)
    run_two = _run_candidate(readiness_two, first_resources)
    assert run_two.run_id == run_one.run_id

    first = build_attempt_plan(
        run_one,
        readiness_one,
        workspace,
        resources=first_resources,
        operation="execute",
    )
    base = lifecycle.default_lifecycle_ops()
    first_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: _after_plan(first),
        host_name=lambda: first.attempt_record["host"],
        process_id=lambda: first.attempt_record["process_id"],
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    admit_run(first, ops=first_ops)
    first_outcome = lifecycle.run_materialized_attempt(
        first.lifecycle_request,
        lambda: publish_attempt(first, ops=first_ops),
        ops=first_ops,
    )
    assert first_outcome.receipt["status"] == "failed"

    selected_runtime_profiles: list[Path] = []

    def inspect_second_runtime(
        _request: Path,
        _workspace: Path,
        runtime_profile: Path,
        **_kwargs: object,
    ) -> doctor.DoctorResult:
        assert _kwargs == {
            "storage_requirement": "slurm",
            "analysis_name": "primary",
            "expected_analysis_revision": first.run.analysis.revision,
            "allow_legacy": False,
        }
        selected_runtime_profiles.append(runtime_profile)
        return readiness_two

    source = readiness_one.analysis.workflow_inputs
    old_locator = Path(source["samples"]["rows"][0]["r1_fastq"]["path"])
    relocated = tmp_path / "relocated-inputs" / old_locator.name
    relocated.parent.mkdir()
    shutil.copy2(old_locator, relocated)
    source["samples"]["rows"][0]["r1_fastq"]["path"] = str(relocated)
    relocated_analysis = replace(
        readiness_one.analysis,
        _workflow_input_bytes=orchestration_contracts.canonical_json_bytes(source),
    )
    readiness_two = replace(
        readiness_two,
        project=readiness_one.project,
        analysis=relocated_analysis,
    )
    relocated_run = _run_candidate(readiness_two, first_resources)
    assert old_locator.is_file() and relocated.is_file()
    assert relocated_run.run_id == run_one.run_id
    assert relocated_analysis.workflow_inputs != readiness_one.analysis.workflow_inputs

    resume_profile = load_execution_profile(
        readiness_one.project.source_path,
        config_path=_slurm_profile(tmp_path),
    )
    monkeypatch.setattr(control.doctor, "inspect_local_pilot", inspect_second_runtime)
    monkeypatch.setattr(control.inspection, "inspect_run", inspection.inspect_run)
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: AllocationCapacity(
            cores=1,
            memory_mb=16_384,
            source="second test allocation",
        ),
    )
    second = control._plan_resume(
        first.run_root,
        execution_profile=resume_profile,
        profile_resources_explicit=False,
        scheduler_job_id="700123",
    )
    assert selected_runtime_profiles == [
        onboarding.runtime_profile_path(readiness_one.project.source_path)
    ]
    assert second.execution_path == first.execution_path
    effective_resume_profile = replace(
        resume_profile,
        resource_policy=second.resources.policy,
    )
    assert second.attempt_record["placement"] == (
        effective_resume_profile.attempt_placement("700123")
    )
    assert (
        second.attempt_record["execution_contract_sha256"]
        == first.attempt_record["execution_contract_sha256"]
        == run_one.run_binding.record_sha256
    )
    second_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: _after_plan(second),
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    second_outcome = lifecycle.run_materialized_attempt(
        second.lifecycle_request,
        lambda: publish_attempt(second, ops=second_ops),
        ops=second_ops,
    )

    assert second_outcome.receipt["status"] == "failed"
    assert second.resources.workflow_memory_mb == 16_384
    assert set(dict(second.resources.reporting_memory_mb).values()) == {16_384}
    first_runtime = next(
        item
        for item in first.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    second_runtime = next(
        item
        for item in second.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert (
        first.attempt_record["source_checkout"]
        != second.attempt_record["source_checkout"]
    )
    assert first_runtime["path"] != second_runtime["path"]
    assert first_runtime["sha256"] != second_runtime["sha256"]
    observed = inspection.inspect_run(second.run_root)
    assert observed.recovery_available, observed.blockers
    assert len(tuple((second.run_root / "attempts").iterdir())) == 2


def test_attempt_publication_leaves_star_index_directory_for_owner(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    step00a = next(
        record
        for record in _dispatch_records(plan)
        if record["machine_key"] == "emrys.stage.construct_STAR_index.v1"
    )
    outputs = tuple(Path(item["path"]) for item in step00a["outputs"])
    index_directories = {path.parent for path in outputs}
    assert len(outputs) == 15
    assert len(index_directories) == 1
    index_directory = next(iter(index_directories))
    workflow_entry_checked = False

    def inspect_workflow_entry(
        _argv: tuple[str, ...], _cwd: Path
    ) -> lifecycle.WorkflowResult:
        nonlocal workflow_entry_checked
        assert index_directory.parent.is_dir()
        assert not index_directory.exists()
        workflow_entry_checked = True
        return lifecycle.WorkflowResult(9, None)

    base = lifecycle.default_lifecycle_ops()
    ops = replace(
        base,
        run_workflow=inspect_workflow_entry,
        now=lambda: _after_plan(plan),
        host_name=lambda: plan.attempt_record["host"],
        process_id=lambda: plan.attempt_record["process_id"],
        process_is_alive=lambda _pid: False,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )

    admit_run(plan, ops=ops)
    outcome = lifecycle.run_materialized_attempt(
        plan.lifecycle_request,
        lambda: publish_attempt(plan, ops=ops),
        ops=ops,
    )

    assert workflow_entry_checked
    assert outcome.receipt["status"] == "failed"


def test_lock_precedes_attempt_publication_failure_and_retains_evidence(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()

    def fail_on_config(path: Path, data: bytes) -> None:
        if path == plan.config_path:
            raise OSError("injected config publication failure")
        base.publish_bytes(path, data)

    ops = replace(
        base,
        publish_bytes=fail_on_config,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    admit_run(plan, ops=ops)

    with pytest.raises(lifecycle.LifecycleError, match="materialize"):
        lifecycle.run_materialized_attempt(
            plan.lifecycle_request,
            lambda: publish_attempt(plan, ops=ops),
            ops=ops,
        )

    assert not (plan.run_root / "locks/run.lock").exists()
    assert (
        plan.run_root / "locks" / f"released-{plan.workflow_attempt_id}-run-lock.json"
    ).is_file()
    assert not (plan.run_root / "attempts" / plan.workflow_attempt_id).exists()
    assert list((plan.run_root / "contract/dispatch").rglob("*.json"))
    assert inspection.inspect_run(plan.run_root).integrity == "blocked"


def test_waiting_stale_resume_exits_before_attempt_materialization(
    tmp_path: Path,
) -> None:
    readiness, resources, _request, workspace = _readiness(tmp_path)
    initial = build_attempt_plan(
        _run_candidate(readiness, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    base = lifecycle.default_lifecycle_ops()
    common_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: _after_plan(initial, minutes=30),
        host_name=lambda: initial.attempt_record["host"],
        process_id=lambda: initial.attempt_record["process_id"],
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage, _inspection: None,
    )
    initial_ops = replace(
        common_ops,
        now=lambda: _after_plan(initial),
    )
    admit_run(initial, ops=initial_ops)
    first = lifecycle.run_materialized_attempt(
        initial.lifecycle_request,
        lambda: publish_attempt(initial, ops=initial_ops),
        ops=initial_ops,
    )
    assert first.receipt["status"] == "failed"
    assert inspection.inspect_run(initial.run_root).recovery_available

    def resume_plan():
        return build_attempt_plan(
            initial.run,
            readiness,
            workspace,
            resources=resources,
            operation="resume",
            supersedes_workflow_attempt_id=initial.workflow_attempt_id,
            retained_dispatches={},
        )

    winner = resume_plan()
    stale = resume_plan()
    context = multiprocessing.get_context("fork")
    winner_entered = context.Event()
    release_winner = context.Event()
    winner_result = context.Queue()
    contender_entered_mutex = False
    contender_acquired_mutex = threading.Event()
    acquired_while_winner_held: list[bool] = []
    release_threads: list[threading.Thread] = []
    stale_materialized = False

    def observed_mutex(event: str, _path: Path) -> None:
        nonlocal contender_entered_mutex
        if event == "before_wait":
            contender_entered_mutex = True
            releaser = threading.Thread(
                target=lambda: (
                    acquired_while_winner_held.append(
                        contender_acquired_mutex.wait(timeout=0.1)
                    ),
                    release_winner.set(),
                )
            )
            release_threads.append(releaser)
            releaser.start()
        elif event == "after_acquire":
            contender_acquired_mutex.set()

    def wait_then_fail(_argv: tuple[str, ...], _cwd: Path) -> lifecycle.WorkflowResult:
        winner_entered.set()
        if not release_winner.wait(timeout=10):
            raise AssertionError("fixture did not release serialized winner")
        return lifecycle.WorkflowResult(9, None)

    winner_ops = replace(
        common_ops,
        run_workflow=wait_then_fail,
    )
    stale_ops = replace(common_ops, observe_mutex=observed_mutex)

    def run_winner() -> None:
        try:
            outcome = lifecycle.run_materialized_attempt(
                winner.lifecycle_request,
                lambda: publish_attempt(winner, ops=winner_ops),
                ops=winner_ops,
            )
            winner_result.put(("ok", outcome.receipt["status"]))
        except BaseException as exc:  # pragma: no cover - asserted below
            winner_result.put(("error", repr(exc)))

    def materialize_stale() -> None:
        nonlocal stale_materialized
        stale_materialized = True
        publish_attempt(stale, ops=stale_ops)

    winner_process = context.Process(target=run_winner)
    winner_process.start()
    if not winner_entered.wait(timeout=10):
        release_winner.set()
        winner_process.join(timeout=10)
        pytest.fail("serialized winner did not enter workflow")
    try:
        with pytest.raises(lifecycle.LifecycleError) as stale_error:
            lifecycle.run_materialized_attempt(
                stale.lifecycle_request,
                materialize_stale,
                ops=stale_ops,
            )
    finally:
        release_winner.set()
        winner_process.join(timeout=10)

    assert not winner_process.is_alive()
    assert winner_process.exitcode == 0
    assert winner_result.get(timeout=1) == ("ok", "failed")
    for releaser in release_threads:
        releaser.join(timeout=1)
    assert contender_entered_mutex
    assert acquired_while_winner_held == [False]
    assert "exact latest workflow attempt" in str(stale_error.value)
    assert not stale_materialized
    assert not (stale.run_root / "locks" / "run.lock").exists()
    assert not (
        stale.run_root / "locks" / f"released-{stale.workflow_attempt_id}-run-lock.json"
    ).exists()
    assert not (stale.run_root / "attempts" / stale.workflow_attempt_id).exists()
    assert all(not item.path.exists() for item in stale.attempt_files)
    mutex = stale.run_root / "locks" / "acquire.mutex"
    assert mutex.is_file() and not mutex.is_symlink() and mutex.read_bytes() == b""
    observed = inspection.inspect_run(stale.run_root)
    assert observed.recovery_available, observed.blockers
    assert observed.latest_attempt is not None
    assert observed.latest_attempt["workflow_attempt_id"] == winner.workflow_attempt_id


def test_public_run_dry_run_is_no_write(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[object] = []
    arguments, workspace = _patch_run_control(
        tmp_path,
        monkeypatch,
        execute_plan=lambda plan, _observe, _inspection: executed.append(plan),
        transform_plan=lambda plan: plan,
    )

    projections = {}
    workspace = arguments.project.parent
    for level in ("normal", "verbose", "debug"):
        monkeypatch.setattr(
            control.sys,
            "stdin",
            _InputStream(
                AssertionError("unconfirmed input was read"),
                terminal=level == "normal",
            ),
        )
        arguments.log_level = level
        assert control.run_from_args(arguments) == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        projections[level] = captured.err
        assert "Dry-run complete" in captured.err
        assert "Execute this plan?" not in captured.err
        assert not (workspace / "runs").exists()
        assert not (workspace / "logs").exists()

    normal = projections["normal"]
    assert "Project: 'project'" in normal
    assert "Analysis: 'primary'" in normal
    assert "Run ID:" in normal
    assert "Scientific boundary: complete analysis" in normal
    assert "Work: 35 pending, 0 reusable" in normal
    assert "Reporting: automatic after scientific work" in normal
    assert "Evidence boundary:" in normal
    for hidden in (
        "Operation:",
        "Analysis ID:",
        "Execution Plan ID:",
        "Run root:",
        "Resources:",
        "Step thread allocations:",
        "Stage concurrency:",
        "Snakemake command:",
        "TASK ",
    ):
        assert hidden not in normal

    verbose = projections["verbose"]
    assert set(normal.splitlines()) <= set(verbose.splitlines())
    assert "Analysis revision: analysis-" in verbose
    assert "Execution Plan ID: plan-" in verbose
    assert "Run root:" in verbose
    assert "Resources: 1 cores, 1024 MiB" in verbose
    assert "Step thread allocations:" in verbose
    assert "Stage concurrency:" in verbose
    assert "Snakemake command:" not in verbose

    debug = projections["debug"]
    assert set(verbose.splitlines()) <= set(debug.splitlines())
    assert "Snakemake command:" in debug
    assert "TASK " in debug
    assert executed == []


def test_processing_run_dry_run_is_no_write_and_truthfully_scoped(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments, workspace = _patch_run_control(
        tmp_path,
        monkeypatch,
        execute_plan=lambda *_args: pytest.fail("dry-run executed processing"),
        transform_plan=lambda plan: plan,
    )
    arguments.through = "processing"
    monkeypatch.setattr(
        control.sys,
        "stdin",
        _InputStream(AssertionError("nonterminal input was read"), terminal=False),
    )

    assert control.run_from_args(arguments) == 0

    rendered = capsys.readouterr().err
    assert (
        "Scientific boundary: sample processing (through Step 06)" in rendered
    )
    assert "Work: 31 pending, 0 reusable" in rendered
    assert "Reporting: not applicable to this partial scientific Run" in rendered
    assert "Dry-run complete; no workspace state was written." in rendered
    assert not (workspace / "runs").exists()
    assert not (workspace / "logs").exists()


@pytest.mark.parametrize(
    ("response", "expected_exit"),
    (("yes\n", 1), ("n\n", 0), ("", 0), (KeyboardInterrupt(), None)),
)
def test_interactive_run_confirms_exact_plan_before_every_write(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    response,
    expected_exit: int | None,
) -> None:
    planned = []
    executed = []
    runtime_inspections: list[RuntimeInspection | None] = []

    def transform(plan):
        planned.append(plan)
        return plan

    def execute(plan, _observe, initial_runtime_inspection):
        executed.append(plan)
        runtime_inspections.append(initial_runtime_inspection)
        return lifecycle.LifecycleOutcome(
            attempt_path=plan.run_root / "attempt.json",
            receipt_path=plan.run_root / "attempt-receipt.json",
            lock_path=plan.run_root / "locks/run.lock",
            released_lock_path=plan.run_root / "locks/released.json",
            receipt={"status": "failed"},
            workflow_result=None,
        )

    arguments, workspace = _patch_run_control(
        tmp_path,
        monkeypatch,
        execute_plan=execute,
        transform_plan=transform,
    )
    log_root = tmp_path / "application-logs"
    arguments.log_root = log_root

    def before_read() -> None:
        assert not (workspace / "runs").exists()
        assert not (workspace / "logs").exists()
        assert not log_root.exists()
        assert executed == []

    monkeypatch.setattr(control.sys, "stdin", _InputStream(response, before_read))
    monkeypatch.setattr(control.sys, "stderr", _TerminalOutput(control.sys.stderr))
    if expected_exit is None:
        with pytest.raises(KeyboardInterrupt):
            control.run_from_args(arguments)
    else:
        assert control.run_from_args(arguments) == expected_exit

    rendered = capsys.readouterr().err
    assert rendered.count("Run ID:") == 1
    assert rendered.index("Run ID:") < rendered.index("Execute this plan? [y/N]")
    if expected_exit == 1:
        assert len(planned) == len(executed) == 1
        assert executed[0] is planned[0]
        assert runtime_inspections == [None]
        assert list(log_root.rglob("*.jsonl"))
    else:
        assert len(planned) == 1 and executed == []
        assert runtime_inspections == []
        assert not (workspace / "runs").exists()
        assert not (workspace / "logs").exists()
        assert not log_root.exists()


def test_interactive_resume_uses_the_same_no_write_gate(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    monkeypatch.setattr(control, "_plan_resume", lambda *_args, **_kwargs: plan)
    monkeypatch.setattr(control.sys, "stdin", _InputStream("no\n"))
    monkeypatch.setattr(control.sys, "stderr", _TerminalOutput(control.sys.stderr))
    arguments = argparse.Namespace(
        run_root=plan.run_root,
        execution_profile=None,
        log_level=None,
        log_root=None,
        execute=False,
    )

    assert control.resume_from_args(arguments) == 0

    rendered = capsys.readouterr().err
    assert "Execute this plan? [y/N]" in rendered
    assert "Dry-run complete; no resume state was written." in rendered
    assert not plan.run_root.exists()


def test_public_execute_logs_and_terminalizes_doctor_failure_before_run_state(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _readiness_result, _resources, request, workspace = _readiness(tmp_path)
    opened = []
    real_open = control.open_attempt_log

    def capture_open(**kwargs):
        attempt = real_open(**kwargs)
        opened.append(attempt)
        return attempt

    def reject_readiness(*_args, **_kwargs):
        log_paths = list((workspace / "logs/application").rglob("*.jsonl"))
        assert len(log_paths) == 1
        records = [json.loads(line) for line in log_paths[0].read_text().splitlines()]
        assert [record["event"] for record in records] == ["attempt_opened"]
        raise doctor.DoctorInputError("injected Doctor failure")

    monkeypatch.setattr(control, "open_attempt_log", capture_open)
    monkeypatch.setattr(control.doctor, "inspect_local_pilot", reject_readiness)
    arguments = argparse.Namespace(
        project=request,
        execution_profile=request.parent / "emrys.execution.yaml",
        log_level=None,
        log_root=None,
        execute=True,
    )

    assert control.run_from_args(arguments) == 2

    assert len(opened) == 1
    with pytest.raises(ApplicationLogError, match="closed"):
        opened[0].logger(component="test", phase="after_preflight")
    log_paths = list((workspace / "logs/application").rglob("*.jsonl"))
    assert len(log_paths) == 1
    records = [json.loads(line) for line in log_paths[0].read_text().splitlines()]
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "attempt_failed",
    ]
    assert records[-1]["phase"] == "preflight"
    assert not (workspace / "runs").exists()
    assert not list(workspace.rglob("run.lock"))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "injected Doctor failure" in captured.err
    assert "phase=preflight status=failed" in captured.err
    assert f"Application log: {log_paths[0]}" in captured.err


def test_execute_preflight_interrupt_terminalizes_log_and_preserves_signal(
    tmp_path: Path,
    capsys,
) -> None:
    plan = _plan(tmp_path)
    controls = LogControls(
        LogLevel.NORMAL,
        tmp_path / "application-logs",
        "default",
        "default",
    )

    with pytest.raises(KeyboardInterrupt):
        control._execute_plan(
            lambda: (_ for _ in ()).throw(KeyboardInterrupt),
            controls=controls,
            workspace=plan.workspace,
            mode="execute",
            scope_id="pending",
            entrypoint="emrys-run",
        )

    records = [
        json.loads(line)
        for line in next(controls.root.rglob("*.jsonl")).read_text().splitlines()
    ]
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "attempt_interrupted",
    ]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "phase=preflight status=interrupted" in captured.err
    assert "Next action: Retry when ready." in captured.err


def test_execute_failure_summary_names_owned_lock_and_recovery(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    lock_path = plan.run_root / "locks" / "run.lock"
    recovery_path = (
        plan.run_root / "attempts" / plan.workflow_attempt_id / "released-run-lock.json"
    )

    def fail_with_owned_paths(_plan, _observe, _inspection):
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text("owned", encoding="utf-8")
        recovery_path.parent.mkdir(parents=True)
        recovery_path.write_text("owned", encoding="utf-8")
        raise lifecycle.LifecycleError("injected lifecycle failure")

    controls = LogControls(
        LogLevel.NORMAL,
        tmp_path / "application-logs",
        "default",
        "default",
    )
    _patch_lifecycle_execution(monkeypatch, plan, fail_with_owned_paths)

    with pytest.raises(control.ControlError, match="injected lifecycle failure"):
        control._execute_plan(
            lambda: plan,
            controls=controls,
            workspace=plan.workspace,
            mode="execute",
            scope_id="pending",
            entrypoint="emrys-run",
            report_enabled=False,
        )

    captured = capsys.readouterr()
    assert f"Owned lock: {lock_path}" in captured.err
    assert f"Owned recovery: {recovery_path}" in captured.err


def test_public_resume_logs_inspection_failure_before_run_state(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    run_root = workspace / "runs" / "run-preflight"

    def reject_inspection(_root: Path) -> inspection.RunInspection:
        raise inspection.InspectionError("injected resume inspection failure")

    monkeypatch.setattr(control.inspection, "inspect_run", reject_inspection)
    arguments = argparse.Namespace(
        run_root=run_root,
        execution_profile=None,
        log_level=None,
        log_root=None,
        execute=True,
    )

    assert control.resume_from_args(arguments) == 2

    log_path = next((workspace / "logs/application").rglob("*.jsonl"))
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "attempt_failed",
    ]
    assert records[0]["scope_id"] == "run-preflight"
    assert not (workspace / "runs").exists()
    captured = capsys.readouterr()
    assert "injected resume inspection failure" in captured.err
    assert "phase=preflight status=failed" in captured.err


def _slurm_profile(tmp_path: Path, *, cpus_per_task: int = 4) -> Path:
    profile = tmp_path / "slurm.yaml"
    profile.write_text(
        yaml.safe_dump(
            {
                "schema_version": "emrys.execution-profile.v1",
                "placement": {
                    "kind": "slurm",
                    "account": None,
                    "partition": None,
                    "qos": None,
                    "cpus_per_task": cpus_per_task,
                    "memory_mb": None,
                    "time": "01:00:00",
                    "exclusive": False,
                    "nodelist": None,
                    "scratch_parent": str(tmp_path / "scratch"),
                    "modules": {"mode": "none", "init": "", "load": []},
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return profile


def test_new_run_doctor_storage_requirement_tracks_execution_placement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readiness, _resources, project_path, _workspace = _readiness(tmp_path)
    requirements: list[str] = []

    def diagnose(
        _project_path: Path,
        *,
        storage_requirement: str,
        analysis_name: str | None,
    ):
        assert analysis_name is None
        requirements.append(storage_requirement)
        return readiness

    monkeypatch.setattr(control.doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: AllocationCapacity(
            cores=4,
            memory_mb=16_384,
            source="placement test allocation",
        ),
    )

    direct = load_execution_profile(project_path)
    slurm = load_execution_profile(
        project_path,
        config_path=_slurm_profile(tmp_path),
    )
    assert (
        control._plan_run(
            project_path,
            execution_profile=direct,
        ).attempt_record["placement"]["kind"]
        == "direct"
    )
    assert (
        control._plan_run(
            project_path,
            execution_profile=slurm,
            scheduler_job_id="700123",
        ).attempt_record["placement"]["kind"]
        == "slurm"
    )
    assert requirements == ["direct", "slurm"]


def _scheduled_run_arguments(tmp_path: Path, *, execute: bool) -> argparse.Namespace:
    return argparse.Namespace(
        project=tmp_path / "project.yaml",
        analysis="sensitivity",
        execution_profile=_slurm_profile(tmp_path),
        log_level=None,
        log_root=None,
        execute=execute,
    )


def test_public_slurm_rejects_cpu_shortfall_before_submission(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    arguments.execution_profile = _slurm_profile(tmp_path, cpus_per_task=3)
    monkeypatch.setattr(
        control.slurm_submission,
        "plan_submission",
        lambda *_args, **_kwargs: pytest.fail(
            "CPU shortfall reached submission planning"
        ),
    )

    assert control.run_from_args(arguments) == 2
    assert (
        "Slurm CPUs per task cannot be lower than workflow cores: 3 < 4"
        in capsys.readouterr().err
    )
    assert not (arguments.project.parent / "logs").exists()


@pytest.mark.parametrize(
    ("workflow_cores", "cpus_per_task", "expected_exit"),
    ((8, 4, 2), (2, 2, 0)),
    ids=("inherited-shortfall", "inherited-exact-fit"),
)
def test_public_slurm_resume_admits_inherited_workflow_cores_before_submission(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    workflow_cores: int,
    cpus_per_task: int,
    expected_exit: int,
) -> None:
    first = _plan(tmp_path, workflow_cores=workflow_cores)
    _failed_run(first)
    arguments = argparse.Namespace(
        run_root=first.run_root,
        execution_profile=_slurm_profile(
            tmp_path,
            cpus_per_task=cpus_per_task,
        ),
        log_level=None,
        log_root=None,
        execute=True,
    )
    submissions = []
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda submission: submissions.append(submission) or "812345",
    )
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: pytest.fail(
            "submit host performed compute-allocation readiness"
        ),
    )

    assert control.resume_from_args(arguments) == expected_exit
    captured = capsys.readouterr()
    if expected_exit == 2:
        assert submissions == []
        assert (
            "Slurm CPUs per task cannot be lower than workflow cores: 4 < 8"
            in captured.err
        )
        assert not (first.workspace / "logs").exists()
    else:
        assert len(submissions) == 1
        assert captured.out.startswith("JOB_ID=812345\n")


def test_public_slurm_dry_run_is_no_write_and_skips_compute_readiness(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=False)
    monkeypatch.setattr(
        control.sys,
        "stdin",
        _InputStream(AssertionError("nonterminal input was read"), terminal=False),
    )
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda _plan: pytest.fail("dry-run submitted a scheduler job"),
    )
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: pytest.fail(
            "submit host performed compute-allocation readiness"
        ),
    )

    projections = {}
    workspace = arguments.project.parent
    for level in ("normal", "verbose", "debug"):
        arguments.log_level = level
        assert control.run_from_args(arguments) == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        projections[level] = captured.err
        assert "Execute this plan?" not in captured.err
        assert not (workspace / "logs").exists()

    normal = projections["normal"]
    assert "Execution placement: Slurm" in normal
    assert "Dry-run complete; no scheduler or workspace state was written." in normal
    assert "Execution profile:" not in normal
    assert "Scheduler stdout:" not in normal
    assert "Scheduler stderr:" not in normal
    assert "Scheduler command:" not in normal

    verbose = projections["verbose"]
    assert set(normal.splitlines()) <= set(verbose.splitlines())
    assert f"Execution profile: {arguments.execution_profile}" in verbose
    assert f"Scheduler stdout: {workspace}/logs/emrys-local-pilot-%j.out" in verbose
    assert f"Scheduler stderr: {workspace}/logs/emrys-local-pilot-%j.err" in verbose
    assert "Scheduler command:" not in verbose

    debug = projections["debug"]
    assert set(verbose.splitlines()) <= set(debug.splitlines())
    assert "Scheduler command:" in debug


@pytest.mark.parametrize("execute", (False, True))
def test_public_slurm_submits_once_only_after_confirmation_or_execute(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    execute: bool,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=execute)
    arguments.analysis = "" if execute else "sensitivity"
    arguments.through = "analysis" if execute else "processing"
    arguments.from_processing_run = "run-" + "a" * 64 if execute else None
    arguments.no_report = True
    workspace = arguments.project.parent
    submissions = []

    def submit(plan):
        submissions.append(plan)
        return "812345"

    if not execute:

        def before_read() -> None:
            assert submissions == []
            assert not (workspace / "logs").exists()

        monkeypatch.setattr(control.sys, "stdin", _InputStream("y\n", before_read))
        monkeypatch.setattr(control.sys, "stderr", _TerminalOutput(control.sys.stderr))
    monkeypatch.setattr(control.slurm_submission, "submit", submit)
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: pytest.fail(
            "submit host performed compute-allocation readiness"
        ),
    )

    assert control.run_from_args(arguments) == 0

    captured = capsys.readouterr()
    assert captured.out == (
        "JOB_ID=812345\n"
        f"OUT={workspace}/logs/emrys-local-pilot-812345.out\n"
        f"ERR={workspace}/logs/emrys-local-pilot-812345.err\n"
    )
    assert len(submissions) == 1
    expected_analysis = "''" if execute else "sensitivity"
    assert f" --analysis {expected_analysis} " in submissions[0].batch_script
    if execute:
        assert " --through processing " not in submissions[0].batch_script
        assert (
            " --from-processing-run run-" + "a" * 64 + " "
            in submissions[0].batch_script
        )
    else:
        assert " --through processing " in submissions[0].batch_script
        assert " --from-processing-run " not in submissions[0].batch_script
    assert " --execute --no-report" in submissions[0].batch_script
    assert list((workspace / "logs").iterdir()) == []
    assert "Execution placement: Slurm" in captured.err
    assert ("Execute this plan? [y/N]" in captured.err) is not execute


def test_private_slurm_delegate_rejects_profile_drift_before_readiness(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    scheduler = control.slurm_submission
    monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
    monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, "0" * 64)
    monkeypatch.setenv(scheduler.SUBMIT_UID_ENV, str(os.getuid()))
    monkeypatch.setenv("SLURM_JOB_ID", "812345")
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: pytest.fail("digest drift reached compute readiness"),
    )

    assert control.run_from_args(arguments) == 2
    assert "Execution-profile SHA-256 differs" in capsys.readouterr().err
    assert not (arguments.project.parent / "logs").exists()


@pytest.mark.parametrize(
    "report_mode",
    ("disabled", "success", "failure"),
)
def test_direct_execution_owns_receipt_ordered_reporting_log(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    report_mode: str,
) -> None:
    plan = _plan(tmp_path)
    receipt_path = tmp_path / "attempt-receipt.json"
    receipt_bytes = b"immutable scientific receipt\n"
    lock_path = tmp_path / "run.lock"
    released_lock_path = tmp_path / "released-lock.json"
    lock_path.write_text("active\n")
    observed_events = []
    report_calls = []
    runtime_inspections = []

    def execute(_plan, observe, initial_runtime_inspection):
        runtime_inspections.append(initial_runtime_inspection)
        for event_name in ("analysis_started", "publication_ready"):
            observed_events.append(event_name)
            observe(event_name)
        receipt_path.write_bytes(receipt_bytes)
        lock_path.replace(released_lock_path)
        return lifecycle.LifecycleOutcome(
            attempt_path=tmp_path / "attempt.json",
            receipt_path=receipt_path,
            lock_path=lock_path,
            released_lock_path=released_lock_path,
            receipt={"status": "succeeded"},
            workflow_result=None,
        )

    controls = LogControls(
        LogLevel.NORMAL,
        tmp_path / "application-logs",
        "default",
        "default",
    )

    def report(run_root: Path, *, execute: bool):
        if report_mode == "disabled":
            pytest.fail("--no-report invoked reporting")
        events = [
            json.loads(line)["event"]
            for line in next(controls.root.rglob("*.jsonl")).read_text().splitlines()
        ]
        report_calls.append(
            (
                run_root,
                execute,
                receipt_path.read_bytes(),
                lock_path.exists(),
                released_lock_path.exists(),
                events[-2:],
            )
        )
        if report_mode == "failure":
            raise reporting_operation.ReportingOperationError("injected failure")
        return reporting_operation.ReportingOperationOutcome(
            status="generated",
            verified_report_locations=(
                ("scientific-report-html", tmp_path / "scientific.html"),
                ("evidence-report-html", tmp_path / "evidence.html"),
            ),
        )

    _patch_lifecycle_execution(monkeypatch, plan, execute)
    monkeypatch.setattr(reporting_operation, "run_reporting", report)

    status = control._execute_plan(
        lambda: plan,
        controls=controls,
        workspace=plan.workspace,
        mode="execute",
        scope_id="pending",
        entrypoint="emrys-run",
        report_enabled=report_mode != "disabled",
    )

    assert status == (1 if report_mode == "failure" else 0)
    assert report_calls == (
        []
        if report_mode == "disabled"
        else [
            (
                plan.run_root,
                True,
                receipt_bytes,
                False,
                True,
                ["attempt_receipt_observed", "reporting_started"],
            )
        ]
    )
    assert receipt_path.read_bytes() == receipt_bytes
    events = [
        json.loads(line)["event"]
        for line in next(controls.root.rglob("*.jsonl")).read_text().splitlines()
    ]
    reporting_events = {
        "disabled": ["reporting_skipped"],
        "success": ["reporting_started", "reporting_completed"],
        "failure": ["reporting_started", "reporting_failed"],
    }
    assert (
        events
        == [
            "attempt_opened",
            "analysis_prepared",
            "analysis_started",
            "publication_ready",
            "attempt_receipt_observed",
        ]
        + reporting_events[report_mode]
    )
    assert observed_events == ["analysis_started", "publication_ready"]
    assert runtime_inspections == [plan.readiness.inspection]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"Evidence: {receipt_path}" in captured.err
    if report_mode == "failure":
        assert "Scientific Results remain complete" in captured.err
        assert f"emrys report --run-root {plan.run_root} --execute" in captured.err


@pytest.mark.parametrize(
    ("fault", "expected_events"),
    (
        ("write", ["attempt_opened", "analysis_prepared"]),
        (
            "sync",
            [
                "attempt_opened",
                "analysis_prepared",
                "analysis_started",
                "publication_ready",
            ],
        ),
    ),
)
def test_application_log_degradation_cannot_change_receipt_or_exit(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    expected_events: list[str],
) -> None:
    plan = _plan(tmp_path)
    receipt_path = tmp_path / "attempt-receipt.json"
    receipt_bytes = b"authoritative receipt\n"

    def execute(_plan, observe, _inspection):
        observe("analysis_started")
        observe("publication_ready")
        receipt_path.write_bytes(receipt_bytes)
        return lifecycle.LifecycleOutcome(
            attempt_path=tmp_path / "attempt.json",
            receipt_path=receipt_path,
            lock_path=tmp_path / "run.lock",
            released_lock_path=tmp_path / "released-lock.json",
            receipt={"status": "succeeded"},
            workflow_result=None,
        )

    controls = LogControls(
        LogLevel.NORMAL,
        tmp_path / "application-logs",
        "default",
        "default",
    )
    if fault == "write":
        real_write = ApplicationLogFile.write_bytes
        write_count = 0

        def fail_third_write(file: ApplicationLogFile, payload: bytes) -> None:
            nonlocal write_count
            write_count += 1
            if write_count == 3:
                raise ApplicationLogStorageError(
                    "injected application-log write failure"
                )
            real_write(file, payload)

        monkeypatch.setattr(ApplicationLogFile, "write_bytes", fail_third_write)
    else:

        def reject_sync(_file: ApplicationLogFile) -> None:
            raise ApplicationLogStorageError("injected application-log sync failure")

        monkeypatch.setattr(ApplicationLogFile, "synchronize", reject_sync)
    _patch_lifecycle_execution(monkeypatch, plan, execute)

    status = control._execute_plan(
        lambda: plan,
        controls=controls,
        workspace=plan.workspace,
        mode="execute",
        scope_id="pending",
        entrypoint="emrys-run",
        report_enabled=False,
    )

    assert status == 0
    assert receipt_path.read_bytes() == receipt_bytes
    records = [
        json.loads(line)
        for line in next(controls.root.rglob("*.jsonl")).read_text().splitlines()
    ]
    assert [record["event"] for record in records] == expected_events
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("Application logging degraded") == 1
    assert "Evidence: " + str(receipt_path) in captured.err


@pytest.mark.parametrize(
    (
        "outcome_status",
        "execute_requested",
        "logging_fails",
    ),
    (
        ("planned", False, False),
        ("reused", False, False),
        ("generated", True, False),
        ("generated", True, True),
        ("reused", True, False),
    ),
)
def test_standalone_report_logging_boundary(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    outcome_status: str,
    execute_requested: bool,
    logging_fails: bool,
) -> None:
    workspace = tmp_path / "workspace"
    run_root = workspace / "runs" / ("run-" + "a" * 64)
    run_root.mkdir(parents=True)
    calls: list[bool] = []
    locations = (
        ("scientific-report-html", run_root / "scientific.html"),
        ("evidence-report-html", run_root / "evidence.html"),
    )

    def report(
        _root: Path,
        *,
        execute: bool,
        observe_generation_start=None,
    ):
        calls.append(execute)
        if execute and outcome_status == "generated":
            assert observe_generation_start is not None
            observe_generation_start()
        return reporting_operation.ReportingOperationOutcome(
            status=outcome_status,
            verified_report_locations=(
                locations if outcome_status != "planned" else ()
            ),
        )

    if logging_fails:

        def reject_log(**_kwargs):
            raise ApplicationLogError(
                "injected standalone-report log failure",
                stage="open",
                path=None,
            )

        monkeypatch.setattr(control, "open_attempt_log", reject_log)
    arguments = argparse.Namespace(
        run_root=run_root,
        execute=execute_requested,
        log_level=None,
        log_root=None,
    )
    monkeypatch.setattr(reporting_operation, "run_reporting", report)

    assert control.report_from_args(arguments) == 0
    generated = execute_requested and outcome_status == "generated"
    assert calls == [execute_requested]
    rendered = capsys.readouterr().err
    assert f"Reporting: {outcome_status}" in rendered
    log_paths = list((workspace / "logs" / "application").rglob("*.jsonl"))
    if logging_fails:
        assert log_paths == []
        assert "Application logging unavailable for reporting" in rendered
    elif generated:
        assert len(log_paths) == 1
        records = [json.loads(line) for line in log_paths[0].read_text().splitlines()]
        assert [record["event"] for record in records] == [
            "attempt_opened",
            "reporting_started",
            "reporting_completed",
        ]
    else:
        assert log_paths == []


def test_next_supported_action_uses_separated_status_domains() -> None:
    def action(
        integrity: str = "valid",
        attempt: str = "succeeded",
        results: str = "complete",
        reporting: str = "complete",
        recovery: bool = False,
    ) -> str:
        return control._next_supported_action(
            SimpleNamespace(
                integrity=integrity,
                attempt_outcome=attempt,
                results_status=results,
                reporting_status=reporting,
                recovery_available=recovery,
                run_root=Path("/run"),
            )
        )

    assert action(integrity="blocked") == (
        "Preserve this Run; review Run integrity blockers. Do not resume."
    )
    assert action(attempt="blocked", results="blocked", reporting="incomplete") == (
        "Preserve this Run; review scientific Results blockers. Do not resume."
    )
    assert action(reporting="blocked") == (
        "Preserve completed Results; do not rerun science. Review blockers."
    )
    assert action(attempt="blocked", results="incomplete", reporting="incomplete") == (
        "Preserve this Run; review retained evidence. Do not resume."
    )
    assert action(
        attempt="not_started", results="incomplete", reporting="incomplete"
    ) == ("Repeat the original emrys run invocation and confirm execution.")
    running = "Wait for the active Attempt to finish, then inspect the Run again."
    assert (
        action(attempt="running", results="incomplete", reporting="incomplete")
        == running
    )
    assert action(attempt="running") == running
    resume = "Use emrys resume for this Run; review and confirm the plan."
    assert (
        action(
            attempt="failed",
            results="incomplete",
            reporting="incomplete",
            recovery=True,
        )
        == resume
    )
    assert (
        action(
            attempt="interrupted",
            results="incomplete",
            reporting="incomplete",
            recovery=True,
        )
        == resume
    )
    assert action() == "Review the verified Results and report paths."
    assert action(reporting="incomplete") == (
        "Generate reports with emrys report --run-root /run --execute."
    )
    assert action(reporting="not applicable") == (
        "Inspect this Run's verified scientific artifacts with --detail debug."
    )


def _status_task(
    step_id: str,
    state: inspection.TaskState,
    index: int = 0,
) -> inspection.TaskInspection:
    expected = inspection.ExpectedTask(
        machine_key=f"owner-{step_id}",
        step_id=step_id,
        scope_type="sample",
        scope_id=f"scope-{index}",
    )
    return inspection.TaskInspection(expected, state, None, None)


def test_status_milestones_partition_steps_and_derive_persisted_progress() -> None:
    declared_steps = [
        step_id for _label, steps in control._MILESTONE_STEPS for step_id in steps
    ]
    assert len(declared_steps) == len(set(declared_steps)) == 14
    assert set(declared_steps) == {
        "00a",
        "00b",
        "00c",
        "01",
        "02",
        "02b",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
    }
    progress = control._milestone_progress(
        (
            *(_status_task(step, "verified") for step in ("00a", "00b", "00c")),
            _status_task("01", "verified"),
            _status_task("02", "pending"),
            _status_task("02b", "blocked"),
            _status_task("09", "pending"),
        )
    )

    assert progress == (
        ("Preparation", "complete", 3, 3),
        ("Alignment and sample processing", "incomplete", 1, 2),
        ("QC evidence", "blocked", 0, 1),
        ("Candidate evidence", "not applicable", 0, 0),
        ("Statistical/context processing", "incomplete", 0, 1),
    )


def test_attempt_elapsed_uses_only_current_or_latest_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = "2026-08-12T20:00:00Z"
    latest = {"created_at": created}
    current = [datetime(2026, 8, 12, 20, 1, 30, tzinfo=UTC)]

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return current[0]

    monkeypatch.setattr(control, "datetime", FixedDateTime)

    assert (
        control._attempt_elapsed_line(
            SimpleNamespace(latest_attempt=None, attempt_outcome="not_started"),
        )
        == "Attempt elapsed: unavailable — no Attempt"
    )
    assert (
        control._attempt_elapsed_line(
            SimpleNamespace(
                latest_attempt=latest,
                latest_receipt=None,
                attempt_outcome="running",
            ),
        )
        == "Current Attempt elapsed: 0:01:30"
    )
    assert (
        control._attempt_elapsed_line(
            SimpleNamespace(
                latest_attempt={
                    **latest,
                    "supersedes_workflow_attempt_id": "workflow-earlier",
                },
                latest_receipt={"finished_at": "2026-08-12T20:02:00Z"},
                attempt_outcome="failed",
            ),
        )
        == "Latest Attempt elapsed: 0:02:00"
    )
    current[0] = datetime(2026, 8, 12, 19, 59, 59, 200_000, tzinfo=UTC)
    assert "invalid timestamp boundary" in control._attempt_elapsed_line(
        SimpleNamespace(
            latest_attempt=latest,
            latest_receipt=None,
            attempt_outcome="running",
        ),
    )


def test_public_help_routes() -> None:
    for command, expected in (
        (("run", "--help"), "usage: emrys run"),
        (("resume", "--help"), "usage: emrys resume"),
        (
            ("inspect", "run", "--help"),
            "usage: emrys inspect run",
        ),
    ):
        result = subprocess.run(
            [sys.executable, "-I", "-m", "emrys", *command],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert expected in result.stdout
        if command[0] == "run":
            assert "--through {analysis,processing}" in result.stdout
            assert "--from-processing-run" in result.stdout
        if command[0] == "resume":
            assert "--through" not in result.stdout


def _clean_checkout(tmp_path: Path) -> tuple[Path, str]:
    checkout = tmp_path / "clean-checkout"
    checkout.mkdir()
    for name in (".Rprofile", "pyproject.toml", "uv.lock", "renv.lock"):
        shutil.copy2(REPO_ROOT / name, checkout)
    shutil.copytree(REPO_ROOT / "src", checkout / "src")
    shutil.copytree(REPO_ROOT / "workflow", checkout / "workflow")
    subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
    subprocess.run(["git", "add", "."], cwd=checkout, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EMRYS Fixture",
            "-c",
            "user.email=emrys-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "B5 no-science source",
        ],
        cwd=checkout,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return checkout, commit


def _doubled_lifecycle_ops(
    base: lifecycle.LifecycleOps,
    *,
    fail_after_rule: str | None = None,
) -> lifecycle.LifecycleOps:
    def run_workflow(
        argv: tuple[str, ...], cwd: Path
    ) -> lifecycle.WorkflowResult:
        separator = argv.index("--")
        invoked = (
            (*argv[:separator], "--until", fail_after_rule, *argv[separator:])
            if fail_after_rule is not None
            else argv
        )
        completed = subprocess.run(
            invoked,
            cwd=cwd,
            env={**os.environ, "XDG_CACHE_HOME": str(cwd / "cache")},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        injected = fail_after_rule is not None and completed.returncode == 0
        return lifecycle.WorkflowResult(
            exit_code=23 if injected else completed.returncode,
            termination_signal=None,
            message=(
                "controlled failure between owner tasks"
                if injected
                else completed.stdout if completed.returncode else None
            ),
        )

    def admit_storage(
        attempt: Mapping[str, object],
        _execution: Mapping[str, object],
    ) -> None:
        assert attempt["execution_mode"] == "local-science-tools"
        return None

    def admit_runtime(
        attempt: Mapping[str, object],
        _request: lifecycle.LifecycleRequest,
        storage_binding: doctor.RuntimeBinding | None,
        _initial_inspection: RuntimeInspection | None,
    ) -> None:
        assert attempt["execution_mode"] == "local-science-tools"
        assert storage_binding is None

    return replace(
        base,
        run_workflow=run_workflow,
        admit_storage_context=admit_storage,
        admit_runtime_context=admit_runtime,
    )


def _verified_snapshot(root: Path) -> dict[Path, tuple[bytes, int]]:
    verified = root / "state/verified"
    return {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in verified.rglob("*.json")
    }


def test_public_adapter_executes_failure_and_byte_preserving_resume(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, resources, request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    real_build = control.build_attempt_plan
    real_ops = control.lifecycle.default_lifecycle_ops
    fail_after_rule: list[str | None] = ["construct_canonical_BAM"]
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: readiness,
    )
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: readiness,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: resources.allocation,
    )
    monkeypatch.setattr(
        control,
        "build_attempt_plan",
        lambda *args, **kwargs: with_owner_doubles(real_build(*args, **kwargs)),
    )
    monkeypatch.setattr(
        control.lifecycle,
        "default_lifecycle_ops",
        lambda: _doubled_lifecycle_ops(
            real_ops(),
            fail_after_rule=fail_after_rule[0],
        ),
    )
    run_arguments = argparse.Namespace(
        project=request,
        execution_profile=request.parent / "emrys.execution.yaml",
        allocated_cores=1,
        execute=True,
    )
    run_id = _run_candidate(readiness, resources).run_id

    assert control.run_from_args(run_arguments) == 1
    failed_output = capsys.readouterr().err
    assert "Results:" not in failed_output.splitlines()
    run_root = workspace / "runs" / run_id
    failed = inspection.inspect_run(run_root)
    assert failed.recovery_available
    assert failed.verified_report_locations == ()
    before = _verified_snapshot(run_root)
    assert 0 < len(before) < 35

    fail_after_rule[0] = None
    resume_arguments = argparse.Namespace(
        run_root=run_root,
        allocated_cores=1,
        execute=False,
    )
    assert control.resume_from_args(resume_arguments) == 0
    dry_output = capsys.readouterr().err
    assert "Work:" in dry_output and " reusable" in dry_output
    assert "Results:" not in dry_output.splitlines()
    assert _verified_snapshot(run_root) == before

    resume_arguments.execute = True
    assert control.resume_from_args(resume_arguments) == 0
    resumed_output = capsys.readouterr().err
    report_root = run_root / "results" / "reports" / run_id
    expected_results = (
        "Results:\n"
        f"  Scientific report: {report_root}/{run_id}.scientific_report.html\n"
        f"  Evidence report: {report_root}/{run_id}.evidence_report.html\n"
    )
    assert expected_results in resumed_output
    completed = inspection.inspect_run(run_root)
    assert completed.authority is not None
    assert (
        completed.integrity,
        completed.attempt_outcome,
        completed.results_status,
        completed.reporting_status,
        completed.recovery_available,
    ) == ("valid", "succeeded", "complete", "complete", False)
    assert completed.verified_report_locations == (
        (
            "scientific-report-html",
            report_root / f"{run_id}.scientific_report.html",
        ),
        (
            "evidence-report-html",
            report_root / f"{run_id}.evidence_report.html",
        ),
    )
    after = _verified_snapshot(run_root)
    assert all(after[path] == value for path, value in before.items())

    inspect_arguments = argparse.Namespace(run_root=run_root, detail="normal")
    assert control.inspect_from_args(inspect_arguments) == 0
    inspect_output = capsys.readouterr().out
    assert "Attempt outcome: succeeded" in inspect_output
    assert "Scientific Results: complete" in inspect_output
    assert "Reporting: complete" in inspect_output
    assert (
        "Next supported action: Review the verified Results and report paths."
        in inspect_output
    )
    assert "Scientific milestones:" in inspect_output
    assert "Current Attempt elapsed:" not in inspect_output
    assert "Latest Attempt elapsed:" in inspect_output
    assert "Run root:" not in inspect_output
    assert "Analysis ID:" not in inspect_output
    assert "Execution Plan ID:" not in inspect_output
    assert "Engine command:" not in inspect_output
    inspect_arguments.detail = "verbose"
    assert control.inspect_from_args(inspect_arguments) == 0
    verbose_output = capsys.readouterr().out
    assert f"Run root: {run_root}" in verbose_output
    assert (
        f"Analysis ID: {completed.authority.analysis_revision.analysis_revision_id}"
        in verbose_output
    )
    assert (
        f"Execution Plan ID: {completed.authority.execution_plan.execution_plan_id}"
        in verbose_output
    )
    assert "Attempt ID:" in verbose_output
    assert "Reporting transactions:" in verbose_output
    assert "Engine command:" not in verbose_output
    inspect_arguments.detail = "debug"
    assert control.inspect_from_args(inspect_arguments) == 0
    debug_output = capsys.readouterr().out
    assert "Engine command:" in debug_output
    assert "Attempt receipt:" in debug_output
    assert "Run authority records:" in debug_output
    assert (
        f"SHA-256={completed.authority.analysis_revision.record_sha256}" in debug_output
    )
    assert f"SHA-256={completed.authority.execution_plan.record_sha256}" in debug_output
    assert f"SHA-256={completed.authority.run_binding.record_sha256}" in debug_output
    assert "Effective plan: backend=local; engine=snakemake" in debug_output
    assert "TASK " in debug_output
    assert "OUTPUT " in debug_output
    assert "size=" in debug_output and "SHA-256=" in debug_output
    first_output = next(
        output
        for inspected in completed.tasks
        if inspected.record is not None
        for output in inspected.record["outputs"]
    )
    assert (
        f"OUTPUT {first_output['role']}: path={first_output['path']}; "
        f"size={first_output['size_bytes']}; SHA-256={first_output['sha256']}"
        in debug_output
    )
    assert "stdout.log" in debug_output and "stderr.log" in debug_output
    assert _verified_snapshot(run_root) == after
    assert expected_results in inspect_output

    resume_arguments.execute = False
    assert control.resume_from_args(resume_arguments) == 2
    assert "Results are complete" in capsys.readouterr().err


def test_public_downstream_run_reuses_processing_without_mutating_its_source(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, resources, project, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
        replicate_count=3,
    )
    authored = yaml.safe_load(project.read_text(encoding="utf-8"))
    authored["analyses"]["sensitivity"] = {
        **authored["analyses"]["primary"],
        "fdr_threshold": 0.01,
        "sample_ids": ["EV_2", "PUM1_2", "EV_3", "PUM1_3"],
    }
    authored["analyses"]["source-drift"] = {
        **authored["analyses"]["sensitivity"],
        "fdr_threshold": 0.02,
    }
    project.write_text(yaml.safe_dump(authored, sort_keys=False), encoding="utf-8")
    admitted_project = admit_project(project, readiness.analysis.profile)
    primary = replace(
        readiness,
        project=admitted_project,
        analysis=admitted_project.select_analysis("primary"),
    )
    sensitivity = replace(
        readiness,
        project=admitted_project,
        analysis=admitted_project.select_analysis("sensitivity"),
    )
    source_drift = replace(
        readiness,
        project=admitted_project,
        analysis=admitted_project.select_analysis("source-drift"),
    )
    assert (
        primary.analysis.revision.canonical_bytes
        != sensitivity.analysis.revision.canonical_bytes
    )
    assert len(primary.analysis.workflow_inputs["samples"]["rows"]) == 6
    assert len(sensitivity.analysis.workflow_inputs["samples"]["rows"]) == 4

    def diagnose(*_args, **kwargs):
        selected = kwargs.get("analysis_name")
        return {
            "primary": primary,
            "sensitivity": sensitivity,
            "source-drift": source_drift,
        }[selected or "primary"]

    real_build = control.build_attempt_plan
    real_ops = control.lifecycle.default_lifecycle_ops
    fail_after_rule: list[str | None] = [None]
    monkeypatch.setattr(control.doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        control.doctor,
        "inspect_local_pilot",
        lambda *_args, **_kwargs: sensitivity,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: resources.allocation,
    )
    monkeypatch.setattr(
        control,
        "build_attempt_plan",
        lambda *args, **kwargs: with_owner_doubles(real_build(*args, **kwargs)),
    )
    monkeypatch.setattr(
        control.lifecycle,
        "default_lifecycle_ops",
        lambda: _doubled_lifecycle_ops(
            real_ops(),
            fail_after_rule=fail_after_rule[0],
        ),
    )

    source_arguments = argparse.Namespace(
        project=project,
        analysis="primary",
        execution_profile=project.parent / "emrys.execution.yaml",
        through="processing",
        execute=True,
    )
    source_run_id = _run_candidate(
        primary,
        resources,
        through="processing",
    ).run_id
    assert control.run_from_args(source_arguments) == 0

    source_root = workspace / "runs" / source_run_id
    validate_verified = task.validate_verified_task
    admitted_records: list[Path] = []

    def count_admission(path: Path, **kwargs):
        admitted_records.append(path)
        return validate_verified(path, **kwargs)

    monkeypatch.setattr(task, "validate_verified_task", count_admission)
    source = inspection.admit_processing_source(source_root)
    assert len(admitted_records) == len(source.state.tasks)
    monkeypatch.setattr(task, "validate_verified_task", validate_verified)
    with pytest.raises(control.ControlError, match="Results are complete"):
        control._admit_resume_predecessor(source_root)
    rendered_source = capsys.readouterr()
    assert "Reporting: not applicable" in rendered_source.err

    source_verified = _verified_snapshot(source_root)
    source_artifacts = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for snapshot in source.artifact_snapshots
        if (path := Path(str(snapshot["path"]))).is_file()
    }

    fail_after_rule[0] = "generate_partitioned_cohort_mpileup_VCFs"
    target_arguments = argparse.Namespace(
        project=project,
        analysis="sensitivity",
        execution_profile=project.parent / "emrys.execution.yaml",
        through="analysis",
        from_processing_run=source_run_id,
        execute=True,
    )
    assert control.run_from_args(target_arguments) == 1
    capsys.readouterr()
    fail_after_rule[0] = None

    target_roots = tuple(
        path for path in (workspace / "runs").iterdir() if path.name != source_run_id
    )
    assert len(target_roots) == 1
    target_root = target_roots[0]
    receipt_path = next(target_root.glob("attempts/*/attempt-receipt.json"))
    failed_receipt = orchestration_contracts.load_record(
        receipt_path,
        "attempt-receipt",
    )
    assert failed_receipt["status"] == "failed"
    assert failed_receipt["blockers"] == []
    assert not tuple((target_root / "state/reporting").glob("*/start.json"))
    failed = inspection.inspect_run(target_root)
    assert failed.recovery_available

    assert (
        control.resume_from_args(
            argparse.Namespace(
                run_root=target_root,
                allocated_cores=1,
                execute=True,
            )
        )
        == 0
    )
    capsys.readouterr()

    completed = inspection.inspect_run(target_root)
    assert (
        completed.integrity,
        completed.attempt_outcome,
        completed.results_status,
        completed.reporting_status,
    ) == ("valid", "succeeded", "complete", "complete")
    assert len(completed.tasks) == 4
    assert all(task.state == "verified" for task in completed.tasks)
    selected_ids = ["EV_2", "PUM1_2", "EV_3", "PUM1_3"]
    selected_manifests = tuple(
        target_root.glob("contract/workflow-inputs/*/samples.tsv")
    )
    assert len(selected_manifests) == 2
    assert all(
        step08.validate_sample_manifest(path)[1] == selected_ids
        for path in selected_manifests
    )
    orientation_root = source_root / "products" / "native" / "orientation"
    consumed_orientation_samples = {
        Path(str(item["path"])).relative_to(orientation_root).parts[0]
        for dispatch_path in target_root.glob("contract/dispatch/*/*/*.json")
        for item in orchestration_contracts.load_json_object(dispatch_path)["inputs"]
        if Path(str(item["path"])).is_relative_to(orientation_root)
    }
    assert consumed_orientation_samples == set(selected_ids)
    assert _verified_snapshot(source_root) == source_verified
    assert all(
        path.read_bytes() == data and path.stat().st_mtime_ns == modified
        for path, (data, modified) in source_artifacts.items()
    )

    source_snapshots = {
        str(snapshot["path"]): snapshot for snapshot in source.artifact_snapshots
    }
    assert any(
        item.get("size_bytes") == source_snapshots[item["path"]]["size_bytes"]
        and item.get("sha256") == source_snapshots[item["path"]]["sha256"]
        for dispatch_path in target_root.glob("contract/dispatch/*/*/*.json")
        for item in orchestration_contracts.load_json_object(dispatch_path)["inputs"]
        if item["path"] in source_snapshots
    )

    assert (
        control.inspect_from_args(
            argparse.Namespace(run_root=target_root, detail="verbose")
        )
        == 0
    )
    inspect_output = capsys.readouterr().out
    assert "Preparation: reused" in inspect_output
    assert "Alignment and sample processing: reused" in inspect_output
    assert "QC evidence: reused" in inspect_output
    assert f"Processing source: {source_run_id} (admitted)" in inspect_output

    mutated_source: list[tuple[Path, bytes, int]] = []

    def drift_workflow(
        _argv: tuple[str, ...],
        _cwd: Path,
    ) -> lifecycle.WorkflowResult:
        drift_root = next(
            path
            for path in (workspace / "runs").iterdir()
            if path not in {source_root, target_root}
        )
        consumed = {
            Path(str(item["path"]))
            for dispatch_path in drift_root.glob("contract/dispatch/*/*/*.json")
            for item in orchestration_contracts.load_json_object(dispatch_path)[
                "inputs"
            ]
        }
        path = next(
            candidate
            for candidate in source_artifacts
            if candidate.is_relative_to(source_root) and candidate not in consumed
        )
        data, modified = source_artifacts[path]
        mutated_source.append((path, data, modified))
        path.write_bytes(b"mutated after downstream workflow\n")
        return lifecycle.WorkflowResult(23, None, "controlled failure")

    drift_ops = replace(
        _doubled_lifecycle_ops(real_ops()),
        run_workflow=drift_workflow,
    )
    monkeypatch.setattr(
        control.lifecycle,
        "default_lifecycle_ops",
        lambda: drift_ops,
    )
    assert (
        control.run_from_args(
            argparse.Namespace(
                project=project,
                analysis="source-drift",
                execution_profile=project.parent / "emrys.execution.yaml",
                through="analysis",
                from_processing_run=source_run_id,
                execute=True,
            )
        )
        == 1
    )
    capsys.readouterr()
    drift_roots = tuple(
        path
        for path in (workspace / "runs").iterdir()
        if path not in {source_root, target_root}
    )
    assert len(drift_roots) == 1
    drift_root = drift_roots[0]
    drift_receipt = orchestration_contracts.load_record(
        next(drift_root.glob("attempts/*/attempt-receipt.json")),
        "attempt-receipt",
    )
    assert drift_receipt["status"] == "blocked"
    assert any(
        "Processing source changed during workflow execution" in blocker
        for blocker in drift_receipt["blockers"]
    )
    assert len(mutated_source) == 1
    mutated_path, original_data, original_mtime = mutated_source[0]
    mutated_path.write_bytes(original_data)
    os.utime(
        mutated_path,
        ns=(mutated_path.stat().st_atime_ns, original_mtime),
    )
    inspection.admit_processing_source(source_root)
    assert not inspection.inspect_run(drift_root).recovery_available
    assert (
        control.resume_from_args(
            argparse.Namespace(
                run_root=drift_root,
                allocated_cores=1,
                execute=True,
            )
        )
        == 2
    )
    assert "not at an admissible between-task resume boundary" in capsys.readouterr().err
