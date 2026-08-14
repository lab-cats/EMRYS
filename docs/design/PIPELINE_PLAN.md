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
[`ORCHESTRATION_READINESS.md`](ORCHESTRATION_READINESS.md). Campaign B and its
adversarial local-pilot hardening follow-up have no remaining implementation
dependency. The selected
[`PORT-NC-01`](../tasks/cards/PORT-NC-01-fix-no-clobber-integration.md) package
replays only current-compatible behavior from `fix/no-clobber`; it does not
broaden scientific or execution scope. Future real-runtime and site/cluster work
requires separate selection and authorization; no such package is selected
here.

## Local-pilot package order

Campaign B proceeded in proof-sized packages. `B1a` through `B6` are complete:
functional owners expose fail-closed local workflow boundaries; dependency
metadata, machine contracts, read-only normalization/reporting projection, and
semantic all-pass checking exist; and the fixed local-CMH profile now has an
exact static Snakemake projection with content-bound task records, three
semantically revalidated reporting transactions, and an internal immutable
attempt/producer-entry/resume/inspection lifecycle. The read-only doctor binds
one normalized request, workspace plan, clean checkout, locked workflow engine,
science tools, Picard jar, guarded `renv`, and Step `08` namespaces without
installing or creating state. The B5 adapter materializes the fixed profile
under the run lock and exposes dry-run-first public run, resume, and inspection
commands without raw engine controls. B6 proves the separate clean-success and
controlled failure/resume journeys from a clean fresh clone with no-science
collaborators and publishes onboarding from that observed path.

| Package | Outcome | Stop boundary |
| --- | --- | --- |
| `B3` — complete | Materialize the static local profile and prove direct Snakemake dry-run, then a test-double walking skeleton in reference, one-sample, and cohort slices. | No public lifecycle CLI or real science-tool claim was added. |
| `B4` — complete | Add artifact-index, run-summary, and Jinja HTML-report rules, durable producer-entry ledgers, then prove failure, interruption, between-task resume, and inspection. | Entered-but-incomplete scopes require future explicit reconciliation; Step `09c` remains explicit and absent; no public lifecycle CLI, real-tool, SLURM, VM, or CSU claim was added. |
| `B5` — complete | Add the read-only doctor, fixed-profile production materializer, and thin public `run`, `resume`, and `inspect local-pilot-run` adapter over B2 intake and the B4 lifecycle. Prove dry-run no-write, locked attempt publication, controlled failure, byte-preserving between-task resume, complete refusal, and derived inspection with no-science owners. | The adapter owns intake/lifecycle policy only; it installs nothing, imports no private owner, exposes no raw engine controls, and adds no real-tool, SLURM, cluster, scientific-review, or biological claim. |
| `B6` — complete | Prove the fresh-clone local pilot, then rewrite root onboarding from the exact proven transcript. | The proof uses deterministic no-science collaborators; it adds no real-tool, cluster, scientific-review, or biological claim. |
| Adversarial local-pilot hardening — complete | Bind runtime and immutable evidence completely, admit safe external sidecar reuse, serialize attempt entry, and terminalize interruption only after child-process quiescence. | The proof remains local and deterministic; it adds no real-tool, distributed-filesystem, SLURM, cluster, scientific-review, or biological claim. |

Real STAR/GATK/science-tool fixture execution remains a separately authorized
local-runtime decision. SLURM, VM, and site-profile evaluation are separate
unselected decisions.

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
