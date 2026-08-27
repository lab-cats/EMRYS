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
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
)
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.local_pilot import (
    control,
    doctor,
    inspection,
    lifecycle,
    materialization,
)
from emrys.orchestration.local_pilot.materialization import (
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    publish_attempt,
)
from emrys.orchestration.local_pilot.normalization import normalize_request
from emrys.orchestration.local_pilot.resource_policy import (
    AllocationCapacity,
    load_resource_plan,
    resolve_resource_policy,
)
from emrys.orchestration.local_pilot.run_implementation import (
    implementation_identity,
)
from tests.orchestration.local_pilot.fixture import build
from tests.orchestration.local_pilot.fixtures.b5_doubles import with_owner_doubles

REPO_ROOT = Path(__file__).resolve().parents[3]


def _readiness(
    tmp_path: Path,
    *,
    source_root: Path = REPO_ROOT,
    source_commit: str = "a" * 40,
    workflow_cores: int = 1,
    stage_concurrency: dict[str, int] | None = None,
    step_threads: dict[str, int] | None = None,
) -> tuple[doctor.DoctorResult, object, object, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    intake = tmp_path / "intake"
    intake.mkdir()
    request = build(intake)
    resource_path = request.parent / "emrys.resources.yaml"
    resource_document = yaml.safe_load(resource_path.read_text(encoding="utf-8"))
    resource_document["workflow_cores"] = workflow_cores
    resource_document["workflow_memory_mb"] = max(1024, workflow_cores * 1024)
    resource_document["stage_concurrency"] = {
        step_id: (
            1 if stage_concurrency is None else stage_concurrency.get(step_id, 1)
        )
        for step_id in ("01", "02", "02b", "03", "04", "05", "06", "07")
    }
    resource_document["step_threads"] = (
        {"00a": 1, "01": 1, "02": 1, "06": 1, "08": 1}
        if step_threads is None
        else step_threads
    )
    resource_path.write_text(
        yaml.safe_dump(resource_document, sort_keys=False), encoding="utf-8"
    )
    normalized = normalize_request(
        request, source_root / "workflow/contracts/local_cmh_v2.json"
    )
    resources = load_resource_plan(
        request,
        AllocationCapacity(
            cores=workflow_cores,
            memory_mb=max(1024, workflow_cores * 1024),
            source="test allocation",
        ),
    )
    runtime = tmp_path / "runtime.tsv"
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
    for _check_id, package in doctor.LOCAL_PILOT_R_PACKAGES:
        package_root = renv_library / package
        package_root.mkdir()
        (package_root / "DESCRIPTION").write_text(
            f"Package: {package}\nVersion: 1.0.0\n", encoding="utf-8"
        )
    observations: list[RuntimeObservation] = []
    rscript = str(tool)
    for check_id, check_type in doctor.LOCAL_PILOT_RUNTIME_CHECKS:
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
            target = next(
                package
                for key, package in doctor.LOCAL_PILOT_R_PACKAGES
                if key == check_id
            )
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
                    doctor.SNAKEMAKE_VERSION
                    if check_id == "snakemake"
                    else f"observed-{check_id}"
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
    workspace = tmp_path / "workspace"
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
        request_path=request,
        workspace=workspace,
        source_root=source_root,
        source_commit=source_commit,
        runtime_profile=runtime,
        runtime_profile_sha256=runtime_inspection.profile_sha256,
        inspection=runtime_inspection,
        bindings=bindings,
        blockers=(),
        remediations=(),
    )
    return readiness, normalized, resources, request, workspace


def _run_candidate(readiness, normalized, resources):
    return build_run_candidate(normalized, readiness, resources.declaration)


def _plan(
    tmp_path: Path,
    *,
    step_threads: dict[str, int] | None = None,
    workflow_cores: int = 1,
    stage_concurrency: dict[str, int] | None = None,
):
    readiness, normalized, resources, _request, workspace = _readiness(
        tmp_path,
        workflow_cores=workflow_cores,
        stage_concurrency=stage_concurrency,
        step_threads=step_threads,
    )
    return build_attempt_plan(
        _run_candidate(readiness, normalized, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
        now=datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
        token="1" * 32,
        host="test-host",
        process_id=123,
    )


def _dispatch_records(plan) -> list[dict[str, object]]:
    return [json.loads(item.data) for item in plan.new_dispatch_files]


def test_owner_doubles_preserve_immutable_run_toolchain(tmp_path: Path) -> None:
    plan = _plan(tmp_path)

    doubled = with_owner_doubles(plan)

    assert doubled.attempt_record["execution_mode"] == "test-double"
    assert (
        doubled.attempt_record["required_tools"]
        == plan.attempt_record["required_tools"]
    )


def test_owner_doubles_use_successor_scopes_inside_reporting_payloads(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    doubled = with_owner_doubles(plan)
    payloads: list[bytes] = []
    for item in doubled.attempt_files:
        if not item.path.name.endswith(".payload.json"):
            continue
        manifest = json.loads(item.data)
        payloads.extend(
            base64.b64decode(output["data_base64"])
            for output in manifest["producer"]
        )
    combined = b"\n".join(payloads)
    analysis = plan.run.normalized.analysis_revision

    assert analysis.scope_id("cohort").encode() in combined
    assert analysis.scope_id("analysis").encode() in combined


def test_plan_is_no_write_and_projects_exact_public_owner_roster(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)

    assert not plan.workspace.exists()
    assert plan.preparation.operation == "execute"
    assert json.loads(plan.preparation.attempt_record_bytes) == plan.attempt_record
    assert plan.dispatch_count == 35
    records = _dispatch_records(plan)
    assert len(records) == 35
    assert len({record["machine_key"] for record in records}) == 14
    assert all("--execute" in record["producer_argv"] for record in records)
    assert all("--execute" in record["validator_argv"] for record in records)
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
    step10 = next(
        record
        for record in records
        if record["machine_key"]
        == "emrys.analysis.project_candidate_scientific_context.v1"
    )
    assert "scientific_context_projection.sh" in " ".join(step10["producer_argv"])
    assert "--motif-catalog" in step10["producer_argv"]
    assert "scientific-context-projection" in step10["validator_argv"]
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


def test_run_identity_excludes_reporting_and_allocation_but_binds_resources_and_tools(
    tmp_path: Path,
) -> None:
    readiness, normalized, resources, _request, _workspace = _readiness(tmp_path)
    baseline = _run_candidate(readiness, normalized, resources)

    reallocated = resolve_resource_policy(
        resources.policy,
        AllocationCapacity(cores=2, memory_mb=2048, source="different allocation"),
    )
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
    assert _run_candidate(readiness, normalized, reallocated).run_id == baseline.run_id
    assert (
        _run_candidate(readiness, normalized, reporting_changed).run_id
        == baseline.run_id
    )

    computational_change = replace(resources.declaration, workflow_cores=2)
    assert (
        build_run_candidate(normalized, readiness, computational_change).run_id
        != baseline.run_id
    )
    tool_changed = replace(
        readiness,
        bindings=tuple(
            replace(binding, sha256="c" * 64)
            if binding.check_id == "star"
            else binding
            for binding in readiness.bindings
        ),
    )
    assert (
        build_run_candidate(normalized, tool_changed, resources.declaration).run_id
        != baseline.run_id
    )


def test_run_identity_excludes_attempt_reporting_and_backend_adapter_code(
    tmp_path: Path,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, normalized, resources, _request, _workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    baseline = _run_candidate(readiness, normalized, resources)

    report_renderer = checkout / "src/emrys/reporting/report.py"
    report_renderer.write_bytes(report_renderer.read_bytes() + b"\n# reporting-only change\n")
    assert _run_candidate(readiness, normalized, resources).run_id == baseline.run_id

    resource_policy = checkout / "src/emrys/orchestration/local_pilot/resource_policy.py"
    resource_policy.write_bytes(resource_policy.read_bytes() + b"\n# policy change\n")
    assert _run_candidate(readiness, normalized, resources).run_id == baseline.run_id

    snakefile = checkout / "workflow/Snakefile"
    snakefile.write_bytes(snakefile.read_bytes() + b"\n# adapter change\n")
    assert _run_candidate(readiness, normalized, resources).run_id == baseline.run_id

    cli_adapter = checkout / "src/emrys/__main__.py"
    cli_adapter.write_bytes(cli_adapter.read_bytes() + b"\n# CLI adapter change\n")
    assert _run_candidate(readiness, normalized, resources).run_id == baseline.run_id

    materializer = checkout / "src/emrys/orchestration/local_pilot/materialization.py"
    materializer.write_bytes(materializer.read_bytes() + b"\n# dispatch change\n")
    assert _run_candidate(readiness, normalized, resources).run_id != baseline.run_id


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
        "src/emrys/libraries/orientation.sh",
        "src/emrys/libraries/signal_traps.sh",
        "src/emrys/analyses/paired_cmh_candidate_ranking/"
        "step_09_cmh_awk_validation_functions.awk",
        "src/emrys/analyses/scientific_context_projection/resources/"
        "pum_motifs_v1.tsv",
    )

    for relative in dependencies:
        path = checkout / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n# identity sensitivity\n")
        assert implementation_identity(checkout) != baseline, relative
        path.write_bytes(original)

    assert implementation_identity(checkout) == baseline


def test_lifecycle_refuses_dispatch_implementation_drift_before_attempt(
    tmp_path: Path,
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, normalized, resources, _request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    plan = build_attempt_plan(
        _run_candidate(readiness, normalized, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
        now=datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
        token="1" * 32,
        host="test-host",
        process_id=123,
    )
    base = lifecycle.default_lifecycle_ops()
    ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: pytest.fail("workflow must not start"),
        host_name=lambda: "test-host",
        process_id=lambda: 123,
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )
    admit_run(plan, ops=ops)
    materializer = checkout / "src/emrys/orchestration/local_pilot/materialization.py"
    materializer.write_bytes(materializer.read_bytes() + b"\n# dispatch drift\n")

    with pytest.raises(lifecycle.LifecycleError, match="implementation content"):
        lifecycle.run_materialized_attempt(
            plan.preparation,
            lambda: publish_attempt(plan, ops=ops),
            ops=ops,
        )

    assert not (plan.run_root / "attempts" / plan.workflow_attempt_id).exists()


@pytest.mark.parametrize("storage_binding_count", (0, 2))
def test_plan_requires_exactly_one_storage_qualification_binding(
    tmp_path: Path,
    storage_binding_count: int,
) -> None:
    readiness, normalized, resources, _request, workspace = _readiness(tmp_path)
    storage_binding = next(
        binding
        for binding in readiness.bindings
        if binding.check_id == "storage_qualification"
    )
    non_storage = tuple(
        binding
        for binding in readiness.bindings
        if binding.check_id != "storage_qualification"
    )
    malformed = replace(
        readiness,
        bindings=non_storage + (storage_binding,) * storage_binding_count,
    )

    with pytest.raises(
        MaterializationError,
        match="Run-bindable",
    ):
        build_attempt_plan(
            _run_candidate(malformed, normalized, resources),
            malformed,
            workspace,
            resources=resources,
            operation="execute",
            now=datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
            token="1" * 32,
            host="test-host",
            process_id=123,
        )


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
            assert producer[producer.index("--threads") + 1] == str(
                allocation[step_id]
            )
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
    config = json.loads(
        next(item.data for item in plan.attempt_files if item.path == plan.config_path)
    )

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
        probe,
        (),
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
    assert observed.state == "prepared"
    assert observed.authority_format == "successor"
    assert observed.run_id == plan.run.run_id
    assert observed.latest_attempt is None
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
    def unexpected_materialization() -> lifecycle.LifecycleRequest:
        raise AssertionError("materialization must remain unreachable")

    with pytest.raises(lifecycle.LifecycleError, match="successor Run"):
        lifecycle.run_materialized_attempt(
            plan.preparation,
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
    quarantines = tuple(
        plan.run_root.parent.glob(f"{plan.run.run_id}.uncommitted-*")
    )
    assert len(quarantines) == 1
    assert (quarantines[0] / "contract" / "analysis.json").is_file()
    assert not (quarantines[0] / "contract" / "run.json").exists()


def test_post_binding_interruption_completes_the_exact_pristine_run(
    tmp_path: Path,
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
    before = tuple((path.read_bytes(), path.stat().st_mtime_ns) for path in authority_paths)

    admit_run(plan, ops=base)

    after = tuple((path.read_bytes(), path.stat().st_mtime_ns) for path in authority_paths)
    assert after == before
    assert inspection.inspect_run(plan.run_root).state == "prepared"
    assert all((plan.run_root / name).is_dir() for name in ("attempts", "locks", "state"))
    control_ops = control.ControlOps(
        inspect_readiness=lambda _request, _workspace, _runtime: plan.readiness,
        normalize=lambda _request, _profile: plan.run.normalized,
        inspect_run=inspection.inspect_run,
        execute_plan=lambda _plan: pytest.fail("planning must not execute"),
        transform_plan=lambda value: value,
        now=lambda: datetime(2026, 8, 12, 20, 1, tzinfo=UTC),
        token=lambda: "2" * 32,
        observe_allocation=lambda: plan.resources.allocation,
    )
    replanned = control.plan_run(
        plan.run.normalized.request_path,
        plan.workspace,
        plan.readiness.runtime_profile,
        ops=control_ops,
    )
    assert replanned.run.run_binding.canonical_bytes == plan.run.run_binding.canonical_bytes


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
        admit_run(plan, ops=replace(base, publish_bytes=obstruct_post_binding_namespace))

    authority = inspection.admit_successor_run(plan.run_root)
    assert authority is not None
    assert authority.run_id == plan.run.run_id
    assert tuple(
        plan.run_root.parent.glob(f"{plan.run.run_id}.uncommitted-*")
    ) == ()
    assert inspection.inspect_run(plan.run_root).state == "blocked"


def test_locked_publication_terminalizes_failure_and_refuses_repeat(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    base = lifecycle.default_lifecycle_ops()
    ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: datetime(2026, 8, 12, 20, 5, tzinfo=UTC),
        host_name=lambda: "test-host",
        process_id=lambda: 123,
        process_is_alive=lambda _pid: False,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )

    admit_run(plan, ops=ops)
    outcome = lifecycle.run_materialized_attempt(
        plan.preparation,
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


def test_successor_resume_allows_relocated_checkout_and_new_runtime_profile(
    tmp_path: Path,
) -> None:
    first_source = tmp_path / "first-source"
    second_source = tmp_path / "second-source"
    first_source.mkdir()
    second_source.mkdir()
    checkout_one, commit_one = _clean_checkout(first_source)
    checkout_two, commit_two = _clean_checkout(second_source)
    readiness_one, normalized, resources, _request, workspace = _readiness(
        tmp_path / "first-case",
        source_root=checkout_one,
        source_commit=commit_one,
    )
    readiness_two, _unused, _unused_resources, _request_two, _workspace_two = (
        _readiness(
            tmp_path / "second-case",
            source_root=checkout_two,
            source_commit=commit_two,
        )
    )
    runtime_bytes = b"different admitted runtime profile\n"
    readiness_two.runtime_profile.write_bytes(runtime_bytes)
    runtime_sha256 = hashlib.sha256(runtime_bytes).hexdigest()
    readiness_two = replace(
        readiness_two,
        request_path=readiness_one.request_path,
        workspace=workspace,
        runtime_profile_sha256=runtime_sha256,
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
            (kind, "workflow")
            for kind, _memory in resources.policy.reporting_memory_mb
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

    run_one = _run_candidate(readiness_one, normalized, first_resources)
    run_two = _run_candidate(readiness_two, normalized, first_resources)
    assert run_two.run_id == run_one.run_id

    first = build_attempt_plan(
        run_one,
        readiness_one,
        workspace,
        resources=first_resources,
        operation="execute",
        now=datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
        token="1" * 32,
        host="test-host",
        process_id=123,
    )
    base = lifecycle.default_lifecycle_ops()
    first_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: datetime(2026, 8, 12, 20, 5, tzinfo=UTC),
        host_name=lambda: "test-host",
        process_id=lambda: 123,
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )
    admit_run(first, ops=first_ops)
    first_outcome = lifecycle.run_materialized_attempt(
        first.preparation,
        lambda: publish_attempt(first, ops=first_ops),
        ops=first_ops,
    )
    assert first_outcome.receipt["status"] == "failed"

    resume_ops = control.ControlOps(
        inspect_readiness=lambda _request, _workspace, _runtime: readiness_two,
        normalize=lambda _request, _profile: normalized,
        inspect_run=inspection.inspect_run,
        execute_plan=lambda _plan: pytest.fail("planning must not execute"),
        transform_plan=lambda value: value,
        now=lambda: datetime(2026, 8, 12, 20, 10, tzinfo=UTC),
        token=lambda: "2" * 32,
        observe_allocation=lambda: AllocationCapacity(
            cores=1,
            memory_mb=16_384,
            source="second test allocation",
        ),
    )
    second = control.plan_resume(
        first.run_root,
        readiness_two.runtime_profile,
        ops=resume_ops,
    )
    second_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: datetime(2026, 8, 12, 20, 15, tzinfo=UTC),
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )
    second_outcome = lifecycle.run_materialized_attempt(
        second.preparation,
        lambda: publish_attempt(second, ops=second_ops),
        ops=second_ops,
    )

    assert second_outcome.receipt["status"] == "failed"
    assert second.resources.workflow_memory_mb == 16_384
    assert set(dict(second.resources.reporting_memory_mb).values()) == {16_384}
    first_runtime = next(
        item for item in first.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    second_runtime = next(
        item for item in second.attempt_record["required_tools"]
        if item["name"] == "runtime_profile"
    )
    assert first.attempt_record["source_checkout"] != second.attempt_record[
        "source_checkout"
    ]
    assert first_runtime["path"] != second_runtime["path"]
    assert first_runtime["sha256"] != second_runtime["sha256"]
    observed = inspection.inspect_run(second.run_root)
    assert observed.state == "resume_available", observed.blockers
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
        now=lambda: datetime(2026, 8, 12, 20, 5, tzinfo=UTC),
        host_name=lambda: "test-host",
        process_id=lambda: 123,
        process_is_alive=lambda _pid: False,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )

    admit_run(plan, ops=ops)
    outcome = lifecycle.run_materialized_attempt(
        plan.preparation,
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
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )
    admit_run(plan, ops=ops)

    with pytest.raises(lifecycle.LifecycleError, match="materialize"):
        lifecycle.run_materialized_attempt(
            plan.preparation,
            lambda: publish_attempt(plan, ops=ops),
            ops=ops,
        )

    assert not (plan.run_root / "locks/run.lock").exists()
    assert (
        plan.run_root / "locks" / f"released-{plan.workflow_attempt_id}-run-lock.json"
    ).is_file()
    assert not (plan.run_root / "attempts" / plan.workflow_attempt_id).exists()
    assert list((plan.run_root / "contract/dispatch").rglob("*.json"))
    assert inspection.inspect_run(plan.run_root).state == "blocked"


def test_waiting_stale_resume_exits_before_attempt_materialization(
    tmp_path: Path,
) -> None:
    readiness, normalized, resources, _request, workspace = _readiness(tmp_path)
    initial = build_attempt_plan(
        _run_candidate(readiness, normalized, resources),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
        now=datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
        token="1" * 32,
        host="test-host",
        process_id=123,
    )
    base = lifecycle.default_lifecycle_ops()
    common_ops = replace(
        base,
        run_workflow=lambda _argv, _cwd: lifecycle.WorkflowResult(9, None),
        now=lambda: datetime(2026, 8, 12, 20, 30, tzinfo=UTC),
        host_name=lambda: "test-host",
        process_id=lambda: 123,
        process_is_alive=lambda _pid: True,
        admit_storage_context=lambda _attempt, _execution: None,
        admit_runtime_context=lambda _attempt, _request, _storage: None,
    )
    initial_ops = replace(
        common_ops,
        now=lambda: datetime(2026, 8, 12, 20, 5, tzinfo=UTC),
    )
    admit_run(initial, ops=initial_ops)
    first = lifecycle.run_materialized_attempt(
        initial.preparation,
        lambda: publish_attempt(initial, ops=initial_ops),
        ops=initial_ops,
    )
    assert first.receipt["status"] == "failed"
    assert inspection.inspect_run(initial.run_root).resume_available

    def resume_plan(token: str, minute: int):
        return build_attempt_plan(
            initial.run,
            readiness,
            workspace,
            resources=resources,
            operation="resume",
            now=datetime(2026, 8, 12, 20, minute, tzinfo=UTC),
            token=token * 32,
            host="test-host",
            process_id=123,
            supersedes_workflow_attempt_id=initial.workflow_attempt_id,
            retained_dispatches={},
        )

    winner = resume_plan("2", 10)
    stale = resume_plan("3", 11)
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
                winner.preparation,
                lambda: publish_attempt(winner, ops=winner_ops),
                ops=winner_ops,
            )
            winner_result.put(("ok", outcome.receipt["status"]))
        except BaseException as exc:  # pragma: no cover - asserted below
            winner_result.put(("error", repr(exc)))

    def materialize_stale() -> lifecycle.LifecycleRequest:
        nonlocal stale_materialized
        stale_materialized = True
        return publish_attempt(stale, ops=stale_ops)

    winner_process = context.Process(target=run_winner)
    winner_process.start()
    if not winner_entered.wait(timeout=10):
        release_winner.set()
        winner_process.join(timeout=10)
        pytest.fail("serialized winner did not enter workflow")
    try:
        with pytest.raises(lifecycle.LifecycleError) as stale_error:
            lifecycle.run_materialized_attempt(
                stale.preparation,
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
    assert observed.state == "resume_available", observed.blockers
    assert observed.latest_workflow_attempt_id == winner.workflow_attempt_id


def test_public_run_dry_run_is_no_write(tmp_path: Path, capsys) -> None:
    readiness, normalized, resources, request, workspace = _readiness(tmp_path)
    runtime = readiness.runtime_profile
    executed: list[object] = []
    ops = control.ControlOps(
        inspect_readiness=lambda _request, _workspace, _runtime: readiness,
        normalize=lambda _request, _profile: normalized,
        inspect_run=lambda _root: (_ for _ in ()).throw(AssertionError()),
        execute_plan=lambda plan: executed.append(plan),
        transform_plan=lambda plan: plan,
        now=lambda: datetime(2026, 8, 12, 20, 0, tzinfo=UTC),
        token=lambda: "2" * 32,
        observe_allocation=lambda: resources.allocation,
    )
    arguments = argparse.Namespace(
        request=request,
        workspace=workspace,
        runtime_profile=runtime,
        allocated_cores=1,
        execute=False,
    )

    status = control.run_from_args(arguments, ops=ops)

    captured = capsys.readouterr()
    assert status == 0
    assert "Owner jobs: 35" in captured.out
    assert "Reporting transactions: 3" in captured.out
    assert "Reporting memory per transaction:" in captured.out
    assert "  artifact_index: 1024 MiB" in captured.out
    assert "  run_summary: 1024 MiB" in captured.out
    assert "  html_report: 1024 MiB" in captured.out
    assert "Dry-run complete" in captured.out
    assert executed == []
    assert not workspace.exists()


def test_completed_states_require_exact_verified_result_locations() -> None:
    for locations in (
        (),
        (
            ("scientific-report-html", Path("/results/scientific.html")),
            ("wrong-output-id", Path("/results/evidence.html")),
        ),
    ):
        with pytest.raises(control.ControlError, match="verified result locations"):
            control._verified_report_location_lines(locations)


def test_public_help_routes() -> None:
    for command, expected in (
        (("run", "--help"), "usage: emrys run"),
        (("resume", "--help"), "usage: emrys resume"),
        (
            ("inspect", "local-pilot-run", "--help"),
            "usage: emrys inspect local-pilot-run",
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


def _real_doubled_executor(plan, *, stop_after_target: str | None = None):
    default_ops = lifecycle.default_lifecycle_ops()

    def run_workflow(argv: tuple[str, ...], cwd: Path) -> lifecycle.WorkflowResult:
        invoked = (*argv[:-1], stop_after_target) if stop_after_target else argv
        completed = subprocess.run(
            invoked,
            cwd=cwd,
            env={**os.environ, "XDG_CACHE_HOME": str(cwd / "cache")},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        exit_code = (
            23
            if stop_after_target and completed.returncode == 0
            else completed.returncode
        )
        return lifecycle.WorkflowResult(
            exit_code=exit_code,
            termination_signal=None,
            message=(
                "controlled failure between owner tasks"
                if exit_code == 23
                else completed.stdout
                if completed.returncode
                else None
            ),
        )

    ops = replace(default_ops, run_workflow=run_workflow)
    if plan.operation == "execute":
        admit_run(plan, ops=ops)
    return lifecycle.run_materialized_attempt(
        plan.preparation,
        lambda: publish_attempt(plan, ops=ops),
        ops=ops,
    )


def _verified_snapshot(root: Path) -> dict[Path, tuple[bytes, int]]:
    verified = root / "state/verified"
    return {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in verified.rglob("*.json")
    }


def test_public_adapter_executes_failure_and_byte_preserving_resume(
    tmp_path: Path, capsys
) -> None:
    checkout, commit = _clean_checkout(tmp_path)
    readiness, normalized, resources, request, workspace = _readiness(
        tmp_path / "case",
        source_root=checkout,
        source_commit=commit,
    )
    first_ops = control.ControlOps(
        inspect_readiness=lambda _request, _workspace, _runtime: readiness,
        normalize=lambda _request, _profile: normalized,
        inspect_run=lambda root: inspection.inspect_run(root),
        execute_plan=lambda plan: _real_doubled_executor(
            plan, stop_after_target="one_sample_slice"
        ),
        transform_plan=with_owner_doubles,
        now=lambda: datetime.now(UTC),
        token=lambda: "3" * 32,
        observe_allocation=lambda: resources.allocation,
    )
    run_arguments = argparse.Namespace(
        request=request,
        workspace=workspace,
        runtime_profile=readiness.runtime_profile,
        allocated_cores=1,
        execute=True,
    )
    run_id = _run_candidate(readiness, normalized, resources).run_id

    assert control.run_from_args(run_arguments, ops=first_ops) == 1
    failed_output = capsys.readouterr().out
    assert "Results:" not in failed_output
    run_root = workspace / "runs" / run_id
    failed = inspection.inspect_run(run_root)
    assert failed.state == "resume_available"
    assert failed.verified_report_locations == ()
    before = _verified_snapshot(run_root)
    assert 0 < len(before) < 35

    resumed_ops = control.ControlOps(
        inspect_readiness=lambda _request, _workspace, _runtime: readiness,
        normalize=lambda _request, _profile: normalized,
        inspect_run=lambda root: inspection.inspect_run(root),
        execute_plan=_real_doubled_executor,
        transform_plan=with_owner_doubles,
        now=lambda: datetime.now(UTC),
        token=lambda: "4" * 32,
        observe_allocation=lambda: resources.allocation,
    )
    resume_arguments = argparse.Namespace(
        run_root=run_root,
        runtime_profile=readiness.runtime_profile,
        allocated_cores=1,
        execute=False,
    )
    assert control.resume_from_args(resume_arguments, ops=resumed_ops) == 0
    dry_output = capsys.readouterr().out
    assert "Reusable completed owner jobs:" in dry_output
    assert "Results:" not in dry_output
    assert _verified_snapshot(run_root) == before

    resume_arguments.execute = True
    assert control.resume_from_args(resume_arguments, ops=resumed_ops) == 0
    resumed_output = capsys.readouterr().out
    report_root = run_root / "products" / "report" / run_id
    expected_results = (
        "Results:\n"
        f"  Scientific report: {report_root}/{run_id}.scientific_report.html\n"
        f"  Evidence report: {report_root}/{run_id}.evidence_report.html\n"
    )
    assert expected_results in resumed_output
    completed = inspection.inspect_run(run_root)
    assert completed.state == "local_pipeline_complete"
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

    inspect_arguments = argparse.Namespace(run_root=run_root)
    assert control.inspect_from_args(inspect_arguments, ops=resumed_ops) == 0
    inspect_output = capsys.readouterr().out
    assert "State: local_pipeline_complete" in inspect_output
    assert expected_results in inspect_output

    resume_arguments.execute = False
    assert control.resume_from_args(resume_arguments, ops=resumed_ops) == 2
    assert "Completed local-pilot run refuses resume" in capsys.readouterr().err
