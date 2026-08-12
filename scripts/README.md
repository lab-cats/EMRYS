# Repository utilities

Repository-level utilities that do not belong to one scientific owner:

| Area | Interfaces |
| --- | --- |
| R environment | [`check_r_environment.R`](check_r_environment.R), [`restore_r_environment.R`](restore_r_environment.R) |
| Documentation and tasks | [`validate_documentation.py`](git_orchestration/validate_documentation.py), [`task_status.py`](git_orchestration/task_status.py) |
| Make implementation | [`make_quality.mk`](make_quality.mk), [`make_reporting.mk`](make_reporting.mk) |

Exact invocations belong in the [runbook](../docs/operations/RUNBOOK.md).
Dependency restoration is explicit operator mutation. Validation, rendering,
and restore success do not establish runtime, cluster, scientific-review, or
biological evidence.
