# GitHub Actions workflows

[`ci.yml`](ci.yml) runs ordinary checks on pull requests. Scheduled and manually
selected lanes add longer synthetic and scheduler checks. The
[test baseline](../../docs/design/TEST_BASELINE.md#validation-lanes) defines each
lane; a green workflow supports only the claims covered by those checks.

The managed golden path also exercises Task descendant cleanup with the
samtools already selected by its synthetic Project. It requires that executable
before running the Linux process fixtures and canonical BAM checks. The job
retains their JUnit results and tiny native outputs beside its existing evidence.
This covers the hosted worker boundary; it does not establish Slurm cancellation,
lost-worker reconciliation or safe postentry retry.


## Doctor namespace-concurrency experiment

An explicitly selected `workflow_dispatch` managed_runtime_golden_path run
also compares four complete read-only Doctor diagnoses of the already-qualified
borrower, in serial / two-worker / two-worker / serial order. Normal PR CI runs
fixture protections only. This measures steady-ready diagnosis; it does not
measure setup, repair, or the earlier two-boundary borrower verification.

Only the temporary CI driver injects two concurrent R namespace workers. Every
Rscript command retains its fresh process, guarded arguments, environment,
parser and 120-second timeout. Check/result ordering and admission boundaries
are preserved. The canonical product probe owner remains serial. Fixtures cover
actual child interruption, launch refusal, timeout versus exit 124, loader
failure, fresh drift checks, Java/GATK context, and counter concurrency.

Trials require zero exit, identical ordered fresh observations apart from
elapsed values, and unchanged borrower bytes/namespace, lstat identity/ownership/mtime/ctime
(excluding atime), plus the existing donor
content/namespace comparisons. Each trial has an isolated process group and a
bounded supervisor. The unreaped trial leader pins its process-group ID through observation and
any cleanup; an empty group receives no signal. Observed surviving group members reject the trial;
process enumeration can race descendant replacement. This apparatus does not
prove kernel descendant closure, production cancellation parity, or containment
of descendants that leave the group.

Already-locked psutil samples simultaneous root/descendant RSS and CPU every
50 ms. RSS sums can count shared pages repeatedly and miss short-lived processes
and true peaks. Sampled CPU is a cumulative lifetime lower bound, including pre-timer startup,
separate from the existing invocation CPU deltas.
Read-counter locks cover updates only; reads stay concurrent. Observation
overhead is included, and existing logical-read/I/O limitations still apply.
No cache flushing or installation is added; host and cache state remain
uncontrolled despite AB/BA ordering.

Retain every doctor-*-measurement.json and doctor-*.log trial, including failed
attempts. Evaluate complete valid pairs only. This temporary apparatus neither
adopts concurrency nor establishes a speedup, setup/repair saving, production
cancellation parity, or site/Slurm/NFS performance. After the experiment, retain
its evidence and decision, then remove the scheduling/comparison apparatus in
the adoption or rejection slice; do not leave it as a second supported backend.
