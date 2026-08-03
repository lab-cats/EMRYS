# MIG-03O — Migrate the scientific-review evidence-package owner

## Objective

Move the complete `assemble_scientific_review_evidence_package` Python
validation/publication implementation, shell launcher, owner-local protection,
and architecture-reviewed evidence-local assets to their frozen final evidence
owner homes while preserving every public, schema, scientific-state,
transaction, artifact, run-summary, report, and coverage contract.

## Why this exists

At clean, published MIG-03N documentation close `68fd2a9`, the refreshed live
required-artifact DAG has exactly one unmigrated functional owner:
`assemble_scientific_review_evidence_package`. Its complete Step `08`
three-output and Step `09` six-output predecessors are migrated. This is the
last owner in the frozen fourteen-owner target topology. No later owner or
final-audit package is created or selected here. This card defines the
smallest next JIT unit but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `68fd2a99d53d9fd2c9b9dcf3fb626c373d3378ea`, the clean, published,
  local/upstream/live-remote-equal MIG-03N documentation/lifecycle close.
- Semantic identity is `assemble_scientific_review_evidence_package`, kind
  `evidence`, machine key
  `norad.evidence.assemble_scientific_review_evidence_package.v1`, historical
  alias `09c`, final source home
  `src/norad/evidence/assemble_scientific_review_evidence_package/`, and
  mirrored test home
  `tests/evidence/assemble_scientific_review_evidence_package/`.
- Candidate native moves are mode-`0644`
  `scripts/step_09c_scientific_validation.py` (`159,620` bytes, `4,533` lines,
  SHA-256
  `7b6b48b71c07249cb791ceb818bd4aef5c30015724cb2406127159815c1e09f8`)
  and mode-`0755` `scripts/step_09c_scientific_validation.sh` (`5,403` bytes,
  `200` lines, SHA-256
  `127a12c87beb9d93745997224917a95f8784f6e5a51503359dde596a4b6f9340`).
  Preserve explicit-interpreter Python use, direct/Bash launcher use, sibling
  delegation, basenames, modes, streams, and exits.
- Candidate owner-local protection moves are mode-`0644`
  `tests/test_step_09c_scientific_validation.py` (`37,179` bytes, `1,195`
  lines, SHA-256
  `8de501596a0f074c608ae6b0e995c2a1caf9147062d00d15384bcf4538f08262`),
  mode-`0755` `tests/shell/test_step_09c_scientific_validation.sh` (`5,574`
  bytes, `170` lines, SHA-256
  `64981262ea170bda2e8bc95c55b8758cffa6ede0f85953b451e1962c0be18b2c`),
  and mode-`0644` `tests/fixtures/step09c/build_fixture.py` (`55,034` bytes,
  `1,525` lines, SHA-256
  `c5dd65a479d4d441da0b88606c9a5d5b1abd57dbebef907326ca198cae68b072`).
  Architecture review must prove the exact owner-local test/fixture boundary.
- Candidate evidence-local support assets are the two public example TSVs
  `configs/step_09c_review_plan.example.tsv` and
  `configs/step_09c_evidence_manifest.example.tsv` plus the thirteen one-line
  `configs/step_09c_evidence_schemas/*.schema.tsv` files. Architecture review
  owns whether each moves with this evidence owner or remains a separately
  justified public configuration surface, the final relative paths, exact
  hashes, every consumer, and the move ceiling. Relocation may not alter a
  header, example row, evidence category, schema meaning, or public version.
- The caller/import hypothesis includes `Makefile`, the public CLI and literal
  expansion owners, `scripts/build_artifact_index.py`,
  `scripts/_run_summary_science.py`, Step `08` and Step `09` validators and
  their private-loader tests, artifact/run-summary fixtures and tests,
  independent contract goldens, the Step `09c` fixture builder, the coverage
  row, and documentation commands. Architecture review must prove the exact
  full set and reject both omitted consumers and unrelated broad edits.
- The moved implementation is currently an import-time contract owner for
  migrated Step `08`/`09` validators and flat artifact/run-summary code.
  Preserve exact constants, schemas, functions, import initialization, and
  failure behavior without a package marker, installed identity, ambient
  `PYTHONPATH`, global `sys.path` mutation, compatibility copy, or public
  re-export. Architecture review owns the narrow private exact-file loading or
  atomic caller solution and its cache/path/readiness/failure oracles.
- Preserve the shell CLI/help, required review and upstream arguments,
  `PYTHON_BIN_OVERRIDE`, side-effect-free dry-run, delegated command rendering,
  arbitrary-CWD behavior, direct Python interface, streams, and exits.
- Preserve exact validation of the sample and partition manifests, complete
  Step `08`/`09` lineage, one-row review plan, evidence manifest and every
  declared payload, path/hash/row-count binding, scientific categories,
  decision/adjudication requirements, allowable status transitions, rerun
  recording, and rejection of reserved
  `biological_interpretation_ready`.
- Preserve the exact thirteen-output transaction, all-thirteen-or-none
  predecessor rule, exclusive review lock, run-token staging/backups, input
  stability rechecks, predecessor-summary removal, twelve payloads then
  summary-last publication, final validation/hash checks, rollback, recovery
  notice and retained lock on incomplete restoration, cleanup, and signals.
  Reliability review must characterize high-risk gaps without fixing or
  blessing them.
- Preserve scientific language. The owner validates and packages declared
  evidence; it does not rerun CMH, infer reviewer decisions, prove production
  execution, complete a production scientific review, validate editing sites,
  or establish biological readiness. `science_review_complete_exploratory`
  remains provisional.
- Preserve `STEP_PRODUCERS["09c"]`, all thirteen artifact adapters,
  `step09c_review_summary_v1` failure-marker meaning, run-summary science
  normalization, report authorization, schema versions, ordering,
  reconciliation, and downstream evidence ceilings except for reviewed source
  path/hash transitions.
- Frozen starting coverage is `1,262/1,534` covered statements and `561/788`
  branches for `scripts/step_09c_scientific_validation.py`; architecture and
  reliability reviews must bind the exact global floors and non-target rows
  from the frozen parent before executable mutation.
- Use only minimal focused checks inside executable slices. Run the complete
  applicable gate at the assembled executable card boundary, then batch the
  owner README, canonical paths/commands, migration links, lifecycle movement,
  small documentation updates, and audit evidence in a separate close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  shell/Python root and arbitrary-CWD journeys, example/schema choices,
  upstream/evidence/output/lock/summary choices, thirteen-file recovery and
  residue preservation, focused tests, artifact/run-summary/report provenance,
  Git rollback, and the synthetic-fixture-only evidence ceiling.
- Add no descriptor, package marker, wrapper, compatibility copy, symlink,
  schema/state/policy redesign, transaction/recovery redesign, public library
  API, dependency action, scheduler/cluster/production work, or future-card
  content.

## Blocked by

- [REVIEW-UX-03O](REVIEW-UX-03O-review-assemble-scientific-review-evidence-package-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal,
  live-remote-equal, and free of recovery, index-lock, or overlapping mutable-
  lane state before selection or executable mutation.
- Refresh only the named native/test/support candidates, exact imports and
  invocations, modes/hashes, artifact/run-summary/report consumers, coverage
  row, active documentation, and safe local failure/recovery states.
- Establish identical-input old-path baselines without dependency
  installation, scheduler submission, production inputs, scientific review,
  or biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `09c`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated evidence contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Python implementation, shell launcher, three candidate direct protection
  assets, example/schema candidates, migrated Step `08`/`09` private loaders,
  artifact and run-summary imports/fixtures/tests, independent goldens, public
  CLI/Make literal routes, coverage baseline, and current transaction/recovery
  diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact move,
  support-asset, caller/import, private-loader, artifact/run-summary, coverage,
  and rollback boundaries; reliability owns transaction, restoration, input-
  mutation, scientific-state, loader, wrapper, and recovery oracles; usability
  owns final commands, configuration/evidence choices, recovery navigation,
  provenance, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, imports/callers, support assets, artifact
  and science-normalization identities, defects, parity rows, coverage counts,
  and rollback evidence before mutation.
- Move only this evidence owner and its reviewed direct assets, cut over every
  reviewed explicit consumer, and make only reviewed path/private-loader
  changes.
- Validate executable slices minimally, run the complete applicable gate at
  the card boundary, and publish executable and documentation checkpoints
  separately before declaring physical migration complete.

## Out of scope

- Changing evidence schemas/categories, scientific-state or review policy,
  input/output formats, artifact/run-summary/report semantics, lock,
  transaction, recovery, or publication behavior; dependency installation;
  public packaging; scheduler/cluster/production work; completed scientific
  review; biological interpretation; or another owner.

## Deliverables

- Reviewed bounded test-only checkpoints only where required, one exact final-
  owner/caller/test/support-asset cutover checkpoint, and one separate
  documentation/lifecycle close on this branch.
- One final evidence owner and mirrored direct-test owner with no live legacy
  implementation, duplicate, wrapper, compatibility copy, or ambient import
  dependency.
- Exact artifact/run-summary/report transition, coverage accounting, supported
  commands, proportional validation, rollback/residue evidence, and a precise
  local synthetic-fixture evidence ceiling.

## Acceptance evidence

- Old/final parity covers Python and shell CLI/help, malformed inputs,
  arbitrary CWD, dry-run/execute effects, thirteen exact outputs, state and
  evidence gates, deterministic bytes, locks, publication order, replacement,
  rollback, incomplete recovery, stable inputs, streams, exits, and unrelated
  files as required by review.
- Import parity preserves Step `08`/`09`, artifact, run-summary, and independent
  golden consumers without ambient discovery or public package identity.
- Exact searches find one final owner and no undeclared old path, duplicate,
  stale command, missing support asset, ambient import, or lifecycle link.
  Coverage and the complete gate satisfy reviewed policy without evidence
  overclaim.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `09c`
  final paths, shell/Python commands, example/schema routes, acceptance, and
  evidence language in `RUNBOOK.md`; Step `09c` lock/partial/summary/restore-
  failure/input-mutation/import/path/review-state recovery routes in
  `TROUBLESHOOTING.md`; directly impacted Step `08`/`09` predecessor,
  artifact/run-summary/report, public CLI/Make, and schema routes; this card;
  review lifecycle links; and the dated audit log. Update diagrams only if
  final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable import/caller, required public package identity,
  permanent wrapper, second functional-owner migration, schema/state/artifact/
  report redesign, parity that requires blessing a defect, missing high-risk
  rollback oracle, dependency or cluster/production action, or scope that
  cannot remain this one evidence owner and its direct wiring.

## Completion record

Not selected. Defined from clean, published MIG-03N close `68fd2a9`; no
executable/test/configuration file changed or ran, and no later owner or audit
card was created or selected.
