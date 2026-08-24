# Local Snakemake execution profile

[`profile.v9+.yaml`](profile.v9+.yaml) supplies conservative engine defaults
for EMRYS's fixed one-host workflow. It selects Snakemake's local executor,
uses a deterministic scheduling baseline, disables engine retries, preserves
incomplete-output evidence, and exposes commands and failed logs.

The admitted request and attempt supply total workflow cores, sample
concurrency, and thread counts for capable owners. Those resource values do not
change scientific identity.

“Local” means every Snakemake job runs on the same host or allocation. This is
not a Slurm submission profile. Full-pipeline scheduled execution enters
through the lifecycle-generated one-allocation wrapper; standalone scientific
stages retain their owner-local scheduler entry points.

Materialization selects this exact checkout file and lifecycle passes it to
Snakemake. Operators should use `emrys run` and `emrys resume`, not invoke the
profile directly. See the parent [workflow overview](../../README.md), the
[local-pilot owner](../../../src/emrys/orchestration/local_pilot/README.md), and
the [Runbook](../../../docs/operations/RUNBOOK.md).
