"""Direct contracts for the fixed production run-coordinator materializer."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import multiprocessing
import os
import selectors
import shutil
import signal
import subprocess
import sys
import threading
import time
import zlib
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import emrys.libraries.installed_package_identity as installed_package_identity
from emrys import analyses as analysis_modules
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration import artifact_inventory
from emrys.contracts.orchestration.application_model import (
    PROCESSING_STEP_IDS,
    build_module_analysis_revision,
    execution_plan_boundary,
)
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.contracts.scientific_evidence import step08
from emrys.evidence.runtime_availability import inspector as runtime_inspector
from emrys.evidence.runtime_availability.inspector import (
    RuntimeBinding,
    runtime_file_bindings,
    RuntimeInspection,
    RuntimeObservation,
    load_runtime_policy,
    runtime_profile_bytes,
    runtime_profile_checks,
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
from emrys.orchestration.run_coordinator import (
    control,
    doctor,
    inspection,
    lifecycle,
    materialization,
    normalization,
    onboarding,
    reporting_operation,
    task,
)
from emrys.orchestration.run_coordinator.materialization import (
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    publish_attempt,
)
from emrys.orchestration.run_coordinator.normalization import (
    admit_project,
)
from emrys.orchestration.run_coordinator.execution_profile import (
    load_execution_profile,
    project_default_profile_bytes,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    AllocationCapacity,
    ResourceOverrides,
    admit_resource_policy_record,
    resolve_resource_policy,
)
from emrys.orchestration.run_coordinator.run_implementation import (
    backend_semantics_identity,
    implementation_identity,
    processing_implementation_identity,
)
from tests.orchestration.run_coordinator.fixture import build
from tests.orchestration.run_coordinator.fixtures.b5_doubles import with_owner_doubles

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_CHECKS = load_runtime_policy()
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


def _command_arguments(project: Path, **options) -> argparse.Namespace:
    return argparse.Namespace(
        project=project, profile=None, log_level=None, log_root=None, **options
    )


def _read_log(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _log_events(path: Path) -> list[str]:
    return [record["event"] for record in _read_log(path)]


def _application_controls(root: Path) -> LogControls:
    return LogControls(LogLevel.NORMAL, root, "default", "default")


def _terminal_input(monkeypatch, response, before_read=lambda: None) -> None:
    monkeypatch.setattr(control.sys, "stdin", _InputStream(response, before_read))
    monkeypatch.setattr(control.sys, "stderr", _TerminalOutput(control.sys.stderr))


def _watch_terminal(monkeypatch) -> None:
    for stream in (control.sys.stdin, control.sys.stdout, control.sys.stderr):
        monkeypatch.setattr(stream, "isatty", lambda: True)
    monkeypatch.setenv("TERM", "xterm")


def _bind_readiness(monkeypatch, readiness, resources) -> None:
    monkeypatch.setattr(control.doctor, "diagnose_project", lambda *_a, **_k: readiness)
    monkeypatch.setattr(
        control.capacity, "observe_allocation", lambda: resources.allocation
    )


def _lifecycle_outcome(root: Path, *, status: str, **paths):
    return lifecycle.LifecycleOutcome(
        attempt_path=paths.get("attempt_path", root / "attempt.json"),
        receipt_path=paths.get("receipt_path", root / "attempt-receipt.json"),
        lock_path=paths.get("lock_path", root / "run.lock"),
        released_lock_path=paths.get("released_lock_path", root / "released-lock.json"),
        receipt={"status": status},
    )


def _readiness(
    tmp_path: Path,
    *,
    source_root: Path = source_authority.PACKAGE_ROOT,
    workflow_cores: int = 1,
    stage_concurrency: dict[str, int] | None = None,
    step_threads: dict[str, int] | None = None,
    replicate_count: int = 2,
    sample_ids: list[str] | None = None,
    regions_file: bool = False,
) -> tuple[doctor.DoctorResult, object, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    workspace = tmp_path / "project"
    workspace.mkdir()
    request = build(workspace, replicate_count=replicate_count)
    if regions_file:
        (workspace / "target.bed").write_text("chrSynthetic\t0\t12\n", encoding="utf-8")
        (workspace / "partitions.tsv").write_text(
            "partition_id\tselector_type\tselector_value\n"
            "p1\tregions_file\ttarget.bed\n",
            encoding="utf-8",
        )
    if sample_ids is not None:
        definition = yaml.safe_load(request.read_text(encoding="utf-8"))
        definition["analyses"]["primary"]["sample_ids"] = sample_ids
        request.write_text(
            yaml.safe_dump(definition, sort_keys=False),
            encoding="utf-8",
        )
    execution_profile_path = request.parent / "runtime/profiles/default.yaml"
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
    )
    analysis = project.select_analysis()
    resources = resolve_resource_policy(
        load_execution_profile(config_path=execution_profile_path).resource_policy,
        AllocationCapacity(
            cores=workflow_cores,
            memory_mb=max(1024, workflow_cores * 1024),
            source="test allocation",
        ),
    )
    runtime = workspace / "runtime/runtime.tsv"
    runtime.parent.mkdir(mode=0o700, exist_ok=True)
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
    choices = {
        check.check_id: tool
        for check in POLICY_CHECKS
        if check.check_type != "r_namespace"
    }
    choices.update(
        python=Path(sys.executable), picard_jar=jar, renv_library=renv_library
    )
    runtime_bytes = runtime_profile_bytes(choices)
    runtime.write_bytes(runtime_bytes)
    observations = tuple(
        RuntimeObservation(
            check=check,
            status="pass",
            observed="9.25.1"
            if check.check_id == "snakemake"
            else f"observed-{check.check_id}",
            detail="test runtime",
            resolved_path=(renv_library / check.target).resolve(strict=True)
            if check.check_type == "r_namespace"
            else None,
        )
        for check in runtime_profile_checks(runtime_bytes, source_root)
    )
    runtime_inspection = RuntimeInspection(
        profile_path=runtime,
        profile_sha256=hashlib.sha256(runtime_bytes).hexdigest(),
        profile_bytes=runtime_bytes,
        observations=tuple(observations),
    )
    storage_receipt = tmp_path / "storage.qualified.json"
    storage_bytes = b"fixed storage qualification receipt\n"
    storage_receipt.write_bytes(storage_bytes)
    storage_binding = RuntimeBinding(
        check_id="storage_qualification",
        path=storage_receipt,
        resolved_path=storage_receipt.resolve(strict=True),
        sha256=hashlib.sha256(storage_bytes).hexdigest(),
        observed="b" * 64,
    )
    bindings = (*runtime_file_bindings(runtime_inspection), storage_binding)
    readiness = doctor.DoctorResult(
        project=project,
        analysis=analysis,
        installed_package=replace(
            source_authority.admit_installed_package(), root=source_root
        ),
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
    through: str = "analysis",
    regions_file: bool = False,
):
    readiness, resources, _request, workspace = _readiness(
        tmp_path,
        workflow_cores=workflow_cores,
        stage_concurrency=stage_concurrency,
        step_threads=step_threads,
        regions_file=regions_file,
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


def _patch_run_control(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    readiness, resources, project_path, workspace = _readiness(tmp_path)
    case = SimpleNamespace(
        arguments=_command_arguments(project_path, execute=False),
        workspace=workspace,
        plans=[],
        executed=[],
        runtime_inspections=[],
    )
    real_build = control.build_attempt_plan

    def diagnose(*_args, **kwargs):
        assert kwargs == {
            "storage_requirement": "direct",
            "analysis_name": None,
            "require_reporter": getattr(case.arguments, "through", "analysis")
            == "analysis"
            and not getattr(case.arguments, "no_report", False),
        }
        return readiness

    def build(*args, **kwargs):
        plan = real_build(*args, **kwargs)
        case.plans.append(plan)
        return plan

    def execute(plan, _observe, initial_runtime_inspection):
        case.executed.append(plan)
        case.runtime_inspections.append(initial_runtime_inspection)
        return _lifecycle_outcome(
            plan.run_root,
            status="failed",
            lock_path=plan.run_root / "locks/run.lock",
            released_lock_path=plan.run_root / "locks/released.json",
        )

    monkeypatch.setattr(control.doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        control.capacity, "observe_allocation", lambda: resources.allocation
    )
    monkeypatch.setattr(control, "build_attempt_plan", build)
    _patch_lifecycle_execution(monkeypatch, lambda: case.plans[-1], execute)
    return case


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


def _task_records(plan) -> list[dict[str, object]]:
    return [
        {
            **record,
            "machine_key": owner,
            "scope": {"scope_type": record["scope_type"], "scope_id": scope},
        }
        for owner, scopes in plan.attempt_record["tasks"].items()
        for scope, record in scopes.items()
        if "workflow_attempt_record" not in record
    ]


def _workflow(plan) -> dict[str, object]:
    return plan.attempt_record["workflow"]


def test_task_definitions_bind_every_admitted_project_input(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path, regions_file=True)
    source = plan.run.analysis.workflow_inputs
    expected_snapshots = (
        source["samples"]["manifest"],
        source["partitions"]["manifest"],
        source["reference"]["fasta"],
        source["reference"]["gtf"],
        *(
            row[key]
            for row in source["samples"]["rows"]
            for key in ("r1_fastq", "r2_fastq")
        ),
        source["partitions"]["rows"][0]["selector_file"],
    )
    expected = {Path(str(item["path"])): item for item in expected_snapshots}
    declarations = [
        item
        for dispatch in _task_records(plan)
        for item in dispatch["inputs"]
        if Path(str(item["path"])) in expected
    ]

    assert {Path(str(item["path"])) for item in declarations} == set(expected)
    assert all(
        (item["size_bytes"], item["sha256"])
        == (
            expected[Path(str(item["path"]))]["size_bytes"],
            expected[Path(str(item["path"]))]["sha256"],
        )
        for item in declarations
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

    assert replace(doubled, attempt_record_bytes=plan.attempt_record_bytes) == plan
    attempt = doubled.attempt_record
    original_attempt = plan.attempt_record
    for owner, scopes in attempt["tasks"].items():
        for scope, replacement in scopes.items():
            original = original_attempt["tasks"][owner][scope]
            replacement["producer_argv"] = original["producer_argv"]
            replacement["validator_argv"] = original["validator_argv"]
    assert attempt == original_attempt

    assert all(
        "--payload-base64" in record[field]
        for record in _task_records(doubled)
        for field in ("producer_argv", "validator_argv")
    )


def test_owner_doubles_use_successor_scopes_inside_reporting_payloads(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    doubled = with_owner_doubles(plan)
    payloads: dict[Path, bytes] = {}
    for record in _task_records(doubled):
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


def test_plan_is_no_write_and_projects_exact_worker_roster(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)

    assert not (plan.workspace / "runs").exists()
    assert not (plan.workspace / "logs").exists()
    assert plan.lifecycle_request.operation == "execute"
    assert (
        json.loads(plan.lifecycle_request.attempt_record_bytes) == plan.attempt_record
    )
    assert (
        plan.attempt_record["executor"]
        == plan.run.execution_plan.record["identity"]["backend"]["backend"]
    )
    assert plan.task_count == 35
    records = _task_records(plan)
    assert len(records) == 35
    assert len({record["machine_key"] for record in records}) == 14
    assert plan.attempt_record["schema_version"] == "emrys.workflow-attempt.v4"
    assert plan.attempt_path not in {item.path for item in plan.attempt_files}
    assert not any(
        "dispatch" in item.path.parts or "workflow-configs" in item.path.parts
        for item in plan.attempt_files
    )
    for record in records:
        assert "--execute" not in record["producer_argv"]
        for output in record["outputs"]:
            assert output["working_path"] != output["path"]
    assert all("--execute" in record["validator_argv"] for record in records)
    owners = {
        str(item["machine_key"]): str(item["step_id"])
        for item in plan.run.analysis.profile["owner_tasks"]
    }
    step09 = next(
        record for record in records if owners[str(record["machine_key"])] == "09"
    )
    assert {item["role"] for item in step09["inputs"]} == {
        "sample_manifest",
        "partition_manifest",
        "step08_sites_v1",
        "step08_inputs_v1",
        "step08_summary_v1",
    }
    assert {item["role"] for item in step09["outputs"]} == {
        "step09_cmh_all_sites_v1",
        "step09_cmh_significant_sites_v1",
        "step09_cmh_summary_v1",
        "step09_mutation_spectrum_tsv_v1",
        "step09_mutation_spectrum_pdf_v1",
        "step09_depth_delta_pdf_v1",
    }

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
    for flag, suffix in (
        ("--output-dir", ".FWD_like.bam"),
        ("--qc-dir", ".orientation_counts.tsv"),
    ):
        output = next(
            item for item in step06["outputs"] if item["path"].endswith(suffix)
        )
        assert producer_argument(step06, flag) == Path(output["working_path"]).parent

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
    fwd_output = next(
        item
        for item in step07["outputs"]
        if item["path"].endswith(".FWD_like.mpileup.vcf")
    )
    assert producer_argument(step07, "--fwd-vcf-output") == Path(
        fwd_output["working_path"]
    )
    assert producer_argument(step07, "--fwd-vcf-final") == Path(fwd_output["path"])
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
    assert producer_argument(step00b, "--bed") == Path(
        step00b["outputs"][0]["working_path"]
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
        'export EMRYS_SHA256_PYTHON="$1"; shift; exec "$@"',
        "emrys-scientific-worker",
    ]
    assert producer[4] == sys.executable
    r_bootstrap = next(item for item in producer if "EMRYS_LOCAL_PILOT_R" in item)
    assert "R_LIBS*|R_PROFILE*|R_ENVIRON*|RENV_*|R_DEFAULT_PACKAGES" in r_bootstrap
    assert "EMRYS_USE_RENV" in r_bootstrap
    assert "RENV_PATHS_LIBRARY" in r_bootstrap
    assert "R_DEFAULT_PACKAGES" in r_bootstrap
    assert "--no-environ" in producer
    assert any(item.endswith("step_08_vcf_preprocessing.R") for item in producer)
    assert str(tmp_path / "renv-library") in producer
    assert_root(step08, "--step07-root", ".FWD_like.mpileup.vcf", 2)
    for flag, suffix in (
        ("--sites-output", ".step08_sites.tsv"),
        ("--summary-output", ".step08_summary.tsv"),
    ):
        output = next(
            item for item in step08["outputs"] if item["path"].endswith(suffix)
        )
        assert producer_argument(step08, flag) == Path(output["working_path"])
    step09 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1"
    )
    producer_argv = tuple(step09["producer_argv"])
    assert any(
        item.endswith("step_09_cmh_editing_site_calling.R") for item in producer_argv
    )
    assert (
        next(item for item in producer_argv if "EMRYS_LOCAL_PILOT_R" in item)
        == r_bootstrap
    )
    assert "step_09_cmh_editing_site_calling.sh" not in " ".join(
        step09["producer_argv"]
    )
    assert producer_argument(step09, "--step08-sites") == next(
        Path(item["path"])
        for item in step09["inputs"]
        if item["path"].endswith(".step08_sites.tsv")
    )
    assert "--expected-mean-dp-threshold" in step09["validator_argv"]
    assert producer_argument(step09, "--all-sites-output") == Path(
        step09["outputs"][0]["working_path"]
    )
    step10 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.analysis.project_candidate_scientific_context.v1"
    )
    assert "scientific_context_projection.sh" in " ".join(step10["producer_argv"])
    assert "--motif-catalog" in step10["producer_argv"]
    assert "scientific-context-projection" in step10["validator_argv"]
    assert producer_argument(step10, "--candidate-context-output") == Path(
        step10["outputs"][0]["working_path"]
    )
    assert producer_argument(step10, "--candidate-context-final") == Path(
        step10["outputs"][0]["path"]
    )
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
    required_tool_fields = {"name", "version", "path", "resolved_path", "sha256"}
    assert all(
        required_tool_fields <= set(item) <= required_tool_fields | {"identity_kind"}
        for item in plan.attempt_record["required_tools"]
    )


def test_distinct_installed_module_materializes_one_typed_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_threads: list[int] = []

    def normalize(config, _context):
        return {"label": str(config["label"]).strip().lower()}

    def plan_task(context):
        observed_threads.append(context.threads)
        (summary,) = context.inputs["step08_summary_v1"]
        result = context.working_outputs["collaborator_result_v1"]
        validation = context.outputs["collaborator_validation_v1"]
        return analysis_modules.TaskCommandPlanV2(
            context.python_command(("collaborator-produce", str(result))),
            context.python_command(("collaborator-validate", str(validation))),
            (analysis_modules.TaskInputV1("cohort_summary", summary),),
        )

    task = analysis_modules.AnalysisTaskV1(
        "collaborator.analysis.echo.v1",
        "09",
        512,
        (
            analysis_modules.AnalysisInputV1(
                "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
                ("step08_summary_v1",),
            ),
        ),
        (
            analysis_modules.AnalysisArtifactV1(
                "collaborator_result",
                "collaborator_result_v1",
                "results/collaborator/{analysis_id}.tsv",
                "tsv",
            ),
            analysis_modules.AnalysisArtifactV1(
                "collaborator_validation",
                "collaborator_validation_v1",
                "products/native/collaborator/{analysis_id}.validation.tsv",
                "validation_report",
                analysis_modules.VALIDATION_REPORT_HEADER,
            ),
        ),
        plan_task,
        2,
    )
    descriptor = analysis_modules.AnalysisModuleDescriptorV1(
        "collaborator.echo",
        "v1",
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["label"],
            "properties": {"label": {"type": "string"}},
        },
        normalize,
        (task,),
        ("python",),
    )

    def provider():
        return descriptor

    source = Path(__file__).resolve()
    package = installed_package_identity.InstalledPackageTreeIdentity(
        source.parent, "c" * 64, (source,)
    )
    installed = installed_package_identity.InstalledProviderV1(
        provider,
        "collaborator_analysis:analysis_module_v1",
        "collaborator-analysis",
        "1.0",
        package,
    )
    loaded = analysis_modules.LoadedAnalysisModuleV1(descriptor, installed)
    monkeypatch.setattr(normalization, "load_analysis_module", lambda _name: loaded)
    monkeypatch.setattr(analysis_modules, "load_analysis_module", lambda _name: loaded)
    fixture_build = build

    def build_collaborator_project(root: Path, *, replicate_count: int = 2) -> Path:
        project_path = fixture_build(root, replicate_count=replicate_count)
        definition = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        authored = definition["analyses"]["primary"]
        definition["analyses"]["primary"] = {
            "module": "collaborator.echo",
            "partitions": authored["partitions"],
            "config": {"label": " Collaborator result "},
        }
        project_path.write_text(
            yaml.safe_dump(definition, sort_keys=False), encoding="utf-8"
        )
        return project_path

    monkeypatch.setitem(globals(), "build", build_collaborator_project)
    rejected_readiness, rejected_resources, _project, rejected_workspace = _readiness(
        tmp_path / "rejected"
    )
    with pytest.raises(MaterializationError, match="requires at least 2 threads"):
        build_attempt_plan(
            _run_candidate(rejected_readiness, rejected_resources),
            rejected_readiness,
            rejected_workspace,
            resources=rejected_resources,
            operation="execute",
        )

    readiness, resources, _project, workspace = _readiness(
        tmp_path / "run",
        workflow_cores=2,
        step_threads={
            "00a": 1,
            "01": 1,
            "02": 1,
            "06": 1,
            "08": 1,
            "09": 2,
            "10": 1,
        },
    )
    run = _run_candidate(readiness, resources)
    plan = build_attempt_plan(
        run,
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )

    assert run.analysis.revision.record["identity"]["analysis_module"][
        "configuration"
    ] == {"label": "collaborator result"}
    binding = run.run_binding.record["binding"]
    assert binding["analysis_revision_sha256"] == run.analysis.revision.identity_sha256
    assert binding["execution_plan_sha256"] == run.execution_plan.identity_sha256
    assert not (workspace / "runs").exists()
    (dispatch,) = (
        record
        for record in _task_records(plan)
        if record["machine_key"] == "collaborator.analysis.echo.v1"
    )
    assert {item["role"] for item in dispatch["inputs"]} == {"cohort_summary"}
    assert {item["role"] for item in dispatch["outputs"]} == {"collaborator_result_v1"}
    assert dispatch["validation_report_path"].endswith(".validation.tsv")
    assert observed_threads == [2]


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
    records = _task_records(plan)

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
    assert plan.task_count == len(records) == 31
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
    assert {item.path: item.data for item in plan.attempt_files}[
        manifest
    ] == selected_bytes
    manifest_binding = {
        "path": str(manifest),
        "size_bytes": len(selected_bytes),
        "sha256": hashlib.sha256(selected_bytes).hexdigest(),
    }
    owners = {
        str(item["machine_key"]): str(item["step_id"])
        for item in readiness.analysis.profile["owner_tasks"]
    }
    records = _task_records(plan)
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
        source_samples.append({**row, "sample_id": f"{condition}_3", "replicate": "3"})
    source_analysis = build_module_analysis_revision(
        samples=source_samples,
        partitions=identity["partitions"],
        reference=identity["reference"],
        **identity["analysis_module"],
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
    sample_changed = build_module_analysis_revision(
        samples=samples,
        partitions=identity["partitions"],
        reference=identity["reference"],
        **identity["analysis_module"],
    )
    reference_changed = build_module_analysis_revision(
        samples=identity["samples"],
        partitions=identity["partitions"],
        reference={**identity["reference"], "fasta_sha256": "4" * 64},
        **identity["analysis_module"],
    )
    different_binding = {**binding, "attempt_receipt_sha256": "5" * 64}
    binding_changed = build_run_candidate(
        readiness.analysis,
        readiness,
        resources.declaration,
        processing_source=different_binding,
    )
    capacity_changed = build_run_candidate(
        readiness.analysis,
        readiness,
        replace(
            resources.declaration,
            workflow_cores=resources.declaration.workflow_cores + 1,
        ),
        processing_source=binding,
    )
    inspection.validate_processing_source(
        source,
        target_analysis=target.analysis.revision,
        target_plan=capacity_changed.execution_plan,
    )
    resources_changed = build_run_candidate(
        readiness.analysis,
        readiness,
        replace(
            resources.declaration,
            stage_memory_mb=tuple(
                (step_id, value + 1 if step_id == "06" else value)
                for step_id, value in resources.declaration.stage_memory_mb
            ),
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


def test_downstream_plan_preserves_admitted_sidecars_for_relocated_reference(
    tmp_path: Path,
) -> None:
    readiness, resources, _project, workspace = _readiness(tmp_path)
    source_run = _run_candidate(readiness, resources, through="processing")
    binding = {
        "source_run_id": source_run.run_id,
        "workflow_attempt_id": "workflow-20260831T120000Z-" + "1" * 32,
        "attempt_receipt_sha256": "2" * 64,
    }
    workflow_inputs = readiness.analysis.workflow_inputs
    original_fasta = Path(workflow_inputs["reference"]["fasta"]["path"])
    relocated_fasta = tmp_path / "relocated" / original_fasta.name
    workflow_inputs["reference"]["fasta"]["path"] = str(relocated_fasta)
    relocated_analysis = replace(
        readiness.analysis,
        _workflow_input_bytes=orchestration_contracts.canonical_json_bytes(
            workflow_inputs
        ),
    )
    relocated_readiness = replace(readiness, analysis=relocated_analysis)
    target = build_run_candidate(
        relocated_analysis,
        relocated_readiness,
        resources.declaration,
        processing_source=binding,
    )
    source_root = workspace / "runs" / source_run.run_id
    rows = artifact_inventory.project_rows(
        {**relocated_analysis.workflow_inputs, "run_id": target.run_id},
        relocated_analysis.profile,
        relocated_analysis.revision,
        source_root,
    )
    old_sidecars = tmp_path / "source-sidecars"
    snapshots_list = []
    output_indexes: dict[tuple[str, str], int] = {}
    for row in rows:
        if (
            row["step_id"] not in PROCESSING_STEP_IDS
            or row["adapter"].endswith("_validation_report_v1")
            or row["adapter"] == "step00c_reference_fasta_v1"
        ):
            continue
        scope = row["step_id"], row["scope_id"]
        snapshots_list.append(
            {
                "step_id": row["step_id"],
                "scope_id": row["scope_id"],
                "output_index": output_indexes.get(scope, 0),
                "role": row["adapter"],
                "path": str(
                    old_sidecars / Path(row["source_path"]).name
                    if row["adapter"]
                    in {"step00c_reference_fai_v1", "step00c_reference_dict_v1"}
                    else Path(row["source_path"])
                ),
                "size_bytes": 1,
                "sha256": "a" * 64,
            }
        )
        output_indexes[scope] = output_indexes.get(scope, 0) + 1
    snapshots = tuple(snapshots_list)
    source = inspection.ProcessingSourceAdmission(
        root=source_root,
        state=SimpleNamespace(),
        binding=binding,
        artifact_snapshots=snapshots,
    )

    plan = build_attempt_plan(
        target,
        relocated_readiness,
        workspace,
        resources=resources,
        operation="execute",
        processing_source=source,
    )

    old_paths = {
        snapshot["path"]
        for snapshot in snapshots
        if snapshot["role"] in {"step00c_reference_fai_v1", "step00c_reference_dict_v1"}
    }
    task_inputs = {
        item["path"]: item
        for record in _task_records(plan)
        for item in record["inputs"]
    }
    old_fai = next(path for path in old_paths if path.endswith(".fai"))
    assert task_inputs[old_fai]["sha256"] == "a" * 64
    inventory = next(
        planned.data
        for planned in plan.attempt_files
        if planned.path.name == "artifact_inventory.tsv"
    )
    assert all(path.encode() in inventory for path in old_paths)
    assert str(relocated_fasta).encode() + b".fai" not in inventory


def _runtime_admission_fixture(
    plan: materialization.AttemptPlan,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[lifecycle.LifecycleRequest, RuntimeBinding]:
    ops = lifecycle.default_lifecycle_ops()
    admit_run(plan, ops=ops)
    request = plan.lifecycle_request
    publish_attempt(plan, ops=ops)
    monkeypatch.setattr(
        source_authority,
        "admit_installed_package",
        lambda **_kwargs: plan.readiness.installed_package,
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

    def inspect(_data, path, **_kwargs):
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
    config = _workflow(plan)

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
    assert direct_plan.attempt_files == scheduled_plan.attempt_files

    direct_config = _workflow(direct_plan)
    scheduled_config = _workflow(scheduled_plan)
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
    assert direct_plan.attempt_record_bytes != scheduled_plan.attempt_record_bytes
    direct_attempt["workflow"]["resource_policy"].pop("allocation")
    scheduled_attempt["workflow"]["resource_policy"].pop("allocation")
    assert direct_attempt == scheduled_attempt

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

    unplaced = build_attempt_plan(run, readiness, workspace, **context)
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

    assert "placement" not in unplaced.attempt_record
    assert direct.attempt_record["placement"] == direct_placement
    assert scheduled.attempt_record["placement"] == slurm_placement
    compatibility = inspection.attempt_fields()
    assert "placement" not in compatibility
    assert {field: direct.attempt_record[field] for field in compatibility} == {
        field: scheduled.attempt_record[field] for field in compatibility
    }


def test_run_identity_excludes_attempt_reporting_and_cli_adapter_code(
    tmp_path: Path,
) -> None:
    checkout = _package_copy(tmp_path)
    readiness, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
    )
    baseline = _run_candidate(readiness, resources)
    baseline_backend = backend_semantics_identity(checkout)
    baseline_processing = processing_implementation_identity(checkout)

    for relative in (
        "reporting/_run_report/context.py",
        "orchestration/run_coordinator/reporting_boundary.py",
        "contracts/orchestration/projection.py",
        "contracts/artifacts/validator.py",
        "contracts/artifacts/_artifact_contracts/artifact.py",
        "contracts/artifacts/_artifact_contracts/inventory.py",
        "contracts/artifacts/_artifact_contracts/report_receipt.py",
        "contracts/artifacts/_artifact_contracts/run_summary_status.py",
        "contracts/artifacts/_artifact_contracts/run_summary_validation.py",
    ):
        report_owner = checkout / relative
        report_owner.write_bytes(
            report_owner.read_bytes() + b"\n# reporting-only change\n"
        )
        assert _run_candidate(readiness, resources).run_id == baseline.run_id
        assert processing_implementation_identity(checkout) == baseline_processing

    resource_policy = checkout / "orchestration/run_coordinator/resource_policy.py"
    resource_policy.write_bytes(resource_policy.read_bytes() + b"\n# policy change\n")
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    snakefile = checkout / "workflow/Snakefile"
    snakefile_bytes = snakefile.read_bytes()
    snakefile.write_bytes(snakefile_bytes + b"\n# adapter change\n")
    assert backend_semantics_identity(checkout) != baseline_backend
    assert _run_candidate(readiness, resources).run_id != baseline.run_id
    snakefile.write_bytes(snakefile_bytes)

    cli_adapter = checkout / "__main__.py"
    cli_adapter.write_bytes(cli_adapter.read_bytes() + b"\n# CLI adapter change\n")
    assert _run_candidate(readiness, resources).run_id == baseline.run_id

    materializer = checkout / "orchestration/run_coordinator/materialization.py"
    materializer.write_bytes(materializer.read_bytes() + b"\n# dispatch change\n")
    assert _run_candidate(readiness, resources).run_id != baseline.run_id


@pytest.mark.parametrize(
    "relative",
    (
        "orchestration/run_coordinator/_inspection_admission.py",
        "orchestration/run_coordinator/_inspection_attempts.py",
        "orchestration/run_coordinator/_inspection_evidence.py",
        "orchestration/run_coordinator/all_pass.py",
        "contracts/orchestration/artifact_inventory.py",
        "contracts/artifacts/_artifact_contracts/definitions.py",
        "contracts/artifacts/_artifact_contracts/identity.py",
        "contracts/artifacts/_artifact_contracts/schema.py",
        "contracts/schemas/orchestration/v2/attempt_receipt.schema.json",
    ),
)
def test_run_identity_binds_semantic_admission_code(
    tmp_path: Path,
    relative: str,
) -> None:
    checkout = _package_copy(tmp_path)
    readiness, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
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
    checkout = _package_copy(tmp_path)
    baseline = implementation_identity(checkout)
    dependencies = (
        ".Rprofile",
        "libraries/argument_parsing.sh",
        "libraries/file_checks.sh",
        "libraries/gatk_invocation.sh",
        "libraries/input_contract.R",
        "contracts/orchestration/artifact_inventory.py",
        "workflow/contracts/local_cmh_v2.json",
    )
    processing_baseline = processing_implementation_identity(checkout)

    for relative in dependencies:
        path = checkout / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        assert implementation_identity(checkout) != baseline, relative
        if relative.endswith(("artifact_inventory.py", "local_cmh_v2.json")):
            assert processing_implementation_identity(checkout) != processing_baseline
        path.write_bytes(original)

    assert implementation_identity(checkout) == baseline


def test_processing_compatibility_binds_only_processing_semantics(
    tmp_path: Path,
) -> None:
    checkout = _package_copy(tmp_path)
    readiness, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
    )
    baseline = _run_candidate(readiness, resources)

    def compatibility(run) -> str:
        return str(
            run.execution_plan.record["identity"]["processing_compatibility_sha256"]
        )

    def with_tool(name: str, digest: str):
        return replace(
            readiness,
            bindings=tuple(
                replace(binding, sha256=digest) if binding.check_id == name else binding
                for binding in readiness.bindings
            ),
        )

    baseline_compatibility = compatibility(baseline)
    for relative in (
        "analyses/__init__.py",
        "stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R",
    ):
        path = checkout / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n# downstream-only change\n")
        changed = _run_candidate(readiness, resources)
        assert changed.run_id != baseline.run_id
        assert compatibility(changed) == baseline_compatibility
        path.write_bytes(original)

    for relative in (
        "orchestration/run_coordinator/materialization.py",
        "workflow/Snakefile",
        "workflow/contracts/local_cmh_v2.json",
    ):
        path = checkout / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        changed = _run_candidate(readiness, resources)
        assert changed.analysis.profile == baseline.analysis.profile
        assert compatibility(changed) != baseline_compatibility
        path.write_bytes(original)

    downstream_tool = build_run_candidate(
        readiness.analysis,
        with_tool("bcftools", "d" * 64),
        resources.declaration,
    )
    assert downstream_tool.run_id != baseline.run_id
    assert compatibility(downstream_tool) == baseline_compatibility

    processing_owner = checkout / "stages/mechanical_orientation/producer.py"
    processing_owner_bytes = processing_owner.read_bytes()
    processing_owner.write_bytes(processing_owner_bytes + b"\n# processing change\n")
    owner_changed = _run_candidate(readiness, resources)
    processing_owner.write_bytes(processing_owner_bytes)
    processing_tool = build_run_candidate(
        readiness.analysis,
        with_tool("star", "e" * 64),
        resources.declaration,
    )
    for changed in (owner_changed, processing_tool):
        assert compatibility(changed) != baseline_compatibility


@pytest.mark.parametrize(
    ("relative", "error"),
    (
        (
            "orchestration/run_coordinator/materialization.py",
            "implementation content",
        ),
        (
            "orchestration/run_coordinator/all_pass.py",
            "implementation content",
        ),
        (
            "contracts/orchestration/artifact_inventory.py",
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
    checkout = _package_copy(tmp_path)
    readiness, resources, _request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
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
    records = _task_records(plan)
    threaded_owners = {
        "emrys.stage.construct_STAR_index.v1",
        "emrys.stage.align_RNA_reads_with_STAR.v1",
        "emrys.stage.construct_canonical_BAM.v1",
        "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1",
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
    }

    assert dict(plan.resources.step_threads) == {**allocation, "09": 1, "10": 1}
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
    config = _workflow(plan)

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
        "09": 1,
        "10": 1,
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
        source_authority.PACKAGE_ROOT,
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
    assert observed["R_PROFILE_USER"] == str(
        source_authority.PACKAGE_ROOT / ".Rprofile"
    )


def test_every_projected_owner_command_is_accepted_by_public_help(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    commands = {
        tuple(command)
        for record in _task_records(plan)
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

    arguments = argparse.Namespace(
        project=plan.run.analysis.source_path,
        run=None,
        detail="normal",
    )
    inspection_bytes = {
        path: path.read_bytes() for path in plan.run_root.rglob("*") if path.is_file()
    }
    assert control.inspect_from_args(arguments) == 0
    normal = capsys.readouterr().out
    assert normal.index("Retained submissions:") < normal.index("Run:")
    assert normal.count(f"Run: {inspection.human_run_name(plan.run.run_id)}") == 1
    assert "Run ID:" not in normal
    assert "Analysis ID:" not in normal
    assert "Execution Plan ID:" not in normal
    assert "Run root:" not in normal
    assert normal.count("Scientific task observations:") == 1
    assert f"  No admitted start: {len(observed.tasks)}" in normal
    assert normal.count("Reporting transactions:") == 1
    assert "Reporting admission: incomplete" in normal
    assert "run_summary: No admitted start" in normal
    assert "html_report: No admitted start" in normal

    arguments.detail = "verbose"
    assert control.inspect_from_args(arguments) == 0
    verbose = capsys.readouterr().out
    assert f"Run ID: {plan.run.run_id}" in verbose
    assert f"Analysis ID: {plan.run.analysis.revision.analysis_revision_id}" in verbose
    assert f"Execution Plan ID: {plan.run.execution_plan.execution_plan_id}" in verbose
    assert "Attempt ID: none" in verbose
    assert verbose.count("Scientific task observations:") == 1
    assert f"  No admitted start: {len(observed.tasks)}" in verbose
    assert verbose.count("Reporting transactions:") == 1

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
    assert "  Verification not admitted: 1" in blocked_output

    started = replace(
        observed,
        reporting_completion_records={
            "run_summary": {
                "start": {
                    "path": "state/reporting/run_summary/start.json",
                    "sha256": "a" * 64,
                },
                "verified": None,
            },
            "html_report": {"start": None, "verified": None},
        },
        reporting_blockers=("run_summary reporting start has no verified completion",),
    )
    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: started)
    for detail in ("normal", "verbose"):
        arguments.detail = detail
        assert control.inspect_from_args(arguments) == 0
        started_output = capsys.readouterr().out
        assert started_output.count("Reporting transactions:") == 1
        assert "Reporting admission: blocked" in started_output
        assert "run_summary: Started; completion unverified" in started_output
        assert "html_report: No admitted start" in started_output
        assert (
            "REPORTING BLOCKER: run_summary reporting start has no verified completion"
            in started_output
        )
        assert "Recovery available: no" in started_output
        assert "Do not resume." in started_output
        assert "reporter is running" not in started_output
    assert {
        path: path.read_bytes() for path in plan.run_root.rglob("*") if path.is_file()
    } == inspection_bytes

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
    assert debug.count("Scientific task observations:") == 1
    for task in observed.tasks:
        assert (
            f"TASK {task.expected.machine_key}/{task.expected.scope_id}: No admitted start"
            in debug
        )

    escaped = replace(
        observed,
        run_root=Path("/tmp/café\\display\n\x1b[31m-run"),
    )
    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: escaped)
    arguments.detail = "verbose"
    assert control.inspect_from_args(arguments) == 0
    escaped_output = capsys.readouterr().out
    assert "\x1b" not in escaped_output
    assert "Run root: /tmp/café\\display\\n\\x1b[31m-run" in escaped_output

    monkeypatch.setattr(
        control.inspection,
        "inspect_run",
        lambda _root: (_ for _ in ()).throw(
            inspection.InspectionError("invalid /tmp/run\n\x1b[31m-root")
        ),
    )
    assert control.inspect_from_args(arguments) == 2
    unsafe_error = capsys.readouterr().err
    assert "\x1b" not in unsafe_error
    assert len(unsafe_error.splitlines()) == 1
    assert r"\n" in unsafe_error
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

    with pytest.raises(lifecycle.LifecycleError, match="Could not admit Run"):
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
            config_path=(
                plan.run.analysis.source_path.parent / "runtime/profiles/default.yaml"
            ),
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
    assert len(_task_records(plan)) == 35
    assert not (plan.run_root / "contract/dispatch").exists()
    assert not (plan.run_root / "contract/workflow-configs").exists()
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
        assert _kwargs == {
            "storage_requirement": "direct",
            "analysis_name": readiness.analysis.evidence_label,
            "expected_analysis_revision": (
                None
                if observed.authority is None
                else observed.authority.analysis_revision
            ),
            "require_reporter": observed.authority is None
            or execution_plan_boundary(observed.authority.execution_plan) == "analysis",
        }
        selected.append(runtime_profile)
        return readiness

    monkeypatch.setattr(control.inspection, "inspect_run", lambda _root: observed)
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        inspect_readiness,
    )
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: resources.allocation,
    )


def test_new_run_rejects_processing_edge_drift_but_existing_run_resumes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readiness, resources, request, workspace = _readiness(tmp_path)
    profile = readiness.analysis.profile
    profile["direct_edges"].pop(0)
    orchestration_contracts.validate_record("profile", profile)
    readiness = replace(
        readiness,
        analysis=replace(
            readiness.analysis,
            _profile_bytes=orchestration_contracts.canonical_json_bytes(profile),
        ),
    )
    monkeypatch.setattr(
        control.doctor, "diagnose_project", lambda *_args, **_kwargs: readiness
    )
    with pytest.raises(control.ControlError, match="Processing dependencies"):
        control._plan_run(request, execution_profile=load_execution_profile())
    assert not (workspace / "runs").exists()

    # This older accepted profile remains an immutable resumable Run.
    first = build_attempt_plan(
        _run_candidate(readiness, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    observed = _failed_run(first)
    _patch_resume_control(monkeypatch, observed, readiness, resources, [])
    second = control._plan_resume(
        first.run_root, execution_profile=load_execution_profile()
    )
    assert second.run.run_id == first.run.run_id
    assert second.run.analysis.profile == profile


@pytest.mark.parametrize("through", ("analysis", "processing"))
def test_successor_resume_snapshots_current_runtime_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    through: str,
) -> None:
    first = _plan(tmp_path, through=through)
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
        execution_profile=load_execution_profile(),
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


def test_placement_profile_inherits_computation_without_reporting_resources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _plan(tmp_path, workflow_cores=2)
    observed = _failed_run(first)
    _patch_resume_control(monkeypatch, observed, first.readiness, first.resources, [])
    selected = tmp_path / "direct.yaml"
    selected.write_text(
        "schema_version: emrys.execution-profile.v1\nplacement: {kind: direct}\n",
        encoding="utf-8",
    )
    profile = load_execution_profile(config_path=selected)

    second = control._plan_resume(
        first.run_root,
        execution_profile=profile,
    )

    assert not profile.computational_resources_explicit
    assert second.resources.declaration == first.resources.declaration
    assert "reporting_memory_mb" not in second.resources.policy.document()
    assert "reporting_memory_mb" not in second.resources.effective_document()
    assert second.attempt_record["placement"]["source"]["path"] == str(selected)


def test_successor_resume_allows_relocated_checkout_and_new_runtime_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_source = tmp_path / "first-source"
    second_source = tmp_path / "second-source"
    first_source.mkdir()
    second_source.mkdir()
    checkout_one = _package_copy(first_source)
    checkout_two = _package_copy(second_source)
    readiness_one, resources, _request, workspace = _readiness(
        tmp_path / "first-case",
        source_root=checkout_one,
    )
    readiness_two, _unused_resources, _request_two, _workspace_two = _readiness(
        tmp_path / "second-case",
        source_root=checkout_two,
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
            "require_reporter": True,
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

    resume_profile = load_execution_profile(config_path=_slurm_profile(tmp_path))
    monkeypatch.setattr(control.doctor, "diagnose_project", inspect_second_runtime)
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
        first.attempt_record["installed_package"]
        != second.attempt_record["installed_package"]
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
        for record in _task_records(plan)
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

    def fail_on_profile(path: Path, data: bytes) -> None:
        if path == plan.attempt_files[-1].path:
            raise OSError("injected runtime profile publication failure")
        base.publish_bytes(path, data)

    ops = replace(
        base,
        publish_bytes=fail_on_profile,
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
    assert (plan.run_root / "contract/profile.json").is_file()
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
            retained_tasks={},
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
    case = _patch_run_control(tmp_path, monkeypatch)
    arguments, workspace = case.arguments, case.workspace
    named = workspace / "runtime/profiles/ci.yaml"
    shutil.copy2(workspace / "runtime/profiles/default.yaml", named)
    arguments.profile = "ci"

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
    assert "Run: " in normal
    assert "Scientific boundary: complete analysis" in normal
    assert "Work: 35 pending, 0 reusable" in normal
    assert "Reporting: automatic after scientific work" in normal
    assert "Evidence boundary:" in normal
    for hidden in (
        "Operation:",
        "Analysis ID:",
        "Execution Plan ID:",
        "Run ID:",
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
    assert case.executed == []
    arguments.profile = "missing"
    assert control.run_from_args(arguments) == 2
    assert "runtime/profiles/missing.yaml" in capsys.readouterr().err


def test_processing_run_dry_run_is_no_write_and_truthfully_scoped(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _patch_run_control(tmp_path, monkeypatch)
    arguments, workspace = case.arguments, case.workspace
    arguments.through = "processing"
    monkeypatch.setattr(
        control.sys,
        "stdin",
        _InputStream(AssertionError("nonterminal input was read"), terminal=False),
    )

    assert control.run_from_args(arguments) == 0
    assert case.executed == []

    rendered = capsys.readouterr().err
    assert "Scientific boundary: sample processing (through Step 06)" in rendered
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
    case = _patch_run_control(tmp_path, monkeypatch)
    arguments, workspace = case.arguments, case.workspace
    log_root = tmp_path / "application-logs"
    arguments.log_root = log_root

    def before_read() -> None:
        assert not (workspace / "runs").exists()
        assert not (workspace / "logs").exists()
        assert not log_root.exists()
        assert case.executed == []

    _terminal_input(monkeypatch, response, before_read)
    if expected_exit is None:
        with pytest.raises(KeyboardInterrupt):
            control.run_from_args(arguments)
    else:
        assert control.run_from_args(arguments) == expected_exit

    rendered = capsys.readouterr().err
    assert rendered.count("Run: ") == 1
    assert rendered.index("Run: ") < rendered.index("Execute this plan? [y/N]")
    if expected_exit == 1:
        assert len(case.plans) == len(case.executed) == 1
        assert case.executed[0] is case.plans[0]
        assert case.runtime_inspections == [None]
        assert list(log_root.rglob("*.jsonl"))
    else:
        assert len(case.plans) == 1 and case.executed == []
        assert case.runtime_inspections == []
        assert not (workspace / "runs").exists()
        assert not (workspace / "logs").exists()
        assert not log_root.exists()


def test_interactive_resume_uses_the_same_no_write_gate(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    plan.run_root.mkdir(parents=True)
    named = plan.workspace / "runtime/profiles/resume-ci.yaml"
    shutil.copy2(
        plan.run.analysis.source_path.parent / "runtime/profiles/default.yaml",
        named,
    )

    def plan_resume(*_args: object, execution_profile, **_kwargs: object):
        assert execution_profile.source_path == named
        return plan

    monkeypatch.setattr(control, "_plan_resume", plan_resume)
    _terminal_input(monkeypatch, "no\n")
    arguments = argparse.Namespace(
        project=plan.run.analysis.source_path,
        run=plan.run.run_id,
        profile="resume-ci",
        log_level=None,
        log_root=None,
        execute=False,
    )

    assert control.resume_from_args(arguments) == 0

    rendered = capsys.readouterr().err
    assert "Execute this plan? [y/N]" in rendered
    assert "Dry-run complete; no resume state was written." in rendered
    assert list(plan.run_root.iterdir()) == []


@pytest.mark.parametrize("placement", ("direct", "slurm"))
@pytest.mark.parametrize("changed", (False, True))
def test_watch_resume_handoff_fresh_plan_and_decline_preserve_every_record(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch, placement, changed
) -> None:
    first = _plan(tmp_path)
    _failed_run(first)
    project = first.run.analysis.source_path
    profile = project.parent / "runtime/profiles/default.yaml"
    profile.write_bytes(
        _slurm_profile(tmp_path).read_bytes()
        if placement == "slurm"
        else b"schema_version: emrys.execution-profile.v1\nplacement: {kind: direct}\n"
    )
    readiness_calls = []

    def diagnose(*args, **kwargs):
        readiness_calls.append((args, kwargs))
        return first.readiness

    monkeypatch.setattr(control.doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        control.capacity, "observe_allocation", lambda: first.resources.allocation
    )

    def forbidden(*args, **kwargs):
        pytest.fail("A declined watch plan must not open logs, execute, or submit")

    monkeypatch.setattr(control, "_execute_plan", forbidden)
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    monkeypatch.setattr(control.slurm_submission, "submit", forbidden)
    handed_off = []
    confirmations = []
    before = {}

    def snapshot():
        return {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            if path.is_file()
            else None
            for path in tmp_path.rglob("*")
        }

    def before_read():
        assert handed_off == [True]
        assert snapshot() == before
        confirmations.append(True)

    monkeypatch.setattr(control.sys, "stdin", _InputStream("no\n", before_read))
    for name in ("stdout", "stderr"):
        monkeypatch.setattr(
            control.sys, name, _TerminalOutput(getattr(control.sys, name))
        )
    monkeypatch.setenv("TERM", "xterm")

    def watch(selected_project, *, run_root, review_actions, **kwargs):
        nonlocal before
        assert selected_project == project and run_root == first.run_root
        assert tuple(key for key, _label, _call in review_actions) == (b"p", b"b")
        if changed:
            profile.write_text("invalid profile selected after watch entry\n")
        before = snapshot()
        handed_off.append(True)
        return review_actions[0][2]()

    monkeypatch.setattr(control._inspection_presentation, "watch", watch)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    arguments = parser.parse_args(
        [first.run.run_id, "--project", str(project), "--watch", "--actions"]
    )
    arguments.execute = True
    assert control.inspect_from_args(arguments) == (2 if changed else 0)
    assert confirmations == ([] if changed else [True])
    assert len(readiness_calls) == int(not changed and placement == "direct")
    rendered = capsys.readouterr().err
    if changed:
        assert "emrys: error:" in rendered
        assert "Execute this plan?" not in rendered
    else:
        assert rendered.index("Run: ") < rendered.index("Execute this plan? [y/N]")
        assert (
            "no scheduler or workspace state was written" in rendered
            if placement == "slurm"
            else "no resume state was written" in rendered
        )
    assert snapshot() == before


@pytest.mark.parametrize("command", ("run", "resume"))
def test_public_preflight_failure_closes_log_without_run_mutation(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    if command == "run":
        _ready, _resources, project, workspace = _readiness(tmp_path)
        message, error = "injected Doctor failure", doctor.DoctorInputError
        owner, method = control.doctor, "diagnose_project"
        run_id = None
    else:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        project = build(workspace)
        run_id = "run-" + "a" * 64
        (workspace / "runs" / run_id).mkdir(parents=True)
        message = "injected resume inspection failure"
        error, owner, method = (
            inspection.InspectionError,
            control.inspection,
            "inspect_run",
        )
    root = workspace / "logs/application"
    opened = []
    real_open = control.open_attempt_log

    def capture_open(**kwargs):
        attempt = real_open(**kwargs)
        opened.append(attempt)
        return attempt

    def reject_preflight(*_args, **_kwargs):
        (log_path,) = root.rglob("*.jsonl")
        assert _log_events(log_path) == ["attempt_opened"]
        raise error(message)

    monkeypatch.setattr(control, "open_attempt_log", capture_open)
    monkeypatch.setattr(owner, method, reject_preflight)
    arguments = _command_arguments(project, execute=True)
    if run_id is not None:
        arguments.run = run_id
    assert getattr(control, f"{command}_from_args")(arguments) == 2
    assert len(opened) == 1
    with pytest.raises(ApplicationLogError, match="closed"):
        opened[0].logger(component="test", phase="after_preflight")
    (log_path,) = root.rglob("*.jsonl")
    records = _read_log(log_path)
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "attempt_failed",
    ]
    assert records[-1]["phase"] == "preflight"
    if run_id is None:
        assert not (workspace / "runs").exists()
    else:
        assert records[0]["scope_id"] == run_id
        assert list((workspace / "runs" / run_id).iterdir()) == []
    assert not list(workspace.rglob("run.lock"))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err
    assert "phase=preflight status=failed" in captured.err
    assert f"Application log: {log_path}" in captured.err


def test_execute_preflight_interrupt_terminalizes_log_and_preserves_signal(
    tmp_path: Path,
    capsys,
) -> None:
    plan = _plan(tmp_path)
    controls = _application_controls(tmp_path / "application-logs")

    with pytest.raises(KeyboardInterrupt):
        control._execute_plan(
            lambda: (_ for _ in ()).throw(KeyboardInterrupt),
            controls=controls,
            workspace=plan.workspace,
            mode="execute",
            scope_id="pending",
            entrypoint="emrys-run",
        )

    records = _read_log(next(controls.root.rglob("*.jsonl")))
    assert [record["event"] for record in records] == [
        "attempt_opened",
        "attempt_interrupted",
    ]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "phase=preflight status=interrupted" in captured.err
    assert "Next action: Retry when ready." in captured.err


@pytest.mark.parametrize("owned_lock", [True, False])
def test_execute_failure_summary_names_only_proven_owned_lock_and_recovery(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    owned_lock: bool,
) -> None:
    plan = _plan(tmp_path)
    lock_path = plan.run_root / "locks" / "run.lock"
    recovery_path = (
        plan.run_root / "attempts" / plan.workflow_attempt_id / "released-run-lock.json"
    )

    def fail_with_owned_paths(_plan, _observe, _inspection):
        lock_path.parent.mkdir(parents=True)
        attempt = plan.attempt_record
        if not owned_lock:
            attempt["owner_token"] = "workflow-owner-foreign"
        lock_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(
                orchestration_contracts.run_lock_record(attempt)
            )
        )
        recovery_path.parent.mkdir(parents=True)
        recovery_path.write_text("owned", encoding="utf-8")
        raise lifecycle.LifecycleError("injected lifecycle failure")

    controls = _application_controls(tmp_path / "application-logs")
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
    assert (f"Owned lock: {lock_path}" in captured.err) is owned_lock
    assert f"Owned recovery: {recovery_path}" in captured.err


def _slurm_profile(tmp_path: Path, *, cpus_per_task: int = 12) -> Path:
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
        require_reporter: bool,
    ):
        assert analysis_name is None
        assert require_reporter is True
        requirements.append(storage_requirement)
        return readiness

    monkeypatch.setattr(control.doctor, "diagnose_project", diagnose)
    monkeypatch.setattr(
        control.capacity,
        "observe_allocation",
        lambda: AllocationCapacity(
            cores=12,
            memory_mb=524_288,
            source="placement test allocation",
        ),
    )

    direct = load_execution_profile()
    slurm = load_execution_profile(config_path=_slurm_profile(tmp_path))
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
    from tests.tools.real_synthetic_e2e import symbolic_resource_document

    project = build(tmp_path / "project")
    profile = _slurm_profile(tmp_path)
    document = yaml.safe_load(profile.read_bytes())
    document["resources"] = symbolic_resource_document()
    profile.write_text(yaml.safe_dump(document), encoding="utf-8")
    return argparse.Namespace(
        project=project,
        analysis="sensitivity",
        profile=str(profile),
        log_level=None,
        log_root=None,
        execute=execute,
    )


@pytest.mark.parametrize("records", ("none", "several", "unavailable"))
def test_public_inspect_retains_submission_observations_before_any_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    records: str,
) -> None:
    from tests.orchestration.run_coordinator.test_slurm_submission import (
        _request_record,
    )

    project = build(tmp_path / "project")
    if records == "several":
        _, first, _ = _request_record(
            project.parent,
            stdout=b"700123;cluster-other\n",
            stderr=b"reason:\x1b[31m\xff\n",
        )
        _, second, _ = _request_record(project.parent, "b", stdout=b"")
        _, partial, _ = _request_record(project.parent, "c")
        (partial / "request.json").unlink()
        malformed = project.parent / "logs/submission-invalid"
        malformed.mkdir()
    elif records == "unavailable":
        (project.parent / "logs").write_bytes(b"not a directory\n")
    before = {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    }
    monkeypatch.setattr(
        control.slurm_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("inspection invoked a subprocess"),
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    arguments = parser.parse_args(["--project", str(project)])
    assert control.inspect_from_args(arguments) == (
        2 if records == "unavailable" else 0
    )
    captured = capsys.readouterr()
    if records == "unavailable":
        assert "emrys: error:" in captured.err
        assert "Runs: none found" not in captured.out
    else:
        assert "Retained submissions:" in captured.out
        assert "Runs: none found at inspection time." in captured.out
        assert "Do not submit again solely because a Run is absent" in captured.out
        if records == "none":
            assert (
                "None found; this does not establish that no job was submitted."
                in captured.out
            )
        else:
            for path in (first, second, partial, malformed):
                assert f"Request: {path}" in captured.out
            assert (
                "Recorded response job ID: 700123; cluster: cluster-other"
                in captured.out
            )
            assert "Recorded response job ID: unconfirmed" in captured.out
            assert "Records: partial" in captured.out
            assert "Records: malformed" in captured.out
            assert (
                "Current scheduler state and Run association are not established"
                in captured.out
            )
            assert r"reason:\x1b[31m" in captured.out
            assert "\x1b" not in captured.out
    assert {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    } == before
    assert (
        control.inspect_from_args(
            parser.parse_args(["run-" + "a" * 64, "--project", str(project)])
        )
        == 2
    )
    assert "Retained submissions:" not in capsys.readouterr().out


@pytest.mark.parametrize("level", ("normal", "verbose", "debug"))
def test_public_stop_preview_is_read_only_and_names_exact_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    level: str,
) -> None:
    from tests.orchestration.run_coordinator.test_slurm_submission import _stop_fixture

    fixture = _stop_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        control,
        "open_attempt_log",
        lambda **_kwargs: pytest.fail("stop preview opened a log"),
    )
    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        lambda *_args: pytest.fail("stop scanned application logs"),
    )
    parser = argparse.ArgumentParser()
    control.configure_stop_parser(parser)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert (
        control.stop_from_args(
            parser.parse_args(
                [
                    "--project",
                    str(fixture.project),
                    "--submission",
                    fixture.root.name,
                    "--log-level",
                    level,
                ]
            )
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"Project: {fixture.project}" in output
    assert fixture.context["scheduler_job_name"] in output
    assert "cluster alpha" in output and f"UID {os.getuid()}" in output
    assert "Preview only" in output and "--ctld" in output and "--me" in output
    assert not fixture.marker.exists()
    assert {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize("changed", (False, True))
def test_watch_stop_handoff_readmits_exact_request_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, changed
) -> None:
    from tests.orchestration.run_coordinator.test_slurm_submission import _stop_fixture

    fixture = _stop_fixture(tmp_path, monkeypatch)
    _watch_terminal(monkeypatch)

    def forbidden(*args, **kwargs):
        pytest.fail("Stop preview must not confirm, open a log, or issue cancellation")

    monkeypatch.setattr(control, "_confirm_execution", forbidden)
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    monkeypatch.setattr(
        control._submission_inspection, "inspect_submission_application", forbidden
    )
    before = {}

    def snapshot():
        return {
            path: path.read_bytes() if path.is_file() else None
            for path in tmp_path.rglob("*")
        }

    def watch(project, *, request, review_actions, **kwargs):
        nonlocal before
        assert project == fixture.project and request.request_root == fixture.root
        assert "run_root" not in kwargs
        assert tuple(key for key, _label, _call in review_actions) == (b"s",)
        assert fixture.queries == []
        if changed:
            (fixture.root / "request.json").write_bytes(b"{}")
        before = snapshot()
        return review_actions[0][2]()

    monkeypatch.setattr(control._inspection_presentation, "watch", watch)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    arguments = parser.parse_args(
        [
            "--project",
            str(fixture.project),
            "--submission",
            fixture.root.name,
            "--watch",
            "--actions",
        ]
    )
    arguments.execute = True
    assert control.inspect_from_args(arguments) == (2 if changed else 0)
    captured = capsys.readouterr()
    if changed:
        assert "emrys: error:" in captured.err
        assert "Preview only" not in captured.out
        assert fixture.queries == []
    else:
        assert "Preview only" in captured.out
        assert len(fixture.queries) == 1
    assert not fixture.marker.exists()
    assert snapshot() == before


@pytest.mark.parametrize(
    "outcome,expected",
    [
        ("terminal", 0),
        ("active", 1),
        ("unknown", 1),
        ("nonzero", 1),
        ("interrupt", 130),
        ("intent-write", 2),
        ("intent-sync", 2),
        ("replace-before-intent", 2),
        ("replace-during-intent", 2),
    ],
)
def test_public_stop_requires_durable_intent_and_preserves_uncertain_outcomes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
    expected: int,
) -> None:
    from emrys.libraries.application_logging.storage import (
        ApplicationLogFile,
        ApplicationLogStorageError,
    )
    from tests.orchestration.run_coordinator.test_slurm_submission import _stop_fixture

    fixture = _stop_fixture(
        tmp_path, monkeypatch, stop_status=7 if outcome == "nonzero" else 0
    )
    if outcome in {"active", "nonzero"}:
        fixture.replies[-1] = "RUNNING"
    elif outcome == "unknown":
        fixture.replies[-1] = None
    log_root = tmp_path / "explicit application logs"
    synchronized_intents = []
    written_intents = []
    write = ApplicationLogFile.write_bytes
    synchronize = ApplicationLogFile.synchronize
    moved = tmp_path / "preserved-stop-attempt"

    def replace_attempt(parent: Path) -> None:
        parent.rename(moved)
        parent.mkdir()

    def observe_write(file: ApplicationLogFile, payload: bytes) -> None:
        entry = json.loads(payload)
        if entry["event"] == "slurm_stop_intent":
            written_intents.append(entry)
            if outcome == "intent-write":
                raise ApplicationLogStorageError("stop intent write failed")
        write(file, payload)

    def observe_sync(file: ApplicationLogFile) -> None:
        latest = json.loads(file.path.read_text().splitlines()[-1])
        if latest["event"] == "slurm_stop_intent":
            if outcome == "intent-sync":
                raise ApplicationLogStorageError("stop intent fsync failed")
            synchronize(file)
            synchronized_intents.append(latest)
            if outcome == "replace-during-intent":
                replace_attempt(file.path.parent)
        else:
            synchronize(file)

    monkeypatch.setattr(ApplicationLogFile, "write_bytes", observe_write)
    monkeypatch.setattr(ApplicationLogFile, "synchronize", observe_sync)
    run = control.slurm_submission.subprocess.run
    mutations = []

    def observed_run(argv: tuple[str, ...], **kwargs: object) -> object:
        if argv[-1] == "--version":
            return run(argv, **kwargs)
        mutations.append(tuple(argv))
        assert len(synchronized_intents) == 1
        assert synchronized_intents[0]["fields"]["argv"] == list(argv)
        result = run(argv, **kwargs)
        if outcome == "interrupt":
            raise KeyboardInterrupt("operator stop interrupted")
        return result

    monkeypatch.setattr(control.slurm_submission.subprocess, "run", observed_run)
    if outcome == "replace-before-intent":
        observe = control.slurm_submission.scheduler_observation.command_bytes

        def replace_during_readmission(*args: object, **kwargs: object) -> object:
            response = observe(*args, **kwargs)
            if len(fixture.queries) == 2:
                (log,) = log_root.glob("maintenance-*/application-*/emrys-stop.jsonl")
                replace_attempt(log.parent)
            return response

        monkeypatch.setattr(
            control.slurm_submission.scheduler_observation,
            "command_bytes",
            replace_during_readmission,
        )
    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        lambda *_args: pytest.fail("stop scanned application logs"),
    )
    parser = argparse.ArgumentParser()
    control.configure_stop_parser(parser)
    arguments = parser.parse_args(
        [
            "--project",
            str(fixture.project),
            "--submission",
            str(fixture.root),
            "--execute",
            "--log-root",
            str(log_root),
        ]
    )
    assert control.stop_from_args(arguments) == expected
    captured = capsys.readouterr()
    attempted = outcome in {"terminal", "active", "unknown", "nonzero", "interrupt"}
    assert fixture.marker.exists() == attempted
    assert len(mutations) == (1 if attempted else 0)
    assert not (tmp_path / "runs").exists()
    assert "native-task quiescence" in captured.out
    assert "Stop diagnostics:" in captured.out
    if attempted:
        (log,) = log_root.glob("maintenance-*/application-*/emrys-stop.jsonl")
        records = _read_log(log)
        assert records[1]["event"] == "slurm_stop_intent"
        fields = records[1]["fields"]
        assert fields["request_root"] == str(fixture.root)
        assert fields["project"] == str(fixture.project)
        assert fields["job_id"] == "700123" and fields["submitter_uid"] == os.getuid()
        assert fields["scheduler_job_name"] == fixture.context["scheduler_job_name"]
        assert fields["client_version"] == "slurm 23.11.6"
        assert isinstance(fields["client_file_binding"], list)
        assert (log.parent / "scancel.stdout").read_bytes() == fixture.stdout
        assert (log.parent / "scancel.stderr").read_bytes() == fixture.stderr
        assert records[-1]["event"] == (
            "attempt_interrupted" if outcome == "interrupt" else "slurm_stop_observed"
        )
        if outcome != "interrupt":
            assert (
                "zero exit status means the controller request was processed"
                in captured.out
            )
            assert "Post-check scheduler observation:" in captured.out
        assert len(fixture.queries) == (2 if outcome == "interrupt" else 3)
    else:
        assert "emrys: error:" in captured.out + captured.err
        if outcome.startswith("replace-"):
            assert (moved / "emrys-stop.jsonl").is_file()
        assert len(fixture.queries) == 2


def test_oversized_submission_context_prevents_scheduler_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    arguments.analysis = "a" * 40000
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda *_args, **_kwargs: pytest.fail("oversized context submitted a job"),
    )
    before = {
        path: path.read_bytes()
        for path in arguments.project.parent.rglob("*")
        if path.is_file()
    }
    assert control.run_from_args(arguments) == 2
    assert "64 KiB" in capsys.readouterr().err
    (request,) = control.slurm_submission.submission_requests(arguments.project)
    assert request.record_status == "partial"
    assert request.recorded_job_id is None
    assert not (request.request_root / "request.json").exists()
    assert {
        path: path.read_bytes()
        for path in arguments.project.parent.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    "state", ("pending", "completed", "failed", "cancelled", "unavailable", "legacy")
)
@pytest.mark.parametrize("selector_kind", ("name", "absolute"))
def test_public_submission_selection_queries_only_the_exact_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
    selector_kind: str,
) -> None:
    from tests.orchestration.run_coordinator.test_slurm_submission import (
        _request_record,
    )

    project = build(tmp_path / "project")
    _, selected, context = _request_record(
        project.parent,
        stdout=b"700123;cluster-a\n",
        version="v1" if state == "legacy" else "v2",
    )
    _, other, _ = _request_record(project.parent, "b", stdout=b"700124\n")
    calls = []
    terminal = state in {"completed", "failed", "cancelled"}
    scheduler_exit = {"failed": "7:0", "cancelled": "0:15"}.get(state, "0:0")

    def query(argv, **_kwargs):
        calls.append(argv)
        assert "700123" in argv and "700124" not in argv
        assert "--clusters=cluster-a" in argv
        if state == "unavailable":
            return None
        if terminal and argv[0] == "squeue":
            return b""
        assert state != "legacy", "legacy diagnostic records cannot query a job"
        fields = (
            "700123",
            str(os.getuid()),
            f"CANCELLED by {os.getuid()}" if state == "cancelled" else state.upper(),
            "cluster-a",
            context["scheduler_stdout_pattern"].replace("%j", "700123"),
            context["scheduler_stderr_pattern"].replace("%j", "700123"),
            "Resources\x1b[31m" if state == "pending" else scheduler_exit,
        )
        return ("|".join(fields) + "\n").encode()

    monkeypatch.setattr(
        control.slurm_submission.scheduler_observation, "command_bytes", query
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    before = {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    }
    assert (
        control.inspect_from_args(parser.parse_args(["--project", str(project)])) == 0
    )
    roster = capsys.readouterr().out
    assert str(selected) in roster and str(other) in roster and calls == []
    monkeypatch.setattr(
        control,
        "_resolve_run_argument",
        lambda _args: pytest.fail("request selection entered Run selection"),
    )
    selector = selected.name if selector_kind == "name" else str(selected)
    assert (
        control.inspect_from_args(
            parser.parse_args(["--project", str(project), "--submission", selector])
        )
        == 0
    )
    output = capsys.readouterr().out
    assert str(selected) in output and str(other) not in output
    expected = state.upper() if state == "pending" or terminal else "UNKNOWN"
    assert f"Scheduler observation: {expected}" in output
    assert "Recorded response job ID: 700123; cluster: cluster-a" in output
    assert "Recorded scheduler stdout:" in output
    assert "Recorded scheduler stderr:" in output
    assert (
        "do not establish workflow entry, Run completion or recovery eligibility"
        in output
    )
    assert len(calls) == (2 if terminal else 0 if state == "legacy" else 1)
    if state == "pending":
        assert r"Queue reason: Resources\x1b[31m" in output
        assert "\x1b" not in output
    if terminal:
        assert "source: sacct" in output
        assert f"Scheduler exit status: {scheduler_exit}" in output
    assert {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    } == before
    calls.clear()
    for extra in (
        ("--submission", "submission-a"),
        ("--submission", selector, "run-" + "a" * 64),
    ):
        assert (
            control.inspect_from_args(
                parser.parse_args(["--project", str(project), *extra])
            )
            == 2
        )
        assert calls == []


@pytest.mark.parametrize("selector_kind", ("name", "absolute"))
def test_public_watch_selected_request_is_one_read_only_nonterminal_snapshot(
    tmp_path, monkeypatch, capsys, selector_kind
):
    from tests.orchestration.run_coordinator.test_submission_inspection import _request

    project = build(tmp_path / "project")
    request, _profile = _request(project.parent, version="v3")
    context = request.context
    calls = []

    def query(argv, **kwargs):
        calls.append(argv)
        return (
            "|".join(
                (
                    request.recorded_job_id,
                    str(os.getuid()),
                    "PENDING",
                    "local",
                    context["scheduler_stdout_pattern"].replace(
                        "%j", request.recorded_job_id
                    ),
                    context["scheduler_stderr_pattern"].replace(
                        "%j", request.recorded_job_id
                    ),
                    "Resources\x1b[31m",
                    context["scheduler_job_name"],
                    "0:00",
                    "1:00:00",
                    "12",
                    "compute",
                    "(Priority)",
                )
            )
            + "\n"
        ).encode()

    def forbidden(*args, **kwargs):
        pytest.fail("watch must not enter workflow, create a log, or choose a Run")

    monkeypatch.setattr(
        control.slurm_submission.scheduler_observation, "command_bytes", query
    )
    monkeypatch.setattr(control, "_resolve_run_argument", forbidden)
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    monkeypatch.setattr(control._inspection_presentation, "RefreshWorker", forbidden)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    assert "--watch" in parser.format_help()
    selector = (
        request.request_root.name
        if selector_kind == "name"
        else str(request.request_root)
    )
    before = {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    }
    argv = ["--project", str(project), "--submission", selector, "--watch"]
    assert control.inspect_from_args(parser.parse_args(argv)) == 0
    output = capsys.readouterr().out
    assert output.count("EMRYS inspection") == 1
    assert "Retained submissions:" not in output
    assert "Scheduler: PENDING" in output
    assert "Resources\\x1b[31m" in output and "\x1b" not in output
    assert "Application association as of" in output
    assert len(calls) == 1
    assert {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    } == before
    calls.clear()
    assert control.inspect_from_args(parser.parse_args([*argv, "run-" + "a" * 64])) == 2
    assert not calls


@pytest.mark.parametrize("explicit", (False, True))
def test_public_watch_run_uses_existing_selection_and_one_scientific_snapshot(
    tmp_path, monkeypatch, capsys, explicit
):
    from tests.orchestration.run_coordinator.test_inspection_presentation import _run

    project = build(tmp_path / "project")
    root = project.parent / "runs" / ("run-" + "a" * 64)
    root.mkdir(parents=True)
    calls = []

    def inspect(path):
        calls.append(path)
        return _run(path)

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Run-only watch must not invent submission identity or create a log"
        )

    monkeypatch.setattr(control.inspection, "inspect_run", inspect)
    monkeypatch.setattr(
        control.slurm_submission, "observe_submission_request", forbidden
    )
    monkeypatch.setattr(
        control._submission_inspection, "inspect_submission_application", forbidden
    )
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    before = {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    }
    argv = ["--project", str(project), "--watch", *([root.name] if explicit else [])]
    assert control.inspect_from_args(parser.parse_args(argv)) == 0
    assert calls == [root]
    output = capsys.readouterr().out
    assert "Run evidence as of:" in output and "Scheduler: UNKNOWN" in output
    assert "No exact submission selected" in output
    assert {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize("state", ["unknown", "candidate", "admitted"])
@pytest.mark.parametrize("selector_kind", ["name", "absolute"])
def test_public_application_correlation_scans_only_selected_request_and_escapes_evidence(
    tmp_path,
    monkeypatch,
    capsys,
    state,
    selector_kind,
):
    from tests.orchestration.run_coordinator.test_submission_inspection import _request
    from tests.orchestration.run_coordinator.test_slurm_submission import (
        _request_record,
    )

    project = build(tmp_path / "project")
    selected, _ = _request(project.parent, version="v3")
    _, other, _ = _request_record(project.parent, "b")
    calls = []
    scheduler_calls = []
    run_root = project.parent / "runs" / ("run-" + "d" * 64)
    values = {"diagnostics": ("recorded issue\nsecond line\x1b[31m",)}
    if state != "unknown":
        values.update(
            status="application-log-bound",
            application_log=tmp_path / "log\x1b[31m.jsonl",
            application_log_sha256="f" * 64,
            recorded_event="analysis_prepared",
            recorded_run_id=run_root.name,
            recorded_workflow_attempt_id="recorded\nAttempt",
            recorded_outcome="attempt_failed",
            recorded_outcome_phase="preflight\nother\x1b[31m",
        )
    if state == "admitted":
        values.update(
            status="run-and-attempt-associated",
            run_root=run_root,
            workflow_attempt_id="workflow-20260915T120000Z-" + "e" * 32,
        )
    observation = control._submission_inspection.SubmissionApplicationObservation(
        **values
    )

    def inspect_application(request):
        calls.append(request.request_root)
        assert request.request_root == selected.request_root
        return observation

    def observe_scheduler(request):
        scheduler_calls.append(request.request_root)
        return control.slurm_submission.scheduler_observation.unknown_observation(
            "fixture queue unavailable"
        )

    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        inspect_application,
    )
    monkeypatch.setattr(
        control.slurm_submission, "observe_submission_request", observe_scheduler
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    before = {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    }
    assert (
        control.inspect_from_args(parser.parse_args(["--project", str(project)])) == 0
    )
    roster = capsys.readouterr().out
    assert str(selected.request_root) in roster and str(other) in roster
    assert calls == scheduler_calls == []
    monkeypatch.setattr(
        control,
        "_resolve_run_argument",
        lambda *_a: pytest.fail("request inspection entered Run picker"),
    )
    selector = (
        selected.request_root.name
        if selector_kind == "name"
        else str(selected.request_root)
    )
    assert (
        control.inspect_from_args(
            parser.parse_args(["--project", str(project), "--submission", selector])
        )
        == 0
    )
    output = capsys.readouterr().out
    assert calls == scheduler_calls == [selected.request_root]
    assert r"recorded issue\nsecond line\x1b[31m" in output and "\x1b" not in output
    assert ("Preparation recorded:" in output) is (state != "unknown")
    assert ("Recorded application outcome:" in output) is (state != "unknown")
    assert ("Admitted Run:" in output) is (state == "admitted")
    assert ("Admitted Attempt record:" in output) is (state == "admitted")
    if state != "unknown":
        assert r"log\x1b[31m.jsonl" in output and r"Attempt=recorded\nAttempt" in output
        assert "Log snapshot SHA-256: " + "f" * 64 in output
        assert r"attempt_failed; phase: preflight\nother\x1b[31m" in output
    assert {
        path: path.read_bytes() for path in project.parent.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize(
    ("placement", "overrides", "message"),
    (
        ({"cpus_per_task": 3}, {}, "Workflow cores exceed Slurm reservation: 4 > 3"),
        (
            {"memory_mb": 4096},
            {"workflow_memory_mb": 8192},
            "Workflow memory exceeds Slurm reservation: 8192 > 4096 MiB",
        ),
        (
            {"memory_mb": 4096},
            {"stage_memory_mb": [("00a", 8192)]},
            "workflow memory within Slurm reservation: 1 x 8192 > 4096 MiB",
        ),
    ),
)
def test_public_slurm_rejects_known_reservation_shortfall_before_submission(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    placement: dict[str, int],
    overrides: dict[str, object],
    message: str,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    profile_path = Path(arguments.profile)
    document = yaml.safe_load(profile_path.read_bytes())
    document["placement"].update(placement)
    profile_path.write_text(yaml.safe_dump(document), encoding="utf-8")
    for key, value in overrides.items():
        setattr(arguments, key, value)
    monkeypatch.setattr(
        control.slurm_submission,
        "plan_submission",
        lambda *_args, **_kwargs: pytest.fail(
            "reservation shortfall reached submission planning"
        ),
    )

    assert control.run_from_args(arguments) == 2
    assert message in capsys.readouterr().err
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
        project=first.run.analysis.source_path,
        run=first.run.run_id,
        profile=str(_slurm_profile(tmp_path, cpus_per_task=cpus_per_task)),
        log_level=None,
        log_root=None,
        execute=True,
    )
    submissions = []
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda submission, **_kwargs: submissions.append(submission) or "812345",
    )
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: pytest.fail(
            "submit host performed compute-allocation readiness"
        ),
    )

    assert control.resume_from_args(arguments) == expected_exit
    captured = capsys.readouterr()
    if expected_exit == 2:
        assert submissions == []
        assert "Workflow cores exceed Slurm reservation: 8 > 4" in captured.err
        assert not (first.workspace / "logs").exists()
    else:
        assert len(submissions) == 1
        assert captured.out.startswith("JOB_ID=812345\n")
        (request_path,) = (first.workspace / "logs").glob("submission-*/request.json")
        request = json.loads(request_path.read_bytes())
        assert request["command"] == "resume"
        assert request["requested_run"] == first.run.run_id
        assert request["project"] == str(first.run.analysis.source_path)
        selected_profile = load_execution_profile(config_path=Path(arguments.profile))
        inherited_profile = replace(
            selected_profile,
            resource_policy=first.resources.policy,
        )
        assert f"Workflow CPU ceiling: {workflow_cores};" in captured.err
        assert inherited_profile.binding_sha256 != selected_profile.binding_sha256
        assert any(
            f"{control.slurm_submission.PROFILE_SHA256_ENV}="
            f"{inherited_profile.binding_sha256}" in value
            for value in submissions[0].argv
        )

        monkeypatch.setenv(
            control.slurm_submission.DELEGATE_MARKER_ENV,
            control.slurm_submission.DELEGATE_MARKER,
        )
        monkeypatch.setenv(
            control.slurm_submission.PROFILE_SHA256_ENV,
            inherited_profile.binding_sha256,
        )
        monkeypatch.setenv(
            control.slurm_submission.SUBMIT_UID_ENV,
            str(os.getuid()),
        )
        monkeypatch.setenv("SLURM_JOB_ID", "812345")
        delegated, job_id = control._resolve_execution_profile(
            arguments,
            first.run.analysis.source_path,
            ResourceOverrides(),
            resume_run_root=first.run_root,
        )
        assert (delegated.binding_sha256, job_id) == (
            inherited_profile.binding_sha256,
            "812345",
        )
        monkeypatch.setenv(
            control.slurm_submission.PROFILE_SHA256_ENV,
            selected_profile.binding_sha256,
        )
        with pytest.raises(
            control.ExecutionProfileError,
            match="Execution-profile binding SHA-256 differs",
        ):
            control._resolve_execution_profile(
                arguments,
                first.run.analysis.source_path,
                ResourceOverrides(),
                resume_run_root=first.run_root,
            )


@pytest.mark.parametrize("interactive", [False, True])
def test_public_slurm_dry_run_is_no_write_and_skips_compute_readiness(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    interactive: bool,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=False)
    token = "d" * 32
    monkeypatch.setattr(control.uuid, "uuid4", lambda: SimpleNamespace(hex=token))
    monkeypatch.setattr(
        control.sys,
        "stdin",
        _InputStream(
            "n\n" if interactive else AssertionError("nonterminal input was read"),
            terminal=interactive,
        ),
    )
    monkeypatch.setattr(control.sys, "stderr", _TerminalOutput(control.sys.stderr))
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda _plan, **_kwargs: pytest.fail("dry-run submitted a scheduler job"),
    )
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
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
        assert ("Execute this plan?" in captured.err) is interactive
        assert not (workspace / "logs").exists()

    normal = projections["normal"]
    assert "Execution placement: Slurm" in normal
    assert "Analysis: 'sensitivity'" in normal
    assert (
        "Allocation request: 12 CPUs, 01:00:00; memory: site default (unknown)"
        in normal
    )
    assert (
        "Node request: 1; requested host(s): scheduler-selected; exact host unknown"
        in normal
    )
    assert "Exclusive allocation: not requested; site policy applies" in normal
    assert (
        "Workflow CPU ceiling: 4; memory ceiling: allocation capacity (unknown until execution)"
        in normal
    )
    assert "Stage thread caps:" in normal
    assert "Repeated-stage concurrency caps:" in normal
    assert "Stage memory:" in normal
    assert "Dry-run complete; no scheduler or workspace state was written." in normal
    assert "Execution profile:" not in normal
    assert "Scheduler stdout:" not in normal
    assert "Scheduler stderr:" not in normal
    assert "Scheduler command:" not in normal

    verbose = projections["verbose"]
    assert set(normal.splitlines()) <= set(verbose.splitlines())
    assert f"Execution profile: {arguments.profile}" in verbose
    assert (
        f"Scheduler stdout: {workspace}/logs/emrys-local-pilot-{token}-%j.out"
        in verbose
    )
    assert (
        f"Scheduler stderr: {workspace}/logs/emrys-local-pilot-{token}-%j.err"
        in verbose
    )
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
    arguments.log_root = tmp_path / "custom application logs"
    arguments.analysis = "" if execute else "sensitivity"
    arguments.through = "analysis" if execute else "processing"
    arguments.from_processing_run = "run-" + "a" * 64 if execute else None
    arguments.no_report = True
    workspace = arguments.project.parent
    if execute:
        (workspace / "runs" / arguments.from_processing_run).mkdir(parents=True)
    submissions = []
    admitted = load_execution_profile(config_path=Path(arguments.profile))
    tokens = []
    original_uuid = control.uuid.uuid4

    def request_uuid():
        value = original_uuid()
        tokens.append(value.hex)
        return value

    monkeypatch.setattr(control.uuid, "uuid4", request_uuid)

    def submit(plan, *, record_path):
        context = json.loads(record_path.with_name("request.json").read_bytes())
        assert context["schema_version"] == "emrys.submission-request.v3"
        assert context["scheduler_job_name"] == plan.job_name
        assert plan.job_name == f"emrys-local-pilot-{tokens[0]}"
        assert f"--job-name={plan.job_name}" in plan.argv
        assert record_path.parent.name == f"submission-{tokens[0]}"
        assert plan.stdout_pattern.name == f"emrys-local-pilot-{tokens[0]}-%j.out"
        assert plan.stderr_pattern.name == f"emrys-local-pilot-{tokens[0]}-%j.err"
        assert context["command"] == "run"
        assert context["project"] == str(arguments.project)
        assert context["requested_run"] is None
        assert context["analysis"] == arguments.analysis
        assert context["application_log_root"] == str(
            control._resolve_controls(arguments, workspace).root
        )
        assert context["profile_binding_sha256"] == admitted.binding_sha256
        assert context["submitter_uid"] == os.getuid()
        assert datetime.fromisoformat(context["created_at"]).tzinfo is not None
        assert "--execute" in context["emrys_argv"]
        assert context["scheduler_stdout_pattern"] == str(plan.stdout_pattern)
        assert context["scheduler_stderr_pattern"] == str(plan.stderr_pattern)
        record_path.write_bytes(b"812345\n")
        record_path.with_suffix(".stderr").write_bytes(b"")
        submissions.append(plan)
        return "812345"

    if not execute:

        def before_read() -> None:
            assert submissions == []
            assert len(tokens) == 1
            assert not (workspace / "logs").exists()

        _terminal_input(monkeypatch, "y\n", before_read)
    monkeypatch.setattr(control.slurm_submission, "submit", submit)
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: pytest.fail(
            "submit host performed compute-allocation readiness"
        ),
    )

    assert control.run_from_args(arguments) == 0

    captured = capsys.readouterr()
    assert len(tokens) == 1
    assert captured.out == (
        "JOB_ID=812345\n"
        f"OUT={workspace}/logs/emrys-local-pilot-{tokens[0]}-812345.out\n"
        f"ERR={workspace}/logs/emrys-local-pilot-{tokens[0]}-812345.err\n"
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
    request_roots = list((workspace / "logs").iterdir())
    assert len(request_roots) == 1
    assert request_roots[0].name.startswith("submission-")
    assert request_roots[0].stat().st_mode & 0o777 == 0o700
    assert (request_roots[0] / "request.json").stat().st_mode & 0o777 == 0o600
    assert sorted(path.name for path in request_roots[0].iterdir()) == [
        "request.json",
        "sbatch.stderr",
        "sbatch.stdout",
    ]
    (retained,) = control.slurm_submission.submission_requests(arguments.project)
    assert retained.record_status == "recorded-response"
    assert retained.recorded_job_id == "812345"
    assert retained.context["analysis"] == arguments.analysis
    assert "Execution placement: Slurm" in captured.err
    assert all(line in captured.err for line in admitted.submission_summary())
    if not execute:
        assert captured.err.index(
            admitted.submission_summary()[-1]
        ) < captured.err.index("Execute this plan?")
    assert ("Execute this plan? [y/N]" in captured.err) is not execute
    assert not arguments.log_root.exists()


@pytest.mark.parametrize("command", ("run", "resume", "report"))
def test_repeated_scheduled_commands_keep_distinct_frozen_streams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    arguments.run = "run-" + "a" * 64
    workspace = arguments.project.parent
    profile = load_execution_profile(config_path=Path(arguments.profile))
    controls = control._resolve_controls(arguments, workspace)
    plans = []

    def submit(plan, *, record_path):
        plans.append(plan)
        record_path.write_bytes(b"812345\n")
        record_path.with_suffix(".stderr").write_bytes(b"")
        return "812345"

    monkeypatch.setattr(control.slurm_submission, "submit", submit)
    for _ in range(2):
        assert (
            control._schedule(
                command, arguments, profile, controls, ResourceOverrides(), workspace
            )
            == 0
        )
    records = control.slurm_submission.submission_requests(arguments.project)
    assert len(records) == len(plans) == 2
    assert plans[0].stdout_pattern != plans[1].stdout_pattern
    assert plans[0].stderr_pattern != plans[1].stderr_pattern
    assert {record.context["scheduler_stdout_pattern"] for record in records} == {
        str(plan.stdout_pattern) for plan in plans
    }
    assert all(record.context["command"] == command for record in records)
    assert all(record.recorded_job_id == "812345" for record in records)


@pytest.mark.parametrize(
    "failure",
    (
        "collision",
        "context_open",
        "context_fsync",
        "request_directory_fsync",
        "logs_directory_fsync",
    ),
)
def test_submission_request_failure_preserves_partial_evidence_before_sbatch(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    request_root = arguments.project.parent / "logs" / ("submission-" + "a" * 32)
    monkeypatch.setattr(control.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    if failure == "collision":
        request_root.mkdir(parents=True)
        (request_root / "preserved").write_bytes(b"prior request evidence")
    elif failure == "context_open":

        def reject_open(*_args, **_kwargs):
            raise OSError("context open refused")

        monkeypatch.setattr(control, "open", reject_open, raising=False)
    elif failure == "context_fsync":

        def reject_fsync(_descriptor):
            raise OSError("context fsync refused")

        monkeypatch.setattr(control.os, "fsync", reject_fsync)
    else:
        synchronized = []

        def synchronize(path):
            synchronized.append(path)
            if path == (
                request_root
                if failure == "request_directory_fsync"
                else request_root.parent
            ):
                raise OSError("directory fsync refused")

        monkeypatch.setattr(control.onboarding, "_fsync_directory", synchronize)
    monkeypatch.setattr(
        control.slurm_submission,
        "submit",
        lambda *_args, **_kwargs: pytest.fail("record failure reached sbatch"),
    )
    assert control.run_from_args(arguments) == 2
    assert "sbatch was not invoked" in capsys.readouterr().err
    assert request_root.is_dir()
    if failure == "collision":
        assert (request_root / "preserved").read_bytes() == b"prior request evidence"
    elif failure == "context_open":
        assert list(request_root.iterdir()) == []
    else:
        assert (
            json.loads((request_root / "request.json").read_bytes())["command"] == "run"
        )
        if failure.endswith("directory_fsync"):
            assert synchronized == (
                [request_root]
                if failure == "request_directory_fsync"
                else [request_root, request_root.parent]
            )
    assert not (arguments.project.parent / "logs/application").exists()


@pytest.mark.parametrize("command", ("run", "resume", "report"))
@pytest.mark.parametrize("failure", ("binding", "allocation", "planning", "submission"))
def test_public_slurm_errors_keep_control_exit_and_never_retry(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    failure: str,
) -> None:
    root = tmp_path / ("project%logs" if failure == "planning" else "fixture")
    root.mkdir()
    if command == "resume":
        plan = _plan(root)
        _failed_run(plan)
        project, run_id = plan.run.analysis.source_path, plan.run.run_id
    else:
        project = build(root / "project")
        run_id = "run-" + "a" * 64
        if command == "report":
            (project.parent / "runs" / run_id).mkdir(parents=True)
    arguments = argparse.Namespace(
        project=project,
        run=run_id,
        profile=str(_slurm_profile(root, cpus_per_task=12)),
        log_level=None,
        log_root=None,
        execute=True,
    )
    scheduler = control.slurm_submission
    for name in (
        scheduler.DELEGATE_MARKER_ENV,
        scheduler.PROFILE_SHA256_ENV,
        scheduler.SUBMIT_UID_ENV,
        "SLURM_JOB_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    if failure == "binding":
        monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
    elif failure == "allocation":
        profile, _job = control._resolve_execution_profile(
            arguments,
            project,
            ResourceOverrides(),
            project.parent / "runs" / run_id if command == "resume" else None,
        )
        monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
        monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, profile.binding_sha256)
        monkeypatch.setenv(scheduler.SUBMIT_UID_ENV, str(os.getuid()))
        monkeypatch.setenv("SLURM_JOB_ID", "0")
    submitted = root / "submitted"
    rejector = root / "sbatch"
    rejector.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib\n"
        "os.close(0)\n"
        f"with pathlib.Path({str(submitted)!r}).open('ab') as stream: stream.write(b'once\\n')\n"
        "os.write(2, b'sbatch: invalid account\\n\\x1b[31m')\n"
        "raise SystemExit(23)\n"
    )
    rejector.chmod(0o700)
    original_plan = scheduler.plan_submission

    def plan_rejected(*args, **kwargs):
        planned = original_plan(*args, **kwargs, sbatch=str(rejector))
        return replace(
            planned, batch_script=planned.batch_script + "# padding\n" * 100_000
        )

    monkeypatch.setattr(scheduler, "plan_submission", plan_rejected)
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: pytest.fail(
            "submission failure reached compute readiness"
        ),
    )
    monkeypatch.setattr(
        reporting_operation,
        "run_reporting",
        lambda *_args, **_kwargs: pytest.fail("submission failure executed reporting"),
    )
    assert getattr(control, f"{command}_from_args")(arguments) == 2
    output = capsys.readouterr()
    assert output.out == ""
    expected = {
        "binding": "Private Slurm delegate context is incomplete",
        "allocation": "canonical positive decimal",
        "planning": "scheduler log directory must not contain",
        "submission": "job ID unconfirmed",
    }
    assert expected[failure] in output.err
    assert "\x1b" not in output.err
    if failure == "submission":
        assert submitted.read_bytes() == b"once\n"
        assert "sbatch exited with 23" in output.err
        assert "invalid account" in output.err
        (request_path,) = (project.parent / "logs").glob("submission-*/sbatch.stderr")
        assert request_path.read_bytes() == b"sbatch: invalid account\n\x1b[31m"
    else:
        assert not submitted.exists()
    assert not (project.parent / "logs/application").exists()


@pytest.mark.parametrize("command", ["run", "resume", "report"])
@pytest.mark.parametrize("request_token", [None, "b" * 32])
def test_delegated_operation_records_request_before_preparation_in_one_unique_log(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    request_token: str | None,
) -> None:
    from tests.orchestration.run_coordinator.test_slurm_submission import (
        _batch_environment,
        _request_record,
    )
    from emrys.orchestration.run_coordinator._submission_inspection import (
        inspect_submission_application,
    )

    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    arguments.log_root = tmp_path / "custom application logs"
    arguments.run = "run-" + "a" * 64
    workspace = arguments.project.parent
    run_root = workspace / "runs" / arguments.run
    if command != "run":
        run_root.mkdir(parents=True)
    profile_path = Path(arguments.profile)
    document = yaml.safe_load(profile_path.read_bytes())
    document["resources"] = load_execution_profile().resource_policy.document()
    profile_path.write_text(yaml.safe_dump(document))
    profile = load_execution_profile(profile_path)
    scheduler = control.slurm_submission
    submission = scheduler.plan_submission(
        profile,
        emrys_argv=("emrys", command),
        log_dir=workspace / "logs",
        request_token=request_token,
    )
    request = None
    if request_token is not None:
        _request_record(
            workspace,
            request_token[0],
            stdout=b"812345\n",
            version="v3",
            command=command,
            project=str(arguments.project),
            requested_run=None if command == "run" else arguments.run,
            application_log_root=str(arguments.log_root),
            profile_binding_sha256=profile.binding_sha256,
        )
        (request,) = scheduler.submission_requests(arguments.project)
    for name in (
        scheduler.DELEGATE_MARKER_ENV,
        scheduler.PROFILE_SHA256_ENV,
        scheduler.SUBMIT_UID_ENV,
        scheduler.REQUEST_TOKEN_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in _batch_environment(submission, job_id="812345").items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        scheduler,
        "submit",
        lambda *_args, **_kwargs: pytest.fail("delegate resubmitted"),
    )
    completed_paths: set[Path] = set()
    identities: set[str] = set()

    def admitted_log() -> None:
        paths = set(arguments.log_root.rglob("*.jsonl")) - completed_paths
        assert len(paths) == 1
        path = paths.pop()
        records = _read_log(path)
        assert records[0]["event"] == "attempt_opened"
        assert records[0]["fields"]["slurm_job_id"] == "812345"
        expected_events = ["attempt_opened"]
        if request_token is not None:
            expected_events.append("submission_context")
            assert records[1]["fields"] == {
                "request_token": request_token,
                "profile_binding_sha256": profile.binding_sha256,
                "project_root": str(workspace),
            }
            assert records[1]["console_detail"] == "durable_only"
        if command == "report":
            expected_events.append("reporting_started")
            assert records[-1]["fields"]["run_root"] == str(run_root)
        assert [record["event"] for record in records] == expected_events
        if request is not None:
            correlated = inspect_submission_application(request)
            assert correlated.status == (
                "unknown" if completed_paths else "application-log-bound"
            )
            assert correlated.application_log == (None if completed_paths else path)
            assert correlated.run_root is correlated.workflow_attempt_id is None
            assert (
                correlated.recorded_outcome is correlated.recorded_outcome_phase is None
            )
        identities.add(records[0]["execution_attempt_id"])
        completed_paths.add(path)

    def preflight(*_args, **_kwargs):
        admitted_log()
        raise control.ControlError("fixture preparation failure")

    def report(_root, *, execute, observe_generation_start):
        assert execute and _root == run_root
        observe_generation_start()
        admitted_log()
        raise reporting_operation.ReportingOperationError("fixture reporting failure")

    monkeypatch.setattr(control.doctor, "diagnose_project", preflight)
    monkeypatch.setattr(control.inspection, "inspect_run", preflight)
    monkeypatch.setattr(reporting_operation, "run_reporting", report)
    for _ in range(2):
        assert getattr(control, f"{command}_from_args")(arguments) == (
            1 if command == "report" else 2
        )
        if request is not None:
            correlated = inspect_submission_application(request)
            if len(completed_paths) == 1:
                assert correlated.status == "application-log-bound"
                assert correlated.recorded_outcome == "attempt_failed"
                assert correlated.recorded_outcome_phase == (
                    "reporting" if command == "report" else "preflight"
                )
                assert correlated.run_root is correlated.workflow_attempt_id is None
            else:
                assert correlated.status == "unknown"
                assert (
                    correlated.recorded_outcome
                    is correlated.recorded_outcome_phase
                    is None
                )
    assert len(completed_paths) == len(identities) == 2
    assert all(path.parent.name in identities for path in completed_paths)
    assert all(
        json.loads(path.read_text().splitlines()[-1])["event"] == "attempt_failed"
        for path in completed_paths
    )
    if request is None:
        assert not (workspace / "logs").exists()
    else:
        assert tuple((workspace / "logs").iterdir()) == (request.request_root,)
    if command == "run":
        assert not (workspace / "runs").exists()
    else:
        assert list(run_root.iterdir()) == []
    if request_token is not None:
        assert request_token not in capsys.readouterr().err


def test_private_slurm_delegate_rejects_profile_drift_before_readiness(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _scheduled_run_arguments(tmp_path, execute=True)
    scheduler = control.slurm_submission
    admitted = load_execution_profile(config_path=Path(arguments.profile))
    selected_profile = Path(arguments.profile)
    selected_profile.write_bytes(
        selected_profile.read_bytes() + b"# equivalent rewrite\n"
    )
    monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
    monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, admitted.binding_sha256)
    monkeypatch.setenv(scheduler.SUBMIT_UID_ENV, str(os.getuid()))
    monkeypatch.setenv("SLURM_JOB_ID", "812345")
    monkeypatch.setattr(
        control.doctor,
        "diagnose_project",
        lambda *_args, **_kwargs: pytest.fail("digest drift reached compute readiness"),
    )

    assert control.run_from_args(arguments) == 2
    assert "Execution-profile binding SHA-256 differs" in capsys.readouterr().err
    assert not (arguments.project.parent / "logs").exists()
    profile = load_execution_profile(config_path=selected_profile)
    monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, profile.binding_sha256)
    monkeypatch.setenv("SLURM_JOB_ID", "01")
    assert control.run_from_args(arguments) == 2
    assert "canonical positive decimal" in capsys.readouterr().err
    direct = load_execution_profile()
    arguments.profile = str(direct.source_path)
    monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, direct.binding_sha256)
    monkeypatch.setenv("SLURM_JOB_ID", "812345")
    assert control.run_from_args(arguments) == 2
    assert "requires Slurm placement" in capsys.readouterr().err


@pytest.mark.parametrize(
    "report_mode,fault,expected_events",
    (
        ("disabled", None, ["reporting_skipped"]),
        ("success", None, ["reporting_started", "reporting_completed"]),
        ("failure", None, ["reporting_started", "reporting_failed"]),
        ("disabled", "write", ["attempt_opened", "analysis_prepared"]),
        (
            "disabled",
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
def test_execution_log_preserves_receipt_and_reporting_boundary(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    report_mode: str,
    fault: str | None,
    expected_events: list[str],
) -> None:
    plan = _plan(tmp_path)
    receipt_path = tmp_path / "attempt-receipt.json"
    receipt_bytes = (
        b"immutable scientific receipt\n"
        if fault is None
        else b"authoritative receipt\n"
    )
    lock_path, released_lock_path = (
        tmp_path / "run.lock",
        tmp_path / "released-lock.json",
    )
    if fault is None:
        lock_path.write_text("active\n")
    observed_events, report_calls, runtime_inspections = [], [], []
    controls = _application_controls(tmp_path / "application-logs")

    def execute(_plan, observe, initial_runtime_inspection):
        runtime_inspections.append(initial_runtime_inspection)
        for event_name in ("analysis_started", "publication_ready"):
            observed_events.append(event_name)
            observe(event_name)
        receipt_path.write_bytes(receipt_bytes)
        if fault is None:
            lock_path.replace(released_lock_path)
        return _lifecycle_outcome(tmp_path, status="succeeded")

    def report(run_root: Path, *, execute: bool):
        assert report_mode != "disabled", "--no-report invoked reporting"
        events = _log_events(next(controls.root.rglob("*.jsonl")))
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
    elif fault == "sync":

        def reject_sync(_file: ApplicationLogFile) -> None:
            raise ApplicationLogStorageError("injected application-log sync failure")

        monkeypatch.setattr(ApplicationLogFile, "synchronize", reject_sync)
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
    events = _log_events(next(controls.root.rglob("*.jsonl")))
    prefix = [
        "attempt_opened",
        "analysis_prepared",
        "analysis_started",
        "publication_ready",
        "attempt_receipt_observed",
    ]
    assert events == (prefix + expected_events if fault is None else expected_events)
    assert observed_events == ["analysis_started", "publication_ready"]
    assert runtime_inspections == [plan.readiness.inspection]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"Evidence: {receipt_path}" in captured.err
    if fault is not None:
        assert captured.err.count("Application logging degraded") == 1
    if report_mode == "failure":
        assert "Scientific Results remain complete" in captured.err
        assert "Inspect the Run and follow its admitted next action" in captured.err
        assert "emrys report" not in captured.err


@pytest.mark.parametrize(
    (
        "outcome_status",
        "execute_requested",
        "logging_fails",
        "via_watch",
    ),
    (
        ("planned", False, False, False),
        ("reused", False, False, False),
        ("generated", True, False, False),
        ("generated", True, True, False),
        ("reused", True, False, False),
        ("planned", False, False, True),
        ("reused", False, False, True),
    ),
)
def test_standalone_report_logging_boundary(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    outcome_status: str,
    execute_requested: bool,
    logging_fails: bool,
    via_watch: bool,
) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "project.yaml"
    run_root = workspace / "runs" / ("run-" + "a" * 64)
    run_root.mkdir(parents=True)
    project.write_text("report selection anchor\n", encoding="utf-8")
    if execute_requested or outcome_status == "planned":
        profile = workspace / "runtime/profiles/default.yaml"
        profile.parent.mkdir(parents=True)
        profile.write_bytes(project_default_profile_bytes())
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
        project=project,
        run=run_root.name,
        execute=execute_requested,
        log_level=None,
        log_root=None,
    )
    monkeypatch.setattr(reporting_operation, "run_reporting", report)
    if not execute_requested and outcome_status == "reused":
        monkeypatch.setattr(
            control,
            "_resolve_execution_profile",
            lambda *_args: pytest.fail(
                "completed reporting resolved an execution profile"
            ),
        )

    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }
    if via_watch:
        _watch_terminal(monkeypatch)

        def forbidden(*args, **kwargs):
            pytest.fail("Watch report preview must not confirm, submit, or open logs")

        monkeypatch.setattr(control, "_confirm_execution", forbidden)
        monkeypatch.setattr(control, "open_attempt_log", forbidden)
        monkeypatch.setattr(control.slurm_submission, "submit", forbidden)

        def watch(selected_project, *, run_root: Path, review_actions, **kwargs):
            assert selected_project == project and run_root.name == arguments.run
            assert calls == []
            return next(
                callback for key, _label, callback in review_actions if key == b"b"
            )()

        monkeypatch.setattr(control._inspection_presentation, "watch", watch)
        parser = argparse.ArgumentParser()
        control.configure_inspect_parser(parser)
        selected = parser.parse_args(
            [run_root.name, "--project", str(project), "--watch", "--actions"]
        )
        selected.execute = True
        assert control.inspect_from_args(selected) == 0
        assert {
            path: path.read_bytes() if path.is_file() else None
            for path in tmp_path.rglob("*")
        } == before
    else:
        assert control.report_from_args(arguments) == 0
    generated = execute_requested and outcome_status == "generated"
    assert calls == [execute_requested]
    rendered = capsys.readouterr().err
    assert f"Reporting: {outcome_status}" in rendered
    assert ("Execution placement: Direct" in rendered) is (outcome_status == "planned")
    log_paths = list((workspace / "logs" / "application").rglob("*.jsonl"))
    if logging_fails:
        assert log_paths == []
        assert "Application logging unavailable for reporting" in rendered
    elif generated:
        assert len(log_paths) == 1
        records = _read_log(log_paths[0])
        assert [record["event"] for record in records] == [
            "attempt_opened",
            "reporting_started",
            "reporting_completed",
        ]
    else:
        assert log_paths == []


@pytest.mark.parametrize("selection", ("missing", "../unsupported"))
def test_planned_report_rejects_an_unavailable_or_unsupported_profile_without_writing(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch, selection: str
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("report selection anchor\n", encoding="utf-8")
    run_root = tmp_path / "runs" / ("run-" + "a" * 64)
    run_root.mkdir(parents=True)
    monkeypatch.setattr(
        reporting_operation,
        "run_reporting",
        lambda _root, *, execute: reporting_operation.ReportingOperationOutcome(
            status="planned", verified_report_locations=()
        ),
    )
    parser = argparse.ArgumentParser()
    control.configure_report_parser(parser)
    arguments = parser.parse_args(
        [run_root.name, "--project", str(project), "--profile", selection]
    )
    before = sorted(tmp_path.rglob("*"))
    assert control.report_from_args(arguments) == 2
    output = capsys.readouterr()
    assert "emrys: error:" in output.err
    assert "Reporting: planned" not in output.err
    assert "Execution placement:" not in output.err
    assert sorted(tmp_path.rglob("*")) == before


def test_watch_report_handoff_freshly_refuses_ineligible_run_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    first = _plan(tmp_path)
    _failed_run(first)
    project = first.run.analysis.source_path
    _watch_terminal(monkeypatch)

    def forbidden(*args, **kwargs):
        pytest.fail("Ineligible report preview must not confirm, open logs, or submit")

    monkeypatch.setattr(control, "_confirm_execution", forbidden)
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    monkeypatch.setattr(control.slurm_submission, "submit", forbidden)
    monkeypatch.setattr(
        control._inspection_presentation,
        "watch",
        lambda _project, *, review_actions, **_kwargs: next(
            callback for key, _label, callback in review_actions if key == b"b"
        )(),
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    arguments = parser.parse_args(
        [first.run.run_id, "--project", str(project), "--watch", "--actions"]
    )
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }
    assert control.inspect_from_args(arguments) == 2
    assert "emrys: error:" in capsys.readouterr().err
    assert {
        path: path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    } == before


@pytest.mark.parametrize("profile_selection", ("default", "named", "absolute"))
def test_standalone_report_uses_project_slurm_placement(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch, profile_selection: str
) -> None:
    parser = argparse.ArgumentParser()
    control.configure_report_parser(parser)

    project = tmp_path / "project.yaml"
    project.write_text("report selection anchor\n", encoding="utf-8")
    run_root = tmp_path / "runs" / ("run-" + "a" * 64)
    run_root.mkdir(parents=True)
    profile = tmp_path / "runtime/profiles/default.yaml"
    profile.parent.mkdir(parents=True)
    if profile_selection != "default":
        profile.write_bytes(project_default_profile_bytes())
        profile = (
            profile.with_name("compute.yaml")
            if profile_selection == "named"
            else tmp_path / "external-profile.yaml"
        )
    profile.write_bytes(project_default_profile_bytes("viking"))
    calls: list[bool] = []
    submissions = []

    def report(_root, *, execute, observe_generation_start=None):
        assert _root == run_root
        calls.append(execute)
        return reporting_operation.ReportingOperationOutcome(
            status="reused" if execute else "planned", verified_report_locations=()
        )

    scheduler = control.slurm_submission
    monkeypatch.setattr(reporting_operation, "run_reporting", report)
    monkeypatch.setattr(
        scheduler,
        "submit",
        lambda plan, **_kwargs: submissions.append(plan) or "812345",
    )
    argv = [run_root.name, "--project", str(project)]
    if profile_selection != "default":
        argv.extend(
            ["--profile", "compute" if profile_selection == "named" else str(profile)]
        )
    assert control.report_from_args(parser.parse_args(argv)) == 0
    assert calls == [False] and submissions == []
    assert not (tmp_path / "logs").exists()
    preview = capsys.readouterr().err
    assert "Execution placement: Slurm" in preview
    assert (
        "Allocation request: 256 CPUs, 12:00:00; memory: site default (unknown)"
        in preview
    )
    assert "Workflow CPU ceiling: 12;" in preview

    assert control.report_from_args(parser.parse_args([*argv, "--execute"])) == 0
    assert calls == [False] and len(submissions) == 1
    submitted = submissions[0]
    (request_path,) = (tmp_path / "logs").glob("submission-*/request.json")
    request = json.loads(request_path.read_bytes())
    assert request["command"] == "report"
    assert request["requested_run"] == run_root.name
    assert request["project"] == str(project)
    assert {
        "--account=viking-users",
        "--partition=long",
        "--qos=normal",
        "--cpus-per-task=256",
        "--time=12:00:00",
        "--exclusive",
    } <= set(submitted.argv)
    assert not any(value.startswith("--mem=") for value in submitted.argv)
    assert (
        f" report {run_root.name} --project {project} --profile {profile} "
        in submitted.batch_script
    )
    assert capsys.readouterr().out.startswith("JOB_ID=812345\n")

    admitted = load_execution_profile(config_path=profile)
    monkeypatch.setenv(scheduler.DELEGATE_MARKER_ENV, scheduler.DELEGATE_MARKER)
    monkeypatch.setenv(scheduler.PROFILE_SHA256_ENV, admitted.binding_sha256)
    monkeypatch.setenv(scheduler.SUBMIT_UID_ENV, str(os.getuid()))
    monkeypatch.setenv("SLURM_JOB_ID", "812345")
    assert (
        control.report_from_args(
            parser.parse_args([*argv, "--profile", str(profile), "--execute"])
        )
        == 0
    )
    assert calls == [False, True] and len(submissions) == 1
    assert capsys.readouterr().out == ""


def test_next_supported_action_uses_separated_status_domains() -> None:
    def action(
        integrity: str = "valid",
        attempt: str = "succeeded",
        results: str = "complete",
        reporting: str = "complete",
        recovery: bool = False,
        receipt: str = "succeeded",
    ) -> str:
        return control._next_supported_action(
            SimpleNamespace(
                integrity=integrity,
                attempt_outcome=attempt,
                results_status=results,
                reporting_status=reporting,
                recovery_available=recovery,
                latest_receipt={
                    "schema_version": "emrys.attempt-receipt.v3",
                    "status": receipt,
                },
                run_root=Path.cwd() / "runs" / ("run-" + "a" * 64),
                run_id="run-" + "a" * 64,
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
    assert action(receipt="failed", reporting="incomplete") == (
        "Preserve this Run; review the latest Attempt receipt. Do not generate reports."
    )
    assert action() == "Review the verified Results and report paths."
    assert action(reporting="incomplete") == (
        "Generate reports with emrys report stimulating-beagle --execute."
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
        step_id
        for _label, steps in control._inspection_presentation._MILESTONE_STEPS
        for step_id in steps
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
    progress = control._inspection_presentation.milestone_progress(
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

    monkeypatch.setattr(control._inspection_presentation, "datetime", FixedDateTime)

    assert (
        control._inspection_presentation.attempt_elapsed_line(
            SimpleNamespace(latest_attempt=None, attempt_outcome="not_started"),
        )
        == "Attempt elapsed: unavailable — no Attempt"
    )
    assert (
        control._inspection_presentation.attempt_elapsed_line(
            SimpleNamespace(
                latest_attempt=latest,
                latest_receipt=None,
                attempt_outcome="running",
            ),
        )
        == "Current Attempt elapsed: 0:01:30"
    )
    assert (
        control._inspection_presentation.attempt_elapsed_line(
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
    assert (
        "invalid timestamp boundary"
        in control._inspection_presentation.attempt_elapsed_line(
            SimpleNamespace(
                latest_attempt=latest,
                latest_receipt=None,
                attempt_outcome="running",
            ),
        )
    )


def test_public_help_routes() -> None:
    for command, expected in (
        (("run", "--help"), "usage: emrys run"),
        (("resume", "--help"), "usage: emrys resume"),
        (("inspect", "--help"), "usage: emrys inspect"),
        (("stop", "--help"), "usage: emrys stop"),
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
            assert "--profile NAME_OR_ABSOLUTE_PATH" in result.stdout
        if command[0] == "resume":
            assert "--through" not in result.stdout
            assert "--profile NAME_OR_ABSOLUTE_PATH" in result.stdout
        if command[0] == "stop":
            assert "--submission REQUEST" in result.stdout
            assert "--execute" in result.stdout and "--profile" not in result.stdout


def _package_copy(tmp_path: Path) -> Path:
    package = tmp_path / "installed-package"
    shutil.copytree(
        source_authority.PACKAGE_ROOT,
        package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return package


def _doubled_lifecycle_ops(
    base: lifecycle.LifecycleOps,
    *,
    fail_after_rule: str | None = None,
) -> lifecycle.LifecycleOps:
    def run_workflow(argv: tuple[str, ...], cwd: Path) -> lifecycle.WorkflowResult:
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
                else completed.stdout
                if completed.returncode
                else None
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
        storage_binding: RuntimeBinding | None,
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


def _public_native_cancellation_child(root: Path) -> None:
    """Keep real Snakemake/Task processes; substitute only scientific effects/readiness."""
    readiness, resources, project, workspace = _readiness(root / "case")
    run_id = _run_candidate(readiness, resources).run_id
    run_root = workspace / "runs" / run_id
    owner = "emrys.stage.construct_canonical_BAM.v1"
    scope = str(readiness.analysis.workflow_inputs["samples"]["rows"][0]["sample_id"])
    gate = (owner, scope, root / "native-ready.fifo")
    processes: list[subprocess.Popen[bytes]] = []
    quiescence_checks: list[str] = []
    real_build = control.build_attempt_plan
    base = _doubled_lifecycle_ops(lifecycle.default_lifecycle_ops())

    def spawn(argv, cwd, environment):
        assert argv[argv.index("-m") + 1] == "snakemake"
        process = base.process_group_ops.spawn(argv, cwd, environment)
        processes.append(process)
        (root / "workflow-processes.json").write_text(
            json.dumps([item.pid for item in processes])
        )
        return process

    def observe_phase(phase: str) -> None:
        if phase in {
            "before_lock_release",
            "before_receipt_publication",
        }:
            native = json.loads((root / "native-ready.json").read_text())
            assert native["parent_pgid"] == processes[0].pid
            for pgid in (*(process.pid for process in processes), native["pgid"]):
                with pytest.raises(ProcessLookupError):
                    os.killpg(pgid, 0)
            quiescence_checks.append(phase)

    ops = replace(
        base,
        run_workflow=None,
        process_group_ops=replace(base.process_group_ops, spawn=spawn),
        observe_phase=observe_phase,
    )
    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(control.doctor, "diagnose_project", lambda *_a, **_k: readiness)
        patched.setattr(
            control.capacity, "observe_allocation", lambda: resources.allocation
        )
        patched.setattr(
            control,
            "build_attempt_plan",
            lambda *a, **k: with_owner_doubles(
                real_build(*a, **k),
                native_gate=gate if k["operation"] == "execute" else None,
            ),
        )
        patched.setattr(control.lifecycle, "default_lifecycle_ops", lambda: ops)
        arguments = argparse.Namespace(
            project=project,
            profile=None,
            allocated_cores=1,
            execute=True,
            log_level="normal",
            log_root=workspace / "logs/application",
        )
        assert control.run_from_args(arguments) == 1
        assert quiescence_checks == [
            "before_lock_release",
            "before_receipt_publication",
        ]
        interrupted = inspection.inspect_run(run_root)
        assert interrupted.integrity == "valid"
        assert interrupted.attempt_outcome == "interrupted"
        assert (
            interrupted.results_status == "incomplete"
            and not interrupted.results_blockers
        )
        assert interrupted.recovery_available
        assert interrupted.latest_receipt["status"] == "interrupted"
        assert interrupted.latest_receipt["termination_signal"] == signal.SIGTERM
        first_id = interrupted.latest_attempt["workflow_attempt_id"]
        first_attempt = run_root / "attempts" / first_id
        assert (first_attempt / "released-run-lock.json").is_file()
        assert (first_attempt / "attempt-receipt.json").is_file()
        assert not (run_root / "locks/run.lock").exists()
        target = next(
            item
            for item in interrupted.tasks
            if (item.expected.machine_key, item.expected.scope_id) == (owner, scope)
        )
        assert target.state == "pending" and target.record is None
        assert target.start_origin == first_id and target.start_reference is not None
        assert not (run_root / "state/verified" / owner / f"{scope}.json").exists()
        (terminal,) = target.terminal_attempts
        assert terminal.record["status"] == "failed"
        assert terminal.record["abort_closure"] == "linux-task-prepublication.v1"
        assert target.retry_task_attempt_record == terminal.record_reference
        assert terminal.record["failure_message"] == "Task interrupted by signal 15"
        planned = interrupted.latest_attempt["tasks"][owner][scope]
        assert all(not Path(item["path"]).exists() for item in planned["outputs"])
        assert all(not Path(path).exists() for path in planned["publication"]["locks"])
        native = json.loads((root / "native-ready.json").read_text())
        assert not Path(native["working_output"]).parent.exists()
        assert not Path(native["work_directory"]).exists()
        assert all(
            record["start"] is None and record["verified"] is None
            for record in interrupted.reporting_completion_records.values()
        )

        verified_before = _verified_snapshot(run_root)
        assert verified_before
        arguments.run = run_id
        preview_namespace = sorted(workspace.rglob("*"))
        preview_before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in workspace.rglob("*")
            if path.is_file()
        }
        arguments.execute = False
        assert control.resume_from_args(arguments) == 0
        assert sorted(workspace.rglob("*")) == preview_namespace
        assert {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in workspace.rglob("*")
            if path.is_file()
        } == preview_before
        arguments.execute = True
        assert control.resume_from_args(arguments) == 0
        completed = inspection.inspect_run(run_root)
        assert (
            completed.integrity,
            completed.attempt_outcome,
            completed.results_status,
        ) == ("valid", "succeeded", "complete")
        assert not completed.recovery_available
        assert len(processes) == 2
        assert quiescence_checks == [
            "before_lock_release",
            "before_receipt_publication",
            "before_lock_release",
            "before_receipt_publication",
        ]
        retained_roots = (
            run_root / "contract",
            first_attempt,
            run_root / "state/verified",
            *(
                run_root / binding["path"]
                for item in interrupted.tasks
                if item.record is not None
                for binding in (
                    *item.record["outputs"],
                    item.record["validation_report"],
                )
            ),
        )
        # Snakemake updates its own incomplete-job metadata during retry. The
        # prior EMRYS records, logs, input projections and verified outputs stay exact.
        assert all(
            (path.read_bytes(), path.stat().st_mtime_ns) == value
            for path, value in preview_before.items()
            if any(
                path == retained or retained in path.parents
                for retained in retained_roots
            )
        )
        verified_after = _verified_snapshot(run_root)
        assert all(
            verified_after[path] == value for path, value in verified_before.items()
        )
        retried = next(
            item
            for item in completed.tasks
            if (item.expected.machine_key, item.expected.scope_id) == (owner, scope)
        )
        assert len(retried.terminal_attempts) == 2
        assert retried.terminal_attempts[0] == terminal
        assert retried.terminal_attempts[1].record["status"] == "succeeded"
        assert (
            retried.terminal_attempts[1].record["task_start_record"]
            != terminal.record["task_start_record"]
        )
        assert (
            completed.latest_attempt["tasks"][owner][scope]["retry_task_attempt_record"]
            == terminal.record_reference
        )
        assert (
            len(completed.latest_receipt["task_start_records"])
            == len(completed.tasks) + 1
        )
        (root / "cancellation-resume-completed.json").write_text(
            json.dumps(
                {
                    "interrupted_attempt": first_id,
                    "completed_attempt": completed.latest_attempt[
                        "workflow_attempt_id"
                    ],
                    "quiescence_checks": quiescence_checks,
                }
            )
        )


@pytest.mark.skipif(
    sys.platform != "linux", reason="Task retry requires Linux descendant closure"
)
def test_public_real_snakemake_native_cancellation_resumes_after_closed_abort(
    tmp_path: Path,
) -> None:
    ready_path = tmp_path / "native-ready.fifo"
    os.mkfifo(ready_path, mode=0o600)
    reader = os.open(ready_path, os.O_RDONLY | os.O_NONBLOCK)
    writer = os.open(ready_path, os.O_WRONLY | os.O_NONBLOCK)
    log_path = tmp_path / "cancellation-journey.log"
    process = None
    completed = False
    try:
        with log_path.open("wb") as stream:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; import sys; "
                    "from tests.orchestration.run_coordinator.test_materialization import "
                    "_public_native_cancellation_child; "
                    "_public_native_cancellation_child(Path(sys.argv[1]))",
                    str(tmp_path),
                ],
                cwd=REPO_ROOT,
                env={**os.environ, "XDG_CACHE_HOME": str(tmp_path / "cache")},
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            with selectors.DefaultSelector() as selector:
                selector.register(reader, selectors.EVENT_READ)
                # Snakemake may schedule other samples before this fixed target.
                deadline = time.monotonic() + 300
                while True:
                    returncode = process.poll()
                    assert returncode is None, (
                        f"Run child exited {returncode} before native readiness.\n"
                        f"{log_path.read_text()}"
                    )
                    remaining = deadline - time.monotonic()
                    assert remaining > 0, (
                        f"Native readiness deadline expired.\n{log_path.read_text()}"
                    )
                    if selector.select(timeout=min(0.1, remaining)):
                        break
                assert os.read(reader, 6) == b"ready\n"
            native = json.loads(ready_path.with_suffix(".json").read_text())
            assert native["pgid"] == native["pid"] != native["parent_pgid"]
            assert native["parent_pgid"] != process.pid
            assert os.getpgid(native["parent_pid"]) == native["parent_pgid"]
            assert not set(native["blocked_signals"]) & task._TASK_SIGNALS
            assert Path(native["working_output"]).is_file()
            (run_root,) = (tmp_path / "case/project/runs").glob("run-*")
            active = inspection.inspect_run(run_root)
            assert active.lock_observation == "local live owner"
            assert active.attempt_outcome == "running" and not active.recovery_available
            assert any(
                item.start_reference and item.record is None for item in active.tasks
            )
            assert os.getpgid(native["pid"]) == native["pgid"]
            os.kill(process.pid, signal.SIGTERM)
            # This now includes a complete resumed pipeline and report production.
            assert process.wait(timeout=300) == 0, log_path.read_text()
        assert (tmp_path / "cancellation-resume-completed.json").is_file()
        completed = True
    finally:
        os.close(writer)
        os.close(reader)
        if process is not None and process.poll() is None:
            os.kill(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        # Only this fixture's explicitly recorded sessions are eligible for cleanup.
        if not completed:
            groups_path = tmp_path / "workflow-processes.json"
            groups = json.loads(groups_path.read_text()) if groups_path.exists() else []
            native_path = ready_path.with_suffix(".json")
            if native_path.exists():
                groups.append(json.loads(native_path.read_text())["pgid"])
            for pgid in groups:
                lifecycle._signal_process_group(pgid, signal.SIGKILL)


def test_public_adapter_executes_failure_and_byte_preserving_resume(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout = source_authority.PACKAGE_ROOT
    readiness, resources, request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
    )
    real_build = control.build_attempt_plan
    real_ops = control.lifecycle.default_lifecycle_ops
    fail_after_rule: list[str | None] = ["construct_canonical_BAM"]
    _bind_readiness(monkeypatch, readiness, resources)
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
        profile=None,
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
        project=request,
        run=run_id,
        profile=None,
        allocated_cores=1,
        execute=False,
    )
    assert control.resume_from_args(resume_arguments) == 0
    dry_output = capsys.readouterr().err
    assert "Work:" in dry_output and " reusable" in dry_output
    assert "Results:" not in dry_output.splitlines()
    assert _verified_snapshot(run_root) == before

    real_publish = reporting_operation._publish_prepared
    reporting_observations = []

    def observe_reporting(kind, phase):
        namespace = sorted(workspace.rglob("*"))
        evidence = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in namespace
            if path.is_file()
        }
        observed = inspection.inspect_run(run_root)
        assert observed.authority is not None
        assert (
            observed.integrity,
            observed.attempt_outcome,
            observed.results_status,
            observed.reporting_status,
            observed.recovery_available,
        ) == ("valid", "succeeded", "complete", "blocked", False)
        assert observed.lock_observation == "no lock"
        assert observed.verified_report_locations == ()
        records = observed.reporting_completion_records
        assert records[kind]["start"] is not None
        assert records[kind]["verified"] is None
        assert not reporting_operation.reporting_boundary.ledger_paths(
            run_root, kind
        ).verified.exists()
        if kind == "run_summary":
            assert records["html_report"] == {"start": None, "verified": None}
        else:
            assert records["run_summary"]["start"] is not None
            assert records["run_summary"]["verified"] is not None
        assert any(
            f"{kind} reporting start has no verified completion" in blocker
            for blocker in observed.reporting_blockers
        )
        # A separate public reader observes the real publisher paused at this boundary.
        public = subprocess.run(
            controlled_python_argv(
                sys.executable,
                "-m",
                "emrys",
                "inspect",
                run_id,
                "--project",
                str(request),
                "--detail",
                "normal" if phase == "before producer" else "verbose",
            ),
            cwd=tmp_path,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert public.returncode == 0, public.stdout + public.stderr
        assert "Run admission: valid" in public.stdout
        assert "Run lock: no lock" in public.stdout
        assert "Attempt outcome: succeeded" in public.stdout
        assert "Scientific Results: complete" in public.stdout
        assert "Reporting admission: blocked" in public.stdout
        assert public.stdout.count("Reporting transactions:") == 1
        assert f"{kind}: Started; completion unverified" in public.stdout
        other_row = (
            "html_report: No admitted start"
            if kind == "run_summary"
            else "run_summary: Verified complete"
        )
        assert other_row in public.stdout
        assert "REPORTING BLOCKER:" in public.stdout
        assert "Run diagnostic logs: 2 association(s); scan complete." in public.stdout
        assert "Recovery available: no" in public.stdout
        assert "Preserve completed Results; do not rerun science." in public.stdout
        assert "Results:" not in public.stdout.splitlines()
        assert "Scientific report:" not in public.stdout
        assert "Evidence report:" not in public.stdout
        assert "reporter is running" not in public.stdout
        assert sorted(workspace.rglob("*")) == namespace
        assert {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in namespace
            if path.is_file()
        } == evidence
        reporting_observations.append((kind, phase))
        return records

    def publish_and_observe(kind, context):
        expected_receipt = (
            context.summary_paths.summary_json
            if kind == "run_summary"
            else context.output_receipt
        )
        assert not expected_receipt.exists()
        started = observe_reporting(kind, "before producer")
        receipt = real_publish(kind, context)
        assert receipt == expected_receipt
        assert receipt.is_file()
        assert observe_reporting(kind, "after producer") == started
        return receipt

    monkeypatch.setattr(reporting_operation, "_publish_prepared", publish_and_observe)
    resume_arguments.execute = True
    assert control.resume_from_args(resume_arguments) == 0
    assert reporting_observations == [
        ("run_summary", "before producer"),
        ("run_summary", "after producer"),
        ("html_report", "before producer"),
        ("html_report", "after producer"),
    ]
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

    application_paths = tuple(sorted((workspace / "logs/application").rglob("*.jsonl")))
    assert {path.name for path in application_paths} == {
        "emrys-run.jsonl",
        "emrys-resume.jsonl",
    }
    assert len(application_paths) == 2

    inspect_arguments = argparse.Namespace(
        project=request,
        run=run_id,
        detail="normal",
    )
    assert control.inspect_from_args(inspect_arguments) == 0
    inspect_output = capsys.readouterr().out
    assert "Run diagnostic logs: 2 association(s); scan complete." in inspect_output
    assert all(str(path) not in inspect_output for path in application_paths)
    assert "Run admission: valid" in inspect_output
    assert "Run lock: no lock" in inspect_output
    assert "Attempt outcome: succeeded" in inspect_output
    assert "Scientific Results: complete" in inspect_output
    assert "Reporting admission: complete" in inspect_output
    assert inspect_output.count("Reporting transactions:") == 1
    assert "run_summary: Verified complete" in inspect_output
    assert "html_report: Verified complete" in inspect_output
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
    assert all(str(path) in verbose_output for path in application_paths)
    assert failed.latest_attempt["workflow_attempt_id"] in verbose_output
    assert completed.latest_attempt["workflow_attempt_id"] in verbose_output
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
    assert verbose_output.count("Reporting transactions:") == 1
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
    checkout = source_authority.PACKAGE_ROOT
    readiness, resources, project, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
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
    admitted_project = admit_project(
        project,
        checkout / "workflow/contracts/local_cmh_v2.json",
    )
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
        profile=None,
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
        profile=None,
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

    predecessor_manifest = next(
        target_root.glob("contract/workflow-inputs/*/samples.tsv")
    ).read_bytes()
    samples_path = project.parent / authored["dataset"]["samples"]
    header, *rows = samples_path.read_text(encoding="utf-8").splitlines()
    samples_path.write_text(
        f"{header}\tnotes\n"
        + "".join(f"{row}\tidentity-neutral resume edit\n" for row in reversed(rows)),
        encoding="utf-8",
    )
    resumed_project = admit_project(
        project,
        checkout / "workflow/contracts/local_cmh_v2.json",
    )
    resumed_analysis = resumed_project.select_analysis("sensitivity")
    assert resumed_analysis.revision == sensitivity.analysis.revision
    assert resumed_analysis.selected_sample_manifest_bytes != predecessor_manifest
    sensitivity = replace(
        sensitivity,
        project=resumed_project,
        analysis=resumed_analysis,
    )

    assert (
        control.resume_from_args(
            argparse.Namespace(
                project=project,
                run=target_root.name,
                profile=None,
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
    assert len(selected_manifests) == 1
    assert {path.read_bytes() for path in selected_manifests} == {predecessor_manifest}
    assert all(
        step08.validate_sample_manifest(path)[1] == selected_ids
        for path in selected_manifests
    )
    orientation_root = source_root / "products" / "native" / "orientation"
    consumed_orientation_samples = {
        Path(str(item["path"])).relative_to(orientation_root).parts[0]
        for manifest_path in target_root.glob("attempts/*/attempt.json")
        for scopes in orchestration_contracts.load_json_object(manifest_path)[
            "tasks"
        ].values()
        for record in scopes.values()
        for item in record.get("inputs", ())
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
        for manifest_path in target_root.glob("attempts/*/attempt.json")
        for scopes in orchestration_contracts.load_json_object(manifest_path)[
            "tasks"
        ].values()
        for record in scopes.values()
        for item in record.get("inputs", ())
        if item["path"] in source_snapshots
    )

    assert (
        control.inspect_from_args(
            argparse.Namespace(
                project=project,
                run=target_root.name,
                detail="verbose",
            )
        )
        == 0
    )
    inspect_output = capsys.readouterr().out
    assert "Preparation: reused" in inspect_output
    assert "Alignment and sample processing: reused" in inspect_output
    assert "QC evidence: reused" in inspect_output
    assert (
        f"Processing source: {inspection.human_run_name(source_run_id)} (admitted)"
        in inspect_output
    )

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
            for manifest_path in drift_root.glob("attempts/*/attempt.json")
            for scopes in orchestration_contracts.load_json_object(manifest_path)[
                "tasks"
            ].values()
            for record in scopes.values()
            for item in record.get("inputs", ())
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
                profile=None,
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
                project=project,
                run=drift_root.name,
                profile=None,
                allocated_cores=1,
                execute=True,
            )
        )
        == 2
    )
    assert "not at an admissible closed-task resume boundary" in capsys.readouterr().err


@pytest.mark.parametrize("changed", ("native", "r_package", "seal"))
def test_borrowed_runtime_survives_run_and_resume_and_rejects_changed_donor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed: str,
) -> None:
    from emrys.evidence.storage_inventory.qualification import QualifiedStorage
    from tests.evidence.runtime_availability.test_runtime_availability import (
        _managed_seal_fixture,
    )

    readiness, resources, request, workspace = _readiness(tmp_path / "borrower")
    seal, donor_inspection = _managed_seal_fixture(tmp_path / "shared", monkeypatch)
    seal.write_bytes(runtime_inspector.runtime_seal_bytes(donor_inspection, seal))
    reference = runtime_inspector.shared_runtime_profile_bytes(
        seal, seal.read_bytes(), Path(sys.executable)
    )
    current_profile = onboarding.runtime_profile_path(request)
    current_profile.write_bytes(reference)
    storage = next(
        item for item in readiness.bindings if item.check_id == "storage_qualification"
    )
    monkeypatch.setattr(
        doctor.storage_qualification,
        "admit_direct_requirement",
        lambda *_args: QualifiedStorage(storage.path, storage.sha256, storage.observed),
    )
    monkeypatch.setattr(
        control.capacity, "observe_allocation", lambda: resources.allocation
    )
    execution = load_execution_profile(
        config_path=workspace / "runtime/profiles/default.yaml"
    )
    first = control._plan_run(request, execution_profile=execution)
    assert first.readiness.inspection.profile_bytes == reference
    assert not first.run_root.exists()
    observed = _failed_run(first)
    assert observed.recovery_available
    retained = next(
        Path(str(item["path"]))
        for item in first.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert retained.read_bytes() == reference
    lifecycle._admit_runtime_context(
        first.attempt_record, first.lifecycle_request, storage, None
    )
    current_profile.unlink()
    second = control._plan_resume(first.run_root, execution_profile=execution)
    assert second.run.run_id == first.run.run_id
    assert second.readiness.inspection.profile_path == retained
    assert second.readiness.inspection.profile_bytes == reference
    next_profile = next(
        Path(str(item["path"]))
        for item in second.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert next_profile != retained
    assert (
        next(item.data for item in second.attempt_files if item.path == next_profile)
        == reference
    )
    if changed == "native":
        (seal.parent / "managed/star").write_bytes(b"changed tool, same version\n")
    elif changed == "r_package":
        (seal.parent / "managed/renv_library/VariantAnnotation/DESCRIPTION").write_text(
            "same version, changed package\n"
        )
    else:
        seal.unlink()
    with pytest.raises(control.ControlError):
        control._plan_resume(first.run_root, execution_profile=execution)
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle._admit_runtime_context(
            first.attempt_record, first.lifecycle_request, storage, None
        )


@pytest.mark.parametrize("selector", ["default", "environment", "cli"])
def test_public_run_diagnostic_log_discovery_uses_exact_root_without_changing_authority(
    tmp_path, monkeypatch, capsys, selector
):
    import io

    plan = _plan(tmp_path)
    observed = _failed_run(plan)
    project, root = plan.run.analysis.source_path, plan.run_root
    log_root = (
        project.parent / "logs/application"
        if selector == "default"
        else tmp_path / "custom diagnostic logs"
    )
    monkeypatch.delenv("EMRYS_LOG_ROOT", raising=False)
    if selector != "default":
        monkeypatch.setenv(
            "EMRYS_LOG_ROOT",
            str(log_root if selector == "environment" else tmp_path / "ignored"),
        )
    application = control.open_attempt_log(
        controls=LogControls(LogLevel.NORMAL, log_root, "default", "command_line"),
        identity=control.AttemptIdentity(
            "run", root.name, "application-" + "e" * 32, "emrys-report"
        ),
        mode="report",
        component="orchestration",
        stderr=io.StringIO(),
    )
    application.logger(component="reporting", phase="reporting").info(
        "Synthetic diagnostic association; no report production.",
        extra=control.event(
            "reporting_started", fields={"run_root": control.field(root)}
        ),
    )
    application.close()
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns) if path.is_file() else None
        for path in tmp_path.rglob("*")
    }
    calls = []
    original = control._submission_inspection.inspect_run_applications

    def discover(selected_project, selected_run, selected_root):
        calls.append((selected_project, selected_run, selected_root))
        return original(selected_project, selected_run, selected_root)

    monkeypatch.setattr(
        control._submission_inspection, "inspect_run_applications", discover
    )
    monkeypatch.setattr(
        control, "open_attempt_log", lambda **_: pytest.fail("Inspection opened a log")
    )
    monkeypatch.setattr(
        control.slurm_submission,
        "observe_submission_request",
        lambda *_: pytest.fail("Run selection queried the scheduler"),
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    assert (
        control.inspect_from_args(parser.parse_args(["--project", str(project)])) == 0
    )
    assert calls == []
    assert "Run diagnostic logs:" not in capsys.readouterr().out
    argv = [root.name, "--project", str(project)]
    if selector == "cli":
        argv.extend(["--log-root", str(log_root)])
    for detail in ("normal", "verbose"):
        assert (
            control.inspect_from_args(parser.parse_args([*argv, "--detail", detail]))
            == 0
        )
        text = capsys.readouterr().out
        assert "Run diagnostic logs: 1 association(s); scan complete." in text
        assert f"Application log search root: {log_root}" in text
        assert (str(application.path) in text) is (detail == "verbose")
        assert (
            "Scientific Results: incomplete" in text
            and "Recovery available: yes" in text
        )
    monkeypatch.setattr(control.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(control.sys.stdout, "isatty", lambda: False)
    assert control.inspect_from_args(parser.parse_args([*argv, "--watch"])) == 0
    text = capsys.readouterr().out
    assert "Run diagnostic logs: 1 association(s); scan complete." in text
    assert (
        str(application.path) in text
        and "Current diagnostic bytes; content not verified" in text
    )
    assert calls == [(project, root, log_root)] * 3

    def failed(*_args):
        raise RuntimeError("diagnostic reader unavailable\x1b[31m")

    monkeypatch.setattr(control._submission_inspection, "_CandidateAdmission", failed)
    assert control.inspect_from_args(parser.parse_args(argv)) == 0
    failed_text = capsys.readouterr().out
    assert "Run diagnostic logs: 0 association(s); scan unknown." in failed_text
    assert (
        "Scientific Results: incomplete" in failed_text
        and "Recovery available: yes" in failed_text
    )
    assert "\x1b" not in failed_text and str(application.path) not in failed_text
    assert calls == [(project, root, log_root)] * 4
    assert inspection.inspect_run(root) == observed
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns) if path.is_file() else None
        for path in tmp_path.rglob("*")
    } == before


@pytest.mark.parametrize("selection", [[], ["--submission", "submission-" + "a" * 32]])
def test_inspect_log_root_requires_explicit_run_before_reads(
    tmp_path, monkeypatch, capsys, selection
):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid log selector performed I/O")

    monkeypatch.setattr(control.onboarding, "project_definition_path", forbidden)
    monkeypatch.setattr(control, "_resolve_run_argument", forbidden)
    monkeypatch.setattr(
        control.slurm_submission, "select_submission_request", forbidden
    )
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    arguments = parser.parse_args(["--log-root", str(tmp_path / "absent"), *selection])
    assert control.inspect_from_args(arguments) == 2
    assert "--log-root requires a Run selector" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "case",
    (
        "closed",
        "changed-input",
        "second-closed",
        "stale-reference",
        "unclosed",
        "active",
        "verified",
        "retained",
        "preentry",
        "late-start-in-old-receipt",
    ),
)
def test_retry_history_keeps_old_closure_separate_from_current_readiness(
    tmp_path, monkeypatch, case
):
    from emrys.orchestration.run_coordinator import _inspection_evidence as evidence
    from emrys.orchestration.run_coordinator import _inspection_attempts as histories
    from emrys.orchestration.run_coordinator import task
    from emrys.orchestration.run_coordinator._inspection_admission import ExpectedTask

    expected = ExpectedTask("fixture.owner", "00a", "reference", "reference")
    marker = tmp_path / "state/verified/fixture.owner/reference.json"
    marker_reference = {"path": str(marker.relative_to(tmp_path)), "sha256": "e" * 64}

    def reference(origin, filename):
        return {
            "path": f"attempts/{origin}/tasks/fixture.owner/reference/{filename}",
            "sha256": origin * 64,
        }

    def entry(origin, *, outcome="abort"):
        start_ref = (
            None if outcome == "preentry" else reference(origin, "task-start.json")
        )
        start = (
            None
            if start_ref is None
            else {
                "workflow_attempt_id": origin,
                "workflow_attempt_record": {
                    "path": f"attempts/{origin}/attempt.json",
                    "sha256": origin * 64,
                },
            }
        )
        record = {
            "workflow_attempt_id": origin,
            "task_start_record": start_ref,
            "status": "succeeded" if outcome == "verified" else "failed",
            "abort_closure": "linux-task-prepublication.v1"
            if outcome == "abort"
            else None,
        }
        terminal = (
            None
            if outcome == "unclosed"
            else histories.TaskAttemptObservation(
                record, reference(origin, "task-attempt.json")
            )
        )
        return histories.TaskHistoryEntry(expected, origin, start, start_ref, terminal)

    def attempt(origin, retry=None, retained=None):
        definition = (
            {"retry_task_attempt_record": retry}
            if retained is None
            else {"workflow_attempt_record": retained}
        )
        return {
            "workflow_attempt_id": origin,
            "tasks": {expected.machine_key: {expected.scope_id: definition}},
        }

    first = entry(
        "a",
        outcome="preentry"
        if case == "preentry"
        else "unclosed"
        if case in {"unclosed", "active"}
        else "abort",
    )
    entries = [first]
    attempts = [attempt("a")]
    verified = None
    if case in {
        "second-closed",
        "stale-reference",
        "verified",
        "retained",
        "late-start-in-old-receipt",
    }:
        second = entry(
            "b",
            outcome="abort"
            if case in {"second-closed", "stale-reference"}
            else "verified",
        )
        entries.append(second)
        attempts.append(attempt("b", first.terminal.record_reference))
        if case == "stale-reference":
            attempts.append(attempt("c", first.terminal.record_reference))
        elif case != "second-closed":
            verified = second.terminal.record
            marker.parent.mkdir(parents=True)
            marker.touch()
            if case == "retained":
                attempts.append(
                    attempt(
                        "c", retained=second.start_record["workflow_attempt_record"]
                    )
                )
    elif case == "preentry":
        attempts.append(attempt("b"))

    fresh = []

    def recheck(**kwargs):
        fresh.append(kwargs["record_reference"])
        if case == "changed-input":
            raise task.TaskBoundaryError("original input changed")
        if verified is not None:
            pytest.fail(
                "Historical abort cannot require absent finals after successful retry"
            )

    monkeypatch.setattr(evidence, "expected_tasks", lambda *_: (expected,))
    monkeypatch.setattr(evidence, "verified_tree_blockers", lambda *_: ())
    monkeypatch.setattr(
        evidence,
        "inspect_attempt_task_trees",
        lambda *_args, **_kwargs: (tuple(entries), ()),
    )
    monkeypatch.setattr(evidence, "_record_reference", lambda *_: marker_reference)
    monkeypatch.setattr(
        task, "validate_verified_task", lambda *_args, **_kwargs: verified
    )
    monkeypatch.setattr(task, "recheck_aborted_task", recheck)
    observed = evidence.inspect_task_evidence(
        tmp_path,
        {},
        {},
        attempts,
        receipts={},
        authority=object(),
        allow_incomplete_origin="a" if case == "active" else None,
    )
    inspected = observed.tasks[0]
    assert len(inspected.terminal_attempts) == sum(
        entry.terminal is not None for entry in entries
    )
    assert len(observed.task_start_records) == sum(
        entry.start_reference is not None for entry in entries
    )
    if case in {"changed-input", "stale-reference", "unclosed"}:
        assert inspected.state == "blocked" and observed.results_blockers
        assert inspected.retry_task_attempt_record is None
    elif verified is not None:
        assert inspected.state == "verified" and not observed.results_blockers
        assert fresh == []
        projections = (
            (
                "task_start_records",
                tuple(
                    (item["workflow_attempt_id"], item)
                    for item in observed.task_start_records
                ),
                "starts",
            ),
            (
                "task_attempt_records",
                tuple(
                    (item["workflow_attempt_id"], item)
                    for item in observed.task_attempt_records
                ),
                "results",
            ),
            ("verified_tasks", (("b", observed.verified_tasks[0]),), "verified"),
        )
        old = {
            "status": "failed",
            "task_start_records": list(observed.task_start_records[:1]),
            "task_attempt_records": list(observed.task_attempt_records[:1]),
            "verified_tasks": [],
        }
        if case == "late-start-in-old-receipt":
            old["task_start_records"] = list(observed.task_start_records)
        integrity, results = evidence._receipt_evidence_blockers(
            attempts, {"a": old}, projections, observed.tasks
        )
        assert not integrity
        assert bool(results) == (case == "late-start-in-old-receipt")
    else:
        assert inspected.state == "pending" and not observed.results_blockers
        if case in {"closed", "second-closed"}:
            assert (
                inspected.retry_task_attempt_record
                == entries[-1].terminal.record_reference
            )
            assert fresh == [inspected.retry_task_attempt_record]
        else:
            assert inspected.retry_task_attempt_record is None and fresh == []


@pytest.mark.parametrize(
    "case",
    (
        "entered",
        "preentry",
        "active",
        "unterminated",
        "foreign",
        "symlink",
        "selected-scope",
        "changed-start",
        "malformed-terminal",
    ),
)
def test_task_history_scanner_closes_exact_current_scope_files(
    tmp_path, monkeypatch, case
):
    from emrys.contracts.orchestration import api as contracts
    from emrys.orchestration.run_coordinator import _inspection_attempts as histories
    from emrys.orchestration.run_coordinator import task
    from emrys.orchestration.run_coordinator._inspection_admission import ExpectedTask

    expected = ExpectedTask("fixture.owner", "00a", "reference", "reference")
    other = ExpectedTask("fixture.owner", "00a", "reference", "other")
    root = tmp_path / "attempts/a/tasks/fixture.owner/reference"
    root.mkdir(parents=True)
    start = {"workflow_attempt_id": "a"}
    start_reference = {
        "path": str((root / "task-start.json").relative_to(tmp_path)),
        "sha256": contracts.canonical_sha256(start),
    }
    if case != "preentry":
        (root / "task-start.json").write_text("start")
    terminal = {"task_start_record": None if case == "preentry" else start_reference}
    if case not in {"active", "unterminated"}:
        for name in ("task-attempt.json", "stdout.log", "stderr.log"):
            (root / name).write_text(name)
    if case == "foreign":
        (root / "unknown.json").touch()
    if case == "symlink":
        (root / "stdout.log").unlink()
        (root / "stdout.log").symlink_to(root / "stderr.log")
    if case == "selected-scope":
        other_root = root.parent / "other"
        other_root.mkdir()
        (other_root / "task-start.json").touch()
    attempts = [
        {
            "workflow_attempt_id": "a",
            "tasks": {
                "fixture.owner": {
                    "reference": {"retry_task_attempt_record": None},
                    "other": {"retry_task_attempt_record": None},
                }
            },
        }
    ]
    monkeypatch.setattr(histories, "expected_tasks", lambda *_: (expected, other))
    monkeypatch.setattr(task, "validate_task_start", lambda *_args, **_kwargs: start)
    monkeypatch.setattr(
        histories,
        "_record_reference",
        lambda *_: (
            {**start_reference, "sha256": "f" * 64}
            if case == "changed-start"
            else start_reference
        ),
    )
    monkeypatch.setattr(
        task,
        "_admit_task_attempt",
        lambda **_kwargs: (
            (_ for _ in ()).throw(task.TaskBoundaryError("malformed terminal"))
            if case == "malformed-terminal"
            else (terminal, {"path": "result", "sha256": "a" * 64})
        ),
    )
    entries, blockers = histories.inspect_attempt_task_trees(
        tmp_path,
        {},
        {},
        attempts,
        authority=object(),
        allow_incomplete_origin="a" if case == "active" else None,
        selected_task=(expected.machine_key, expected.scope_id)
        if case == "selected-scope"
        else None,
    )
    assert bool(blockers) == (
        case
        in {"unterminated", "foreign", "symlink", "changed-start", "malformed-terminal"}
    )
    if case in {"unterminated", "foreign", "symlink", "malformed-terminal"}:
        assert len(entries) == 1
        assert entries[0].start_reference == start_reference
        assert entries[0].terminal is None
    if not blockers:
        assert len(entries) == 1
        assert entries[0].expected == expected
        assert (entries[0].terminal is None) == (case == "active")
        assert (entries[0].start_record is None) == (case == "preentry")


@pytest.mark.parametrize("tamper", (None, "omit", "repoint"))
def test_selected_task_admission_rechecks_receipt_projection(
    tmp_path, monkeypatch, tamper
):
    from emrys.orchestration.run_coordinator import _inspection_evidence as evidence
    from emrys.orchestration.run_coordinator import _inspection_attempts as histories
    from emrys.orchestration.run_coordinator import task
    from emrys.orchestration.run_coordinator._inspection_admission import ExpectedTask

    expected = ExpectedTask("fixture.owner", "00a", "reference", "reference")
    scope = expected.scope
    start = {
        "path": "attempts/a/tasks/fixture.owner/reference/task-start.json",
        "sha256": "a" * 64,
    }
    terminal = {
        "path": "attempts/a/tasks/fixture.owner/reference/task-attempt.json",
        "sha256": "b" * 64,
    }
    result = {
        "workflow_attempt_id": "a",
        "task_start_record": start,
        "abort_closure": "linux-task-prepublication.v1",
        "status": "failed",
    }
    entry = histories.TaskHistoryEntry(
        expected,
        "a",
        {"workflow_attempt_id": "a"},
        start,
        histories.TaskAttemptObservation(result, terminal),
    )

    def projection(reference):
        return {
            "workflow_attempt_id": "a",
            "machine_key": expected.machine_key,
            "scope": scope,
            "record": reference,
        }

    receipt = {
        "status": "failed",
        "task_start_records": [projection(start)],
        "task_attempt_records": [projection(terminal)],
        "verified_tasks": [],
    }
    if tamper == "omit":
        receipt["task_attempt_records"] = []
    elif tamper == "repoint":
        receipt["task_attempt_records"][0]["record"] = {**terminal, "sha256": "f" * 64}
    # Other scopes are validated by the full caller, without rehashing their
    # output trees at each parallel Task entry.
    for field in ("task_start_records", "task_attempt_records", "verified_tasks"):
        other = copy.deepcopy(projection(terminal))
        other["machine_key"] = "other.owner"
        receipt[field].append(other)
    monkeypatch.setattr(evidence, "expected_tasks", lambda *_: (expected,))
    monkeypatch.setattr(
        evidence, "inspect_attempt_task_trees", lambda *_a, **_k: ((entry,), ())
    )
    monkeypatch.setattr(task, "recheck_aborted_task", lambda **_k: None)
    observed = evidence.inspect_task_evidence(
        tmp_path,
        {},
        {},
        [
            {
                "workflow_attempt_id": "a",
                "tasks": {
                    expected.machine_key: {
                        expected.scope_id: {"retry_task_attempt_record": None}
                    }
                },
            }
        ],
        receipts={"a": receipt},
        authority=object(),
        selected_task=(expected.machine_key, expected.scope_id),
    )
    assert not observed.integrity_blockers
    assert bool(observed.results_blockers) == (tamper is not None)
    if tamper is not None:
        assert "cumulative Task attempts" in observed.results_blockers[0]
