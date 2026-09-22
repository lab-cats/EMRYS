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

The 130-pair real-synthetic lane is three independent matrix jobs:
clean direct/Slurm parity, controlled failure/resume parity, and fresh active
Slurm stop/resume. They run in parallel when capacity permits, with fail-fast
disabled and separate controller, worker, accounting database, workspace, and
evidence roots. The 100,000-pair production-like Slurm scenario remains a
separate weekly or manually selected job. A full prepared runner cannot be
shared safely across these jobs; only lock-keyed dependency caches are shared,
and one designated job may publish each cache to avoid concurrent writers.

Every job configures a disposable single-runner Slurm service with matching
supported binaries. Setup must prove versions, readiness, cluster registration,
and exact `squeue --clusters=emrys-ci` observation before its scenario starts.
Private service state stays on that runner; the scenario artifact contains only
bounded operator, runtime, setup, and terminal evidence. Infrastructure
readiness alone is not proof that an active Task was cancelled or that
cross-node Viking behavior works.

## Doctor namespace experiment disposition

The temporary two-worker R namespace comparison is retired; product probes
remain serial. [Run 34995028343](https://github.com/lab-cats/EMRYS/actions/runs/34995028343)
at `45bd9cd2b7b5dc98046aa7df862200b1b674c99d` retained four valid, fresh,
read-only diagnoses of one qualified borrower in serial/two/two/serial order.
Mean wall time was 57.45/41.53 seconds and sampled root-plus-descendant RSS
1204.32/1634.18 MiB for serial/two workers. Ordered observations and owner reads
matched. RSS sums can count shared pages repeatedly and miss peaks; host/cache
state was uncontrolled. This does not measure setup, repair or site performance.

The higher memory demand and unproven caller-complete resource/cancellation
ownership do not justify product adoption. Keep the retained measurements,
logs and donor comparisons in the run's `emrys-managed-golden-1` artifact;
the baseline donor/borrower measurement driver remains. Retirement removes
the temporary scheduler, supervisor, sampler, comparison and their fixtures.
