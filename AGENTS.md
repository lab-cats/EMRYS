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
package acceptance in [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md), exact commands in
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
authorize mutation or replace live inspection and an approved plan. Selection
and ordinary execution are transient work context, not card lifecycle states:
do not move a card or create a status-only commit when work is selected,
paused, resumed, accepted, or declined. Keep surviving cards at their existing
paths and delete a card when it is completed or retired; do not maintain a
completed-card archive or repair surviving cards merely because old targets
disappear. Rules remain in the [`task registry`](docs/tasks/README.md).
`UNREFINED` proposals cannot be selected.

## Git authority

Use one authoritative mutable worktree and branch at a time. Inspect other
worktrees read-only unless the user explicitly changes the authority boundary.
Do not share a mutable worktree or branch between actors.

Do not merge, rebase, rename, delete, overwrite, or force-push stage branches
without explicit user direction.

## Package delivery guard

Follow the [`package-delivery procedure`](docs/operations/TASK_DELIVERY.md#default-delivery)
and the exact [`RUNBOOK.md` gate](docs/operations/RUNBOOK.md#local-validation-gate).
Implement only the approved package. Default to one semantic commit per
package or slice containing its implementation, tests, directly affected
canonical documentation, and any real lifecycle change. Use focused checks as
useful feedback, then run one de-duplicated complete applicable gate on the
final combined tranche state. Re-run a gate only when later changes invalidate
its evidence.

A qualifying standalone documentation-only package uses one documentation
commit and Git/documentation validation without computational Python, shell, R,
report-runtime, full-suite, or cluster validation. Runtime and cluster
promotion remain upstream-sequential. Publication is a separate authorized
action: batch pushes at a coherent tranche boundary by default, then prove the
published ref and upstream equality once. Never promote a downstream stage
before its prerequisite runtime gates pass.

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
mpileup, and analysis must run through the applicable owner-local `.slurm`
entry point under `src/norad/{stages,analyses,evidence,ingestion}/`. The
[functional-owner inventory](docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md)
owns the exact current job roster.

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

Each mutable fact has one canonical live owner. Preserve operative contracts,
defects, safety rules, and evidence ceilings before removing an owner; task
cards and immutable history are not live path-repair obligations. Retain
intentional action-point safety repetition. Do not duplicate live branch names,
commit IDs, test totals, tool versions, roadmaps, or next-step narratives.
Ownership boundaries remain in the
[`ownership map`](docs/sitemap/DOCUMENTATION_OWNERSHIP.md), while documentation
impact and card close follow [`TASK_START.md`](docs/operations/TASK_START.md)
and [`TASK_DELIVERY.md`](docs/operations/TASK_DELIVERY.md).

The implemented repository map belongs in [`README.md`](README.md#repository-map).
Target principles remain in
[`FUTURE_ARCHITECTURE.md`](docs/architecture/FUTURE_ARCHITECTURE.md); exact
target homes and dependency direction remain in
[`SOURCE_TOPOLOGY.md`](src/norad/contracts/SOURCE_TOPOLOGY.md). Target
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
