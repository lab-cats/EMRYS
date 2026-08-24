"""Observe the CPU and memory capacity available to the local executor process."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from emrys.orchestration.local_pilot.resource_policy import (
    AllocationCapacity,
    ResourceConfigError,
)

_CGROUP_MEMORY_FILES = (
    Path("/sys/fs/cgroup/memory.max"),
    Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
)
_CGROUP_V2_CPU_FILE = Path("/sys/fs/cgroup/cpu.max")
_CGROUP_V1_CPU_FILES = (
    Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"),
    Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us"),
)


def _positive_environment_integer(
    environment: Mapping[str, str],
    name: str,
) -> int | None:
    raw = environment.get(name)
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ResourceConfigError(f"{name} must be a positive integer") from exc
    if value < 1:
        raise ResourceConfigError(f"{name} must be a positive integer")
    return value


def _affinity_cores() -> int:
    if hasattr(os, "sched_getaffinity"):
        count = len(os.sched_getaffinity(0))
    else:
        count = os.cpu_count() or 0
    limits = [count]
    try:
        quota_text, period_text = _CGROUP_V2_CPU_FILE.read_text(
            encoding="ascii"
        ).split()
        if quota_text != "max":
            quota = int(quota_text)
            period = int(period_text)
            if quota > 0 and period > 0:
                limits.append(max(1, quota // period))
    except (OSError, ValueError):
        try:
            quota = int(_CGROUP_V1_CPU_FILES[0].read_text(encoding="ascii"))
            period = int(_CGROUP_V1_CPU_FILES[1].read_text(encoding="ascii"))
            if quota > 0 and period > 0:
                limits.append(max(1, quota // period))
        except (OSError, ValueError):
            pass
    count = min(limits)
    if count < 1:
        raise ResourceConfigError("Could not observe any process CPU capacity")
    return count


def _host_cores() -> int:
    count = os.cpu_count() or 0
    if count < 1:
        raise ResourceConfigError("Could not observe any host CPU capacity")
    return count


def _host_memory_mb() -> int:
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
    except (OSError, TypeError, ValueError) as exc:
        raise ResourceConfigError("Could not observe host memory capacity") from exc
    memory_mb = page_size * page_count // (1024 * 1024)
    if memory_mb < 1:
        raise ResourceConfigError("Could not observe positive host memory capacity")
    return memory_mb


def _memory_limit_mb() -> int:
    host_memory = _host_memory_mb()
    limits = [host_memory]
    for path in _CGROUP_MEMORY_FILES:
        try:
            raw = path.read_text(encoding="ascii").strip()
        except OSError:
            continue
        if raw == "max":
            continue
        try:
            value = int(raw)
        except ValueError as exc:
            raise ResourceConfigError(
                f"Could not parse process memory limit {path}"
            ) from exc
        memory_mb = value // (1024 * 1024)
        if memory_mb > 0:
            limits.append(memory_mb)
    return min(limits)


def observe_allocation(
    environment: Mapping[str, str] | None = None,
) -> AllocationCapacity:
    """Return process-visible capacity, constrained by Slurm when present."""

    selected = os.environ if environment is None else environment
    affinity_cores = _affinity_cores()
    process_memory_mb = _memory_limit_mb()
    job_id = selected.get("SLURM_JOB_ID")
    if not job_id:
        return AllocationCapacity(
            cores=affinity_cores,
            memory_mb=process_memory_mb,
            source="process affinity and memory limit",
        )

    slurm_cores = _positive_environment_integer(selected, "SLURM_CPUS_PER_TASK")
    if slurm_cores is None:
        raise ResourceConfigError(
            "SLURM_CPUS_PER_TASK is required inside the one-task allocation"
        )
    per_node = _positive_environment_integer(selected, "SLURM_MEM_PER_NODE")
    per_cpu = _positive_environment_integer(selected, "SLURM_MEM_PER_CPU")
    if per_node is not None and per_cpu is not None:
        raise ResourceConfigError(
            "Slurm exposed both SLURM_MEM_PER_NODE and SLURM_MEM_PER_CPU"
        )
    if per_node is not None:
        slurm_memory_mb = per_node
        memory_source = "SLURM_MEM_PER_NODE"
    elif per_cpu is not None:
        slurm_memory_mb = per_cpu * slurm_cores
        memory_source = "SLURM_MEM_PER_CPU x SLURM_CPUS_PER_TASK"
    else:
        host_cores = _host_cores()
        if slurm_cores != affinity_cores or affinity_cores != host_cores:
            raise ResourceConfigError(
                "Slurm did not expose SLURM_MEM_PER_NODE or SLURM_MEM_PER_CPU "
                "and the job does not have complete node CPU visibility"
            )
        slurm_memory_mb = process_memory_mb
        memory_source = "complete-node CPU allocation with process-visible memory"
    return AllocationCapacity(
        cores=min(slurm_cores, affinity_cores),
        memory_mb=min(slurm_memory_mb, process_memory_mb),
        source=(
            "Slurm allocation constrained by process affinity/memory limit "
            f"({memory_source}, job {job_id})"
        ),
    )


__all__ = ("observe_allocation",)
