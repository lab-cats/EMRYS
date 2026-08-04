# Project handoff

This is the canonical current takeover snapshot. Roadmap, status, acceptance,
and delivery-required lineage live in
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); exact commands live in
[`RUNBOOK.md`](RUNBOOK.md). Frozen delivery and branch history lives in the
[`operations-history record`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md).

## Checkout

- Branch: `codex/doc-cons-08e-separate-live-state-from-history`.
- Package base:
  `9cb4bb88788d5d58b9c918baa7993cafff145c5b`, the clean, published,
  upstream-equal `MIG-03O` documentation/lifecycle close.
- Selection checkpoint:
  `9bb7a1a99ba96f0412271b2a0c24b85a605bbc3c`, published and proved equal
  before authoring.
- Current documentation tip: the commit containing this handoff; resolve its
  exact local, upstream, and live-remote identity from Git.
- Completed package: documentation-only/non-consuming
  [`DOC-CONS-08E`](../tasks/COMPLETED/DOC-CONS-08E-separate-live-state-from-history.md).
  It created the operations-history owner, separated frozen material from
  three live views, and changed no executable, configuration, dependency,
  schema, fixture, report template, test-selection, scheduler, runtime,
  cluster, scientific-review, or biological surface. No card is selected.
- Physical migration: complete. `MIG-03A` extracted the neutral reporting
  library; `MIG-03B` through `MIG-03O` migrated the frozen fourteen-owner
  topology. Final ownership routes through
  [`FUNCTIONAL_OWNER_INVENTORY.md`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
  and
  [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).
- Default-branch integration remains outside this package and requires a
  separate explicit decision.

## Active concurrent lanes

No mutable concurrent lane shares this worktree, branch, card, or write set.
The canonical branch above is the sole integration/control lane for
`DOC-CONS-08E`. Frozen recovery sources, completed synthetic-exchange
identities, and preserved unmanaged worktrees are historical state, not active
lanes; their exact identities and cautions remain in the
[`operations-history record`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md#frozen-coordination-and-recovery-identities).

The post-`CONCURRENCY-01` first-use strategy condition is satisfied. That
removes only the discussion pause; it does not select work, accept candidate
content, or relax planning, lane-packet, integration, validation, or
publication requirements.

Any future concurrent mutation requires a fresh lane packet under
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#required-lane-packet). Historical
source preservation does not grant write, integration, publication, runtime,
or evidence authority.

## Evidence boundary

| Surface | Current verified state |
| --- | --- |
| Physical source/test ownership | The neutral validation-report library and all fourteen functional owners are physically migrated; legacy executable/test owners and temporary compatibility paths are absent. This is contract-preserving local migration evidence, not new runtime or cluster proof. |
| Steps `00a` through `06` | Earlier production executions remain cluster-proven, including refreshed Step `02b` QC across the six final Step `02` BAMs. That evidence predates the physical cutovers; migration acceptance was local and does not relabel the new paths as newly cluster-proven. |
| Step `07` | Implemented and fixture/mock-bcftools tested locally; no real-bcftools or cluster proof. |
| Steps `08` and `09` | Implemented and shell/fake-R plus guarded-real-R tested locally; no cluster or production proof. Step `09` emits CMH-ranked candidates, not validated editing sites. |
| Step `09c` | Implemented and synthetic-fixture tested locally; no production evidence package or completed scientific review. |
| Schemas, adapters, run summary, report bundle, and populated demo | Implemented and synthetic-fixture tested, including pinned local rendering where applicable; no production transaction, report, or evidence promotion. |
| Runtime, reference, and storage helpers | Implemented and locally fixture-tested. No CSU batch runtime report, production reference report, production storage report, or approved production retention policy exists. |
| Structured step validators | All Step `00a` through `09` validators are implemented and locally fixture/report tested. Their exact checks and limitations belong to the adjacent owner contracts and completed migration cards. |
| Final migration acceptance | The final `MIG-03O` executable state passed its focused suites, final-path coverage, and exact complete applicable gate after the documentation links were repaired. The earlier sandbox-DNS stop and later eight-link aggregate failure remain non-green attempts; the final pass does not relabel them. Exact commands, totals, timings, and coverage remain in the [`MIG-03O` card](../tasks/COMPLETED/MIG-03O-migrate-assemble-scientific-review-evidence-package-owner.md) and [dated refactor log](../history/audits/2026-08-02-refactor-log.md). |
| Latest documentation package | `DOC-CONS-08E` is documentation-only/non-consuming. Its applicable acceptance was semantic no-loss review plus Git and documentation validation; computational and cluster suites were not applicable. |

Transaction completion establishes only reconciliation of the declared
transaction. It does not prove every source exists or passed and does not
promote runtime, cluster, scientific, or biological state. Current validation
policy and risk routes remain in
[`TEST_BASELINE.md`](../design/TEST_BASELINE.md); dated totals and timings remain
in [testing history](../history/testing/).

## Cohort and preserved scientific evidence

The paired-end cohort remains:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Explicit paired strata remain:

```text
replicate 2: ABE_EV_2 / ABE_PUM1_2
replicate 3: ABE_EV_3 / ABE_PUM1_3
replicate 4: ABE_EV4  / ABE_PUM1_4
```

`ABE_EV4` intentionally lacks an underscore. Pairing comes from explicit
manifest metadata, never from sample names.

Step `03` found all libraries reverse-stranded / first-strand-style:

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| --- | ---: | ---: | ---: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The post-hardening `ABE_EV_2` Step `03` rerun matched its earlier report.
`ABE_EV_2` remains a mapping outlier, not an established pipeline failure.
`FWD_like` and `REV_like` are mechanical flag groupings;
`legacy_provisional_v1` is a compatibility policy, not a validated biological
strand model.

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` remains reserved and rejected until a
separately approved policy defines and unlocks stricter exit criteria. No
validated editing-site or causal biological conclusion exists.

## Preserved local recovery constraint

An earlier sibling-worktree `renv` activation attempted automatic bootstrap
before failing on missing packages and may have left ignored local cache
material. The exact malformed ignored path
`renv/library/macos/R-4.6/aarch64-apple-darwin23/macos/` contained only nested
empty `R-4.6/aarch64-apple-darwin23` directories (`0B`) and is absent from this
worktree. Its original directory tree remains preserved at
`/private/tmp/norad-r-library-quarantine.Z645n8/macos`.

Do not delete, repair, reuse, or automatically restore that quarantine. No
package was installed, restored, removed, or updated. Successful guarded checks
use the existing primary project library through `RENV_PATHS_LIBRARY`; the
earlier temporary Python-environment symlink remains removed.

## Current blockers

- The full production `samples.tsv` is not in this checkout. Its immutable
  cluster copy, explicit replicate values, persistence, and hash require
  inspection.
- Step `07` lacks real-bcftools and cluster evidence.
- CSU batch-visible R and package availability remain unresolved.
- Storage quota, scratch capacity, and retention policy remain unresolved.
- The exact Novogene annotation release remains partially unresolved.
- No production scientific-evidence review has been completed.
- The Step `09` structured validator does not independently recompute the CMH
  statistic, p-value, common odds ratio, or table estimability from DP/AD
  counts. The independent oracle characterizes a later compatible correction;
  it did not change production validation.
- Exact check rosters and all public Python, shell, R, Make, SLURM, and utility
  surfaces are characterized. Shared roster-consumer defects, public CLI
  exceptions, embedded or mode-less jobs, the Bash `3.2` empty-array dry-run
  defect, default dry-run side effects, and non-uniform submit-CWD, module,
  file-mode, and output-validation policies remain characterized behavior, not
  approved design.
- Publication-fault tests intentionally preserve the confirmed same-size
  rewrite, late-foreign-final, incomplete-rollback, descriptor, and stale-lock
  failure states. Passing characterization does not bless those recovery
  behaviors.
- Owner-specific scheduler, direct-final publication, replacement, rollback,
  stale-output, and transaction defects remain exactly as characterized in
  the completed migration cards and dated refactor log. Physical relocation
  did not fix or approve them.

## Immediate resume point

`DOC-CONS-08E` is complete in the commit containing this handoff. Its one
documentation commit contains the history destination, the three compressed
live owners, direct navigation/ownership repairs, lifecycle completion, and
the complete documentation gate result. No computational or cluster suite was
applicable because the predecessor-to-final diff is non-consuming Markdown.

Physical migration is complete and no final-audit or later-owner package is
preloaded. `PROGRAM-01`, `CONCURRENCY-03`, `TASK-EPIC-01`, `AUDIT-99`, the
remaining documentation-consolidation cards, recovered TODO work, and all
UNREFINED proposals remain outside this package and unselected unless their
own lifecycle files state otherwise.

No card is selected. Verify the exact branch, `HEAD`, upstream and live remote
equality, cleanliness including untracked files, and recovery/lock state before
continuing. Any continuation begins with one dependency-valid JIT selection
and a separately approved task-specific plan; history links do not authorize
it.
