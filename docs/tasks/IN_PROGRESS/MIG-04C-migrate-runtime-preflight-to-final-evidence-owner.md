# MIG-04C — Migrate runtime preflight to its final evidence owner

## Objective

Move the public runtime-preflight command and its direct suite to the exact
permanent evidence-owner homes fixed by `SOURCE_TOPOLOGY.md`, cutting over every
repository-owned path consumer without changing non-path behavior.

## Why this exists

Runtime preflight remains one of the final implementation-bearing flat
source/test pairs even though its functional owner and final paths are already
fixed. Its explicit profile is a root-owned public operator input, while the
command itself has no repository-relative implementation dependency or native
asset, so the evidence owner can move directly without a compatibility path.

## Fixed decisions

- Move `scripts/runtime_preflight.py` to
  `src/norad/evidence/runtime_preflight/runtime_preflight.py` and
  `tests/test_runtime_preflight.py` to
  `tests/evidence/runtime_preflight/test_runtime_preflight.py`.
- Use one Git-preserving direct atomic cutover. Every discovered live path
  consumer is repository-owned, and no external or unmovable caller is named
  in repository evidence or canonical operational routes. Hypothetical
  external use does not justify a wrapper, copy, symlink, re-export, package
  marker, descriptor, console script, installation metadata, `PYTHONPATH`, or
  `sys.path` mutation.
- Preserve the basename, shebang, source mode `0755`, test mode `0644`, public
  arguments/help/streams/exits, interpreter and direct execution, arbitrary-CWD
  behavior, dry-run side effects, exact profile/result headers, row order,
  status semantics, hashes, deterministic report bytes, and intentional exit
  zero when result rows are `fail`, `blocked`, or `not_checked`.
- Preserve exact profile stability checks, locking, staging, predecessor
  validation, replacement, publication order, rollback, and cleanup, including
  all three characterized recovery defects: lock-fsync descriptor/lock
  leakage, incomplete rollback leaving `.previous` without a lock or recovery
  marker, and swallowed lock-cleanup failure after successful publication.
  This card relocates behavior; it does not repair or approve it.
- Move the source byte-identically because it has no repository-relative
  implementation dependency or native asset. Repair only the moved suite's
  repository-root/source anchors and add one bounded arbitrary-CWD
  dry-run/execute/repeat parity guard.
- Keep public `configs/runtime_preflight.example.tsv` at root with exact bytes
  and mode. It is an explicit operator input, not an owner-native private
  asset.
- The old source/test paths must be absent after cutover. Historical completed
  cards and dated audit records retain their time-specific paths.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal MIG-04B documentation close
  `ad5a2bf239ba09c0e958e0df5957094e9b261f45`.
- Reverify the exact two-file owner roster, every Make/test/coverage/current-doc
  path consumer, any named external or unmovable caller in current evidence,
  and the root-starter boundary.
- Freeze source/test/config modes, sizes, hashes; help and parse-failure bytes;
  dry-run/execute/repeat output; transaction/fault behavior; arbitrary-CWD
  behavior; and current measured coverage before movement.

## Required context

- `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and
  `MIG-04B`, the command and direct suite, public-CLI/Make characterization,
  coverage policy, publication-fault characterization, and current operational
  routes only.

## Questions owned by this card

- None.

## In scope

- The two Git-preserving moves; moved-suite root/source anchor repairs and one
  bounded arbitrary-CWD parity guard; Make/golden, public-CLI, and coverage-
  identity cutovers; exact old-path/duplicate/wrapper guards; focused parity
  and measured coverage; and impact-directed documentation/lifecycle close.

## Out of scope

- Root starter-profile movement; CLI, profile/result schema, probing, status,
  hashing, output, transaction, locking, rollback, recovery, or defect repair;
  storage owner movement; contract-test convergence; legacy-test review; final
  audit; setup-doctor or packaging work; scheduler, ingestion,
  orchestration/profile, runtime execution, cluster, production,
  scientific-review, or biological work.

## Deliverables

- One final runtime-preflight command, one mirrored direct suite, every
  repository caller on the final paths, and no legacy implementation or
  compatibility path.

## Acceptance evidence

- Pre/post interpreter and direct-exec help, malformed arguments, dry-run,
  execute, and repeat execution from repository root and an unrelated working
  directory have exact stdout/stderr/exits and report bytes, apart from
  approved repository command-path substitutions outside product output.
- Source mode and bytes remain exact. A normalized moved-test diff contains
  only its repository-root/source anchors and approved parity guard. The root
  starter profile retains mode `0644`, size `697`, and SHA-256
  `4b73b407b5af0290586850e8ffd3820e78a800d470063b6028d9d9fe766e346e`.
- The moved direct suite, public CLI/Make contracts, coverage-policy tests,
  publication/recovery faults, static and shell lanes, complete Python
  coverage, documentation validation, semantic diff review, and exact live
  old-path searches pass at the final executable state.
- Coverage identity moves atomically from `scripts/runtime_preflight.py` to the
  final path with `311/361` covered/total lines and `102/140` covered/total
  branches, no owner/global regression, and no unrelated baseline promotion.
- Exact searches prove one final command, no wrapper/copy/symlink/package or
  install surface, and no moved or modified starter profile.
- Evidence remains local relocation, fixture, and parity evidence only; it is
  not runtime validation, cluster proof, scientific review, or biological
  readiness.

## Canonical documentation updates

- Functional-owner inventory and residual counts, source-topology implemented
  state, public runbook and troubleshooting commands, `TEST_BASELINE.md`,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, lifecycle links, and this card.

## Escalation conditions

- Stop for an external unmovable caller; any wrapper, compatibility, package,
  descriptor, console-script, install, or path-mutation need; any source-byte,
  CLI/profile/result/header/order/status/hash/transaction/fault/coverage delta;
  source/test mode drift; starter-profile movement or modification; unknown
  generated caller; or scope into storage, contract-test convergence, setup
  doctor, scheduler, ingestion, orchestration/profile, runtime execution,
  cluster, scientific-review, or biological work.

## Completion record

Selected from clean, published, live-remote-equal MIG-04B documentation close
`ad5a2bf239ba09c0e958e0df5957094e9b261f45`. The bounded read-only audit found
exactly two owned files; every discovered path consumer is repository-owned,
with no external or unmovable caller identified in canonical repository
evidence. Pre-change source evidence is mode `0755`, `21,674` bytes, SHA-256
`d455d65bd35405cba1dbcda9f656e6ba28e23ebf8610ca50e2215efff8cb8173`;
the direct suite is mode `0644`, `20,055` bytes, SHA-256
`8a56ea7c7e35379f6be36b613437983203505db615dc4763301421964aa21a3a`.
The 22-test direct suite passed; the command, public-CLI, and coverage-policy
focused roster passed `149` tests. Arbitrary-CWD interpreter and direct help
are each `594` stdout bytes at SHA-256
`e53ddb3fd536eba508875dc39de63f0e2603bf700e1785c72ccf521db4c659eb`
with empty stderr and status `0`; unknown-option failure has empty stdout,
status `2`, and stderr SHA-256
`cad357470e6acb1e3d7b9ba407cae1d078e9cfdf9c3c8bb65bf0afb7a8f4d696`.
From an unrelated working directory, tracked-profile dry-run returned status
`0`, empty stderr, and stdout SHA-256
`3963acb6a02cdb57c1567df5e5afb3a1db7c6d92873fdfc0336d71b024f353de`;
execute and repeat returned identical streams and a `1,191`-byte report at
SHA-256
`8082a5b420edd6361fcd6dfc167550896fbff940584b58febaae349990abd512`,
with no invocation-directory or transaction residue. Those raw, unnormalized
hashes use profile
`/Users/elisteiger/dev/norad/configs/runtime_preflight.example.tsv`, output
`/private/tmp/norad-mig04c-parity.uzl05m/output/preflight.tsv`, and working
directory `/private/tmp/norad-mig04c-parity.uzl05m/invocation`. Executable/test
work has not begun.
