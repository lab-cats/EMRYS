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


def test_slurm_without_observed_memory_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 8192)

    with pytest.raises(ResourceConfigError, match="did not expose"):
        capacity.observe_allocation(
            {"SLURM_JOB_ID": "789", "SLURM_CPUS_PER_TASK": "4"}
        )
