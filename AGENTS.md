# NORAD safety guard

NORAD is research software for local development and CSU SLURM execution.
Correctness, recoverability, scientific meaning, and honest evidence claims
take priority over speed or convenience.

## Authority

- Use the
  [task-start context](docs/operations/TASK_START.md) to load the smallest
  sufficient current context.
- Use one authoritative mutable worktree and branch. Other worktrees are
  read-only unless the user explicitly changes the authority boundary.
- Implement only the approved outcome. Merging, rebasing, force-pushing,
  deleting branches, dependency installation, cluster execution, production
  mutation, destructive cleanup, scientific review, and evidence promotion
  require their own explicit authority.
- Local commits do not authorize a push. Follow the short
  [workflow kernel](docs/operations/WORKFLOW.md).

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

Use **CMH-ranked candidates**, not validated editing sites. `FWD_like` and
`REV_like` are mechanical labels, not biological strand claims.
`science_review_complete_exploratory` remains provisional, and
`biological_interpretation_ready` remains reserved until a separately approved
scientific policy defines and satisfies its exit.

## Owner rule

Each functional owner keeps its commands, contract, tests, diagnostics, and
recovery detail beside its implementation. Cross-owner identity and dependency
direction are organized by the [architecture index](docs/architecture/README.md).
Current evidence belongs in [HANDOFF](docs/operations/HANDOFF.md), roadmap and
acceptance in [PIPELINE_PLAN](docs/design/PIPELINE_PLAN.md), cross-cutting
commands in the [RUNBOOK](docs/operations/RUNBOOK.md), and common recovery in
[TROUBLESHOOTING](docs/operations/TROUBLESHOOTING.md).
