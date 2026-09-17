from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from emrys.orchestration.run_coordinator import execution_profile, slurm_submission
from emrys.orchestration.run_coordinator.execution_profile import (
    DirectPlacement,
    ExecutionProfileError,
    SlurmPlacement,
    load_execution_profile,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    AllocationCapacity,
    ResourceConfigError,
    ResourceOverrides,
    resolve_resource_policy,
)
from tests.tools.real_synthetic_e2e import symbolic_resource_document

REPO_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_SCHEMA_VERSION = "emrys.local-pilot-resources.v1"


def _write_profile(path: Path, document: dict[str, object]) -> Path:
    path.write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _slurm_placement(root: Path) -> dict[str, object]:
    return {
        "kind": "slurm",
        "account": "site-account",
        "partition": "compute",
        "qos": None,
        "cpus_per_task": 8,
        "memory_mb": 65536,
        "time": "04:00:00",
        "exclusive": False,
        "nodelist": None,
        "scratch_parent": str(root / "scratch"),
        "modules": {"mode": "none", "init": "", "load": []},
    }


def test_project_profile_selection_is_default_named_or_absolute(tmp_path: Path) -> None:
    project = tmp_path / "project.yaml"
    default = tmp_path / "runtime/profiles/default.yaml"
    named = tmp_path / "runtime/profiles/viking.yaml"
    absolute = tmp_path / "external.yaml"
    assert execution_profile.project_execution_profile_path(project, None) == default
    assert execution_profile.project_execution_profile_path(project, "viking") == named
    assert (
        execution_profile.project_execution_profile_path(project, absolute) == absolute
    )
    for invalid in ("nested/viking", "viking.yaml"):
        with pytest.raises(ExecutionProfileError, match="safe Project profile"):
            execution_profile.project_execution_profile_path(project, invalid)

    default.parent.mkdir(parents=True)
    default.write_bytes(execution_profile.PROJECT_DEFAULT_PROFILE_BYTES)
    profile = load_execution_profile(config_path=default)
    assert isinstance(profile.placement, DirectPlacement)
    assert profile.resource_policy.declaration.workflow_cores == "allocation"
    assert profile.source_path == default
    assert not profile.computational_resources_explicit
    assert profile.document()["placement"] == {"kind": "direct"}

    default.write_bytes(execution_profile.project_default_profile_bytes("viking"))
    viking = load_execution_profile(config_path=default)
    assert viking.document()["placement"] == {
        "kind": "slurm",
        "account": "viking-users",
        "partition": "long",
        "qos": "normal",
        "cpus_per_task": "node",
        "memory_mb": 0,
        "time": "12:00:00",
        "exclusive": True,
        "nodelist": None,
        "scratch_parent": "/tmp",
        "modules": {"mode": "none", "init": "", "load": []},
    }
    assert viking.resource_policy == profile.resource_policy
    assert not viking.computational_resources_explicit
    retained = load_execution_profile(
        REPO_ROOT / "configs/execution_profile.csu_viking_ev_pum1.yaml"
    )
    retained_policy = retained.resource_policy.document()
    assert viking.resource_policy.document() == retained_policy
    for memory_mb in (262144, 524287, 524288, 1048576):
        resolved = resolve_resource_policy(
            viking.resource_policy, AllocationCapacity(256, memory_mb, "fixture")
        )
        assert resolved.workflow_cores == resolved.threads_for("00a") == 256
        assert resolved.workflow_memory_mb == memory_mb
        assert dict(resolved.stage_memory_mb)["00a"] == memory_mb
    for capacity, message in (
        ((11, 524288), "Stage 01 concurrency x threads exceeds workflow cores"),
        ((256, 245759), "Stage 01 concurrency x memory exceeds workflow memory"),
    ):
        with pytest.raises(ResourceConfigError, match=message):
            resolve_resource_policy(
                viking.resource_policy, AllocationCapacity(*capacity, "undersized")
            )
    submission = slurm_submission.plan_submission(
        viking, emrys_argv=("emrys", "run"), log_dir=tmp_path / "logs"
    )
    assert {
        "--nodes=1",
        "--ntasks=1",
        "--mem=0",
        "--exclusive",
        "--time=12:00:00",
    }.issubset(submission.argv)
    assert not any(value.startswith("--cpus-per-task=") for value in submission.argv)
    summary = "\n".join(viking.submission_summary())
    assert (
        "Workflow CPU ceiling: allocation capacity (unknown until execution); memory ceiling: "
        "allocation capacity (unknown until execution)" in summary
    )
    assert "Stage thread caps: 00a=workflow, 01=2, 02=1, 06=1, 08=4" in summary
    assert "Repeated-stage concurrency caps: 01=6" in summary
    assert "all node CPUs" in summary
    assert "all node memory (unknown until execution)" in summary


def test_default_project_profile_rejects_retired_adjacent_configuration(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project.yaml"
    retired = ("emrys.resources.yaml", "norad.launcher.yaml")
    for name in retired:
        (tmp_path / name).write_text("retired: true\n", encoding="utf-8")

    with pytest.raises(ExecutionProfileError, match="requires migration") as caught:
        execution_profile.project_execution_profile_path(project, None)
    assert all(name in str(caught.value) for name in retired)
    assert execution_profile.project_execution_profile_path(project, "default") == (
        tmp_path / "runtime/profiles/default.yaml"
    )


def test_whole_node_cpu_request_requires_exclusive_placement(tmp_path: Path) -> None:
    selected = tmp_path / "profile.yaml"
    selected.write_bytes(
        execution_profile.project_default_profile_bytes("viking").replace(
            b"exclusive: true", b"exclusive: false"
        )
    )
    with pytest.raises(
        ExecutionProfileError, match="Whole-node CPUs require exclusive"
    ):
        load_execution_profile(config_path=selected).validate_reservation()


def test_selected_resource_fragment_then_explicit_overrides(tmp_path: Path) -> None:
    default_sha256 = load_execution_profile().resource_policy.default_sha256
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": {
                **symbolic_resource_document(),
                "workflow_cores": 6,
                "step_threads": {"00a": 6},
            },
        },
    )

    profile = load_execution_profile(
        config_path=selected,
        resource_overrides=ResourceOverrides(
            workflow_cores=8,
            step_threads=(("00a", 8),),
        ),
    )

    assert isinstance(profile.placement, DirectPlacement)
    assert profile.resource_policy.declaration.workflow_cores == 8
    assert dict(profile.resource_policy.declaration.step_threads)["00a"] == 8
    assert profile.resource_policy.override_labels == (
        "workflow_cores",
        "step_threads.00a",
    )
    assert profile.resource_policy.config_path == selected
    assert profile.resource_policy.default_sha256 == default_sha256
    assert (
        profile.resource_policy.config_sha256
        == hashlib.sha256(selected.read_bytes()).hexdigest()
    )


def test_placement_only_profile_does_not_change_resource_policy(
    tmp_path: Path,
) -> None:
    direct = load_execution_profile()
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )

    scheduled = load_execution_profile(config_path=selected)

    assert isinstance(scheduled.placement, SlurmPlacement)
    assert scheduled.placement.cpus_per_task == 8
    assert scheduled.resource_policy.document() == direct.resource_policy.document()
    assert (
        scheduled.resource_policy.declaration.identity_document()
        == direct.resource_policy.declaration.identity_document()
    )
    assert scheduled.resource_policy.config_path is None
    assert "placement" not in scheduled.resource_policy.document()
    assert scheduled.sha256 != direct.sha256


@pytest.mark.parametrize("exclusive", (False, True))
@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        (
            ResourceOverrides(workflow_cores=9),
            "Workflow cores exceed Slurm reservation: 9 > 8",
        ),
        (
            ResourceOverrides(workflow_memory_mb=8192),
            "Workflow memory exceeds Slurm reservation: 8192 > 4096 MiB",
        ),
        (
            ResourceOverrides(stage_memory_mb=(("00a", 8192),)),
            "workflow memory within Slurm reservation: 1 x 8192 > 4096 MiB",
        ),
    ),
)
def test_reservation_fit_rejects_only_declared_conflicts_without_mutation(
    tmp_path: Path,
    exclusive: bool,
    overrides: ResourceOverrides,
    message: str,
) -> None:
    placement = {
        **_slurm_placement(tmp_path),
        "exclusive": exclusive,
        "memory_mb": 4096,
    }
    source = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": symbolic_resource_document(),
            "placement": placement,
        },
    )
    profile = load_execution_profile(source, resource_overrides=overrides)
    before = profile.document(), profile.binding_sha256, source.read_bytes()

    with pytest.raises(ExecutionProfileError, match=message):
        profile.validate_reservation()
    with pytest.raises(ExecutionProfileError, match=message):
        slurm_submission.plan_submission(
            profile, emrys_argv=("emrys", "run"), log_dir=tmp_path / "logs"
        )

    assert (profile.document(), profile.binding_sha256, source.read_bytes()) == before
    assert not (tmp_path / "logs").exists()


@pytest.mark.parametrize("exclusive", (False, True))
@pytest.mark.parametrize("memory_mb", (None, 8192))
def test_reservation_fit_preserves_symbols_and_actual_allocation_admission(
    tmp_path: Path, exclusive: bool, memory_mb: int | None
) -> None:
    source = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": symbolic_resource_document(),
            "placement": {
                **_slurm_placement(tmp_path),
                "exclusive": exclusive,
                "memory_mb": memory_mb,
            },
        },
    )
    profile = load_execution_profile(
        source, resource_overrides=ResourceOverrides(stage_memory_mb=(("00a", 8192),))
    )
    before = profile.document(), profile.binding_sha256
    profile.validate_reservation()
    assert profile.resource_policy.declaration.workflow_memory_mb == "allocation"
    assert dict(profile.resource_policy.declaration.stage_memory_mb)["01"] == "workflow"
    with pytest.raises(
        ResourceConfigError, match="workflow memory: 1 x 8192 > 4096 MiB"
    ):
        resolve_resource_policy(
            profile.resource_policy, AllocationCapacity(8, 4096, "actual fixture")
        )
    resolved = resolve_resource_policy(
        profile.resource_policy, AllocationCapacity(8, 16384, "actual fixture")
    )
    assert resolved.workflow_memory_mb == 16384
    assert (profile.document(), profile.binding_sha256) == before


@pytest.mark.parametrize(
    ("resources", "overrides"),
    (
        ({"workflow_cores": 2}, ResourceOverrides(workflow_cores=4)),
        ({"step_threads": {"00a": 5}}, ResourceOverrides(step_threads=(("00a", 4),))),
    ),
)
def test_profile_relationships_are_checked_after_explicit_correcting_overrides(
    tmp_path: Path, resources: dict[str, object], overrides: ResourceOverrides
) -> None:
    source = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": {**symbolic_resource_document(), **resources},
        },
    )
    before = source.read_bytes()
    with pytest.raises(ExecutionProfileError, match="concurrency x threads"):
        load_execution_profile(source)

    profile = load_execution_profile(source, resource_overrides=overrides)

    assert profile.resource_policy.declaration.workflow_cores == 4
    assert dict(profile.resource_policy.declaration.step_threads)["00a"] == 4
    assert profile.resource_policy.override_labels == overrides.labels()
    assert profile.source_raw_sha256 == hashlib.sha256(before).hexdigest()
    assert source.read_bytes() == before


@pytest.mark.parametrize("scheduled", (False, True))
@pytest.mark.parametrize("explicit", (False, True))
def test_submission_summary_keeps_requests_limits_and_unknown_capacity_distinct(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scheduled: bool,
    explicit: bool,
) -> None:
    from emrys.orchestration.run_coordinator import slurm_submission

    placement = _slurm_placement(tmp_path)
    placement.update(
        account="site-account" if explicit else None,
        partition="compute" if explicit else None,
        qos="normal" if explicit else None,
        memory_mb=65536 if explicit else None,
        exclusive=explicit,
        nodelist="node[01-02]" if explicit else None,
    )
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": symbolic_resource_document(),
            "placement": placement if scheduled else {"kind": "direct"},
        },
    )
    profile = load_execution_profile(
        config_path=selected,
        resource_overrides=ResourceOverrides(
            workflow_cores=6,
            workflow_memory_mb=8192 if explicit else None,
            step_threads=(("00a", 2),),
            stage_concurrency=(("01", 1),),
            stage_memory_mb=(("00a", 1024),) if explicit else (),
        ),
    )
    before = profile.document(), profile.binding_sha256
    monkeypatch.setattr(
        execution_profile,
        "read_bytes",
        lambda *_args: pytest.fail("summary reread the selected profile"),
    )
    summary = "\n".join(profile.submission_summary())
    assert (profile.document(), profile.binding_sha256) == before
    assert f"Execution placement: {'Slurm' if scheduled else 'Direct'}" in summary
    assert (
        "Workflow CPU ceiling: 6; memory ceiling: "
        + ("8192 MiB" if explicit else "allocation capacity (unknown until execution)")
        in summary
    )
    assert "Stage thread caps: 00a=2, 01=4" in summary
    assert "Repeated-stage concurrency caps: 01=1" in summary
    assert (
        "Stage memory: workflow ceiling; explicit MiB caps: "
        + ("00a=1024" if explicit else "none")
        in summary
    )
    assert "Actual allocation capacity is unknown until execution" in summary
    assert "do not guarantee utilization" in summary
    if not scheduled:
        assert "Allocation request:" not in summary
        assert "Node request:" not in summary
        return
    submission = slurm_submission.plan_submission(
        profile,
        emrys_argv=("emrys", "run"),
        log_dir=tmp_path / "logs",
        environment={},
        submitter_uid=1000,
    )
    assert "--nodes=1" in submission.argv
    assert "--cpus-per-task=8" in submission.argv
    assert "--time=04:00:00" in submission.argv
    assert (
        "Allocation request: 8 CPUs, 04:00:00; memory: "
        + ("65536 MiB" if explicit else "site default (unknown)")
        in summary
    )
    assert (
        "Node request: 1; requested host(s): "
        + ("node[01-02]" if explicit else "scheduler-selected; exact host unknown")
        in summary
    )
    assert (
        "Exclusive allocation: "
        + ("requested" if explicit else "not requested; site policy applies")
        in summary
    )
    assert (
        "Account: "
        + (
            "site-account; partition: compute; QoS: normal"
            if explicit
            else "site default; partition: site default; QoS: site default"
        )
        in summary
    )
    for argument in (
        "--exclusive",
        "--nodelist=node[01-02]",
        "--mem=65536M",
        "--account=site-account",
        "--partition=compute",
        "--qos=normal",
    ):
        assert (argument in submission.argv) is explicit
    assert not (tmp_path / "logs").exists()


def test_attempt_placement_projects_direct_and_slurm_provenance(
    tmp_path: Path,
) -> None:
    direct = load_execution_profile()

    assert direct.source_path.is_absolute()
    assert (
        direct.source_raw_sha256
        == hashlib.sha256(direct.source_path.read_bytes()).hexdigest()
    )
    assert direct.attempt_placement() == {
        "kind": "direct",
        "source": {
            "path": str(direct.source_path),
            "sha256": direct.source_raw_sha256,
        },
        "effective_sha256": direct.sha256,
        "request": {"kind": "direct"},
        "scheduler_job_id": None,
    }

    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )
    scheduled = load_execution_profile(config_path=selected)

    assert scheduled.source_path == selected
    assert (
        scheduled.source_raw_sha256 == hashlib.sha256(selected.read_bytes()).hexdigest()
    )
    assert scheduled.attempt_placement("700123") == {
        "kind": "slurm",
        "source": {
            "path": str(selected),
            "sha256": scheduled.source_raw_sha256,
        },
        "effective_sha256": scheduled.sha256,
        "request": scheduled.placement.document(),
        "scheduler_job_id": "700123",
    }


@pytest.mark.parametrize("job_id", ("", "0", "00", "01", "-1", "1.0", " 1", 1, True))
def test_attempt_placement_rejects_noncanonical_job_ids(
    tmp_path: Path,
    job_id: object,
) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )
    profile = load_execution_profile(config_path=selected)

    with pytest.raises(ExecutionProfileError, match="canonical positive decimal"):
        profile.attempt_placement(job_id)  # type: ignore[arg-type]


def test_selected_source_binding_is_admitted(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": {"kind": "direct"},
        },
    )
    admitted = load_execution_profile(config_path=selected)

    profile = load_execution_profile(
        config_path=selected,
        expected_binding_sha256=admitted.binding_sha256,
    )

    assert profile.binding_sha256 == admitted.binding_sha256
    assert profile.source_path == selected
    assert (
        profile.source_raw_sha256 == hashlib.sha256(selected.read_bytes()).hexdigest()
    )
    with pytest.raises(ExecutionProfileError, match="SHA-256 differs"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256="0" * 64,
        )
    with pytest.raises(ExecutionProfileError, match="64 lowercase hex"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256="invalid",
        )

    selected.write_bytes(selected.read_bytes() + b"# equivalent rewrite\n")
    rewritten = load_execution_profile(config_path=selected)
    assert rewritten.sha256 == admitted.sha256
    with pytest.raises(ExecutionProfileError, match="binding SHA-256 differs"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256=admitted.binding_sha256,
        )


def test_builtin_source_digest_can_be_bound(tmp_path: Path) -> None:
    expected = load_execution_profile().binding_sha256

    profile = load_execution_profile(expected_binding_sha256=expected)

    assert profile.binding_sha256 == expected


@pytest.mark.parametrize("selected", (False, True))
def test_byte_admission_matches_file_admission_without_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selected: bool
) -> None:
    source = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )
    defaults = execution_profile.DEFAULT_PROFILE_PATH.read_bytes()
    data = source.read_bytes()
    expected = load_execution_profile(source if selected else None)
    monkeypatch.setattr(
        execution_profile,
        "read_bytes",
        lambda *_args: pytest.fail("byte admission read a file"),
    )
    observed = execution_profile.admit_execution_profile_bytes(
        defaults, source if selected else None, data if selected else None
    )
    assert observed == expected
    assert not observed.computational_resources_explicit
    assert (
        observed.source_raw_sha256
        == hashlib.sha256(data if selected else defaults).hexdigest()
    )
    with pytest.raises(ExecutionProfileError, match="supplied together"):
        execution_profile.admit_execution_profile_bytes(defaults, source)


def test_selected_profile_must_be_one_stable_real_file(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {"schema_version": execution_profile.SCHEMA_VERSION},
    )
    link = tmp_path / "profile-link.yaml"
    link.symlink_to(selected)

    with pytest.raises(ExecutionProfileError, match="canonical and nonsymlink"):
        load_execution_profile(config_path=link)


@pytest.mark.parametrize(
    ("text", "message"),
    (
        (
            "schema_version: emrys.execution-profile.v1\n"
            "schema_version: emrys.execution-profile.v1\n",
            "Duplicate YAML mapping key",
        ),
        (
            "schema_version: emrys.execution-profile.v1\nbase: &base\n  kind: direct\nplacement:\n  <<: *base\n",
            "YAML merge keys are not allowed",
        ),
        (
            "schema_version: emrys.execution-profile.v1\nunknown: true\n",
            "execution profile",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "resources:\n"
            "  schema_version: emrys.local-pilot-resources.v1\n"
            "  reporting_memory_mb: {html_report: 1024}\n",
            "reporting_memory_mb",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "resources:\n"
            "  schema_version: emrys.local-pilot-resources.v1\n"
            "  workflow_cores: true\n",
            "execution profile",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "resources:\n"
            "  schema_version: emrys.local-pilot-resources.v1\n"
            "  workflow_cores: {env: EMRYS_SLURM_CPUS}\n",
            "execution profile",
        ),
    ),
)
def test_profile_yaml_is_closed_without_environment_references(
    tmp_path: Path,
    text: str,
    message: str,
) -> None:
    selected = tmp_path / "profile.yaml"
    selected.write_text(text, encoding="utf-8")

    with pytest.raises(ExecutionProfileError, match=message):
        load_execution_profile(config_path=selected)


@pytest.mark.parametrize(
    ("relative_path", "workflow_cores", "cpus_per_task", "exclusive"),
    (
        ("configs/execution_profile.example.yaml", "allocation", "node", True),
        (
            "configs/execution_profile.csu_viking_ev_pum1.yaml",
            "allocation",
            "node",
            True,
        ),
    ),
)
def test_tracked_execution_profile_examples_are_admissible(
    relative_path: str,
    workflow_cores: str,
    cpus_per_task: str,
    exclusive: bool,
) -> None:
    profile = load_execution_profile(config_path=REPO_ROOT / relative_path)

    assert isinstance(profile.placement, SlurmPlacement)
    assert profile.resource_policy.declaration.workflow_cores == workflow_cores
    assert profile.placement.cpus_per_task == cpus_per_task
    assert profile.placement.exclusive is exclusive
    assert profile.placement.memory_mb == 0


def test_exact_module_realization_is_typed(tmp_path: Path) -> None:
    placement = _slurm_placement(tmp_path)
    placement["modules"] = {
        "mode": "exact",
        "init": "/etc/profile.d/modules.sh",
        "load": ["STAR/2.7.11b", "samtools/1.19.2"],
    }
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": placement,
        },
    )

    profile = load_execution_profile(config_path=selected)

    assert isinstance(profile.placement, SlurmPlacement)
    assert profile.placement.module_init == Path("/etc/profile.d/modules.sh")
    assert profile.placement.modules == ("STAR/2.7.11b", "samtools/1.19.2")
