# Local Snakemake profile

[`profile.v9+.yaml`](profile.v9+.yaml) selects the local executor, deterministic
scheduling defaults, no engine retries, retained incomplete outputs, and visible
commands and failed logs. The Execution Plan and Attempt supply total cores,
sample concurrency, and supported task thread counts; those settings do not
change scientific identity.

Every job runs on the same host or allocation. Slurm submission enters this
same profile inside the allocation; there are no standalone stage scheduler
commands. Materialization binds the exact checkout file and the lifecycle passes
it to Snakemake. Use `emrys run` or `emrys resume`, as described in the
[workflow overview](../../README.md) and [runbook](../../../../../docs/operations/RUNBOOK.md).
