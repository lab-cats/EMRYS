# Repository utilities

Repository-level utilities that do not belong to one scientific owner:

| Area | Interfaces |
| --- | --- |
| R environment | [`check_r_environment.R`](check_r_environment.R), [`restore_r_environment.R`](restore_r_environment.R) |
| Documentation and tasks | [`validate_documentation.py`](git_orchestration/validate_documentation.py), [`task_status.py`](git_orchestration/task_status.py) |
| Make implementation | [`make_quality.mk`](make_quality.mk), [`make_reporting.mk`](make_reporting.mk) |
| Resource benchmarking | [`benchmark_stage_resources.py`](benchmark_stage_resources.py) |

Exact invocations belong in the [runbook](../docs/operations/RUNBOOK.md).
The resource benchmark is opt-in and manifest-driven. It runs only exact argv
arrays supplied by the operator, writes one create-absent result tree, records
producer wall time and GNU `time` peak RSS, validates every trial, and recommends
the smallest value within five percent of the fastest successful median. It is
not part of normal validation and its recommendation applies only to the tested
dataset, machine, runtime, and storage system.
Dependency restoration is explicit operator mutation. Validation, rendering,
and restore success do not establish runtime, cluster, scientific-review, or
biological evidence.
