# MIG-04A — Migrate artifact-contract validation to its final neutral owner

## Objective

Move artifact-contract validation, its five public schemas, direct tests, and
valid fixtures to their exact permanent neutral-contract homes and cut over
every repository consumer without changing non-path behavior or schema
identity.

## Why this exists

The neutral artifact validator and schemas remain under legacy root
`scripts/` and `schemas/` paths even though `PLAN-03A` fixes their final
ownership under `src/norad/contracts/`. Reporting relocation and later
validator decomposition must begin from that one truthful owner rather than
extending the flat tree.

## Fixed decisions

- Move `scripts/validate_artifact_contracts.py` to
  `src/norad/contracts/artifacts/validate_artifact_contracts.py` and the five
  existing schema basenames to
  `src/norad/contracts/schemas/artifacts/v1/`.
- Move `tests/test_artifact_schema_contracts.py` and the four valid JSON
  fixtures to the exact mirrored homes in `SOURCE_TOPOLOGY.md`.
- Preserve validator mode `0755`; preserve schema, test, and fixture modes
  `0644` and exact schema bytes, `$id`, `$ref`, versions, closed shapes, and
  validation semantics.
- Use one direct atomic cutover. Every known caller is repository-owned, so no
  legacy wrapper, compatibility copy, symlink, package import, `PYTHONPATH`
  mutation, console script, or installation metadata is permitted.
- Preserve the validator basename and public CLI semantics. The exact
  old-to-final command/resource path substitutions and corresponding path-
  bearing roster, coverage, fixture, and documentation updates are the only
  approved relocation delta; the legacy path must be absent after cutover.
- Preserve CLI/help, arguments, streams, exit codes, arbitrary-CWD behavior,
  deterministic bytes, inventory reconciliation, and characterized defects.

## Blocked by

- None.

## Completion unblocks

- [RPT-05A](../TODO/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: reporting also requires concrete removal of its private Step `09c` dependency before relocation.
- [SIZE-07F](../TODO/SIZE-07F-decompose-artifact-contract-validator.md) — Partially: decomposition also requires its live size refresh and independent review blockers.

## Prerequisites

- Reverify clean campaign parent, exact file modes and hashes, all direct
  imports/invocations, schema and fixture path consumers, public CLI/coverage
  rosters, runbook commands, and documentation references.
- Freeze focused old-path behavior from repository root and an unrelated
  working directory before movement.

## Required context

- `SOURCE_TOPOLOGY.md` cross-cutting target homes,
  `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and `LIB-02F`, and the current
  functional-owner inventory.
- The validator, five schemas, direct suite, four valid fixtures;
  `_run_summary_science.py`, `build_artifact_index.py`,
  `build_run_summary.py`, `render_run_report.py`, and
  `render_run_report_bundle.py`; the report shell preflight; independent
  contract goldens; public-CLI and coverage baselines; direct operator and
  documentation commands.

## Questions owned by this card

- None.

## In scope

- One Git-preserving source/schema/test/fixture move, internal resource-path
  repair, complete direct-consumer cutover, exact path-only golden updates,
  focused parity evidence, old-path absence checks, and impact-directed
  documentation close.

## Out of scope

- Schema redesign or version changes; validator decomposition; reporting
  relocation; Step `09c` or reference-contig seam extraction; packaging,
  installation, public-command basename, argument, or semantic changes beyond
  the approved physical-path substitution; scientific policy, scheduler,
  ingestion, orchestration, runtime, or cluster work.

## Deliverables

- One final neutral validator implementation, five schemas in their permanent
  schema home, mirrored direct tests/fixtures, all consumers on final paths,
  and no legacy implementation or compatibility path.

## Acceptance evidence

- Pre/post direct CLI parity covers help, schema-only validation, valid and
  malformed documents, inventory reconciliation, streams, exits, arbitrary
  working directory, and side-effect boundaries.
- Schema and fixture hashes and modes are unchanged; path-only fixtures and
  rosters change only where they truthfully name the moved source.
- The direct artifact-contract suite, affected reporting/adapter/summary and
  independent-golden suites, public-CLI characterization, measured Python
  coverage, complete applicable local gate, documentation gate, and exact
  legacy-path searches pass on the final executable state.

## Canonical documentation updates

- `README.md`, current architecture and functional-owner inventory,
  `SOURCE_TOPOLOGY.md`, `RUNBOOK.md`, `TROUBLESHOOTING.md`, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, public task links, coverage path, and this card.

## Escalation conditions

- Stop for an external unmovable caller, changed schema/output semantics,
  non-path golden delta, required indefinite wrapper, packaging/import
  requirement, unknown generated consumer, or any reporting/scientific-policy
  change needed to make the move pass.

## Completion record

Selected after the clean, published, upstream-equal `LIB-02F` decision close.
Selection begins bounded plan/review only; no executable source, schema, test,
fixture, caller, configuration, or documentation path has moved.
