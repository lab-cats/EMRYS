# Repository utilities

Repository-level utilities that do not belong to one scientific owner:

| Area | Interfaces |
| --- | --- |
| R environment | [`check_r_environment.R`](check_r_environment.R), [`restore_r_environment.R`](restore_r_environment.R) |
| Documentation structure | [`validate_documentation.py`](git_orchestration/validate_documentation.py) |
| Make implementation | [`make_quality.mk`](make_quality.mk), [`make_reporting.mk`](make_reporting.mk), [`make_operations.mk`](make_operations.mk) |
| Resource benchmarking | [`benchmark_stage_resources.py`](benchmark_stage_resources.py) |

Exact invocations belong in the [runbook](../docs/operations/RUNBOOK.md).
The read-only `make dashboard` operator view is implemented by
[`make_operations.mk`](make_operations.mk). With no override it queries bounded
recent Slurm metadata for the current user and admits only a job whose exact
EMRYS wrapper streams can be proved from live control metadata or accounting's
declared stdout/stderr paths. `JOB_ID=<id>` selects an explicit job;
`LOG_DIR=<absolute-directory>` may accompany `JOB_ID` and must agree with
scheduler-declared streams. After live metadata expires, exact bounded
accounting can still select a terminal job by `JOB_ID` alone when it reports
both stream paths. If site accounting omits those fields, the explicit
`JOB_ID`/`LOG_DIR` pair remains available only when exact accounting identity,
current ownership, and the log contract all pass. Discovery validates the
wrapper filenames, current ownership, readability, real directory and
regular-file types, and the absence of symlinked paths; it does not scan
shared storage.

The dashboard is an operational convenience over scheduler metadata and
append-only logs. It does not derive or display result locations. Its state,
progress, and timing are not completion, validation, or evidence authority;
final EMRYS inspection and the applicable owner records remain authoritative.
The current implementation is specialized to the CSU local-pilot wrapper,
fixed qualified stage topology, six-sample cohort, and 25-partition
qualification run. Portable, request-derived topology, machine-readable
events, and bounded generic parsing remain deferred dashboard work. Effective
workflow cores, per-stage concurrency, per-step threads, and memory policy are
read from the selected run's control stream rather than hard-coded to one
benchmark policy.

The resource benchmark is opt-in and manifest-driven. It runs only exact argv
arrays supplied by the operator, writes one create-absent result tree, records
producer wall time and child-process peak RSS, validates every trial, and recommends
the smallest value within five percent of the fastest successful median. It is
not part of normal validation and its recommendation applies only to the tested
dataset, machine, runtime, and storage system.
Dependency restoration is explicit operator mutation. Validation, rendering,
and restore success do not establish runtime, cluster, scientific-review, or
biological evidence.
