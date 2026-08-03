# REVIEW-ARCH-03O — Review scientific-review package migration architecture

## Objective

Challenge `MIG-03O` for live-DAG choice, final evidence/test/support-asset
placement, exact import/caller cutover, migrated Step `08`/`09` private loading,
artifact/run-summary/report ownership, coverage continuity, and reversible
removal of the flat Step `09c` implementation paths.

## Why this exists

Step `09c` is the only dependency-valid unmigrated functional owner, but its
4,533-line Python implementation is also imported by migrated validators and
flat artifact/run-summary code. Its public examples and thirteen evidence
schema TSVs may be evidence-local assets or separately retained configuration
surfaces. Relocation must assign every asset and consumer once without a
package, ambient import path, compatibility owner, schema change, or future-
package preload.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test/configuration source under this card.
- Apply the frozen semantic identity, direct DAG, evidence/test homes,
  dependency direction, and migration mechanics without reopening descriptor,
  schema, scientific-state, artifact, report, or transaction policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, installed/public package identity, ambient
  `PYTHONPATH`, global `sys.path` mutation, and any later owner or audit preload.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03O](../TODO/REVIEW-REL-03O-review-assemble-scientific-review-evidence-package-migration.md) — Fully: reliability review requires an architecture-corrected owner, asset, loader, consumer, artifact, coverage, and rollback boundary.

## Prerequisites

- Review committed `MIG-03O` against frozen parent `68fd2a9` without running or
  changing executable/test/configuration files.

## Required context

- `MIG-03O`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `09c` evidence contract; Python/shell
  implementation; candidate direct tests/fixture and example/schema assets;
  migrated Step `08`/`09` private loaders; artifact/run-summary imports and
  fixtures; report consumers; independent goldens; public CLI/Make literal
  maps; coverage identity; and every proposed current/final path.

## Questions owned by this card

- Is Step `09c` the only dependency-valid unmigrated owner and the last unit in
  the frozen functional-owner target topology?
- Which native, test, fixture, example, and evidence-schema assets move, which
  remain under a justified owner, and what are the exact move and integration-
  owner ceilings?
- What exact final roots and private module identities preserve migrated Step
  `08`/`09`, artifact, run-summary, fixture, and independent-golden consumers,
  including initialization/cache/path/failure behavior, without a public
  package or global search-path mutation?
- Do modes, projected hashes, direct/explicit-interpreter behavior, artifact
  producer identity, coverage row, atomic cutover, and reverse rollback remain
  assigned exactly once without a wrapper or schema change?

## In scope

- DAG eligibility; final source/test/support placement; modes/hashes; Python/
  shell sibling relationship; exact imports/callers; private-loader identities;
  permissible path edits; atomic cutover; artifact/run-summary/report
  provenance; coverage row; old/final evidence; and exact reverse rollback.

## Out of scope

- Executable/test/configuration mutation; reliability or usability execution;
  schema/state/helper extraction; public package identity; transaction,
  scientific-review, artifact, or report redesign; dependency action;
  scheduler/cluster/production work; and future packages.

## Deliverables

- Finding-by-finding architecture disposition with exact corrections to
  `MIG-03O`, this review, and current status/audit owners.

## Acceptance evidence

- Every native/test/support asset, import/caller, Make/public route, artifact/
  run-summary/report consumer, coverage row, and rollback edge has one old
  owner and one projected final owner. Exact searches support the fixed ceiling
  and loader reasoning covers initialization/cache/path/spec/partial failures
  without changing public identity.

## Canonical documentation updates

- This card, `MIG-03O`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop for an unmovable import/caller, unavoidable public package or permanent
  wrapper, schema/artifact/report redesign, dependency action, or any boundary
  broader than one Step `09c` owner and its direct wiring.

## Completion record

Selected alone from clean, published, local/upstream/live-remote-equal
definition checkpoint `86b888804c8f6a124c2a431665105814c4768e7a`. Review
remains read-only; no executable/test/configuration file changed or ran.
