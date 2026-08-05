# DOC-CONS-08G — Consolidate demo views

## Objective

Keep distinct walkthrough and PI discussion value while consolidating shared
product/report prose and giving any cohort snapshot a dated evidence owner.

## Why this exists

The two demo documents repeat product, report, and evidence prose. They also
contain presentation-specific narrative and scientific cautions that are
useful at the action point, while one undated cohort snapshot is currently
described elsewhere as dated.

## Fixed decisions

- Preserve walkthrough order, the PI evidence-model table, discussion prompts,
  and presentation action-point scientific cautions.
- Shared mutable product/report/current-evidence facts link their canonical
  owners rather than remaining copied.
- A historical snapshot must be explicitly dated/provenanced beneath the
  established history owner or removed as a current claim; do not invent a
  date.
- Until an authorized inspection establishes otherwise, dormant demo sources
  are unverified preservation material, not dead files, current guidance, or
  report-contract inputs. File presence preserves their possible unique
  meaning; it does not activate or approve their contents.
- Presenter execution and audience explanation are separate responsibilities.
  Do not create another narrative without a named consumer and review
  milestone, and do not make report-card coupling until a guide is verified as
  a report or evidence consumer.
- Semantic category: bounded documentation or low-risk maintenance.
- Validation category: documentation-only/non-consuming. Computational,
  report-runtime, dependency, cluster, scientific-review, and biological
  evidence are not changed or promoted.

## Blocked by

- [DOC-CONS-08D](../COMPLETED/DOC-CONS-08D-establish-dated-documentation-history.md) — Required: a dated demo snapshot needs an indexed history destination.

## Completion unblocks

- None.

## Prerequisites

- Verify whether the cohort snapshot has repository-backed date/provenance and
  whether `PI_DEMO_REPORT.md` is a current presentation or a frozen snapshot.
- Approve a bounded read-only inventory before opening any otherwise dormant
  body. Audit root routes, inbound links, and named external consumers before
  proposing activation, rename, replacement, or deletion.

## Required context

- The two demo files, direct root/current-evidence/report links, the history
  index, and the demo rows in `DOCUMENTATION_OWNERSHIP.md`.

## Questions owned by this card

- None.

## In scope

- Creating and registering the `docs/history/demos/` child beneath the
  established shallow history index when a dated snapshot is retained.
- Adding local demo navigation if not already supplied by `DOC-README-03`.
- Replacing shared mutable prose with precise owner links.
- Dating/archiving the cohort snapshot or removing its stale current copy after
  preserving any unique evidence.
- Relabeling presentation versus historical artifacts accurately and repairing
  direct links.
- If activation is approved later, update source labels, local routing, root
  routes, inbound links, and affected terminology atomically. Commands and
  mutable current state must link to their canonical owners rather than being
  copied into either guide.

## Out of scope

- Changing report behavior, evidence state, scientific conclusions, current
  handoff truth, or presentation-specific safety cautions.

## Deliverables

- Two distinct, concise demo views and one explicit disposition for every
  snapshot/history statement.

## Acceptance evidence

- Walkthrough narrative, PI evidence table, prompts, and cautions remain.
- No demo owns mutable current evidence or report contracts.
- Every historical statement is dated/provenanced and indexed exactly once.
- Every source has a no-loss destination, purposeful-retention rationale, or
  explicit human-review point; uncertainty is never resolved by silent
  deletion or activation.
- Documentation links and the documentation gate pass.

## Canonical documentation updates

- `docs/demo/`, affected root/history/current-evidence links, the ownership
  ledger, and this card.

## Escalation conditions

- Stop if a snapshot cannot be dated/provenanced or consolidation weakens a
  scientific caveat needed during presentation.

## Completion record

Selected on 2026-08-05 from clean, published, live-remote-equal predecessor
`8617635eecd848d684c695a5299354066ee02167` on
`codex/residual-source-topology-convergence`. This status-only selection does
not open dormant sources, change presentation/evidence claims, create demo
history, select a successor, or promote evidence. The approved implementation
is limited to the two named demo views, their direct routes, and any snapshot
whose date/provenance is proved from repository evidence; it stops on an
undatable snapshot or weakened scientific caution.
