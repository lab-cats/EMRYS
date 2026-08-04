# Refactor delivery and branch lineage

- Frozen date: 2026-08-03.
- Originating documents:
  [`HANDOFF.md`](../../operations/HANDOFF.md),
  [`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md), and
  [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md).
- Immutable source commit:
  `9cb4bb88788d5d58b9c918baa7993cafff145c5b`.

This record preserves operational and branch-lineage facts removed from the
live owners by `DOC-CONS-08E`. It is not current checkout, roadmap, lane,
validation, runtime, cluster, scientific-review, or biological evidence.
Resolve those states from the live owners and Git.

## Frozen delivery boundary

At the source snapshot:

- the documentation, architecture, testing, concurrency, and recovery
  packages preceding physical migration were complete as recorded in the
  [dated refactor log](../audits/2026-08-02-refactor-log.md), the
  [testing-history record](../testing/2026-08-01-test-baseline-and-public-contract-traceability.md),
  and their completed task cards;
- `MIG-03A` had extracted the neutral validation-report library, and
  `MIG-03B` through `MIG-03O` had migrated the frozen fourteen-owner physical
  topology one dependency-valid owner at a time;
- the physical migration was complete at documentation/lifecycle checkpoint
  `9cb4bb8`, after executable/test checkpoint `d1cce50` for the final Step
  `09c` owner;
- no final-audit package or later owner was created or selected;
- no mutable concurrent lane shared the canonical worktree or branch; and
- remote `master` remained outside the campaign at
  `3d761a596d6cdf6595087bcfa9645af3d4b4b758`. That is a frozen observation,
  not a current remote claim.

Five checkpoint identities were unique to the removed live-view chronology
and are preserved here:

| Checkpoint | Frozen role |
| --- | --- |
| `dd19f0f` | Validation-efficiency implementation checkpoint preceding the measured serial and parallel gates. |
| `ead6ff4` | Published LOG-01 current-output characterization close. |
| `3f91fce` | Published MIG-03M documentation/lifecycle close and base of the neutral remediation lane. |
| `2df3e6c` | Repository-health program-decision checkpoint on that remediation lineage. |
| `4fde698` | MIG-03O selection checkpoint preceding its five test-only slices and executable cutover. |

The exact migration definitions, sequential reviews, test-only checkpoints,
cutovers, validation results, documentation closes, characterized defects,
and evidence ceilings remain in the
[`MIG-03A` through `MIG-03O` completed cards](../../tasks/COMPLETED/README.md)
and the [dated refactor log](../audits/2026-08-02-refactor-log.md). Current
implementation ownership routes through the
[`FUNCTIONAL_OWNER_INVENTORY.md`](../../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
and the
[`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md)
contract instead of this history record.

## Frozen coordination and recovery identities

The required post-`CONCURRENCY-01` first-use strategy discussion completed on
2026-07-31. That removed only the discussion pause; it did not select work,
accept candidate content, or relax planning, lane-packet, integration,
validation, or publication requirements. The durable policy remains in
[`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md).

| Record | Frozen identity and disposition |
| --- | --- |
| Consolidated recovery source | Lane `reconciliation-consolidated-01-sidecar`; worktree `/Users/elisteiger/dev/norad-worktrees/reconciliation-consolidated-01-sidecar`; branch `codex/reconciliation-consolidated-01-sidecar`; base `44a27f033092cd42b79a9504b7fc292d3cc40f20`; canonical parent `0fd6348e6cfe54457fef5f65f3468bea106e61f9`; immutable source `5a35a057cd9ca259f83ee1dde3116fee63928d72`. The source was consumed without merge, rebase, replay, or cherry-pick and retained no write reservation. |
| Recovery integration | `RECONCILIATION-CONSOLIDATED-01` covered 11 immutable packets, 16 proposal commits, 132 changed-path rows, and 80 requests: 51 `accept`, two `partial`, 24 `defer`, three `stale`, and zero `reject`. Commit trailers preserve the exact request and residual dispositions. The package created eight TODO cards and eight nonselectable UNREFINED proposals; its nine then-expected location findings were later resolved by completed `TASK-LIFECYCLE-01`, not waived by recovery. |
| Synthetic exchange | Lane `c02-synthetic-v2`; worktree `/Users/elisteiger/dev/norad-worktrees/concurrency-02-synthetic-exchange-reconciliation`; branch and remote source ref `codex/concurrency-02-synthetic-exchange-reconciliation`; base `8ba7a5cb39a7c87bc60e833eb0d061aaf758ad7c`; frozen source `7385668edf52a5bb2db0a18ac50c7b890f596ac9`; canonical parent `590ba1e9981159bb5814996d41b90c333f036ccb`; coordination checkpoint `a47ce4c`. Package `CONCURRENCY-02-SYNTHETIC-V2` was applied, the source was preserved, and its temporary fragment was removed after terminal dispositions. |
| Synthetic requests | `C02-SYNTH-V2-01` was accepted; `C02-SYNTH-V2-02` was partial, with the authorized lifecycle clarification accepted and automatic semantic acceptance rejected; `C02-SYNTH-V2-03` was rejected because a fragment archive would create a shadow backlog; `C02-SYNTH-V2-04` was deferred to existing `CONCURRENCY-03`. |
| Preserved proposal state | Local proposals `8374c96`, `823f198`, and `1afae15` remained historical review evidence and were not merged, rebased, or replayed. The earlier researcher-path pilot was accounted for through the immutable consolidated source; transient status and duplicate ownership were not replayed. |
| Preserved unmanaged checkout | Detached worktree `/Users/elisteiger/dev/norad-demo-report` at `f9aef17f4d6a2aa6e88feb41f85c1364af194889` predated the concurrency policy. At the snapshot it remained unmanaged preserved state and required separate inspection and operator direction before reuse, movement, or removal. |

The completed
[`CONCURRENCY-02`](../../tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md)
card and the dated refactor log retain the protocol, source provenance, and
evidence boundary. None of these exchanges established executable, runtime,
cluster, scientific-review, or biological evidence.

## Legacy local branch lineage

The following source-owned branch view preceded the physical-migration
campaign. Bracketed entries were planning boundaries, not branch names or
completed lineage:

```text
report-html-v1a-report-table-approvals
└── report-html-v1b-docs-responsibility-consolidation
    └── report-exports-v1
        └── post09-runtime-preflight
            └── post09-reference-provenance
                └── post09-storage-inventory-retention
                    └── post09-validation-report-00a
                        └── post09-validation-report-00b
                            └── post09-validation-report-00c
                                └── post09-validation-report-01
                                    └── post09-validation-report-02
                                        └── post09-validation-report-02b
                                            └── post09-validation-report-03
                                                └── post09-validation-report-04
                                                    └── post09-validation-report-05
                                                        └── post09-validation-report-06
                                                            └── post09-validation-report-07
                                                                └── post09-validation-report-08
                                                                    └── post09-validation-report-09
                                                                        └── refactor-00-comprehensive-audit
                                                                            └── refactor-01-test-baseline
                                                                                └── refactor-01a-step09-independent-cmh-oracle
                                                                                    └── refactor-01a1-demo-report-command
                                                                                        └── refactor-01aa-validation-efficiency
                                                                                            └── refactor-01b-validation-publication-faults
                                                                                                └── refactor-01-architecture-direction-docs
                                                                                                    └── codex/context-start-policy
                                                                                                        └── codex/concurrent-doc-sidecars
                                                                                                            └── codex/strategy-task-cards
                                                                                                                └── codex/refactor-01c-validation-check-rosters
                                                                                                                    └── codex/refactor-01d-public-cli-contracts
                                                                                                                        └── codex/refactor-01e-slurm-contracts
                                                                                                                            └── codex/refactor-01f-independent-goldens
                                                                                                                                └── codex/refactor-01z-test-sufficiency-gate
                                                                                                                                    └── codex/log-01-characterize-current-output-reconciliation
                                                                                                                                        └── codex/log-02-define-logging-contract-reconciliation
                                                                                                                                            └── codex/concurrency-02-fragment-protocol-reconciliation
                                                                                                                                                └── codex/program-01-slice-1-critical-runway
                                                                                                                                                    └── codex/arch-02a-slice-7-infer-paired-read-orientation-contract
                                                                                                                                                        └── [future descendants selected after reassessment]
                                                                                                                                                            └── refactor-99-final-audit
```

Subsequent package-by-package lineage and publication evidence is recorded in
the dated refactor log and completed cards rather than duplicated here.

## No-loss destination map

| Removed live-view material | Canonical frozen destination |
| --- | --- |
| Package definitions, reviews, implementation/test checkpoints, documentation closes, rollback order, and characterized defects | Completed task cards and the [dated refactor log](../audits/2026-08-02-refactor-log.md) |
| Test totals, timings, coverage, failure ceilings, dependency state, and validation provenance | The dated refactor log, completed cards, and [testing history](../testing/) |
| Completed capability rosters and final source homes | [`FUNCTIONAL_OWNER_INVENTORY.md`](../../architecture/FUNCTIONAL_OWNER_INVENTORY.md), source-local READMEs/contracts, and completed cards |
| Recovery, synthetic-exchange, preserved-source, and detached-worktree identities | This record, `CONCURRENCY-02`, and source-provenance trailers |
| Legacy branch-name chain | This record |
| Current checkout, lanes, evidence limits, blockers, and resume point | [`HANDOFF.md`](../../operations/HANDOFF.md) only |
| Current roadmap, status, acceptance, and delivery-required lineage | [`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md) only |
