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

The unselected local-pilot dependency order is:

```text
SETUP-03A + INTAKE-03A + PROFILE-03A
                -> CLI-03A -> E2E-03A -> ONBOARD-03A
```

`INTAKE-03A` also requires an accepted `INTAKE-02E` design. These
relationships do not select work.

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

## Scientific exit boundary

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
scientific policy defines and satisfies its exit criteria. No local structural
or reporting gate may promote either state.
