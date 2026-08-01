# TEST-01Z — Decide behavior-contract sufficiency

## Objective

Make and record the measured readiness decision that gates architectural
planning.

## Why this exists

Passing tests and high line coverage do not prove that protected behavior is
adequately characterized. The refactor needs an explicit, reviewable decision
over every applicable contract row before production structure changes.

## Fixed decisions

- Classify each behavior row as `preserved contract`, `characterized defect`,
  `undefined — decision required`, or `environment-deferred` under the
  [behavior-first decision](../../design/DECISIONS.md#protect-behavior-before-architectural-mutation).
- Exit requires 100% of applicable preserved-contract rows protected; it does
  not require 100% line coverage.
- A negative decision creates small `TEST-01G-*` closure cards and a later
  `TEST-01Z-R*` decision card; it does not create a dependency cycle or begin
  architecture work.

## Blocked by

- [TEST-01F](../COMPLETED/TEST-01F-create-independent-contract-goldens.md) — Required: all approved Phase 01 characterization evidence must be complete.

## Completion unblocks

- [ARCH-02A](../TODO/ARCH-02A-inventory-functional-stages-and-contracts.md) — Fully: only an affirmative recorded decision releases this target.
- [RPT-01](../TODO/RPT-01-characterize-comprehensive-report.md) — Fully: only an affirmative recorded decision releases this target.
- [LOG-01](../TODO/LOG-01-characterize-current-output.md) — Fully: only an affirmative recorded decision releases this target.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Fully: only an affirmative recorded decision releases this target.
- [CODEDOC-05](../TODO/CODEDOC-05-inventory-code-documentation.md) — Partially: it also requires the documentation ownership model.
- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Partially: it also requires the functional-stage inventory.

## Prerequisites

- Refresh measured line/branch evidence without treating it as the sole gate.
- Confirm every `TG-03` through `TG-06` completion and any accepted deferral.

## Required context

- `TEST_BASELINE.md`, completed Phase 01 task records, `REFACTOR_AUDIT.md`,
  the live public-contract inventory, and the latest complete local gate.

## Questions owned by this card

- None.

## In scope

- Row-by-row contract classification, evidence links, accepted/deferred risk,
  coverage refresh, and an explicit affirmative or negative readiness result.

## Out of scope

- Production refactoring, silent acceptance of uncovered behavior, fixing
  characterized defects, or weakening independent tests.

## Deliverables

- A closed behavior-contract matrix and readiness decision.
- If negative, bounded closure cards and a new sufficiency-decision card.

## Acceptance evidence

- Every applicable preserved-contract row names independent regression
  evidence and every other row has an explicit disposition.
- The decision, rationale, and consequences are independently reviewable.
- Only an affirmative decision releases Phase 02 roots.

## Canonical documentation updates

- `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, `TODO.md`,
  `DECISIONS.md` if a durable exception is approved, and this card.

## Escalation conditions

- Stop for any undefined high-risk behavior, unreviewed environment deferral,
  coverage regression, or pressure to infer readiness from pass totals alone.

## Completion record

Completed locally on 2026-07-31 on
`codex/refactor-01z-test-sufficiency-gate`.

- `TEST_BASELINE.md` closes all 88 public-entry-point, cross-cutting-risk, and
  fixture/evidence rows with only the four authorized dispositions. Zero rows
  are `undefined — decision required`.
- Every preserved-contract component names independent regression evidence.
  Characterized defects remain defects, and every environment-deferred
  component remains bounded by the reviewed runtime, cluster, scientific, and
  biological evidence limits.
- The checked Python refresh passed with 843 tests and 17 expected skips,
  measuring 8,585/10,551 lines (81.3667%) and 3,111/4,404 branches (70.6403%)
  across 26 production modules. The tracked baseline was not rewritten.
- The initial combined TEST-01C–TEST-01F reviewer did not request a repair. A
  later Phase `0` adversarial review found that the claimed Make-expansion and
  R-argument protections were not independently exercised, so the branch was
  held from publication rather than treating that first verdict as final.
- Test-only correction `0c64d1a` adds the missing literal Make oracle and real
  R rejection-path execution. The first final review then blocked on bare
  recursive-Make portability; follow-up `44d3255` explicitly protects bare
  and absolute `make` and `gmake` identities. The focused tests and reopened
  complete local gate pass; the affirmative decision is unchanged, but final
  Phase `0` reconciliation still requires adversarial acceptance of the exact
  corrected tip.
- The decision is affirmative only for separate task selection of `ARCH-02A`,
  `RPT-01`, `LOG-01`, and `DOC-IA-01`. TEST-01Z's partial dependency is
  satisfied for `CODEDOC-05` and `SIZE-07`, whose other blockers remain.
- No closure card was created. No Phase `02` work began. Reconciliation changed
  only tests, literal test fixtures, and their documentation; no production,
  dependency, schema, runtime, cluster, scientific-policy, evidence-state, or
  biological behavior changed.
