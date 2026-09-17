"""Computational-resource admission, resolution, and persistence contracts."""

from __future__ import annotations

import argparse
import copy
from collections.abc import Callable
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    resolve_computational_resources,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    REPEATABLE_STAGE_IDS,
    STAGE_IDS,
    AllocationCapacity,
    ResourceConfigError,
    ResourceOverrides,
    add_resource_override_arguments,
    admit_resource_policy,
    admit_resource_policy_record,
    overrides_from_args,
    resolve_resource_policy,
    resource_override_argv,
    resume_resource_policy,
)

from tests.tools.real_synthetic_e2e import (
    symbolic_resource_document as _document,
)

DEFAULT_SHA256 = "d" * 64


@pytest.mark.parametrize(
    "cores,memory_mb,samples,expected",
    [
        (256, 524288, 6, (6, 42, 87381)),
        (96, 131072, 20, (3, 32, 43690)),
        (8, 65536, 1, (1, 8, 65536)),
    ],
)
def test_automatic_stage_shares_follow_workload_and_memory_minimum(
    cores, memory_mb, samples, expected
):
    document = _document()
    document["workflow_cores"] = "allocation"
    document["stage_concurrency"]["01"] = "auto"
    document["step_threads"]["01"] = "auto"
    document["stage_memory_mb"]["01"] = {"minimum_mb": 40960}
    policy = _policy(document)
    resolved = resolve_resource_policy(
        policy,
        _allocation(cores=cores, memory_mb=memory_mb),
        workload={"samples": samples, "partitions": 1},
    )
    assert (
        dict(resolved.stage_concurrency)["01"],
        resolved.threads_for("01"),
        dict(resolved.stage_memory_mb)["01"],
    ) == expected
    assert admit_resource_policy_record(resolved.policy_record()) == resolved
    assert policy.document() == document
    assert expected[0] * expected[1] <= cores
    assert expected[0] * expected[2] <= memory_mb


def test_automatic_partition_parallelism_has_no_twelve_task_cap():
    document = _document()
    document["workflow_cores"] = "allocation"
    document["stage_concurrency"]["07"] = "auto"
    document["stage_memory_mb"]["07"] = {"minimum_mb": 8192}
    resolved = resolve_resource_policy(
        _policy(document),
        _allocation(cores=96, memory_mb=524288),
        workload={"samples": 6, "partitions": 100},
    )
    assert dict(resolved.stage_concurrency)["07"] == 64
    assert dict(resolved.stage_memory_mb)["07"] == 8192


def test_automatic_policy_reallocates_without_changing_run_declaration():
    document = _document()
    document["workflow_cores"] = "allocation"
    document["stage_concurrency"]["01"] = "auto"
    document["step_threads"]["01"] = "auto"
    document["stage_memory_mb"]["01"] = {"minimum_mb": 40960}
    policy = _policy(document)
    workload = {"samples": 20, "partitions": 10}
    first = resolve_resource_policy(
        policy, _allocation(cores=96, memory_mb=131072), workload=workload
    )
    retained = admit_resource_policy_record(first.policy_record())
    resumed = resolve_resource_policy(
        resume_resource_policy(retained.policy),
        _allocation(cores=256, memory_mb=524288),
        workload=workload,
    )
    assert first.policy.document() == resumed.policy.document() == document
    assert dict(first.stage_concurrency)["01"] == 3
    assert dict(resumed.stage_concurrency)["01"] == 12


@pytest.mark.parametrize(
    "workload",
    [[], 2, {}, {"samples": True, "partitions": 1}, {"samples": 1, "partitions": 0}],
)
def test_resource_workload_rejects_malformed_counts(workload):
    with pytest.raises(ResourceConfigError, match="workload"):
        resolve_resource_policy(_policy(), _allocation(), workload=workload)


def test_auto_threads_cannot_resolve_to_zero():
    document = _document()
    document["stage_concurrency"]["01"] = 5
    document["step_threads"]["01"] = "auto"
    document["stage_memory_mb"]["01"] = "auto"
    with pytest.raises(ResourceConfigError, match="concurrency exceeds workflow cores"):
        _policy(document)


def test_auto_concurrency_still_rejects_one_task_exceeding_known_cpu_budget():
    document = _document()
    document["stage_concurrency"]["01"] = "auto"
    document["step_threads"]["01"] = 5
    with pytest.raises(ResourceConfigError, match="cannot fit one task"):
        _policy(document)


def test_auto_cli_controls_round_trip():
    parser = argparse.ArgumentParser()
    add_resource_override_arguments(parser)
    overrides = ResourceOverrides(
        stage_concurrency=(("01", "auto"),),
        step_threads=(("02b", "auto"),),
        stage_memory_mb=(("01", "auto"),),
    )
    assert (
        overrides_from_args(parser.parse_args(resource_override_argv(overrides)))
        == overrides
    )


def test_automatic_policy_requires_workload_and_one_task_must_fit():
    document = _document()
    document["stage_concurrency"]["01"] = "auto"
    document["step_threads"]["01"] = "auto"
    document["stage_memory_mb"]["01"] = {"minimum_mb": 40960}
    policy = _policy(document)
    with pytest.raises(ResourceConfigError, match="workload"):
        resolve_resource_policy(policy, _allocation(memory_mb=65536))
    with pytest.raises(ResourceConfigError, match="one task|minimum"):
        resolve_resource_policy(
            policy, _allocation(), workload={"samples": 6, "partitions": 1}
        )


@pytest.mark.parametrize("cores", (8, 96, 256))
def test_allocation_cpu_policy_resolves_threads_and_survives_readmission(
    cores: int,
) -> None:
    document = _document()
    document["workflow_cores"] = "allocation"
    document["step_threads"]["00a"] = "workflow"
    policy = _policy(document)
    resolved = resolve_resource_policy(policy, _allocation(cores=cores))
    assert resolved.workflow_cores == resolved.threads_for("00a") == cores
    assert resolved.declaration.workflow_cores == "allocation"
    assert dict(resolved.declaration.step_threads)["00a"] == "workflow"
    assert admit_resource_policy_record(resolved.policy_record()) == resolved
    resumed = resolve_resource_policy(
        resume_resource_policy(policy), _allocation(cores=32)
    )
    assert resumed.workflow_cores == resumed.threads_for("00a") == 32
    assert resumed.policy.document() == policy.document()


def test_workflow_threads_follow_explicit_cpu_budget_and_reject_oversubscription() -> (
    None
):
    document = _document()
    document["step_threads"]["00a"] = "workflow"
    resolved = resolve_resource_policy(_policy(document), _allocation(cores=96))
    assert resolved.workflow_cores == resolved.threads_for("00a") == 4
    document["step_threads"]["01"] = "workflow"
    document["stage_concurrency"]["01"] = 2
    with pytest.raises(ResourceConfigError, match="concurrency x threads"):
        _policy(document)


def test_integral_yaml_numbers_remain_canonical_integer_tool_limits() -> None:
    document = _document()
    document["workflow_cores"] = 4.0
    document["workflow_memory_mb"] = 16384.0
    document["step_threads"]["00a"] = 4.0
    document["stage_memory_mb"]["00a"] = 8192.0
    resolved = resolve_resource_policy(_policy(document), _allocation())
    assert type(resolved.workflow_cores) is int
    assert type(resolved.workflow_memory_mb) is int
    assert type(resolved.threads_for("00a")) is int
    assert type(dict(resolved.stage_memory_mb)["00a"]) is int


def _policy(
    document: dict[str, Any] | None = None,
    *,
    override_labels: tuple[str, ...] = (),
):
    return admit_resource_policy(
        _document() if document is None else document,
        default_sha256=DEFAULT_SHA256,
        override_labels=override_labels,
    )


def _allocation(
    *,
    cores: int = 8,
    memory_mb: int = 16_384,
    slurm_job_id: str | None = None,
) -> AllocationCapacity:
    return AllocationCapacity(
        cores=cores,
        memory_mb=memory_mb,
        source="test allocation",
        slurm_job_id=slurm_job_id,
    )


def test_symbolic_declaration_is_allocation_independent_and_persistable() -> None:
    policy = _policy()
    first = resolve_resource_policy(policy, _allocation(memory_mb=16_384))
    second = resolve_resource_policy(policy, _allocation(memory_mb=32_768))

    assert policy.document() == _document()
    numeric_workflow = {
        **policy.declaration.identity_document(),
        "workflow_memory_mb": 4096,
    }
    assert resolve_computational_resources(numeric_workflow) == numeric_workflow
    assert policy.declaration == first.declaration == second.declaration
    assert first.declaration.workflow_memory_mb == "allocation"
    assert set(dict(first.declaration.stage_memory_mb).values()) == {"workflow"}
    assert first.declaration.identity_document() == {
        "workflow_cores": 4,
        "workflow_memory_mb": "allocation",
        "stage_concurrency": dict(first.stage_concurrency),
        "step_threads": dict(first.step_threads),
        "stage_memory_mb": dict(first.declaration.stage_memory_mb),
    }
    assert first.workflow_memory_mb == 16_384
    assert second.workflow_memory_mb == 32_768
    assert dict(first.stage_concurrency) == {
        step_id: 1 for step_id in REPEATABLE_STAGE_IDS
    }
    assert dict(first.step_threads) == {
        "00a": 4,
        "01": 4,
        "02": 1,
        "06": 4,
        "08": 1,
        "09": 1,
        "10": 1,
    }
    assert set(dict(first.stage_memory_mb).values()) == {16_384}
    assert "reporting_memory_mb" not in first.effective_document()
    assert dict(first.scheduler_limits()) == {
        "mem_mb": 16_384,
        **{f"stage_{step_id}_slots": 1 for step_id in REPEATABLE_STAGE_IDS},
    }

    record = first.policy_record()
    assert record["symbolic"] == policy.document()
    admitted = admit_resource_policy_record(record)
    assert admitted.policy == first.policy
    assert admitted.effective_document() == first.effective_document()
    reallocated = resolve_resource_policy(
        admitted.policy, _allocation(memory_mb=32_768)
    )
    assert reallocated.workflow_memory_mb == 32_768


def test_resume_applies_explicit_overrides() -> None:
    baseline = _policy(override_labels=("stage_concurrency.01",))
    resumed = resume_resource_policy(
        baseline,
        overrides=ResourceOverrides(
            workflow_cores=5,
            step_threads=(("01", 2),),
        ),
    )

    assert resumed.declaration.workflow_cores == 5
    assert dict(resumed.declaration.step_threads)["01"] == 2
    assert resumed.override_labels == (
        "stage_concurrency.01",
        "workflow_cores",
        "step_threads.01",
    )


def test_persisted_policy_rejects_missing_symbolic_fields_and_tampering() -> None:
    large_job_id = "9" * 5000
    current = resolve_resource_policy(
        _policy(),
        _allocation(slurm_job_id=large_job_id),
    )
    record = current.policy_record()

    assert record["allocation"]["slurm_job_id"] == large_job_id
    assert admit_resource_policy_record(record).allocation == current.allocation
    no_job_id = copy.deepcopy(record)
    no_job_id["allocation"].pop("slurm_job_id")
    assert (
        admit_resource_policy_record(
            no_job_id,
        ).allocation.slurm_job_id
        is None
    )

    historical = {
        key: value
        for key, value in record.items()
        if key not in {"symbolic", "symbolic_sha256"}
    }
    with pytest.raises(ResourceConfigError, match="Persisted resource policy keys"):
        admit_resource_policy_record(historical)

    symbolic_tamper = copy.deepcopy(record)
    symbolic_tamper["symbolic_sha256"] = "0" * 64
    with pytest.raises(ResourceConfigError, match="symbolic resource digest differs"):
        admit_resource_policy_record(symbolic_tamper)
    effective_tamper = copy.deepcopy(record)
    effective_tamper["effective_sha256"] = "0" * 64
    with pytest.raises(ResourceConfigError, match="effective resource digest differs"):
        admit_resource_policy_record(effective_tamper)

    changed = copy.deepcopy(record)
    changed["effective"]["workflow_memory_mb"] = 1024
    changed["effective_sha256"] = orchestration_contracts.canonical_sha256(
        changed["effective"]
    )
    with pytest.raises(ResourceConfigError, match="does not reproduce its resolution"):
        admit_resource_policy_record(changed)
    with pytest.raises(ResourceConfigError, match="Slurm job ID"):
        _allocation(slurm_job_id="0")


@pytest.mark.parametrize(
    ("allocation", "overrides", "message"),
    (
        (
            _allocation(cores=4),
            ResourceOverrides(workflow_cores=5),
            "Workflow cores exceed observed allocation",
        ),
        (
            _allocation(memory_mb=8192),
            ResourceOverrides(workflow_memory_mb=8193),
            "Workflow memory exceeds observed allocation",
        ),
        (
            _allocation(memory_mb=4096),
            ResourceOverrides(
                stage_concurrency=(("01", 2),),
                step_threads=(("01", 1),),
                stage_memory_mb=(("01", 3072),),
            ),
            "concurrency x memory exceeds workflow memory",
        ),
    ),
)
def test_resolution_rejects_invalid_resource_relationships(
    allocation: AllocationCapacity,
    overrides: ResourceOverrides,
    message: str,
) -> None:
    policy = resume_resource_policy(_policy(), overrides=overrides)

    with pytest.raises(ResourceConfigError, match=message):
        resolve_resource_policy(policy, allocation)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        (ResourceOverrides(step_threads=(("00a", 5),)), "concurrency x threads"),
        (
            ResourceOverrides(
                stage_concurrency=(("01", 2),), step_threads=(("01", 3),)
            ),
            "concurrency x threads",
        ),
        (
            ResourceOverrides(
                workflow_memory_mb=4096,
                stage_concurrency=(("01", 2),),
                step_threads=(("01", 1),),
                stage_memory_mb=(("01", 3072),),
            ),
            "concurrency x memory",
        ),
        (
            ResourceOverrides(
                stage_concurrency=(("01", 2),), step_threads=(("01", 1),)
            ),
            "2 x workflow > workflow",
        ),
        (
            ResourceOverrides(
                workflow_memory_mb=4096, stage_memory_mb=(("00a", 4097),)
            ),
            "concurrency x memory",
        ),
    ),
)
def test_admission_and_resume_reject_impossible_declared_limits_without_allocation(
    overrides: ResourceOverrides, message: str
) -> None:
    document = _document()
    predecessor = _policy(document)
    with pytest.raises(ResourceConfigError, match=message):
        admit_resource_policy(
            document, default_sha256=DEFAULT_SHA256, overrides=overrides
        )
    with pytest.raises(ResourceConfigError, match=message):
        resume_resource_policy(predecessor, overrides=overrides)
    assert document == predecessor.document() == _document()


def test_numeric_stage_memory_stays_unresolved_until_allocation_is_known() -> None:
    policy = resume_resource_policy(
        _policy(),
        overrides=ResourceOverrides(
            stage_concurrency=(("01", 2),),
            step_threads=(("01", 2),),
            stage_memory_mb=(("01", 2048),),
        ),
    )
    before = policy.document()
    assert policy.declaration.workflow_memory_mb == "allocation"
    assert dict(policy.declaration.stage_memory_mb)["00a"] == "workflow"
    resolved = resolve_resource_policy(policy, _allocation(memory_mb=4096))
    assert resolved.workflow_memory_mb == 4096
    assert dict(resolved.stage_memory_mb)["01"] == 2048
    with pytest.raises(ResourceConfigError, match="concurrency x memory"):
        resolve_resource_policy(policy, _allocation(memory_mb=4095))
    assert policy.document() == before


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda record: record.__setitem__("unknown", 1), "Additional properties"),
        (lambda record: record.__setitem__("workflow_cores", 0), "workflow_cores"),
        (
            lambda record: record["step_threads"].__setitem__("11", 1),
            "Additional properties",
        ),
        (
            lambda record: record["stage_concurrency"].pop("07"),
            "Resolved stage_concurrency keys",
        ),
        (
            lambda record: record.pop("stage_concurrency"),
            "Resolved stage_concurrency keys",
        ),
        (
            lambda record: record["step_threads"].pop("08"),
            "Resolved step_threads keys must be exactly",
        ),
    ),
)
def test_policy_admission_rejects_invalid_or_incomplete_documents(
    mutate: Callable[[dict[str, Any]], Any],
    message: str,
) -> None:
    document = _document()
    mutate(document)

    with pytest.raises(ResourceConfigError, match=message):
        _policy(document)


def test_resource_overrides_reject_invalid_assignments() -> None:
    with pytest.raises(ResourceConfigError, match="Duplicate command-line"):
        ResourceOverrides(stage_concurrency=(("01", 2), ("01", 3)))
    with pytest.raises(ResourceConfigError, match="Unknown command-line"):
        ResourceOverrides(stage_concurrency=(("00a", 1),))
    with pytest.raises(ResourceConfigError, match="positive integer"):
        ResourceOverrides(step_threads=(("01", 0),))


def test_resource_override_arguments_round_trip_exact_delegate_argv() -> None:
    expected = ResourceOverrides(
        workflow_cores=8,
        workflow_memory_mb=12_000,
        stage_concurrency=(("01", 4), ("02", 2)),
        step_threads=(("01", 2),),
        stage_memory_mb=(("01", 3000),),
    )
    argv = resource_override_argv(expected)

    assert argv == (
        "--workflow-cores",
        "8",
        "--workflow-memory-mb",
        "12000",
        "--stage-concurrency",
        "01=4",
        "--stage-concurrency",
        "02=2",
        "--step-threads",
        "01=2",
        "--stage-memory-mb",
        "01=3000",
    )
    parser = argparse.ArgumentParser()
    add_resource_override_arguments(parser)
    assert overrides_from_args(parser.parse_args(argv)) == expected
    assert resource_override_argv(ResourceOverrides()) == ()
    with pytest.raises(SystemExit):
        parser.parse_args(["--workflow-cores", "0"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--reporting-memory-mb", "html_report=1000"])


def test_symbolic_resource_overrides_round_trip_delegate_argv() -> None:
    expected = ResourceOverrides(
        workflow_cores="allocation",
        workflow_memory_mb="allocation",
        step_threads=(("00a", "workflow"),),
        stage_memory_mb=(("00a", "workflow"),),
    )
    parser = argparse.ArgumentParser()
    add_resource_override_arguments(parser)
    assert (
        overrides_from_args(parser.parse_args(resource_override_argv(expected)))
        == expected
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["--stage-concurrency", "01=workflow"])
