# Repository and delivery decisions

These decisions govern how maintainers change NORAD. Exact commands belong in
the [`RUNBOOK`](../../operations/RUNBOOK.md), current task mechanics in
[`TASK_DELIVERY.md`](../../operations/TASK_DELIVERY.md), and current state in
the task registry and handoff.

## Repository conventions

### Use TSV manifests

Use tab-separated manifests for sample, partition, inventory, approval, and
evidence tables. TSV remains easy to inspect consistently from shell, Python,
and R, so exact headers and row order are public contracts. A future YAML run
request may carry policy while referencing a TSV sample manifest.

### Develop locally and scale through SLURM

Editing, fixtures, mocks, and syntax checks run locally; heavy production
computation runs through SLURM. Heavy work does not run on the login node.

### Keep executable programs out of Markdown

Markdown may show short invocations, but branching, validation, mutation,
recovery, and publication logic belongs in parameterized, tested source files.
Documentation explains authority, sequence, inputs, outputs, and
interpretation and links to the executable owner.

### Keep active and future tests separate

Runnable tests live in active test owners. Non-runnable plans remain explicitly
separate and are not wired into validation targets.

### Treat legacy scripts as protocol references

Translate useful legacy behavior into parameterized, tested interfaces. Do not
preserve hardcoded paths, samples, or undocumented assumptions merely because
they existed in an old script.

## Reviewable delivery

### Use descendant branches and separate docpatch gates

The default delivery protocol maintains one linear, attributable Git lineage
and keeps an executable state and its documentation close as separate
reviewable commits. Documentation-only work does not need an artificial
executable checkpoint, and an approved campaign may sequence bounded cards on
one branch. Exact branch and commit procedure is owned by
[`TASK_DELIVERY.md`](../../operations/TASK_DELIVERY.md).

### Permit isolated concurrent authoring with serialized integration

Concurrent mutation uses isolated branches and worktrees with bounded write
sets. One authoritative integration lane serializes candidates and validates
their combined state. A candidate is a proposal, not authorization, current
state, or evidence. Detailed roles and recovery belong in
[`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md).

### Use transient integration fragments for cross-owner proposals

An isolated candidate may request a canonical-owner change through one
structured transient fragment. The fragment grants no authority; the
integration owner verifies its source, gives every request and residual a
terminal disposition, routes accepted meaning, and removes the fragment before
publication. This preserves provenance without creating a shadow archive.

### Run one complete computational gate per executable state

Use focused tests during implementation and one complete applicable gate on the
final executable state. Reuse that evidence for a documentation-only close only
when Git proves that no executable, dependency, test, schema, fixture,
template, or gate semantics changed. A non-consuming documentation change needs
only its Git and documentation checks.

### Prefer failure-first validation output

Routine success stays concise; failures and explicit verbose runs retain full,
attributable diagnostics. Parallel defaults require exact result and coverage
parity, measured benefit, bounded cleanup, pinned dependencies, and a
deterministic serial fallback. Historical tuning measurements are not ongoing
performance guarantees.

### Route task context by revision and impact

Start from live Git state, the selected task, its bounded surfaces, and the
applicable canonical sections. Reuse context only when its revision is known
and unchanged. Contradictions or unbounded scientific, evidence, safety,
recovery, publication, ownership, or public-contract impact broaden inspection;
a phase boundary alone does not require a full-corpus read.

### Use proportional planning categories and bounded approval envelopes

Classify semantic planning and validation impact independently. Tests follow
affected contracts and risk rather than topic labels. One explicit approval may
cover routine work inside a fixed objective, write set, evidence boundary,
exclusions, and stop conditions; scope expansion requires new authority.

### Make documentation consistency impact-directed

Use the final diff, canonical ownership, inbound references, targeted searches,
and the structural documentation gate to find affected documentation. Broaden
manual review for cross-cutting, contradictory, ownership-changing, or
unbounded impact rather than rereading the whole corpus by default.

## Maintainability controls

### Measure Python coverage without replacing scenario gates

Measure line and branch coverage across the complete Python suite and configured
subprocesses against a deterministic reviewed baseline. Reject ratio
regressions and removed modules; new shared Python modules start at 90% line and
85% branch coverage. Coverage does not replace independent scenarios, public
contract checks, real-R tests, cluster execution, or scientific review.

### Documentation ownership

Each information category has one canonical owner in
[`DOCUMENTATION_OWNERSHIP.md`](../../sitemap/DOCUMENTATION_OWNERSHIP.md).
Documents link instead of copying mutable state, commands, identities, counts,
or diagrams. Unique meaning must be discoverable at its destination before an
old copy is removed; purposeful action-point safety repetition may remain.

### Treat documentation and maintainer context as architecture

Use shallow parent READMEs and detailed local owner documentation so routine
work can remain bounded. Headers own purpose and interfaces; comments explain
non-obvious rationale, scientific limits, safety, and recovery. Correctness and
discoverability outrank compression, and operational prose links tested
programs instead of embedding them.

### Apply risk-based source-size thresholds

A materially changed file above 600 lines receives a cohesion review, and new
files normally remain below 600. A file above 1,000 lines needs a decomposition
plan or explicit justification before architectural mutation. During the
active repo-spanning refactor, a file above 1,500 lines must be eliminated
unless the owner approves an explicit exception. Split by responsibility and
scenario, never by arbitrary line count.

### Defer repository skills until the underlying practice is proven

Automate a workflow as a repository skill only after repeated use has stabilized
its judgment, inputs, and safety boundary. A skill must not become another
unowned checklist or encode unsettled policy.
