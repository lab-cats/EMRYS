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
- Schema bytes, hashes, identities, and modes are unchanged. The report-receipt
  fixture remains byte-identical; the other three fixture files change only in
  the four approved self-test path occurrences, while every embedded hash and
  non-path byte remains unchanged. Test and fixture modes remain unchanged.
- The direct artifact-contract suite, affected reporting/adapter/summary and
  independent-golden suites, public-CLI characterization, measured Python
  coverage, applicable independent local lanes, documentation gate, and exact
  legacy-path searches pass on the final executable state. The complete
  aggregate gate is attempted and any unrelated environment deferral is
  recorded without a passing-gate claim or dependency mutation.

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

Selected from clean, published, upstream-equal `LIB-02F` decision close
`96c64365705eff08bd9509a76a97b8b5ee04eb1b`; status-only selection checkpoint
`ca5497f40442f9d7427f56458372e3b701efa0ff` was the frozen implementation
parent. Executable/test checkpoint
`17090acb523d1a882bfae51ff738b5f8b9e391c9` then moved exactly the validator,
five schemas, direct suite, and four valid fixtures and cut over the six
reviewed reporting-chain consumers. No wrapper, copy, symlink, package import,
`PYTHONPATH` mutation, installation metadata, console script, schema change,
or reporting/scientific-policy change was added.

- The validator remains mode `0755`; schemas, direct test, and fixtures remain
  `0644`. The five schema SHA-256 values remain, respectively,
  `5bf367ff9f4f3142bbbc77cbd187b85902758613225958d009b30bd89f8cf41e`,
  `f67385bbc65820f3efd6ad30b11e5e131ce42a8da5a9efcdd414819d22709b95`,
  `6035cda8b393a161efa19f0c8fb2d4080be5525dee785c4ce33aebc690eba28a`,
  `a2ea0f551eab4848f487f03a277de43a10264cfb550e14eee121f03cc4ac6884`,
  and `67ff7068a4b1dbc911eaccc0a484eefd10ba48d0362cb61e89c64e7d37c089bf`.
  `report_receipt.json` remains byte-identical at
  `e98edba4a48a409ffd0b66e5a5108e6317fd4f61d64e6e48a6986b73f3d41f2e`;
  the other three valid fixtures contain only the four approved self-test path
  substitutions and retain all embedded hashes and non-path bytes.
- Old-path and final-path focused sets each passed `398` tests with `17`
  skips. The moved direct suite passed `58` tests, and the independent loader/
  golden suite passed `44`. Help, five-line schema check, valid and malformed
  documents, inventory reconciliation, streams, exits, arbitrary-CWD
  execution, and side-effect behavior matched with only the approved physical
  paths changed. All Python consumers resolve one exact final module identity.
- Final executable coverage ran `1,346` passes with `17` skips. Current measured
  coverage was `0.834998` line and `0.729303` branch across `32` files; the
  affected-only committed floor increased to `0.818662` line and `0.705324`
  branch. The moved validator retained exactly `658/777` lines and `361/472`
  branches; no unrelated transient coverage gain was promoted.
- Static preflight, the complete shell-contract lane, guarded Step `08`/`09`
  real-R semantic fixtures, and pinned report-runtime lane passed; report
  runtime was `17` passes with `60` deselected. The exact network-enabled
  aggregate gate remained status `2`, not green, solely because CRAN began
  advertising `renv 1.2.4` after the last known green run while the installed
  library and `renv.lock` remain synchronized at `1.2.3`. There were zero
  too-new packages, no existing compatible `1.2.4` library, and no dependency,
  lockfile, cache, or runtime mutation. This is an explicit environmental
  deferral, not a passing aggregate-gate claim or a MIG-04A regression.
- Final exact searches find no non-document consumer at the legacy validator,
  schema, direct-test, or valid-fixture paths and no duplicate implementation.
  Documentation validation and `git diff --check` pass at lifecycle close.
  These results are local contract-preserving engineering evidence only; they
  add no cluster, production, scientific-review, or biological-readiness proof.
