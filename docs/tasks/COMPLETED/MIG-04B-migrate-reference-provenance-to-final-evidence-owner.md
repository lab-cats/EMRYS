# MIG-04B — Migrate reference provenance to its final evidence owner

## Objective

Move the public reference-provenance command and its direct suite to the exact
permanent evidence-owner homes fixed by `SOURCE_TOPOLOGY.md`, cutting over every
repository-owned path consumer without changing non-path behavior.

## Why this exists

Reference provenance remains one of the final implementation-bearing flat
source/test pairs even though its functional owner and final paths are already
fixed. Completed `LIB-02K` removed the two peer-owner parser bridges and left
the command as a consumer of the permanent neutral `reference_contigs` seam,
so the evidence owner can now move directly without a compatibility path.

## Fixed decisions

- Move `scripts/reference_provenance.py` to
  `src/norad/evidence/reference_provenance/reference_provenance.py` and
  `tests/test_reference_provenance.py` to
  `tests/evidence/reference_provenance/test_reference_provenance.py`.
- Use one Git-preserving direct atomic cutover. Every discovered live path
  consumer is repository-owned, and no external or unmovable caller is named
  in repository evidence or canonical operational routes. Hypothetical
  external use does not justify a wrapper, copy, symlink, re-export, package
  marker, descriptor, console script, installation metadata, `PYTHONPATH`, or
  `sys.path` mutation.
- Preserve the basename, shebang, source mode `0755`, test mode `0644`, public
  arguments/help/streams/exits, interpreter and direct execution, arbitrary-CWD
  behavior, dry-run side effects, evidence rows and schemas, deterministic
  bytes, hashing/agreement rules, and valid `overall_status=fail` exit-zero
  behavior.
- Preserve exact locking, staging, predecessor validation, publication order,
  rollback, cleanup, stable-input checks, and characterized recovery defects,
  including the incomplete-restoration state that retains `.previous` files
  while removing the lock and without creating a recovery marker. This card
  relocates behavior; it does not repair or approve it.
- Repair only the source's self-relative neutral-library anchor and the moved
  suite's repository-root/source anchors. The final resolved
  `reference_contigs.py` path, private identity, readiness/API checks, loader
  errors, cache/partial cleanup, and all parser semantics remain exact.
- Keep public `configs/reference_provenance.example.tsv` at root with exact
  bytes and mode. It is an explicit operator input, not an owner-native private
  asset.
- The old source/test paths must be absent after cutover. Historical completed
  cards and dated audit records retain their time-specific paths.

## Blocked by

- [LIB-02K](../COMPLETED/LIB-02K-extract-reference-contig-parser-library.md) — Required: the completed neutral parser extraction removes both peer-owner bridges that otherwise prevent a direct evidence-owner move.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal LIB-02K documentation close
  `696d403947cf28a97d7a9ce2f9b441ee83cbd72e`.
- Reverify the exact two-file owner roster, every Make/test/coverage/current-doc
  path consumer, any named external or unmovable caller in current evidence,
  and the root-starter boundary.
- Freeze source/test/config modes, sizes, hashes; help and parse-failure bytes;
  dry-run/execute/repeat output; transaction/fault behavior; arbitrary-CWD
  behavior; and current measured coverage before movement.

## Required context

- `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and
  `LIB-02K`, the command and direct suite, the neutral parser consumer guard,
  public-CLI/Make characterization, coverage policy, and current operational
  routes only.

## Questions owned by this card

- None.

## In scope

- The two Git-preserving moves; two self-relative anchor repairs; Make/golden,
  public-CLI, neutral-library consumer-roster, and coverage-identity cutovers;
  exact old-path/duplicate/wrapper guards; focused parity and measured coverage;
  and impact-directed documentation/lifecycle close.

## Out of scope

- Root starter-config movement; parser behavior or ownership; evidence schema,
  agreement, hashing, output, transaction, locking, rollback, recovery, or
  defect repair; runtime/storage owner moves; contract-test convergence;
  legacy-test review; final audit; packaging; scheduler, ingestion,
  orchestration/profile, runtime execution, cluster, production,
  scientific-review, or biological work.

## Deliverables

- One final reference-provenance command, one mirrored direct suite, every
  repository caller on the final paths, and no legacy implementation or
  compatibility path.

## Acceptance evidence

- Pre/post interpreter and direct-exec help, malformed arguments, dry-run,
  execute, and repeat execution from repository root and an unrelated working
  directory have exact stdout/stderr/exits and three output TSV bytes, apart
  from approved repository command-path substitutions outside product output.
- Source/test modes remain exact. A normalized source diff contains only the
  final neutral-library anchor; a normalized moved-test diff contains only its
  repository-root/source anchors and any approved parity guard. The root
  starter config retains mode `0644`, size `1,210`, and SHA-256
  `5a36c7a02acc7636a85089075e18e58e476d20a6fd14f31f96538c1d15e9e3c7`.
- The moved direct suite, neutral parser suite, public CLI/Make contracts,
  coverage-policy tests, publication/recovery faults, static and shell lanes,
  complete Python coverage, documentation validation, semantic diff review,
  and exact live old-path searches pass at the final executable state.
- Coverage identity moves atomically to the final path with no owner/global
  regression and no unrelated baseline promotion.
- Exact searches prove one final command, no wrapper/copy/symlink/package
  marker, no validator dependency on reference provenance, and only the neutral
  owner defining reference-contig parsers.

## Canonical documentation updates

- Functional-owner inventory and residual counts, source-topology implemented
  state, public runbook and troubleshooting commands, `TEST_BASELINE.md`,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, lifecycle links, and this card.

## Escalation conditions

- Stop for an external unmovable caller; any wrapper, compatibility, package,
  descriptor, console-script, install, or path-mutation need; inability to
  exact-load the neutral parser from the final owner without broader refactor;
  any non-path CLI/evidence/header/order/hash/transaction/fault/coverage delta;
  source/test mode drift; config movement; parser-seam reopening; unknown
  generated caller; or scope into a later residual or deferred domain.

## Completion record

Selected from clean, published, live-remote-equal LIB-02K documentation close
`696d403947cf28a97d7a9ce2f9b441ee83cbd72e`. The bounded read-only audit found
exactly two owned files; every discovered path consumer is repository-owned,
with no external or unmovable caller identified in canonical repository
evidence. Pre-change source evidence is mode `0755`, `22,323` bytes, SHA-256
`c303a68d0155f1ae206a1131bf7c360e74ce96870e697a398ec8988b9b92b81b`;
the direct suite is mode `0644`, `15,814` bytes, SHA-256
`81dc33d51f6ac0b0d18cf817f4c02fadc36ba7ee917777880faefd8d0e531454`.
The 14-test direct suite passed; the command, neutral-parser, public-CLI, and
coverage-policy focused roster passed `182` tests. Arbitrary-CWD help is `422`
stdout bytes at SHA-256
`466d4e1bf4def032f5450ecc01df8f93694d0e8f2aadfa9c11bbf1ddf410d75b`
with empty stderr and status `0`; unknown-option failure has empty stdout,
status `2`, and stderr SHA-256
`21f50c761b8a8b8af35a186b24dbef66313b9125a58fe21619ff942499312bfe`.
The selection checkpoint `e4223ba4072ca4da12631258fc7c50ec78d9c72b`
was published and verified live before executable mutation.

Executable checkpoint `bbc09c9b52f365e46c9e28711efa1cd0ce90ccfe`
then Git-moved the command and direct suite to their exact final evidence-owner
homes. The only source change repaired the self-relative neutral-library anchor
from the legacy root layout to final
`src/norad/libraries/reference_contigs.py`; the moved suite changed only its
root/source anchors and added one bounded arbitrary-CWD dry-run/execute/repeat
parity guard. Make and its literal golden, the public-CLI path map, the neutral-
parser consumer roster, and the coverage identity moved atomically. The old
source/test paths are absent; exact searches found one final command and one
mirrored suite with no wrapper, copy, symlink, package marker, install surface,
validator dependency, or later-domain payload. Final source evidence is mode
`0755`, `22,297` bytes, SHA-256
`d2c44e1ef9163902b67ff47f4c29464706921bf0048ac0de2e0a25b521d0d407`;
the final suite is mode `0644`, `17,319` bytes, SHA-256
`56cda54d73d3d0a26cd4ffe3a6db151e29264d56d82ca19d8c0b1bce542cfbbc`.
The root starter config retained its pre-change mode, size, and SHA-256 exactly.

Normalized source comparison found exactly the approved loader-anchor
substitution. Old-versus-new execution from an unrelated working directory
matched dry-run and execute status/stdout/stderr and all three published TSV
byte maps; repeat execution was byte-stable and left no invocation-directory
residue. Help and unknown-option results retained their exact pre-change
lengths, hashes, streams, and statuses. The direct suite passed `15` tests and
the command/neutral-parser/public-CLI/coverage-policy affected roster passed
`183`. Static and every shell lane passed. The first complete undeselected
Python attempt passed `1,589` tests with `17` skips and failed only the expected
documentation assertion naming the intentionally not-yet-closed legacy paths;
the same final executable state passed `1,589` with `17` skips and that one
assertion explicitly deselected. Its standalone coverage comparison passed at
`0.847971` line and `0.750396` branch coverage across `36` files, with the
relocated owner frozen at `332/379` lines and `107/142` branches and no baseline
value promotion.

At documentation/lifecycle close, the undeselected complete Python lane passed
`1,590` tests with `17` skips at `0.847971` line and `0.750594` branch coverage
across `36` files. Documentation validation passed `224` documents, `141` task
cards, and `6` Mermaid sources. Three independent executable reviews found no
scope, code, semantic, parity, coverage, or relocation-induced transaction
delta. This package installed, restored, removed, or updated no dependency;
moved no public config; repaired none of the characterized recovery defects;
and created no runtime, cluster, scientific-review, biological, scheduler,
ingestion, or orchestration evidence.
