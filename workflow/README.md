# Local CMH workflow projection

This directory contains NORAD's fixed, source-checkout-bound Snakemake
projection. It schedules public functional owners; it does not implement their
science, infer work from filenames, or treat Snakemake metadata as completion
evidence.

## Directory map

| Path | Purpose |
| --- | --- |
| [`Snakefile`](Snakefile) | Static scheduling projection for the supported local CMH graph and its reporting tail. |
| [`contracts/`](contracts/README.md) | Reviewed workflow-projection instances that select owners, scopes, edges, and reportable artifacts. |
| [`profiles/`](profiles/README.md) | Snakemake engine settings selected by NORAD's lifecycle. |

The canonical semantic owner identities and artifact edges live in
[`STAGE_MAP.md`](../src/norad/contracts/STAGE_MAP.md). Exact workflow-profile
validation belongs to the
[`contracts/orchestration`](../src/norad/contracts/orchestration/README.md)
owner. Functional behavior, native outputs, validation, and recovery remain
with each stage, analysis, or evidence owner.

## How execution enters

The supported flow is:

```text
norad run / norad resume
  -> request admission and lifecycle materialization
  -> fixed Snakefile plus checkout-bound local engine profile
  -> public owner producers and validators
  -> artifact index, run summary, and report bundle
```

The lifecycle materializes an immutable attempt-specific configuration and
dispatch for every expected owner/scope pair. The Snakefile invokes those
bound public owners and declares only their verified records. Native scientific
outputs, locks, receipts, and rollback remain owner-controlled rather than
becoming generic Snakemake outputs.

Verified task and reporting records are reusable only after NORAD re-admits
their canonical identities, bound evidence, and semantic transactions. A path,
timestamp, process exit, `.snakemake` entry, or receipt name alone is not
completion authority. The local-pilot
[`README`](../src/norad/orchestration/local_pilot/README.md) and
[`CONTRACT`](../src/norad/orchestration/local_pilot/CONTRACT.md) own the exact
state, recovery, and resume rules.

## Fixed projection

The Snakefile projects fourteen executable scientific and evidence owners.
Steps `02b` and `03` are required evidence leaves of a complete run but do not
gate downstream scientific computation. After the owner graph completes, the
workflow runs the artifact-index, run-summary, and report transactions in
order. Reporting consumes only explicit admitted inputs and never reruns an
analysis.

The checked-in projection instance is
[`contracts/local_cmh_v2.json`](contracts/local_cmh_v2.json). The lifecycle
binds its exact canonical bytes into the run and expands its declared scopes;
the Snakefile separately checks that it matches the supported static graph.

## Reviewable targets

Three bounded review slices expose smaller input-only closures without changing
owner dependencies:

- `reference_slice`: reference preparation;
- `one_sample_slice`: reference preparation plus one declared sample; and
- `cohort_slice`: the complete scientific/evidence owner graph.

The default `local_pipeline_slice` adds the ordered reporting tail. These
targets support review and deterministic tests; they are not alternate
scientific profiles.

## Execution boundary

[`profiles/local/profile.v9+.yaml`](profiles/local/profile.v9+.yaml) runs every
Snakemake job on one host. The admitted request supplies total workflow cores,
sample concurrency, and owner thread counts. A workstation or one allocated
Slurm node may be that host, but this is not a distributed or Slurm-executor
profile.

Operators use `norad run` and `norad resume`; bare Snakemake invocation and ad
hoc configs are unsupported. Standalone stage execution remains supported
through each functional owner's direct command and owner-local scheduler entry
point. See the [Runbook](../docs/operations/RUNBOOK.md) for cross-cutting
operator routes.
