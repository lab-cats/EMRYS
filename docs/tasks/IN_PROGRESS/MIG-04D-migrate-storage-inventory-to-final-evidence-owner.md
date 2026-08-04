# MIG-04D — Migrate storage inventory to its final evidence owner

## Objective

Move the public storage-inventory command and its direct suite to the exact
permanent evidence-owner homes fixed by `SOURCE_TOPOLOGY.md`, cutting over every
repository-owned path consumer without changing non-path behavior.

## Why this exists

Storage inventory remains the final implementation-bearing flat source/test
pair whose functional owner and permanent paths are already fixed. Its two
explicit TSV contracts are root-owned public operator inputs, while the command
has no repository-relative implementation dependency or native asset, so the
evidence owner can move directly without a compatibility path.

## Fixed decisions

- Move `scripts/storage_inventory.py` to
  `src/norad/evidence/storage_inventory/storage_inventory.py` and
  `tests/test_storage_inventory.py` to
  `tests/evidence/storage_inventory/test_storage_inventory.py`.
- Use one Git-preserving direct atomic cutover. Every discovered live path
  consumer is repository-owned, and no external or unmovable caller is named
  in repository evidence or canonical operational routes. Hypothetical
  external use does not justify a wrapper, copy, symlink, re-export, package
  marker, descriptor, console script, installation metadata, `PYTHONPATH`, or
  `sys.path` mutation.
- Preserve the basename, shebang, intentional interpreter-only source mode
  `0644`, test mode `0644`, public arguments/help/streams/exits, arbitrary-CWD
  behavior, dry-run side effects, exact input/output headers and row order,
  path resolution, hashes, measurement/status/count semantics, and intentional
  exit zero when a published summary has `overall_status=fail`.
- Preserve read-only measurement: symlinks are counted but never followed, and
  the command never deletes, moves, archives, compresses, repairs, or cleans
  storage. Retention rows record approval state only; no action is executed.
- Preserve exact input stability checks, three-file summary-last publication,
  lock/staging/backups, predecessor validation, rollback, and cleanup,
  including the characterized incomplete-restoration defect that can retain
  all three `.previous` backups while removing the lock and without creating a
  recovery marker. This card relocates behavior; it does not repair or approve
  it.
- Move the source byte-identically because it has no repository-relative
  implementation dependency or native asset. Repair only the moved suite's
  repository-root/source anchors and add one bounded arbitrary-CWD
  dry-run/execute/repeat parity guard.
- Keep `configs/storage_roots.example.tsv` and
  `configs/retention_policy.example.tsv` at root with exact bytes and modes.
  They are explicit operator inputs, not owner-native private assets.
- The old source/test paths must be absent after cutover. Historical completed
  cards and dated audit records retain their time-specific paths.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal MIG-04C documentation close
  `e52f4e8526562f02ce82e2302f979ffc66269633`.
- Reverify the exact two-file owner roster, every Make/test/coverage/current-doc
  path consumer, any named external or unmovable caller in current evidence,
  and the two root-starter boundaries.
- Freeze source/test/config modes, sizes, hashes; help and parse-failure bytes;
  dry-run/execute/repeat output; measurement, approval, transaction, and fault
  behavior; arbitrary-CWD behavior; and current measured coverage before
  movement.

## Required context

- `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, completed `PLAN-03A` and
  `MIG-04C`, the command and direct suite, public-CLI/Make characterization,
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

- Root starter-contract movement; CLI, input/output schema, measurement,
  retention/approval, status, hashing, transaction, locking, rollback,
  recovery, or defect repair; any retention action or CSU storage/quota work;
  contract-test convergence; legacy-test review; final audit; setup-doctor or
  packaging work; scheduler, ingestion, orchestration/profile, runtime
  execution, cluster, production, scientific-review, or biological work.

## Deliverables

- One final storage-inventory command, one mirrored direct suite, every
  repository caller on the final paths, and no legacy implementation or
  compatibility path.

## Acceptance evidence

- Pre/post interpreter help, malformed arguments, dry-run, execute, and repeat
  execution from repository root and an unrelated working directory have exact
  stdout/stderr/exits and fixed-fixture report bytes, apart from approved
  repository command-path substitutions outside product output. Live available-
  root inventory capacity/free-space fields are not claimed universally stable.
- Source mode and bytes remain exact. A normalized moved-test diff contains
  only its repository-root/source anchors and approved parity guard. The root
  starters retain their exact modes, sizes, and SHA-256 values:
  `storage_roots.example.tsv` is mode `0644`, size `270`, SHA-256
  `5205e1f1656b66c886c6a6d77d33a58457ba7eb078e2e9554fa7c59c9150e433`;
  `retention_policy.example.tsv` is mode `0644`, size `335`, SHA-256
  `e51cffd118cd4d2726e4a7c4bb554ad6cac0ffe05a0a841c2a77190631ab3836`.
- The moved direct suite, public CLI/Make contracts, coverage-policy tests,
  storage publication/recovery faults, static and shell lanes, complete Python
  coverage, documentation validation, semantic diff review, and exact live
  old-path searches pass at the final executable state.
- Coverage identity moves atomically from `scripts/storage_inventory.py` to the
  final path with `240/281` covered/total lines and `74/106` covered/total
  branches, no owner/global regression, and no unrelated baseline promotion.
- Exact searches prove one final command, no wrapper/copy/symlink/package or
  install surface, and no moved or modified starter contract.
- Evidence remains local relocation, synthetic-fixture, transaction-
  characterization, and parity evidence only. It is not production/CSU storage
  or quota evidence, retention approval, runtime or cluster proof, scientific
  review, or biological readiness.

## Canonical documentation updates

- Functional-owner inventory and residual counts, source-topology implemented
  state, public runbook commands, `TEST_BASELINE.md`, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, lifecycle links, and this card.

## Escalation conditions

- Stop for an external unmovable caller; any wrapper, compatibility, package,
  descriptor, console-script, install, or path-mutation need; any source-byte,
  CLI/input/output/header/order/status/hash/measurement/transaction/fault/
  coverage delta; source/test mode drift; starter-contract movement or
  modification; retention action; unknown generated caller; or scope into
  contract-test convergence, legacy review, setup doctor, scheduler, ingestion,
  orchestration/profile, runtime execution, cluster, scientific-review, or
  biological work.

## Completion record

Selected from clean, published, live-remote-equal MIG-04C documentation close
`e52f4e8526562f02ce82e2302f979ffc66269633`. The bounded read-only audit found
exactly two owned files; every discovered path consumer is repository-owned,
with no external or unmovable caller identified in canonical repository
evidence. Pre-change source evidence is mode `0644`, `16,395` bytes, SHA-256
`06f624b972812cc5f0b26d9cfefde1d79154f10e910487d80ae79548416338e0`;
the direct suite is mode `0644`, `9,270` bytes, SHA-256
`1c70368862954d41e7f3295f7cd5a3b19755fc396066f7b146991291d71b8f3e`.
The 8-test direct suite passed; the command, public-CLI, and coverage-policy
focused roster passed `135` tests. Arbitrary-CWD interpreter help is `415`
stdout bytes at SHA-256
`b63be2c5d4ed6b54cad3749d8fadb3a30d03240f8c294a2b1c26b642193a67a8`
with empty stderr and status `0`; unknown-option failure has empty stdout,
status `2`, and `287` stderr bytes at SHA-256
`7682056671d834f913d8cbd98a86c66f89b2b1941e8142a3bc63e0b60855c76d`.
From unrelated working directory
`/private/tmp/norad-storage-parity.qTDP4V/invocation`, tracked-contract dry-run
returned status `0`, empty stderr, and stdout SHA-256
`deeb142d7991389458bc3dd6bec91223a56719d1c256ddbea39b8080786cfbd6`;
execute and repeat returned identical streams and identical three-file bytes
under `/private/tmp/norad-storage-parity.qTDP4V/output`, with no invocation-
directory or transaction residue: `storage_inventory.tsv` is `591` bytes at
SHA-256
`a75a7ab7f3f279124552d85962877ad8783cbd932bab6ab9b42b6c6385997e65`,
`retention_policy.tsv` is `335` bytes at SHA-256
`e51cffd118cd4d2726e4a7c4bb554ad6cac0ffe05a0a841c2a77190631ab3836`,
and `storage_retention_summary.tsv` is `389` bytes at SHA-256
`9a4768da297ab56be164189584725aa3a730d2fdb973402c9ce3d0c8c6af2ced`.
Executable/test work has not begun.
