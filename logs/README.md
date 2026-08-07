# Runtime logs

`logs/` is the repository-level destination for scheduler standard output and
error streams. SLURM opens declared log paths before a job body runs, so this
directory must exist before `sbatch`; see the
[runbook site procedure](../docs/operations/RUNBOOK.md#checkout-and-site-orientation).

This README keeps the directory present in a fresh checkout. Generated log
content is ignored and must not be committed. Individual stage or evidence
owners define their own log names and immediate diagnostic meaning; this root
does not centralize stage behavior or prove successful execution.

## Retention and cleanup

Ignored does not mean disposable. Preserve logs while jobs are active, a
failure or recovery state is unresolved, or the streams support runtime or
cluster review. Confirm scheduler state and evidence needs before targeted
cleanup; NORAD does not automatically rotate, truncate, archive, or delete
logs. For missing paths or unexpected names, use
[`TROUBLESHOOTING.md`](../docs/operations/TROUBLESHOOTING.md).
