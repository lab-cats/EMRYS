# NORAD / CSU HPC agent instructions

This repository supports a local-first, SLURM-scaled RNA-seq and RNA-editing
workflow. Develop it as maintainable research software: explicit inputs and
outputs, reproducible commands, small local tests, useful logs, and clear
evidence boundaries.

Use context and tokens responsibly. Correctness, safety, scientific and
evidence integrity, and effective task completion take priority over token
reduction. When approaches are otherwise equivalent, prefer targeted context,
concise output, and de-duplicated work. Never omit required inspection,
reasoning, validation, evidence, or user communication solely to save tokens.

Current state belongs in [`HANDOFF.md`](docs/operations/HANDOFF.md), roadmap and
status in [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md), exact commands in
[`RUNBOOK.md`](docs/operations/RUNBOOK.md), and documentation ownership in the
[`ownership map`](docs/sitemap/DOCUMENTATION_OWNERSHIP.md).

## Task approval and routing

Begin each selected card or other explicitly bounded package in plan/review
mode. A follow-up within the same uninterrupted package is not a new task start.
Before editing, branching, installing dependencies, or running any mutating
command:

1. apply this file's exact current instructions;
2. read [`TASK_START.md`](docs/operations/TASK_START.md) and the selected card,
   when one exists, in full unless Git proves the retained versions exact and
   sufficient;
3. inspect live Git state and use the task-start router to select canonical
   sections and expansion triggers; and
4. inspect the bounded affected implementation, contracts, consumers, tests,
   and fixtures, propose the task-specific plan, and obtain user approval.

Phase boundaries require renewed impact, ownership, interface, and acceptance
assessment, not an automatic complete-corpus read. Broaden for the triggers in
`TASK_START.md`.

A card preserves scope, dependencies, and acceptance evidence; it does not
authorize mutation or replace live inspection and an approved plan. When the
user explicitly selects a TODO card, the integration owner may move it with
`git mv` to `IN_PROGRESS` and repair inbound links as the only status-only
mutation before plan approval. That move begins read-only planning only. Task
lifecycle rules remain in the [`task registry`](docs/tasks/README.md).
`UNREFINED` proposals cannot be selected. A card in `INTEGRATION_REVIEW` is
frozen: only review/integration may continue there, and correction authoring
requires an integration-owner move back to `IN_PROGRESS` first.

## Concurrent work and Git authority

Concurrent mutation must follow
[`CONCURRENT_WORK.md`](docs/operations/CONCURRENT_WORK.md). Verify the assigned
absolute worktree, base, packet, write set, and branch or detached execution
state. Agent identity is not filesystem isolation. Never share a mutable
worktree, branch, card ID, or path across lanes; use one canonical integration
lane, at most one implementation-candidate or immutable-execution lane, and
only disjoint documentation/card sidecars.

Candidate state is proposal state. Only the integration owner updates canonical
status, priority, lineage, lifecycle, completion, or evidence and serializes
accepted changes into canonical history. Coupled documentation cannot land
independently. Final validation applies to the combined canonical tree, and
execution evidence remains bound to its recorded commit and declared inputs.

Do not provision the first active delivery lane until `HANDOFF.md` records the
required post-`CONCURRENCY-01` strategy discussion as complete. When concurrent
lanes depend on durable packets, one special documentation-only coordination
commit may record those packets and directly required status links before the
ordinary implementation/documentation-patch sequence. Validate, push, and prove
that checkpoint upstream-equal; it does not establish implementation or
completion evidence. Detailed procedure remains in `CONCURRENT_WORK.md` and
exact integration commands remain in `RUNBOOK.md`.

Do not merge, rebase, rename, delete, overwrite, or force-push stage branches
without explicit user direction.

## Package delivery guard

Follow the [`package-delivery procedure`](docs/operations/TASK_DELIVERY.md#package-delivery)
and the exact [`RUNBOOK.md` gate](docs/operations/RUNBOOK.md#local-validation-gate).
Use a clean descendant of the latest clean documentation-patched predecessor,
implement only the approved package, run the complete applicable gate against
the final executable state, and keep implementation/tests separate from the
impact-directed documentation patch. Executable change after that patch
reopens the sequence.

A qualifying standalone documentation-only package uses one documentation
commit and Git/documentation validation without computational Python, shell, R,
report-runtime, full-suite, or cluster validation. Runtime and cluster
promotion remain upstream-sequential; never promote a downstream stage before
its prerequisite runtime gates pass.

## Evidence language

Keep these states distinct:

- implemented locally
- locally fixture-tested
- real-runtime tested
- runtime validation blocked
- cluster dry-run validated
- cluster-proven
- scientific evidence incomplete
- `science_review_complete_exploratory`
- `biological_interpretation_ready`

Never claim cluster proof without inspected scheduler state, logs, validation
commands, and outputs. Tool availability, a dry-run, mocked tests, or local
runtime tests are not cluster proof.

Never treat schema validation, artifact indexing, transaction completion,
report generation, or PI review as computational proof, completed scientific
review, or biological validation.

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
scientific policy defines and unlocks its exit criteria. Tools must reject an
unauthorized ready-state request.

Use “CMH-ranked candidates,” not “validated editing sites.”

## Local, cluster, and data safety

Local development should use tiny fixtures, mocks, syntax checks, and explicit
runtime overrides. Do not require full FASTQ, BAM, VCF, or production result
data for local tests.

The cluster login node is for Git operations, small transfers, editing, light
inspection, job submission, and small smoke tests. Heavy alignment, sorting,
mpileup, and analysis must run through `jobs/*.slurm`.

Never commit:

- FASTQ, SAM, BAM, CRAM, VCF, indexes, large tables, logs, or results;
- credentials, tokens, keys, `.env` files, or private data; or
- machine-specific runtime libraries, caches, or restored tools.

Tiny synthetic, safe fixtures may be committed.

Do not delete, repair, move, compress, or overwrite shared or production
artifacts without explicit operator intent. Preserve locks and recovery
evidence when cleanup or rollback cannot be proved complete.

## Execution, publication, and dependency safety

Apply the neutral
[`engineering conventions`](docs/operations/ENGINEERING_CONVENTIONS.md) to new
or changed work. The
[`functional-owner inventory`](docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md)
and colocated contracts remain authoritative for current legacy exceptions.
Inspect a supported dry-run before execution, and never publish final artifacts
from dry-run.

Multi-file publication preserves validation-before-publication, owned locks
and staging, stable-input checks, explicit no-clobber rules including any
owner-contract-authorized replacement boundary, rollback, recovery, and
receipt-or-summary-last completion. Report rendering uses only explicit
validated inputs and never installs tools, runs analysis, discovers inputs, or
promotes evidence state.

Dependency restoration is an explicit operator action. Compute scripts,
validators, SLURM jobs, report renderers, and tests must not bootstrap or
install R, Quarto, system packages, or analysis dependencies.

## Documentation and topology routes

Each mutable fact has one canonical owner. Move unique information before
removing its old copy, repair links in the same change, and retain intentional
action-point safety repetition. Do not duplicate live branch names, commit IDs,
test totals, tool versions, roadmaps, or next-step narratives; link instead.
Detailed ownership and no-loss dispositions remain in the
[`ownership map`](docs/sitemap/DOCUMENTATION_OWNERSHIP.md), while documentation
impact and card close follow [`TASK_START.md`](docs/operations/TASK_START.md)
and [`TASK_DELIVERY.md`](docs/operations/TASK_DELIVERY.md).

The implemented repository map belongs in [`README.md`](README.md#repository-map).
Target principles remain in
[`FUTURE_ARCHITECTURE.md`](docs/architecture/FUTURE_ARCHITECTURE.md); exact
target homes and migration mechanics remain in
[`SOURCE_TOPOLOGY.md`](src/norad/contracts/SOURCE_TOPOLOGY.md) and
[`MIGRATION_MECHANICS.md`](src/norad/contracts/MIGRATION_MECHANICS.md). Target
architecture is not implemented current truth.

## Biological interpretation caution

Keep library strandedness, read orientation, transcript strand, and biological
sense/antisense interpretation separate. Mechanical read-orientation labels do
not establish biological strand interpretation.

Preserve neutral orientation labels until an approved scientific policy and
evidence gate justify stronger language. Computational success is not a
biological conclusion.

## Engineering standard

Prefer designs that are explicit, boring, portable, testable, debuggable, and
easy to hand off. Avoid broad refactors, orchestration layers, job arrays, or
shared abstractions before stable behavior and evidence justify them.
