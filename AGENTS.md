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
  every maintained surface. Follow the campaign's
  [per-slice protocol](docs/tasks/architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol).
  Implementation defaults to net-negative maintained product code and no
  product-file growth; any quantified exception requires explicit user
  approval.
- long running checks should be run in CI, with quick targeted checks
  being run locally
- prefer using standard libraries over bespoke implementation except
  when standard libraries would be insufficient or when bespoke implementation
  would permit for a smaller implementation
- features should be implemented with the MINIMUM possible footprint
  while still maintaining repo quality
- Treat boundary values as immutable by default. A `Run` is an immutable plan:
  changing that plan creates a distinct `Run`, never an in-place mutation. This
  settles no other public noun, nesting, identity, API, backend, persistence,
  or policy choice until after audit review and a separate approved decision.

## Repository, runtime, and data safety

- Preserve public CLIs, paths, schemas, headers, ordering, hashes, check IDs,
  exits, receipts, locks, rollback, recovery, and scientific semantics unless
  an approved change explicitly replaces them.
- Use tiny safe fixtures locally. Heavy alignment, sorting, mpileup, and
  analysis run only through the applicable owner-local SLURM entry point.
- Never commit production reads, BAM/CRAM/VCF data, large results, logs,
  credentials, private data, restored tools, runtime libraries, or caches.
- Do not delete, repair, move, compress, overwrite, or adopt shared or
  production artifacts without explicit operator intent. Preserve ambiguous
  locks, partials, backups, logs, and recovery markers.
- Compute, validation, rendering, and scheduler code never installs or repairs
  dependencies. Restoration is a separate operator action.

## Evidence guard

Keep implementation, local fixtures, real local runtime, cluster dry-run,
cluster proof, scientific review, and biological interpretation distinct.
Scheduler success, output presence, schema validity, a receipt, or a report is
not proof of a higher layer.

Protections are executable/static defenses; evidence is retained support for a
claim, reproduction, or recovery. A dual-purpose artifact obeys both
[campaign guardrails](docs/design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
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
