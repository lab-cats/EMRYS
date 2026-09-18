"""Observe the CPU and memory capacity available to the local executor process."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from emrys.orchestration.run_coordinator.resource_policy import (
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
_CGROUP_MEMBERSHIP = Path("/proc/self/cgroup")


def _cgroup_files(root_file: Path, controller: str) -> tuple[Path, ...]:
    """Include this process's cgroup and ancestor limits on standard Linux mounts."""
    paths = {root_file}
    try:
        memberships = _CGROUP_MEMBERSHIP.read_text(
            encoding="utf-8", errors="surrogateescape"
        ).splitlines()
    except OSError:
        memberships = []
    for line in memberships:
        parts = line.split(":", 2)
        if len(parts) != 3 or controller not in parts[1].split(","):
            continue
        relative = Path(parts[2].lstrip("/"))
        if ".." in relative.parts:
            continue
        directory = root_file.parent / relative
        while directory != root_file.parent:
            paths.add(directory / root_file.name)
            directory = directory.parent
    return tuple(sorted(paths))


def _positive_environment_integer(
    environment: Mapping[str, str],
    name: str,
    *,
    allow_zero: bool = False,
) -> int | None:
    raw = environment.get(name)
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ResourceConfigError(f"{name} must be a positive integer") from exc
    if value < (0 if allow_zero else 1):
        raise ResourceConfigError(f"{name} must be a positive integer")
    return value


def _affinity_cores() -> int:
    if hasattr(os, "sched_getaffinity"):
        count = len(os.sched_getaffinity(0))
    else:
        count = os.cpu_count() or 0
    limits = [count]
    for path in _cgroup_files(_CGROUP_V2_CPU_FILE, ""):
        try:
            quota_text, period_text = path.read_text(encoding="ascii").split()
            quota, period = int(quota_text), int(period_text)
            if quota > 0 and period > 0:
                limits.append(max(1, quota // period))
        except (OSError, ValueError):
            pass
    for path in _cgroup_files(_CGROUP_V1_CPU_FILES[0], "cpu"):
        try:
            quota = int(path.read_text(encoding="ascii"))
            period = int(
                path.with_name(_CGROUP_V1_CPU_FILES[1].name).read_text(encoding="ascii")
            )
            if quota > 0 and period > 0:
                limits.append(max(1, quota // period))
        except (OSError, ValueError):
            pass
    count = min(limits)
    if count < 1:
        raise ResourceConfigError("Could not observe any process CPU capacity")
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
    paths = (
        path
        for root_file in _CGROUP_MEMORY_FILES
        for path in _cgroup_files(
            root_file, "" if root_file.name == "memory.max" else "memory"
        )
    )
    for path in paths:
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
            slurm_job_id=None,
        )

    slurm_cores = _positive_environment_integer(selected, "SLURM_CPUS_PER_TASK")
    if slurm_cores is None:
        slurm_cores = _positive_environment_integer(selected, "SLURM_CPUS_ON_NODE")
    if slurm_cores is None:
        raise ResourceConfigError(
            "SLURM_CPUS_PER_TASK or SLURM_CPUS_ON_NODE is required inside the one-task allocation"
        )
    per_node = _positive_environment_integer(
        selected, "SLURM_MEM_PER_NODE", allow_zero=True
    )
    per_cpu = _positive_environment_integer(selected, "SLURM_MEM_PER_CPU")
    if per_node is not None and per_cpu is not None:
        raise ResourceConfigError(
            "Slurm exposed both SLURM_MEM_PER_NODE and SLURM_MEM_PER_CPU"
        )
    if per_node is not None:
        slurm_memory_mb = per_node or process_memory_mb
        memory_source = "SLURM_MEM_PER_NODE" + (
            "=0; all process-visible node memory" if per_node == 0 else ""
        )
    elif per_cpu is not None:
        slurm_memory_mb = per_cpu * slurm_cores
        memory_source = "SLURM_MEM_PER_CPU x SLURM_CPUS_PER_TASK"
    else:
        slurm_memory_mb = process_memory_mb
        memory_source = "process-visible memory; Slurm memory limit unspecified"
    return AllocationCapacity(
        cores=min(slurm_cores, affinity_cores),
        memory_mb=min(slurm_memory_mb, process_memory_mb),
        source=(
            "Slurm allocation constrained by process affinity/memory limit "
            f"({memory_source})"
        ),
        slurm_job_id=job_id,
    )


__all__ = ("observe_allocation",)
