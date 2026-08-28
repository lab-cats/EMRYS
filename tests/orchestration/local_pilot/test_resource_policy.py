"""Computational-resource admission, resolution, and persistence contracts."""

from __future__ import annotations

import argparse
import copy
from collections.abc import Callable
from typing import Any

import pytest

from emrys.orchestration.local_pilot.resource_policy import (
    REPORTING_KINDS,
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
    resume_resource_plan,
)

DEFAULT_SHA256 = "d" * 64


def _document() -> dict[str, Any]:
    return {
        "schema_version": "emrys.local-pilot-resources.v1",
        "workflow_cores": 4,
        "workflow_memory_mb": "allocation",
        "stage_concurrency": {step_id: 1 for step_id in REPEATABLE_STAGE_IDS},
        "step_threads": {
            "00a": 4,
            "01": 4,
            "02": 1,
            "06": 4,
            "08": 1,
        },
        "stage_memory_mb": {step_id: "workflow" for step_id in STAGE_IDS},
        "reporting_memory_mb": {kind: "workflow" for kind in REPORTING_KINDS},
    }


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
    }
    assert set(dict(first.stage_memory_mb).values()) == {16_384}
    assert set(dict(second.reporting_memory_mb).values()) == {32_768}
    assert dict(first.scheduler_limits()) == {
        "mem_mb": 16_384,
        **{f"stage_{step_id}_slots": 1 for step_id in REPEATABLE_STAGE_IDS},
    }

    record = first.policy_record()
    assert record["symbolic"] == policy.document()
    admitted = admit_resource_policy_record(record, require_symbolic=True)
    assert admitted.policy == first.policy
    assert admitted.effective_document() == first.effective_document()
    reallocated = resume_resource_plan(record, _allocation(memory_mb=32_768))
    assert reallocated.workflow_memory_mb == 32_768

def test_reporting_is_not_run_bound_and_resume_applies_explicit_overrides() -> None:
    baseline = _policy(override_labels=("stage_concurrency.01",))
    changed_document = _document()
    changed_document["reporting_memory_mb"]["html_report"] = 1024
    reporting_changed = _policy(changed_document)
    resumed = resume_resource_policy(
        baseline,
        overrides=ResourceOverrides(
            workflow_cores=5,
            step_threads=(("01", 2),),
        ),
    )

    assert reporting_changed.declaration == baseline.declaration
    reporting_plan = resolve_resource_policy(reporting_changed, _allocation())
    assert dict(reporting_plan.reporting_memory_mb)["html_report"] == 1024
    assert resumed.declaration.workflow_cores == 5
    assert dict(resumed.declaration.step_threads)["01"] == 2
    assert resumed.override_labels == (
        "stage_concurrency.01",
        "workflow_cores",
        "step_threads.01",
    )


def test_current_and_historical_persisted_policy_resume() -> None:
    large_job_id = "9" * 5000
    current = resolve_resource_policy(
        _policy(),
        _allocation(slurm_job_id=large_job_id),
    )
    record = current.policy_record()

    assert record["allocation"]["slurm_job_id"] == large_job_id
    assert (
        admit_resource_policy_record(record, require_symbolic=True).allocation
        == current.allocation
    )
    no_job_id = copy.deepcopy(record)
    no_job_id["allocation"].pop("slurm_job_id")
    assert (
        admit_resource_policy_record(
            no_job_id,
            require_symbolic=True,
        ).allocation.slurm_job_id
        is None
    )

    historical = {
        key: value
        for key, value in record.items()
        if key not in {"symbolic", "symbolic_sha256"}
    }
    resumed = resume_resource_plan(historical, _allocation(memory_mb=32_768))
    assert resumed.effective_document() == current.effective_document()
    assert resumed.allocation.memory_mb == 32_768
    with pytest.raises(ResourceConfigError, match="Persisted resource policy keys"):
        admit_resource_policy_record(historical, require_symbolic=True)

    symbolic_tamper = copy.deepcopy(record)
    symbolic_tamper["symbolic_sha256"] = "0" * 64
    with pytest.raises(ResourceConfigError, match="symbolic resource digest differs"):
        admit_resource_policy_record(symbolic_tamper, require_symbolic=True)
    effective_tamper = copy.deepcopy(historical)
    effective_tamper["effective_sha256"] = "0" * 64
    with pytest.raises(ResourceConfigError, match="effective resource digest differs"):
        resume_resource_plan(effective_tamper, _allocation())
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
            _allocation(cores=4),
            ResourceOverrides(
                stage_concurrency=(("01", 2),),
                step_threads=(("01", 3),),
            ),
            "concurrency x threads exceeds workflow cores",
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
        (
            _allocation(memory_mb=4096),
            ResourceOverrides(reporting_memory_mb=(("html_report", 4097),)),
            "Reporting html_report memory exceeds workflow memory",
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
    ("mutate", "message"),
    (
        (lambda record: record.__setitem__("unknown", 1), "Additional properties"),
        (lambda record: record.__setitem__("workflow_cores", 0), "less than"),
        (
            lambda record: record["step_threads"].__setitem__("09", 1),
            "Additional properties",
        ),
        (
            lambda record: record["stage_concurrency"].pop("07"),
            "Resolved stage_concurrency keys",
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
        reporting_memory_mb=(("html_report", 1000),),
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
        "--reporting-memory-mb",
        "html_report=1000",
    )
    parser = argparse.ArgumentParser()
    add_resource_override_arguments(parser)
    assert overrides_from_args(parser.parse_args(argv)) == expected
    assert resource_override_argv(ResourceOverrides()) == ()
    with pytest.raises(SystemExit):
        parser.parse_args(["--workflow-cores", "0"])
