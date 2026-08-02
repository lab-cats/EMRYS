# Direct migration mechanics

This file is the canonical reusable procedure for future bounded source-
migration cards. Target homes and dependency direction are owned by
[`SOURCE_TOPOLOGY.md`](SOURCE_TOPOLOGY.md); this procedure defines reversible,
contract-preserving movement to those homes. It performs no migration and does
not authorize packaging, public-version distribution, orchestration, or job
materialization.

## Migration unit and invariants

One migration unit is one functional owner or one separately approved neutral
concern. Its final source and test homes must already be unambiguous in the
target topology. At migration start, refresh only that unit's direct imports,
invocations, Make callers, jobs, tests, report consumers, documentation links,
file modes, and native assets.

The unit preserves all characterized contracts unless its approved migration
card explicitly identifies a separate interface change:

- inputs, outputs, filenames, schemas, ordering, hashes, and receipts;
- help, arguments, environment overrides, working-directory behavior, and
  stdout/stderr roles;
- dry-run/execute selection, side effects, exit status, and signals;
- validation, locking, publication, no-clobber, replacement, rollback,
  recovery, and cleanup behavior;
- scientific method, neutral orientation language, evidence states, and
  biological-readiness rejection; and
- scheduler delegation, resource assumptions, and native asset semantics.

Relocation never makes a characterized defect an approved contract. It either
preserves the characterized behavior for a separately owned correction or
stops when parity cannot be defined without changing it.

## Reversible checkpoints

Every migration records these boundaries as coherent commits; a phase may be
combined with its neighbor only when no intermediate caller can break.

1. **Frozen baseline** — exact clean parent, direct-consumer roster, file modes,
   applicable characterization, and rollback target are recorded before a
   move.
2. **Final-owner introduction** — implementation and native assets move once
   to the target owner. If known callers cannot move atomically, the old path
   becomes only an approved temporary wrapper; it never retains a second
   implementation.
3. **Caller cutover** — direct callers move in bounded dependency order while
   old/new parity remains observable. New callers use only the final path.
4. **Compatibility removal** — any temporary wrapper is removed only after its
   named consumers and parity obligations are closed.
5. **Documentation close** — current topology, commands, links, diagrams, and
   the migration card change after the final executable state is fixed.

Before compatibility removal, rollback reverts caller cutovers in reverse
order and then the final-owner introduction. After removal, rollback first
restores the wrapper checkpoint, then reverses callers and the move. Rollback
uses repository history; it does not copy an implementation back into a second
owner or delete runtime, production, lock, backup, or recovery artifacts.

The final accepted tree has one implementation owner and no migration wrapper.
A hybrid tree is an explicit, time-bounded checkpoint, never target
architecture.

## Temporary-wrapper policy

A legacy-path wrapper is necessary only when at least one named, currently
supported caller cannot move atomically with the implementation and a direct
cutover would otherwise break that caller. The migration card records every
such caller and the parity check that permits its later cutover.

A wrapper is not justified by hypothetical external use, convenience for
stale tests or documentation, avoidance of caller discovery, or a desire to
keep two public paths indefinitely. When all known callers are repository-
owned and can change coherently with the move, migration uses a direct cutover
without a wrapper.

An approved wrapper:

- occupies only the legacy path and preserves its executable mode when that
  mode is part of the public contract;
- resolves the final entry point independently of caller working directory;
- forwards arguments, environment, standard input/output/error, signals, and
  exit status without reinterpretation;
- contains no defaults, validation, scientific logic, output creation,
  locking, publication, cleanup, or fallback implementation; and
- emits no new warning or diagnostic unless that output change is separately
  approved and parity-tested.

The wrapper is removable only when all named callers use the final path, exact
repository searches find no undeclared legacy invocation/import, both paths
have passed the applicable parity obligations, runbook and documentation links
use the final path, and the rollback checkpoint can restore the wrapper. The
removal commit deletes the wrapper and its wrapper-only tests together; it does
not retain a forwarding module in the target package.
