# NORAD pipeline plan

This document owns open package families and package acceptance. Open intent
and selected scope belong to the [task registry](../tasks/README.md), current
evidence ceilings and blockers to [`HANDOFF.md`](../operations/HANDOFF.md),
implemented system views to the [architecture index](../architecture/README.md),
commands to the [`RUNBOOK.md`](../operations/RUNBOOK.md), and rationale to
[`DECISIONS.md`](DECISIONS.md).

## Current state

Current evidence and blockers are not restated here. Use the live
[`HANDOFF.md`](../operations/HANDOFF.md); implemented structure and exact source
ownership remain with the [architecture index](../architecture/README.md) and
its routed owners.

## Open package families

The accepted local-pilot architecture is defined by
[`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md), and the canonical
owner-admission dispositions are tracked in
[`ORCHESTRATION_READINESS.md`](ORCHESTRATION_READINESS.md). The unselected
implementation dependency order is:

```text
ORCH-03A + SETUP-03A + INTAKE-03A
                  -> PROFILE-03A -> CLI-03A -> E2E-03A -> ONBOARD-03A
```

These relationships do not select work. Backlog blockers record only
unavailable technical outputs.

## Local-pilot package order

Campaign B proceeds in proof-sized packages. Each package ends with focused
evidence; the full-pipeline gate waits until the assembled local profile
exists.

| Package | Outcome | Stop boundary |
| --- | --- | --- |
| `B1a` | Harden and prove the reference branch (`00a`, `00b`, `00c`) through direct public commands, without adding Snakemake. | Stop if reference materialization ownership or safe publication is unresolved. |
| `B1b` | Harden one owner at a time through the one-sample `01`–`06` spine, then `02b` and `03`, using existing focused owner tests. | Stop at the first ambiguous partial/backup/lock state; do not centralize recovery or execute real tools. |
| `B1c` | Harden cohort owners `07` and `08`; confirm `09` meets the shared admission proof without changing its scientific method. | Stop before Step `09c`, scientific review, or evidence promotion. |
| `B2` | Add the isolated `uv` workflow dependency group, versioned machine contracts, request normalizer, reporting projection, and semantic all-pass checker. | Stop before workflow rules or dependency installation by runtime commands. |
| `B3` | Materialize the static local profile and prove direct Snakemake dry-run, then a test-double walking skeleton in reference, one-sample, and cohort slices. | Stop before the public lifecycle CLI or real science-tool claims. |
| `B4` | Add artifact-index, run-summary, and Jinja HTML-report rules, then prove failure, interruption, clean-boundary resume, and inspection. | Step `09c` remains explicit and absent; no SLURM/VM/CSU claim. |
| `B5` | Add the thin public `run`, `resume`, and `inspect` adapter only after direct Snakemake operation and state semantics are stable. | The adapter owns intake/lifecycle policy only; no private imports or scientific logic. |
| `B6` | Prove the fresh-clone local pilot, then rewrite root onboarding from the exact proven transcript. | One full assembled gate; no cluster, scientific-review, or biological claim. |

Real STAR/GATK/science-tool fixture execution is a separately authorized local
runtime proof after the structural/test-double profile is stable. SLURM and VM
evaluation remains later still.

Reporting remains split across characterization, contract, projection,
usability, and default-profile cards; renderer decomposition is implemented.
Logging, validation
receipts, documentation maintenance, future acquisition/analysis, and
installable-control-plane items remain unselected. Backlog proposals are not
actionable.

## Package acceptance

Every package must:

- remain inside one approved objective and preserve public behavior unless a
  separately authorized decision changes it;
- update directly affected implementation, tests, contracts, and live
  operational documentation;
- preserve deterministic bytes, schemas, exit behavior, validation-before-
  publication, locking, no-clobber rules, rollback, recovery, and evidence
  vocabulary where contracted;
- retain stage-specific semantics unless multiple real consumers and
  independent tests justify a neutral seam;
- label local fixtures, real runtime, cluster execution, scientific review, and
  biological readiness separately; and
- validate in proportion to changed behavior and shared risk.

Documentation-only work must preserve live operational and scientific meaning
and pass the documentation gate. JIT cards and historical records are not live
subject-matter owners: completed detail is deleted, every dependent backlog
edge is repaired atomically, and `docs/history` is maintained separately.

### Local-pilot owner admission

A row in [`ORCHESTRATION_READINESS.md`](ORCHESTRATION_READINESS.md) may move
from `harden` to `ready` only when its owner-local contract and focused tests
prove:

- side-effect-free help and declared dry-run behavior;
- explicit inputs, outputs, commands, tool requirements, and scope identity;
- success plus zero-exit incomplete-output failure;
- existing valid output, partial output, foreign lock, and stale owned residue;
- signal/interruption behavior;
- rollback or fail-closed recovery preservation;
- validator publication and semantic all-pass distinction; and
- safe task-boundary reuse under the orchestration contract.

The final assembled local profile additionally requires one failure/resume E2E
and one clean E2E from a fresh clone. Neither promotes local evidence to
cluster, scientific-review, or biological proof.

## Scientific exit boundary

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
scientific policy defines and satisfies its exit criteria. No local structural
or reporting gate may promote either state.
