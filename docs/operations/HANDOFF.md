# Project handoff

This file records only live takeover facts that are not safely reconstructed
from Git, task cards, or history. Resolve the exact commit, upstream relation,
and worktree contents from Git; use
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) for durable queue order,
[`RUNBOOK.md`](RUNBOOK.md) for commands, and the
[`operations history`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md)
for frozen branch and delivery detail.

## Checkout

- Active branch: `codex/residual-source-topology-convergence`.
- The approved PI-readiness tranche is locally complete. Inspect Git for the
  exact clean-tree, tip, publication, and upstream-equality state.
- Cleanup modernized the user entry path and canonical documentation, removed
  the root `jobs/` scaffold, moved the retained cluster probe to its evidence
  owner, and retired the unused generic scheduler scaffold. Two unconsumed
  workflow profiles remain inert and deferred; no orchestrator reads them.
- `DOC-PIPE-04`, `SIZE-07A`, `SIZE-07B`, `SIZE-07D`, `SIZE-07E`, `SIZE-07F`,
  and the bounded `LIB-03` seam each have their own outcome commit. The
  standalone size-inventory prerequisite is retired, and no successor package
  is selected.

## Active concurrent lanes

No independently authorized external integration lane or active tranche lane
is recorded. Git status and explicit integration coordination are
authoritative; do not reset, stash, rebase, clean untracked paths, or modify
preserved worktrees to manufacture a clean checkout.

Any future independent mutation lane requires a fresh packet under
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#required-lane-packet). Historical
recovery material grants no write, integration, publication, runtime, or
evidence authority.

## Evidence boundary

| Surface | Current evidence ceiling |
| --- | --- |
| Physical ownership | Pipeline stages, neutral contracts/libraries, reporting, and evidence helpers are in their final owners; legacy compatibility owners are absent. This is contract-preserving local migration and static-review evidence, not new cluster or production proof. Exact topology belongs to [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md). |
| Steps `00a`–`06` | Earlier production executions remain cluster-proven, including refreshed Step `02b` QC for the six final Step `02` BAMs. That evidence predates physical relocation and does not relabel the new paths as newly cluster-proven. |
| Step `07` | Implemented and fixture/mock-bcftools tested locally; no real-bcftools or cluster proof. |
| Steps `08`–`09` | Implemented and shell/fake-R plus guarded-real-R tested locally; no cluster or production proof. Step `09` produces CMH-ranked candidates, not validated editing sites. |
| Step `09c` and reporting | Scientific-review packaging, schemas, adapters, run summary, report bundle, and populated demo are synthetic-fixture/local-render tested where applicable. There is no production evidence package, completed scientific review, production transaction, or production report. |
| Validators and operational helpers | Structured Step `00a`–`09` validators and runtime, reference, and storage helpers have local fixture/report evidence. There is no CSU batch runtime report, production reference or storage report, or approved production retention policy. |
| Completed cleanup/size tranche | Documentation and structural refactors do not promote runtime, cluster, scientific-review, or biological evidence. Final local evidence is `1625` Python passes with `17` skips and coverage `0.851502` line / `0.749803` branch across `71` files, all `14` shell-contract components, and `17` report-runtime passes with `60` deselections. Guarded R stops at the separately owned `renv` freshness check. |

A successful transaction proves only reconciliation of its declared inputs and
outputs. It does not prove every source exists or passed, and it does not
promote runtime, cluster, scientific, or biological state. Validation policy
and risk routes belong to [`TEST_BASELINE.md`](../design/TEST_BASELINE.md);
dated totals and timings belong in [testing history](../history/testing/).

## Cohort and preserved scientific evidence

The operational cohort has three explicit paired strata:

| Replicate | EV | PUM1 |
| --- | --- | --- |
| `2` | `ABE_EV_2` | `ABE_PUM1_2` |
| `3` | `ABE_EV_3` | `ABE_PUM1_3` |
| `4` | `ABE_EV4` | `ABE_PUM1_4` |

`ABE_EV4` intentionally lacks an underscore. Pairing comes from manifest
metadata, never from sample-name inference.

Step `03` classified every library as reverse-stranded / first-strand-style:

| Sample | Failed | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| --- | ---: | ---: | ---: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The hardened `ABE_EV_2` rerun matched its earlier report. `ABE_EV_2` remains
a mapping outlier, not an established pipeline failure. `FWD_like` and
`REV_like` are mechanical groupings; `legacy_provisional_v1` is a
compatibility policy, not a validated biological strand model.

`science_review_complete_exploratory` remains provisional, and
`biological_interpretation_ready` remains reserved and rejected pending a
separately approved policy. No validated editing site or causal biological
conclusion exists.

## Preserved local recovery constraint

An earlier sibling-worktree `renv` activation created the malformed empty path
`renv/library/macos/R-4.6/aarch64-apple-darwin23/macos/`. It remains absent
from this worktree. Its former `/private/tmp` quarantine payload is also absent;
the quarantine root is empty, and the empty directory tree must not be
fabricated or automatically restored.

The preserved project library was not installed into, restored, or updated
during this tranche. Guarded checks bind `RENV_PATHS_LIBRARY` to the project-
library root (`renv/library`), not its platform-qualified leaf. Final
dependency validation identifies installed `renv` `1.2.3` as the sole out-of-
date package, so the aggregate R lane remains non-green until a separately
reviewed dependency-maintenance package resolves the drift.

## Current blockers

- The production `samples.tsv` is not in this checkout. Its immutable cluster
  copy, explicit replicate values, persistence, and hash still require
  inspection.
- Step `07` lacks real-bcftools and cluster evidence; Steps `08`, `09`, and
  `09c` lack production/cluster evidence and completed scientific review.
- CSU batch-visible R and package availability remain unresolved. The guarded
  local dependency check reports only installed `renv` `1.2.3` as out of date;
  do not mutate the environment as incidental refactor work.
- Storage quota, scratch capacity, retention policy, and the exact Novogene
  annotation release remain unresolved.
- The Step `09` structured validator does not independently recompute the CMH
  statistic, p-value, common odds ratio, or table estimability from DP/AD
  counts. The independent oracle characterizes a compatible future
  correction; it did not change production validation.
- Publication and recovery characterization intentionally retains known
  same-size rewrite, late-foreign-final, incomplete-rollback, descriptor, and
  stale-lock failure states. Passing characterization does not approve those
  behaviors. Other live defects and recheck routes remain indexed in
  [`REFACTOR_AUDIT.md`](../design/REFACTOR_AUDIT.md).

## Immediate resume point

No implementation or documentation slice remains in the approved tranche, and
no successor is selected. Any later work requires fresh user direction; the
formal onboarding family, runtime/cluster evidence, dependency maintenance,
scientific review, and production execution remain separate scopes.

The only non-green local gate component is the explicit `renv` freshness
check. Resolving it requires a separately reviewed dependency-maintenance
package and a fresh guarded-R run; it does not invalidate the passing Python,
shell-contract, report-runtime, or focused real-R evidence recorded above.

On any interrupted resume, first inspect the exact branch, `HEAD`, upstream,
worktree (including untracked files), active diff/card, locks, and preserved
recovery state. Dependency mutation, destructive cleanup, preserved-worktree
removal, default-branch integration, runtime or cluster execution, scientific
review, evidence promotion, and biological interpretation remain outside this
tranche.
