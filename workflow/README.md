# Workflow projection

This directory contains the private Snakemake projection selected by the EMRYS
Run lifecycle. Snakemake schedules admitted functional owners; it does not own
their science, infer work from filenames, admit completion, or define public
configuration.

Planning combines the reviewed common-processing base
[`contracts/local_cmh_v2.json`](contracts/local_cmh_v2.json) with one admitted
analysis-module descriptor and binds the canonical result into the immutable
Run. [`Snakefile`](Snakefile) checks and schedules that exact owner/scope graph.
The base is neither a complete Run profile nor an installed-module registry.

A full Run executes the common graph through Step `08`, the selected module's
Step `09`, and its optional Step `10`, followed by reporting outside Snakemake.
`emrys run --through processing` instead closes after evidence-complete Steps
`00`–`06`; a distinct downstream Run may reuse that compatible immutable
processing result. Reporting is not a scientific stage.

The checked-in [`local engine profile`](profiles/local/profile.v9+.yaml) runs
all jobs on one host. That host may be a workstation or one Slurm allocation;
the profile is not a distributed or Slurm executor. Run planning supplies its
capacity and task resource values.

Operators enter through `emrys run` and `emrys resume`, never bare Snakemake or
these internal files. Canonical owner identities and edges are defined by
[`STAGE_MAP.md`](../src/emrys/contracts/STAGE_MAP.md); exact materialization,
completion, reuse, reporting, recovery, and resume rules belong to the
[run-coordinator contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md).
