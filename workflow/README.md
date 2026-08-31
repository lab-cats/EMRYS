# Local CMH workflow projection

This directory contains EMRYS's fixed, source-checkout-bound Snakemake
projection. It schedules public functional owners; it does not implement their
science, infer work from filenames, or treat Snakemake metadata as completion
evidence.

## Directory map

| Path | Purpose |
| --- | --- |
| [`Snakefile`](Snakefile) | Static scheduling projection for the supported local CMH scientific graph. |
| [`contracts/`](contracts/README.md) | Reviewed workflow-projection instances that select owners, scopes, edges, and reportable artifacts. |
| [`profiles/`](profiles/README.md) | Snakemake engine settings selected by EMRYS's lifecycle. |

The canonical semantic owner identities and artifact edges live in
[`STAGE_MAP.md`](../src/emrys/contracts/STAGE_MAP.md). Exact workflow-profile
validation belongs to the
[`contracts/orchestration`](../src/emrys/contracts/orchestration/README.md)
owner. Functional behavior, native outputs, validation, and recovery remain
with each stage, analysis, or evidence owner.

## How execution enters

The supported flow is:

```text
emrys run [--through processing] / emrys resume
  -> Project admission and lifecycle materialization
  -> fixed Snakefile plus checkout-bound local engine profile
  -> plan-selected public owner producers and validators through cohort_slice
  -> terminal scientific Attempt receipt and released Run lock
  -> downstream reporting for a full Run; not applicable to a processing Run
```

The default `emrys run` behavior remains the complete Steps `00`–`10` Analysis.
`emrys run --through processing` instead creates a distinct immutable Run whose
successful boundary is the evidence-complete, all-sample Steps `00`–`06`
closure. That closure is 31 owner tasks for the four-sample synthetic fixture.
Reporting is not applicable, and the successful Run is complete rather than
resumable. This slice establishes only the processing/future-reuse boundary.
A future downstream Analysis would require a new Run, but compatible cross-Run
reuse and downstream launch remain unimplemented ANALYSIS-01 work.

The lifecycle materializes an immutable attempt-specific configuration and
dispatch for every expected owner/scope pair. The Snakefile invokes those
bound public owners and declares only their verified records. Native scientific
outputs, locks, receipts, and rollback remain owner-controlled rather than
becoming generic Snakemake outputs.

Within one Run's Attempt chain, verified task records are reusable only after
EMRYS re-admits their canonical identities and bound evidence. Reporting is a
separate post-Attempt operation:
it reuses only a fully validated report set, generates only into exactly empty
reporting state, and fails closed on partial or ambiguous state. A path,
timestamp, process exit, `.snakemake` entry, or receipt name alone is not
completion authority. The local-pilot
[`README`](../src/emrys/orchestration/local_pilot/README.md) and
[`CONTRACT`](../src/emrys/orchestration/local_pilot/CONTRACT.md) own the exact
state, recovery, and resume rules.

## Fixed projection

The Snakefile projects fourteen executable scientific and evidence owners.
Steps `02b` and `03` are required evidence leaves of a complete run but do not
gate downstream scientific computation. The default backend target is
`cohort_slice`; reporting is not a Snakemake rule or scientific stage.

The checked-in projection instance is
[`contracts/local_cmh_v2.json`](contracts/local_cmh_v2.json). The lifecycle
binds its exact canonical bytes into the run and expands its declared scopes;
the Snakefile separately checks that it matches the supported static graph.

## Reviewable targets

Two bounded review slices expose selected closures without changing
owner dependencies:

- `reference_slice`: reference preparation;
- `cohort_slice`: the plan-selected scientific/evidence owner graph and default
  backend target. Without `--through processing`, it remains the complete graph.

These targets support review and deterministic tests; they are not alternate
scientific profiles. The public processing boundary is selected through the
immutable Execution Plan, not by invoking a raw target. The former composite
`local_pipeline_slice` is retired.

## Execution boundary

[`profiles/local/profile.v9+.yaml`](profiles/local/profile.v9+.yaml) runs every
Snakemake job on one host. The immutable Execution Plan and Attempt-local
resolution supply total workflow cores, sample concurrency, and owner thread counts. A workstation or one allocated
Slurm node may be that host, but this is not a distributed or Slurm-executor
profile.

Operators use `emrys run` and `emrys resume`; bare Snakemake invocation and ad
hoc configs are unsupported. Standalone owner commands remain expert direct
routes, while supported scheduler placement belongs to the grouped whole-Run
transport. See the [Runbook](../docs/operations/RUNBOOK.md) for cross-cutting
operator routes.
