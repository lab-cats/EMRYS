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

## Caller-migration order

Cutover follows the refreshed direct-consumer graph from the moved owner
outward. A wrapper-backed migration uses this order; a wrapper-free migration
applies the same order within one atomic executable commit.

1. Introduce the final-owner implementation and make its owner-local relative
   resources, imports, and native-asset references resolve there.
2. Move same-owner launchers and validators to the final implementation while
   preserving their public interfaces and independent checks.
3. Update stage-local SLURM entry points and any neutral scheduler adapter that
   invokes the owner.
4. Update direct workflow/orchestration callers and literal Make expansions;
   do not replace explicit paths with discovery or numeric-order inference.
5. Update artifact adapters, report consumers, configuration, and schema
   references only when they name the source path; artifact identities and
   data contracts otherwise remain unchanged.
6. Move owner-local tests and fixtures with the owner, update independent
   contract/integration suites as consumers, and retain old/new parity coverage
   until wrapper removal.
7. After executable and test state is final, update runbook commands, current-
   topology documentation, diagrams, links, and the migration card.

Each committed checkpoint must leave every supported caller executable through
either the final path or the single declared wrapper. A migration never edits
an output schema, scientific policy, or evidence vocabulary merely to make a
source path cutover easier.

## Parity evidence by migration class

The migration card selects only the rows applicable to its owner. “Parity”
means comparison against the frozen old-path baseline with identical explicit
inputs and controlled environment; it is not a license to bless newly observed
behavior.

| Class | Required parity evidence | Cutover and rollback boundary |
| --- | --- | --- |
| Python | Compare direct interpreter and executable-mode entry where supported: help, malformed arguments, arbitrary working directory, imports, dry-run and execute effects, stdout/stderr roles, exit status, deterministic artifacts, modes, and applicable focused/independent tests. Preserve the measured line/branch baseline across the path rename; a moved module is not treated as an unreviewed disappearance plus unrelated new file. | Update same-owner imports before external imports. A named CLI-path caller may receive a pure delegating wrapper; a named import caller may receive a temporary re-export only when exact imported names and import side effects are parity-tested. Do not require installation or alter `sys.path` globally. Roll back import callers before reverting the moved module, and restore the recorded executable bit and shebang behavior. |
| Shell | Compare explicit-interpreter and direct execution where each is supported: help, missing/malformed arguments, arbitrary working directory, environment overrides, resolved child commands, dry-run side effects, execute outputs, stdout/stderr, child exit, signals, modes, locks, staging, rollback, recovery evidence, and cleanup. Preserve interpreter requirements and characterized non-executable modes rather than silently “fixing” them during relocation. | A required legacy shell wrapper resolves the final path from its own location and uses `exec` with the original interpreter contract so arguments, streams, signals, and status pass through. It performs no setup or cleanup and does not change caller working directory. Cut over shell callers before removing the wrapper; roll them back first, then revert the moved script and its exact mode. |
