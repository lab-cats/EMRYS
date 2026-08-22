"""Process-local allocation observation contracts."""

from __future__ import annotations

import pytest

from norad.orchestration.local_pilot import capacity
from norad.orchestration.local_pilot.resource_policy import ResourceConfigError


def test_local_capacity_uses_process_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 6)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 12_000)

    observed = capacity.observe_allocation({})

    assert observed.cores == 6
    assert observed.memory_mb == 12_000
    assert observed.source == "process affinity and memory limit"


def test_slurm_capacity_is_constrained_by_process_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 3)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 7000)

    observed = capacity.observe_allocation(
        {
            "SLURM_JOB_ID": "123",
            "SLURM_CPUS_PER_TASK": "4",
            "SLURM_MEM_PER_NODE": "8192",
        }
    )

    assert observed.cores == 3
    assert observed.memory_mb == 7000
    assert "SLURM_MEM_PER_NODE" in observed.source


def test_slurm_per_cpu_memory_is_multiplied_by_allocated_cpus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 8)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 20_000)

    observed = capacity.observe_allocation(
        {
            "SLURM_JOB_ID": "456",
            "SLURM_CPUS_PER_TASK": "4",
            "SLURM_MEM_PER_CPU": "2048",
        }
    )

    assert observed.cores == 4
    assert observed.memory_mb == 8192
    assert "SLURM_MEM_PER_CPU" in observed.source


def test_slurm_without_cpu_declaration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 8192)

    with pytest.raises(ResourceConfigError, match="SLURM_CPUS_PER_TASK is required"):
        capacity.observe_allocation(
            {"SLURM_JOB_ID": "567", "SLURM_MEM_PER_NODE": "8192"}
        )


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("SLURM_CPUS_PER_TASK", "0"),
        ("SLURM_CPUS_PER_TASK", "not-an-integer"),
        ("SLURM_MEM_PER_NODE", "0"),
        ("SLURM_MEM_PER_NODE", "not-an-integer"),
        ("SLURM_MEM_PER_CPU", "0"),
        ("SLURM_MEM_PER_CPU", "not-an-integer"),
    ),
)
def test_slurm_invalid_numeric_declaration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 8192)
    environment = {
        "SLURM_JOB_ID": "678",
        "SLURM_CPUS_PER_TASK": "4",
        "SLURM_MEM_PER_NODE": "8192",
    }
    if name == "SLURM_MEM_PER_CPU":
        environment.pop("SLURM_MEM_PER_NODE")
    environment[name] = value

    with pytest.raises(
        ResourceConfigError, match=rf"{name} must be a positive integer"
    ):
        capacity.observe_allocation(environment)


def test_slurm_with_both_memory_declarations_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 8192)

    with pytest.raises(ResourceConfigError, match="exposed both"):
        capacity.observe_allocation(
            {
                "SLURM_JOB_ID": "679",
                "SLURM_CPUS_PER_TASK": "4",
                "SLURM_MEM_PER_NODE": "8192",
                "SLURM_MEM_PER_CPU": "2048",
            }
        )


def test_slurm_full_node_without_memory_declaration_uses_process_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 256)
    monkeypatch.setattr(capacity, "_host_cores", lambda: 256)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 1_547_848)

    observed = capacity.observe_allocation(
        {"SLURM_JOB_ID": "605306", "SLURM_CPUS_PER_TASK": "256"}
    )

    assert observed.cores == 256
    assert observed.memory_mb == 1_547_848
    assert "complete-node CPU allocation" in observed.source


def test_slurm_partial_node_without_memory_declaration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_host_cores", lambda: 256)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 1_547_848)

    with pytest.raises(ResourceConfigError, match="complete node CPU visibility"):
        capacity.observe_allocation(
            {"SLURM_JOB_ID": "789", "SLURM_CPUS_PER_TASK": "4"}
        )
