# EMRYS safety guard

EMRYS is research software for local development and CSU SLURM execution.
Correctness, recoverability, scientific meaning, and honest evidence claims
take priority over speed or convenience.

## Authority

- Use the [workflow kernel](docs/operations/WORKFLOW.md) to load the smallest
  sufficient current context and deliver one approved bounded outcome.
- Use one authoritative mutable worktree and branch. Other worktrees are
  read-only unless the user explicitly changes the authority boundary.
- Implement only the approved outcome. Merging, rebasing, force-pushing,
  deleting branches, dependency installation, cluster execution, production
  mutation, destructive cleanup, scientific review, and evidence promotion
  require their own explicit authority.
- Every architecture audit records concrete compression opportunities across
  every maintained surface. Follow the permanent
  [architecture guardrails](docs/design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
  Implementation defaults to a meaningful net reduction in maintained product
  code and no product-file growth; any quantified exception requires explicit
  user approval.
- Before implementing any slice, search the touched code and adjacent
  production owners for duplicate mechanics and existing abstractions, record
  concrete consolidation or retirement candidates, and prefer caller-complete
  reuse or removal over parallel logic.
- Run quick targeted checks locally and long checks in CI.
- Before adding owned machinery, evaluate the existing repository authority,
  the standard library, a mature maintained tool/library, and the relevant
  established package manager. Bespoke code requires a recorded capability
  gap or a demonstrably smaller total maintained surface.
- Add a shared policy authority only when at least two production owners make
  the same decision from equivalent inputs with the same semantics and one
  bounded migration retires every duplicate caller net-negatively. Re-admission
  at a distinct trust or mutation boundary is not duplication.
- Snakemake remains the sole execution backend and Slurm remains transport.
  Reconsider that boundary only for a concrete approved extension or a
  demonstrated caller-complete reduction, with parity and no duplicate
  authority. Do not add a distinct Artifact Store without a separately approved
  concrete unmet need; current class-specific authorities remain valid.
- Implement the smallest complete feature. A token deletion beside new parallel
  logic is not meaningful compression: audit duplicate callers, branches,
  adapters, compatibility paths, tests, scripts, configuration, and docs across
  the touched vertical, and retire every safely superseded surface.
- Treat boundary values as immutable by default. A `Run` is an immutable plan:
  changing that plan creates a distinct `Run`, never an in-place mutation. This
  settles no other public noun, nesting, identity, API, backend, persistence,
  or policy choice until after audit review and a separate approved decision.

## Repository, runtime, and data safety

- Preserve public CLIs, paths, schemas, headers, ordering, hashes, check IDs,
  exits, receipts, locks, rollback, recovery, and scientific semantics unless
  an approved change explicitly replaces them.
- Use tiny safe fixtures locally. Heavy alignment, sorting, mpileup, and
  analysis run only inside an approved compute allocation through the grouped
  whole-Run SLURM path.
- Never commit production reads, BAM/CRAM/VCF data, large results, logs,
  credentials, private data, restored tools, runtime libraries, or caches.
- Do not delete, repair, move, compress, overwrite, or adopt shared or
  production artifacts without explicit operator intent. Preserve ambiguous
  locks, partials, backups, logs, and recovery markers.
- Compute, validation, rendering, and scheduler code never installs or repairs
  dependencies. Explicit Doctor/runtime repair is a separate operator action
  that delegates dependency solving and installation to an established package
  manager within the selected environment and authority boundary.

## Evidence guard

Keep implementation, local fixtures, real local runtime, cluster dry-run,
cluster proof, scientific review, and biological interpretation distinct.
Scheduler success, output presence, schema validity, a receipt, or a report is
not proof of a higher layer.

Protections are executable/static defenses; evidence is retained support for a
claim, reproduction, or recovery. A dual-purpose artifact obeys the
[architecture guardrails](docs/design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
An existing surviving defense may satisfy equal-or-stronger replacement.
Deleting exact evidence requires separate explicit user approval and its own
commit, and never offsets implementation growth.

Use **CMH-ranked candidates**, not validated editing sites. `FWD_like` and
`REV_like` are mechanical labels, not biological strand claims. EMRYS ends
with computational candidates and provenance. Candidate review, adjudication,
and biological interpretation are external work-process records, not pipeline
steps, gates, artifacts, or completion states.

## Owner rule

Each functional owner keeps its commands, contract, tests, diagnostics, and
recovery detail beside its implementation. Cross-owner identity and dependency
direction are organized by the [architecture index](docs/architecture/README.md).
Live Git owns checkout state; exact checks and retained artifacts bound to a
commit own validation observations. Accepted work and acceptance live in the
[findings matrix](docs/tasks/backlog_matrix.md), cross-cutting commands in the
[RUNBOOK](docs/operations/RUNBOOK.md), and common recovery in
[TROUBLESHOOTING](docs/operations/TROUBLESHOOTING.md).
