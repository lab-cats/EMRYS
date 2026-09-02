# Repository and delivery rationale

## Representation and execution

### Explicit manifests

Use TSV when ordered scientific or evidence records must be inspected by shell,
Python, and R. Exact schemas remain versioned contracts. The scientist-facing
Project YAML references those manifests and owns scientific policy; EMRYS
generates normalized execution and evidence records internally.

### Local development, Slurm production

Small fixtures, focused tests, syntax checks, and read-only inspection run
locally. Heavy scientific work runs only inside an approved allocation through
the whole-Run Slurm placement. Hosted disposable Slurm and CSU Viking require
separate evidence and neither implies production or scientific validity.

### Programs stay out of Markdown

Markdown may show short invocations. Branching, validation, mutation, recovery,
and publication logic belongs in parameterized tested source. A repeated inline
program is either extracted to one owner or explicitly retained when extraction
would increase the maintained surface.

### Active and future tests remain distinct

Runnable regression protection lives with active test owners. Test ideas and
historical scaffolds do not remain in the executable tree after their behavior
is mapped to a current suite or explicitly discarded.

## Reviewable delivery

A bounded change normally has one semantic commit containing implementation,
direct protection, contracts, and affected documentation. Committing,
publishing, running cluster work, deleting evidence, and merging are distinct
authorities unless the user explicitly combines them.

Focused checks provide fast feedback. Run the complete applicable gate against
the final affected state; do not repeatedly run long lanes locally or claim
unselected CI work. Report exactly what ran and preserve distinctions among
static, fixture, real-runtime, scheduler, site, production, scientific-review,
and biological evidence.

Start from live Git, the bounded objective, its owner, and direct consumers.
Broaden context when behavior crosses public, scientific, persistence,
concurrency, recovery, security, provenance, or evidence boundaries. Routine
success output stays concise; failures retain attributable diagnostics.

## Maintainability

- Each functional owner keeps exact behavior, diagnostics, recovery, and direct
  tests beside its implementation. Cross-cutting docs explain relationships,
  not duplicate owner contracts.
- Prefer deletion or caller-complete consolidation to wrappers, registries,
  adapters, generated configuration, and compatibility paths. Large files are
  reviewed for mixed responsibility; line count alone does not justify an
  arbitrary split.
- Coverage is a regression signal, not a replacement for scenario, transaction,
  real-R, runtime, scheduler, numerical-oracle, or scientific review.
- Automate a repository workflow only after repeated use stabilizes its inputs,
  decisions, and safety boundary. Automation never encodes unsettled policy.
- Live Git owns source state. Checks and retained artifacts bound to an exact
  revision own validation observations. The findings matrix owns accepted work.

## Documentation authority and compression

Documentation exists only when it has a clear audience and durable owner:

| Need | Authority |
|---|---|
| Scientist purpose, setup, run, and Results journey | Root [`README.md`](../../../README.md) and [`quickstart.md`](../../../quickstart.md) |
| Operator commands, recovery, dependencies, CI, and site boundaries | [`RUNBOOK.md`](../../operations/RUNBOOK.md) and [`TROUBLESHOOTING.md`](../../operations/TROUBLESHOOTING.md) |
| Current system relationships | [`ARCHITECTURE.md`](../../architecture/ARCHITECTURE.md) |
| Exact owner behavior | Owner-local `CONTRACT.md`, schemas, implementation, and direct tests |
| Durable rationale and safety rules | [`DECISIONS.md`](../DECISIONS.md) and its focused decision records |
| Scientific identities and import direction | [`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md) and [`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| Accepted work and acceptance | [`backlog_matrix.md`](../../tasks/backlog_matrix.md) |
| Dated validation observations | Compact records under [`docs/history`](../../history/) or retained artifacts |

The 2026-09-02 repository-wide audit applied these rules to every tracked
Markdown file. At this recorded boundary, the maintained set fell from 163
files and 17,929 lines to 80 files and 5,711 lines. Those figures are observed
outcomes, not deletion quotas. It retired the temporary campaign and ranking,
legacy handoff/readiness pages, duplicate cross-cutting orchestration contract,
redundant directory and private-package indexes, routine test READMEs, and
placeholder workspace placards. Durable campaign decisions moved into the
architecture and decision records; unique dated handoff observations moved to
[`validation-evidence.md`](../../history/validation-evidence.md); active work
moved into the scored findings matrix. Detailed source-to-destination ledgers,
completed-package chronology, superseded options, and deleted bytes remain in
Git history rather than a second permanent documentation system.

This audit intentionally preserves concise prose for intent, rationale, trust
boundaries, non-goals, evidence meaning, and recovery. Machine-verifiable
schemas and behavior should be referenced, generated, or tested instead of
copied into Markdown. Implementation code does not become its own independent
specification, and direct conformance protection remains required.
