# NORAD / CSU HPC agent instructions

This repository supports a local-first, SLURM-scaled RNA-seq and
RNA-editing workflow. Develop it as maintainable research software: explicit
inputs and outputs, reproducible commands, small local tests, useful logs, and
clear evidence boundaries.

Use context and tokens responsibly. Correctness, safety, scientific and
evidence integrity, and effective task completion take priority over token
reduction. When approaches are otherwise equivalent, prefer targeted context,
concise output, and de-duplicated work. Never omit required inspection,
reasoning, validation, evidence, or user communication solely to save tokens.

Current project state belongs in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md). The authoritative
roadmap and status matrix belong in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).

## Required task start

Begin each selected card or other explicitly bounded package in plan/review
mode; a follow-up message within the same uninterrupted package is not a new
task start. Before editing, branching, installing dependencies, or running
mutating commands:

1. apply this file's exact current instructions, reading it from disk when the
   active context does not already contain that version;
2. read [`docs/operations/TASK_START.md`](docs/operations/TASK_START.md) and
   the selected task card, when one exists, in full unless the exact unchanged
   version is already available in the active context;
3. inspect live Git state and use the task-start router to select applicable
   canonical sections and expansion triggers; and
4. inspect the relevant implementation, contracts, consumers, tests, and
   fixtures before proposing changes.

Existing context may replace a reread only when its exact revision is known,
Git proves the relevant content unchanged, and the retained context is
sufficient for the current decision. Phase boundaries require renewed impact,
ownership, interface, and acceptance assessment—not an automatic complete-
corpus read. Broaden immediately for the triggers in `TASK_START.md`. Do not
edit until the user approves the task-specific plan.

Future work may also have a card in [`docs/tasks/`](docs/tasks/). A card
preserves settled constraints, bounded scope, direct dependencies, and required
acceptance evidence; it does not replace the reads and live inspection above,
serve as an implementation plan, or authorize mutation. When the user
explicitly selects a TODO card, move it with `git mv` to `IN_PROGRESS` and
repair inbound links as the status-only start of read-only planning. Obtain
separate approval for the task-specific plan before implementation.
That status/link move is the only permitted repository mutation before the
task-specific plan is approved.

## Development gate

Every implementation package uses a linear descendant branch from the latest
clean, docpatched predecessor:

1. Verify the predecessor is clean, pushed, and upstream-equal.
2. Create the package branch.
3. Implement only that package and directly required contracts.
4. Add focused tests and run one de-duplicated complete applicable local gate
   against the final executable state.
5. Commit implementation and tests.
6. Use the final diff, canonical ownership map, and targeted link/search
   results to identify affected documents and diagrams. Inspect the affected
   sections, their canonical owners, and direct references.
7. Perform a repository-wide documentation impact check. Broaden semantic
   inspection only when the change is cross-cutting, ownership changes, a
   contradiction appears, or the affected scope cannot be bounded safely.
8. Commit the docpatch separately.
9. Run the documentation gate. Do not repeat computational suites when the
   docpatch leaves executable configuration, dependencies, Make targets,
   schemas, fixtures, report templates, and test-harness selection and execution
   semantics unchanged. Require a clean worktree, inspect history, and push.
10. Confirm upstream equality before creating another branch.

If implementation changes after the docpatch, reopen the gate: retest, commit
the correction, and perform another separate docpatch.

A standalone documentation-only package uses one documentation commit. When
its complete predecessor-to-final diff changes only documentation artifacts
that are not consumed by executable, configuration, generation, schema,
fixture, report-template, or test-harness selection or execution behavior,
computational validation is not applicable. Run Git and documentation
validation only; do not fabricate an implementation commit or run
computational Python, shell, R, or report-runtime test suites.

During implementation, use focused tests repeatedly and reserve the complete
computational gate for the final executable state. Pytest is quiet by default
and retains captured output for failures; use the quiet Make and log-capture
commands in `docs/operations/RUNBOOK.md`. Full output is for failures or an
explicit verbose run. A recorded full-gate result may be reused after a
documentation-only patch when Git inspection proves the executable state is
unchanged.

Runtime and cluster promotion are upstream-sequential even when an approved
local-only sequence advances through descendant branches. Never runtime-
promote a downstream stage before its prerequisite runtime gates pass.

Do not merge, rebase, rename, delete, overwrite, or force-push stage branches
without explicit user direction.

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

## Local and cluster safety

Local development should use tiny fixtures, mocks, syntax checks, and explicit
runtime overrides. Do not require full FASTQ, BAM, VCF, or production result
data for local tests.

The cluster login node is for Git operations, small transfers, editing, light
inspection, job submission, and small smoke tests. Heavy alignment, sorting,
mpileup, and analysis must run through `jobs/*.slurm`.

Never commit:

- FASTQ, SAM, BAM, CRAM, VCF, indexes, large tables, logs, or results;
- credentials, tokens, keys, `.env` files, or private data;
- machine-specific runtime libraries, caches, or restored tools.

Tiny synthetic, safe fixtures may be committed.

Do not delete, repair, move, compress, or overwrite shared or production
artifacts without explicit operator intent. Preserve locks and recovery
evidence when cleanup or rollback cannot be proved complete.

## Repository conventions

Use:

```text
scripts/        parameterized workflow and validation scripts
jobs/           thin SLURM wrappers
tests/          active tests and synthetic fixtures
tests/pending/  non-runnable future test plans
configs/        explicit example contracts and configuration
schemas/        versioned public schemas
reports/        report views and styles
docs/           design, operations, architecture, and demo material
```

This is the implemented current layout. The approved target and migration
constraints live only in
[`docs/architecture/FUTURE_ARCHITECTURE.md`](docs/architecture/FUTURE_ARCHITECTURE.md)
until a separately planned migration changes current truth.

Prefer workflow entry points shaped as:

```text
scripts/step_XX_<name>.sh
jobs/step_XX_<name>.slurm
tests/shell/test_step_XX_<name>.sh
```

The manifest is the source of truth for sample metadata. Prefer explicit,
tab-separated manifests and manifest-driven selection. Do not infer pairings,
sample order, or partitions from filenames.

Do not hardcode user- or machine-specific paths in analysis code. Use CLI
arguments, explicit config, environment overrides, and resolved output roots.
Do not discover scientific or report inputs by glob.

## Script and publication conventions

Scripts should:

- accept explicit arguments and provide useful `--help`;
- validate inputs before expensive work;
- print resolved context and exact commands;
- use explicit output paths;
- fail loudly with actionable messages;
- support local fixtures or mocked tools;
- validate outputs before publication;
- avoid hidden global state.

Bash scripts use strict mode, portable syntax, quoted variables, and arrays
where helpful. Python scripts use `argparse`, `pathlib`, a guarded `main`, and
separable parsing, validation, and publication logic. R scripts validate
arguments and avoid hardcoded working directories.

Workflow and SLURM entry points are dry-run-first:

```text
script without --execute -> validate and print only
script with --execute    -> publish
EXECUTE=0                -> SLURM dry-run
EXECUTE=1                -> SLURM execute
other EXECUTE value      -> fail
```

Dry-run must not create final outputs and should avoid creating output
directories when that could confuse validation.

Multi-file outputs use validation-before-publication, owned locks, run-token
staging, stable input rechecks, explicit no-clobber rules, rollback, and a
receipt or summary published last as the transaction marker.

Report renderers consume one explicit validated canonical run summary and only
supplemental tables authorized by exact path, hash, row count, and role.
Rendering never installs software, runs analysis engines, discovers inputs,
or promotes evidence state.

## Runtime and dependency rules

Dependency restoration is an explicit operator action. Compute scripts,
validators, SLURM jobs, report renderers, and tests must not bootstrap or
install R, Quarto, system packages, or analysis dependencies.

The repository-local R environment is opt-in only through
`NORAD_USE_RENV=1`; `0` leaves normal startup unchanged and any other value
must fail. Keep automatic snapshots disabled and review lockfile changes.

Exact setup, execution, validation, and recovery commands belong only in
[`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md).

## SLURM wrappers

SLURM wrappers call scripts rather than embedding analysis logic. They use
strict mode, default to dry-run, log job context and resolved inputs/outputs,
load required modules inside the job, and validate `EXECUTE`.

Capture module output with `module list 2>&1 || true`. Do not add explicit
memory requests unless the relevant cluster contract has been confirmed.

## Documentation responsibilities

Each mutable fact has one canonical owner:

| Document | Responsibility |
| --- | --- |
| `AGENTS.md` | Stable conduct, safety, conventions, evidence language, and gates |
| `README.md` | Concise entry point, purpose, minimal quick start, and repository map |
| `TODO.md` | Short prioritized pending work and current blockers |
| `HANDOFF.md` | Current takeover snapshot and evidence boundary |
| `PIPELINE_PLAN.md` | Pipeline/package/evidence roadmap, status matrix, acceptance criteria, and branch lineage |
| `QUESTIONS.md` | Open operational/scientific questions, open design choices, and a resolved-question index |
| `RUNBOOK.md` | Executable setup, validation, cluster, and recovery commands |
| `TASK_START.md` | Version-aware task-start routing, context freshness, expansion triggers, and documentation-impact selection |
| `DECISIONS.md` | Durable decisions, rationale, alternatives, and consequences |
| `TROUBLESHOOTING.md` | Symptom, cause, diagnosis, and fix |
| `ARCHITECTURE.md` | Current topology, boundaries, contracts, and data flow |
| `FUTURE_ARCHITECTURE.md` | Target architecture and future constraints |
| `docs/tasks/` | Bounded task scope, task-workflow status by directory, direct dependencies, acceptance evidence, and historical completion records |
| Demo documents | Presentation walkthroughs or explicitly dated snapshots |
| Standalone `.mmd` files | Canonical diagram sources |

Do not duplicate live branch names, commit IDs, test totals, tool versions,
roadmaps, or next-step narratives outside their canonical owner. Link instead.
Do not maintain inline copies of standalone Mermaid sources.

After each task, suggest relevant updates to these documents. When behavior
changes, complete the impact-directed docpatch and repository-wide impact
check; update every affected status, interface, command, path, schema,
limitation, diagram, and next-step claim. Update the selected task card and all
inbound links as part of the same docpatch. Durable architectural truth remains
in the canonical owners above, not in the card.

## Biological interpretation caution

Keep library strandedness, read orientation, transcript strand, and biological
sense/antisense interpretation separate. Mechanical read-orientation labels
do not establish biological strand interpretation.

Preserve neutral orientation labels until an approved scientific policy and
evidence gate justify stronger language. Computational success is not a
biological conclusion.

## Engineering standard

Prefer designs that are explicit, boring, portable, testable, debuggable, and
easy to hand off. Avoid broad refactors, orchestration layers, job arrays, or
shared abstractions before stable behavior and evidence justify them.
