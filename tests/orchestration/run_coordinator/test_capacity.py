"""Process-local allocation observation contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from emrys.orchestration.run_coordinator import capacity
from emrys.orchestration.run_coordinator.resource_policy import ResourceConfigError


def test_local_capacity_uses_process_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 6)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 12_000)

    observed = capacity.observe_allocation({})

    assert observed.cores == 6
    assert observed.memory_mb == 12_000
    assert observed.source == "process affinity and memory limit"
    assert observed.slurm_job_id is None


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
    assert observed.slurm_job_id == "123"


@pytest.mark.parametrize("job_id", ("0", "not-a-job", "-1", "١٢٣"))
def test_slurm_job_id_must_be_positive_ascii_decimal(
    monkeypatch: pytest.MonkeyPatch,
    job_id: str,
) -> None:
    monkeypatch.setattr(capacity, "_affinity_cores", lambda: 4)
    monkeypatch.setattr(capacity, "_memory_limit_mb", lambda: 8192)

    with pytest.raises(ResourceConfigError, match="Slurm job ID"):
        capacity.observe_allocation(
            {
                "SLURM_JOB_ID": job_id,
                "SLURM_CPUS_PER_TASK": "4",
                "SLURM_MEM_PER_NODE": "8192",
            }
        )


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
        capacity.observe_allocation({"SLURM_JOB_ID": "789", "SLURM_CPUS_PER_TASK": "4"})


def test_affinity_cores_honors_cgroup_v2_quota(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu_max = tmp_path / "cpu.max"
    cpu_max.write_text("250000 100000\n", encoding="ascii")
    monkeypatch.setattr(capacity, "_CGROUP_V2_CPU_FILE", cpu_max)
    monkeypatch.setattr(
        capacity,
        "_CGROUP_V1_CPU_FILES",
        (tmp_path / "missing-quota", tmp_path / "missing-period"),
    )
    monkeypatch.setattr(
        capacity.os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False
    )

    assert capacity._affinity_cores() == 2


def test_affinity_cores_falls_back_to_cgroup_v1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quota = tmp_path / "quota"
    period = tmp_path / "period"
    quota.write_text("300000\n", encoding="ascii")
    period.write_text("100000\n", encoding="ascii")
    monkeypatch.setattr(capacity, "_CGROUP_V2_CPU_FILE", tmp_path / "missing-v2")
    monkeypatch.setattr(capacity, "_CGROUP_V1_CPU_FILES", (quota, period))
    monkeypatch.setattr(
        capacity.os, "sched_getaffinity", lambda _pid: set(range(12)), raising=False
    )

    assert capacity._affinity_cores() == 3


def test_affinity_cores_uses_host_fallback_and_rejects_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(capacity.os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(capacity, "_CGROUP_V2_CPU_FILE", tmp_path / "missing-v2")
    monkeypatch.setattr(
        capacity,
        "_CGROUP_V1_CPU_FILES",
        (tmp_path / "missing-quota", tmp_path / "missing-period"),
    )
    monkeypatch.setattr(capacity.os, "cpu_count", lambda: 5)
    assert capacity._affinity_cores() == 5

    monkeypatch.setattr(capacity.os, "cpu_count", lambda: None)
    with pytest.raises(ResourceConfigError, match="process CPU capacity"):
        capacity._affinity_cores()


def test_host_capacity_observation_rejects_unavailable_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capacity.os, "cpu_count", lambda: None)
    with pytest.raises(ResourceConfigError, match="host CPU capacity"):
        capacity._host_cores()

    monkeypatch.setattr(capacity.os, "sysconf", lambda _name: 0)
    with pytest.raises(ResourceConfigError, match="positive host memory"):
        capacity._host_memory_mb()

    def unavailable(_name: str) -> int:
        raise OSError("unavailable")

    monkeypatch.setattr(capacity.os, "sysconf", unavailable)
    with pytest.raises(ResourceConfigError, match="host memory capacity"):
        capacity._host_memory_mb()


def test_host_memory_uses_page_size_and_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {"SC_PAGE_SIZE": 4096, "SC_PHYS_PAGES": 262144}
    monkeypatch.setattr(capacity.os, "sysconf", values.__getitem__)

    assert capacity._host_memory_mb() == 1024


def test_memory_limit_uses_smallest_cgroup_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unlimited = tmp_path / "memory.max"
    limited = tmp_path / "memory.limit_in_bytes"
    unlimited.write_text("max\n", encoding="ascii")
    limited.write_text(str(768 * 1024 * 1024), encoding="ascii")
    monkeypatch.setattr(capacity, "_CGROUP_MEMORY_FILES", (unlimited, limited))
    monkeypatch.setattr(capacity, "_host_memory_mb", lambda: 2048)

    assert capacity._memory_limit_mb() == 768


def test_memory_limit_rejects_invalid_cgroup_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = tmp_path / "memory.max"
    invalid.write_text("not-a-number\n", encoding="ascii")
    monkeypatch.setattr(capacity, "_CGROUP_MEMORY_FILES", (invalid,))
    monkeypatch.setattr(capacity, "_host_memory_mb", lambda: 2048)

    with pytest.raises(ResourceConfigError, match="parse process memory limit"):
        capacity._memory_limit_mb()
