# MIG-04E — Converge independent contract goldens under final contract-integration owner

## Objective

Move the independent contract-golden suite and its eight fixture/provenance
files to the exact permanent contract-integration owner fixed by
`SOURCE_TOPOLOGY.md`, without changing any contract oracle or non-path behavior.

## Why this exists

The residual cross-owner contract-test group contains two distinct final
owners. The independent goldens have one self-contained suite/fixture boundary,
while validation-roster agreement has a separate suite/helper boundary and
fourteen exact-file consumers. This card moves only the independent-golden
owner so the repository continues to execute one bounded JIT owner at a time.

## Fixed decisions

- Move `tests/test_independent_contract_goldens.py` and all eight tracked files
  under `tests/fixtures/independent_contract_goldens/` directly into
  `tests/contract_integration/independent_contract_goldens/`. The final owner
  contains the suite, `README.md`, and seven JSON/TSV golden files at one level;
  it does not add a nested `fixtures/` directory.
- Use one Git-preserving direct cutover. The fixture directory has only this
  suite as a consumer, no other test imports the suite, recursive pytest
  discovery selects its final path, and no external or unmovable caller is
  named in repository evidence or canonical operational routes.
- Change only the moved suite's repository-root anchor from `parents[1]` to
  `parents[3]` and its golden anchor to `Path(__file__).resolve().parent`.
  Preserve its reporting-only `sys.path` setup, private loader identities,
  cache handling, imports, cases, assertions, and collection identity.
- Move all eight fixture/provenance files byte-identically at mode `0644`.
  Preserve literal schemas, ordered headers, canonical JSON bytes, TSV/receipt
  bytes, state vocabularies, policy oracles, mutation guards, and the README's
  evidence limits.
- Add no package marker, import re-export, wrapper, compatibility copy,
  symlink, descriptor, installation surface, `PYTHONPATH`, or additional
  global `sys.path` mutation; preserve the suite's existing reporting-only
  insertion exactly. The old suite and fixture paths must be absent.
- Leave `tests/test_validation_check_rosters.py` and
  `tests/validation_roster_expectations.py`, all fourteen roster-helper callers,
  and the final `tests/contract_integration/validation_rosters/` owner entirely
  untouched and unselected.
- Historical completed cards and dated audit records retain their
  time-specific paths.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal MIG-04D documentation close
  `797aede33700a73ff39898ce2f683d26f7b5f1d1`.
- Reverify the exact nine-file owner roster, suite/fixture consumers, recursive
  discovery, current documentation links, final direct-root layout, modes,
  sizes, hashes, and absence of an external or unmovable caller.
- Freeze the exact collected node-ID set and results from repository root and
  an unrelated working directory before movement.

## Required context

- `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and
  `MIG-04D`, the independent suite and fixtures, current test/coverage policy,
  and current operational routes only.

## Questions owned by this card

- None.

## In scope

- The nine Git-preserving moves; the two suite-local anchor repairs; exact
  fixture, mode, collection, root/arbitrary-CWD, focused, complete-coverage,
  and old-path parity checks; and impact-directed documentation/lifecycle
  close.

## Out of scope

- Validation-roster suite/helper movement or caller cutover; any schema,
  header, serialization, receipt, status, state, policy, cache, loader, report,
  artifact, scientific-evidence, or production behavior change; new package or
  compatibility surfaces; legacy-test review; final audit; scheduler,
  ingestion, orchestration/profile, runtime execution, cluster, production,
  scientific-review, or biological work.

## Deliverables

- One final independent-contract-goldens owner containing the direct suite and
  eight byte-identical fixture/provenance files, with no legacy or compatibility
  path and no change to the separate validation-roster owner.

## Acceptance evidence

- The exact `82` collected tests pass before and after from repository root and
  an unrelated working directory; normalized node IDs differ only by the
  approved path prefix.
- The eight fixture/provenance files retain mode `0644`, sizes, and SHA-256
  identities. A normalized suite diff contains only the approved repository-
  root and owner-local-golden anchors.
- Focused contract/scientific-evidence/reporting consumers, static validation,
  applicable shell contracts, complete undeselected Python coverage,
  documentation validation, semantic diff review, and exact live old-path
  searches pass at the final executable state.
- Production coverage remains exact across the same `36` files at
  `10592/12491` lines and `3789/5048` branches, rates `0.847971` and `0.750594`,
  with no baseline promotion or measured-file identity change.
- Exact searches prove one final suite/fixture owner; both validation-roster
  files and all fourteen current callers remain unchanged; no package marker,
  wrapper, copy, symlink, re-export, descriptor, or new path-environment
  mutation exists, and the existing reporting-only insertion remains exact.
- Evidence remains local synthetic-characterization and relocation parity
  only. It is not runtime, cluster, production, scientific-review, or
  biological-readiness evidence.

## Canonical documentation updates

- Functional-owner inventory and residual counts, source-topology implemented
  state, independent-golden commands/links in `TEST_BASELINE.md`, `RUNBOOK.md`,
  and the Step `09c` evidence-owner README, `PIPELINE_PLAN.md`, `HANDOFF.md`,
  lifecycle routes, documentation ownership, and this card.

## Escalation conditions

- Stop for fixture byte/mode/oracle drift; any schema, header, serialization,
  receipt, status, state, policy, cache, loader, test-count, collection, or
  production-coverage change; an external/unmovable or unknown caller; any
  compatibility/package/path-environment need; or scope into validation
  rosters, legacy review, final audit, scheduler, ingestion,
  orchestration/profile, runtime execution, cluster, scientific-review, or
  biological work.

## Completion record

Selected from clean, published, live-remote-equal MIG-04D documentation close
`797aede33700a73ff39898ce2f683d26f7b5f1d1`. The bounded read-only audit found
exactly nine owned mode-`0644` files, one fixture consumer, recursive pytest
discovery, no importing test, and no external or unmovable caller. The direct
suite is `693` lines, `23,040` bytes, SHA-256
`9558db0cc18c31609ff4ab42c6639759f5d92f4050ecec712535c4392d402474`.
The eight fixture/provenance SHA-256 identities are: `README.md`
(`1,212` bytes)
`c05fb3d08aae6dbd11467fa296875c2719374f527ce9a148e81c9d526f2dfcd7`;
`canonical_object.json`
(`119` bytes)
`379c4d37bb2b17003e66bf115da089341b0a86c812da719890555788a822d15e`;
`headers.json`
(`3,666` bytes)
`80c96c96549c39692d1b08f43a9a3883a7e88b92c863edab1673d64ab319d46d`;
`report_receipt.tsv`
(`990` bytes)
`77f24a97b9514f4b7dbb0da2eddc67134398fc8dbcd0724a3797768ffd3a634c`;
`report_receipt_input.json`
(`620` bytes)
`b16108c35ecb0b7a0941eef5b8519b558507fcc1dab1aafd23a74e7fdef2b596`;
`schema_contracts.json`
(`3,835` bytes)
`00764f63686d6a8d76ea0af6511aa30d462a3172fe952921a0ab9f435178109e`;
`scientific_state_contracts.json`
(`7,621` bytes)
`c5da390fdaef1a621353dadaaf4c9d53e52d874778c19c8f049f405aab9b7b78`;
and `small_table.tsv`
(`84` bytes)
`9d67cc544f8a46b8bd600003ac228806e8f66122013755a4d452937dcce5b0ec`.
The exact `82` tests passed from repository root and unrelated working
directory `/private/tmp` in `0.17s` each. The separate two-file validation-
roster owner and its fourteen callers remain unselected. Selection checkpoint
`79427416a9631b30fe354fdf18cbf29bce57c37f` was published and verified live
before executable mutation.

Executable checkpoint `9434b0adb2550b0e6290f16df44af0b5d5df62c4`
published the direct nine-file Git move. All eight fixture/provenance files
remain byte-identical at mode `0644`, their frozen sizes and hashes above, and
the final owner contains exactly those files plus the suite at one level. The
suite remains `693` lines and mode `0644`; its final size is `23,006` bytes and
SHA-256 is
`6cab669cf26c008de0dc354af8b97c786fbaf95260e6f6112b76ceba5ce12017`.
Its normalized diff changes only `REPO_ROOT` from `parents[1]` to `parents[3]`
and `GOLDENS` to its resolved parent. Both old paths are absent; no package
marker, wrapper, copy, symlink, re-export, descriptor, install surface, or new
path-environment mutation exists. The existing reporting-only `sys.path`
insertion, both validation-roster files, all fourteen roster callers, and the
coverage baseline remain unchanged.

Post-move, the exact `82` tests passed from repository root and `/private/tmp`
with collection differing only by the approved path prefix. The focused
contract, scientific-evidence, reporting, and producer/validator roster passed
`612` tests with `17` expected renderer skips. Static validation and the full
shell-contract lane passed. The pre-close undeselected complete Python run
passed `1,591` tests with `17` skips and failed only the expected current-
documentation assertion for the moved README link. Its recovered coverage
artifact passed policy at exact rates `0.847971` line and `0.750594` branch
across `36` files (`10592/12491` lines and `3789/5048` branches), with no
measured-file or baseline change. Three independent executable reviews found
no source, fixture, path, collection, roster, coverage, package, compatibility,
or evidence-boundary defect.

Current ownership, lifecycle, command, test-baseline, and README links were
then repaired; the residual inventory fell from `98` to `89` while retaining
the separate two-path validation-roster owner. No dependency was installed,
restored, removed, or updated, and no contract oracle, production behavior, or
characterized defect changed. This remains local synthetic-characterization
and relocation-parity evidence only, not runtime, cluster, production,
scientific-review, or biological-readiness evidence. The close selects no
successor and pauses before the still-unselected validation-roster owner.

After those close repairs, the undeselected complete Python gate passed
`1,592` tests with `17` skips and the coverage policy remained exact at
`0.847971` line and `0.750594` branch across `36` files. Documentation
validation passed `227` Markdown documents, `144` task cards, and `6` Mermaid
sources. Three independent final close reviews found only two evidence-
recording omissions: this prospective review sentence and the handoff's missing
final-green clause. Both are repaired; final re-review found no remaining
lifecycle, path, residual-count, scope, or evidence-record defect.
