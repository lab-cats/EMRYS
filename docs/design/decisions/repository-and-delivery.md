# Repository and delivery decisions

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

Keep implementation, direct tests, contracts, and affected documentation in
one reviewable change so a reviewer can assess the complete behavior. The
[workflow](../../operations/WORKFLOW.md) defines approval, verification, and
delivery steps. Approval of a code change does not by itself authorize cluster
work, evidence deletion, or merging.

Focused local checks provide fast feedback; applicable final checks establish
what was verified. Long checks belong in CI. Report the actual revision and
evidence level, and retain useful failure diagnostics.

### Validation tools

`uv` owns the Python environment. Nox was considered and rejected: preserving
the existing process-group cancellation and retained failure diagnostics would
require a larger custom supervisor. The [test baseline](../TEST_BASELINE.md)
owns validation policy; [Engineering](../../operations/ENGINEERING_CONVENTIONS.md#development-validation)
owns the commands.

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
  revision own validation observations. The findings matrix routes accepted work
  to its authoritative backlog.

## Documentation authority and compression

Documentation exists only when it has a clear audience and durable owner:

| Need | Authority |
|---|---|
| Scientist purpose, setup, run, and Results journey | Root [`README.md`](../../../README.md) and [`quickstart.md`](../../../quickstart.md) |
| Operator commands, recovery, and site boundaries | [`RUNBOOK.md`](../../operations/RUNBOOK.md) and [`TROUBLESHOOTING.md`](../../operations/TROUBLESHOOTING.md) |
| Development, dependencies, tests, and CI | [`ENGINEERING_CONVENTIONS.md`](../../operations/ENGINEERING_CONVENTIONS.md) and [`TEST_BASELINE.md`](../TEST_BASELINE.md) |
| Current system relationships | [`ARCHITECTURE.md`](../../architecture/ARCHITECTURE.md) |
| Exact owner behavior | Owner-local `CONTRACT.md`, schemas, implementation, and direct tests |
| Durable rationale and safety rules | [`DECISIONS.md`](../DECISIONS.md) and its focused decision records |
| Scientific identities and import direction | [`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md) and [`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| Accepted work and acceptance | [`backlog_matrix.md`](../../tasks/backlog_matrix.md) |
| Dated validation observations | Compact records under [`docs/history`](../../history/) or retained artifacts |

Do not preserve routine progress, branch names, audit totals, completed-work
chronology, or source-to-destination ledgers in permanent documentation; Git
history already owns that information. Keep concise prose for purpose,
rationale, trust boundaries, non-goals, evidence meaning, and recovery.
Reference schemas and tests instead of copying machine-checkable details into
Markdown. Source code is not an independent specification, and direct contract
tests remain required.
