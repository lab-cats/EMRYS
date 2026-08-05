# Project handoff

This is the canonical current takeover snapshot. Roadmap, status, acceptance,
and delivery-required lineage live in
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); exact commands live in
[`RUNBOOK.md`](RUNBOOK.md). Frozen delivery and branch history lives in the
[`operations-history record`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md).

## Checkout

- Branch: `codex/residual-source-topology-convergence`.
- Campaign base:
  `3efe461ee7111291852417ad5e4165977937de4c`, the clean, published,
  upstream-equal `PLAN-03A` documentation/lifecycle close.
- Latest executable/test checkpoint:
  `8921ec37348d78e8a9b0a374c155ea8cd1be0d53`, the `MIG-04F` direct
  validation-roster relocation and fourteen-caller cutover, and the frozen
  executable basis for this documentation/lifecycle close.
- Current package predecessor:
  `1311db325c20d00a6f37c73289892a519ac4ffa8`, the clean, published,
  live-remote-equal `REVIEW-LEGACY-04A` documentation/lifecycle close.
- Current tip and upstream relationship: resolve the exact identity and
  equality from Git; this handoff owns the branch and lifecycle state rather
  than duplicating a moving commit ID.
- Completed planning predecessor: documentation-only/non-consuming
  [`PLAN-03A`](../tasks/COMPLETED/PLAN-03A-inventory-and-sequence-residual-source-topology-convergence.md).
  It partitions the residual source/test roster, fixes cross-cutting target
  homes and JIT order, corrects mutable report dependencies, and changes no
  executable, configuration, dependency, schema, fixture, report template,
  test-selection, scheduler, runtime, cluster, scientific-review, or biological
  surface.
- Completed decision package:
  [`LIB-02F`](../tasks/COMPLETED/LIB-02F-define-shared-library-ownership.md)
  settled the two observed peer-implementation seams without changing a
  consumed surface. It fixed bottom-up neutral scientific-evidence contracts,
  a reporting-local committed-package reader/projection, and a neutral
  `reference_contigs` parser library as the permanent directions.
- Completed residual migration:
  [`MIG-04A`](../tasks/COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
  moved the neutral artifact validator, five schemas, direct test, and four
  valid fixtures to their permanent owners and cut over all reviewed consumers
  without a wrapper or schema/behavior change.
- Completed residual extractions:
  [`LIB-02G`](../tasks/COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md)
  moved the public Step `08` table/manifest contract and direct suite into
  their permanent neutral owners, cut over every reviewed Python consumer, and
  left no Step `08` compatibility owner or package-path dependency. Completed
  [`LIB-02H`](../tasks/COMPLETED/LIB-02H-extract-step09-scientific-evidence-contract.md)
  did the same for the public Step `09` output contract without changing the
  Step `09c` review-package policy or publication behavior. Completed
  [`LIB-02I`](../tasks/COMPLETED/LIB-02I-extract-step09c-review-package-contract.md)
  moved the public thirteen-file Step `09c` review-package roster, headers,
  vocabularies, bindings, and state reducer into their permanent neutral owner,
  and eliminated artifact indexing's private Step `09c` dependency. Completed
  [`LIB-02J`](../tasks/COMPLETED/LIB-02J-remove-run-summary-private-step09c-dependency.md)
  then replaced run-summary's remaining private Step `09c` context/policy edge
  with a reporting-local committed-package reader/projection without changing
  the normalized record or Step `09c`. Completed
  [`RPT-05A`](../tasks/COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md)
  then moved all six reporting sources, three private assets, five direct
  suites, and three fixture groups into their final owners with no wrapper and
  no behavior delta beyond approved path-derived provenance. Completed
  [`LIB-02K`](../tasks/COMPLETED/LIB-02K-extract-reference-contig-parser-library.md)
  then extracted the characterized ordered FASTA, FAI, and DICT parsers into
  the permanent neutral `reference_contigs` library, added its independent
  suite, cut over reference provenance plus the final Step `00c`/`05`
  validators, and removed both peer-owner bridges without moving the evidence
  command.
- Completed evidence-owner relocation:
  [`MIG-04B`](../tasks/COMPLETED/MIG-04B-migrate-reference-provenance-to-final-evidence-owner.md)
  directly moved the public reference-provenance command and mirrored suite
  into their fixed final evidence-owner homes, repaired only their self-
  relative anchors, and cut over every repository path consumer without a
  wrapper or public starter-config move. Completed
  [`MIG-04C`](../tasks/COMPLETED/MIG-04C-migrate-runtime-preflight-to-final-evidence-owner.md)
  then directly moved the public runtime-preflight command and mirrored suite
  into their fixed final evidence-owner homes, repaired only the suite's self-
  relative anchors, and cut over every repository path consumer without a
  wrapper or public starter-profile move. Completed
  [`MIG-04D`](../tasks/COMPLETED/MIG-04D-migrate-storage-inventory-to-final-evidence-owner.md)
  then directly moved the public storage-inventory command and mirrored suite
  into their fixed final evidence-owner homes, repaired only the suite's self-
  relative anchors, and cut over every repository path consumer without a
  wrapper or public starter-contract move. Completed
  [`MIG-04E`](../tasks/COMPLETED/MIG-04E-converge-independent-contract-goldens.md)
  then directly moved the independent-contract-golden suite and eight
  fixture/provenance files into their fixed final contract-integration owner,
  repairing only the suite's repository-root and owner-local-golden anchors.
  Completed
  [`MIG-04F`](../tasks/COMPLETED/MIG-04F-converge-validation-roster-agreement.md)
  then directly moved the validation-roster suite/helper into their fixed
  final contract-integration owner and cut over fourteen exact-file callers,
  repairing only the moved suite's repository-root anchor and caller path
  literals.
- Completed no-loss review:
  [`REVIEW-LEGACY-05A`](../tasks/COMPLETED/REVIEW-LEGACY-05A-confirm-step05-operational-checker-owner.md)
  confirms the unchanged Step `05` operational output checker at its permanent
  current repository-level owner. Its unique scheduler/cohort/TSV behavior is
  distinct from the stage validator, and its known duplicate-`tee` and silent-
  replacement defects remain characterized. Completed documentation-only/non-
  consuming
  [`REVIEW-LEGACY-04A`](../tasks/COMPLETED/REVIEW-LEGACY-04A-retire-step04-pending-test-scaffold.md)
  confirms `RETAIN_ROOT` for the byte-identical Step `04` pending scaffold.
  Its pre-Picard input-sort requirement is absent and adversarial dry-run
  quoting protection is not independently established.
- Selected package: documentation-only/non-consuming
  [`AUDIT-RESIDUAL-04A`](../tasks/IN_PROGRESS/AUDIT-RESIDUAL-04A-confirm-residual-source-topology-convergence.md).
  It reconciles only the fixed 87-path residual roster, completed moves, and
  retained/deferred/separately-retired boundaries.
- Pipeline-owner physical migration: complete. `MIG-03A` extracted the neutral
  validation-report library; `MIG-03B` through `MIG-03O` migrated the frozen
  fourteen-owner DAG topology. The residual artifact-contract owner is also
  migrated through `MIG-04A`, and the neutral Step `08`, Step `09`, and public
  review-package contracts are extracted through `LIB-02G`, `LIB-02H`, and
  `LIB-02I`, reporting's private Step `09c` dependency is removed through
  `LIB-02J`, and the reporting owner is physically final through `RPT-05A`.
  The reference-contig seam is final through `LIB-02K`, and reference-
  provenance evidence is physically final through `MIG-04B`.
  Runtime-preflight evidence is physically final through `MIG-04C`, and storage
  evidence is physically final through `MIG-04D`, and the independent-golden
  owner is physically final through `MIG-04E`. The validation-roster owner and
  its fourteen exact-file caller cutovers are final through `MIG-04F`.
  Current and target ownership route through
  [`FUNCTIONAL_OWNER_INVENTORY.md`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
  and
  [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).
- Default-branch integration remains outside this package and requires a
  separate explicit decision.

## Active concurrent lanes

No mutable concurrent lane shares this worktree, branch, card, or write set.
The branch above is the sole integration/control lane for the residual source-
topology campaign. Frozen recovery sources, completed synthetic-exchange
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
| Physical source/test ownership | The neutral validation-report, BAM-validation, and reference-contig libraries; all fourteen semantic DAG owners; the neutral artifact-contract validator/schemas/direct evidence; the neutral Step `08`, Step `09`, and public review-package scientific-evidence contracts/direct suites; the reporting source/assets/direct suites/fixtures; the reference-provenance, runtime-preflight, and storage-inventory source/direct-suite pairs; the independent contract goldens; and the validation-roster agreement are physically final. Their legacy ownership and temporary compatibility paths are absent. `REVIEW-LEGACY-05A` confirms the unchanged Step `05` operator checker at its permanent current repository-level owner, and `REVIEW-LEGACY-04A` confirms the unchanged Step `04` pending scaffold at `RETAIN_ROOT`. Other retained/deferred roots remain dispositioned by `PLAN-03A`. This is contract-preserving local migration/static-review evidence, not new runtime or cluster proof. |
| Steps `00a` through `06` | Earlier production executions remain cluster-proven, including refreshed Step `02b` QC across the six final Step `02` BAMs. That evidence predates the physical cutovers; migration acceptance was local and does not relabel the new paths as newly cluster-proven. |
| Step `07` | Implemented and fixture/mock-bcftools tested locally; no real-bcftools or cluster proof. |
| Steps `08` and `09` | Implemented and shell/fake-R plus guarded-real-R tested locally; no cluster or production proof. Step `09` emits CMH-ranked candidates, not validated editing sites. |
| Step `09c` | Implemented and synthetic-fixture tested locally; no production evidence package or completed scientific review. |
| Schemas, adapters, run summary, report bundle, and populated demo | Implemented and synthetic-fixture tested, including pinned local rendering where applicable; no production transaction, report, or evidence promotion. |
| Runtime, reference, and storage helpers | Implemented and locally fixture-tested. No CSU batch runtime report, production reference report, production storage report, or approved production retention policy exists. |
| Structured step validators | All Step `00a` through `09` validators are implemented and locally fixture/report tested. Their exact checks and limitations belong to the adjacent owner contracts and completed migration cards. |
| Final migration acceptance | The final `MIG-03O` executable state passed its focused suites, final-path coverage, and exact complete applicable gate after the documentation links were repaired. The earlier sandbox-DNS stop and later eight-link aggregate failure remain non-green attempts; the final pass does not relabel them. Exact commands, totals, timings, and coverage remain in the [`MIG-03O` card](../tasks/COMPLETED/MIG-03O-migrate-assemble-scientific-review-evidence-package-owner.md) and [dated refactor log](../history/audits/2026-08-02-refactor-log.md). |
| Latest residual package | Documentation-only `REVIEW-LEGACY-04A` confirms `RETAIN_ROOT` for `tests/pending/test_step_04_mark_duplicates.sh`. Static comparison proves the producer does not validate input sort order before Picard and its simple-path dry-run suite does not independently establish adversarial shell quoting; deterministic output naming is protected, and missing-input/tool handling has broad but explicitly bounded coverage. The scaffold remains byte-identical at mode `0644`, size `417` bytes, and SHA-256 `bfbec48adee7307f93890986f7087f60583fdc4a6c550056e6155dabc9d129a1`. No product executable or computational test ran or changed; only documentation validation applies, and the residual roster remains 87 paths. This creates no new runtime, cluster, production, scientific-review, or biological evidence. |

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
package was installed, restored, removed, or updated. Guarded checks use the
existing primary project library through `RENV_PATHS_LIBRARY`; the earlier
temporary Python-environment symlink remains removed. The latest unrestricted
read-only environment check reached dependency validation and reported one
out-of-date package without printing its identity, so the aggregate R lane is
explicitly non-green until a separately reviewed dependency-maintenance
package diagnoses and resolves that drift.

## Current blockers

- The full production `samples.tsv` is not in this checkout. Its immutable
  cluster copy, explicit replicate values, persistence, and hash require
  inspection.
- Step `07` lacks real-bcftools and cluster evidence.
- CSU batch-visible R and package availability remain unresolved.
- Guarded local R dependency validation reports one out-of-date package; the
  checker did not print its identity, and RPT-05A installed or updated no
  dependency.
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

`AUDIT-RESIDUAL-04A` is the sole selected residual package. Recompute the exact
87-path roster, verify completed final homes and old-path absences, recheck
retained/deferred/separately-retired boundaries, and close only the source-
topology campaign at the local/static evidence ceiling.

No later owner move, broad audit, scheduler, ingestion, orchestration/profile,
runtime execution, cluster, or default-branch package is preloaded.
`PROGRAM-01`, `CONCURRENCY-03`,
`TASK-EPIC-01`, `AUDIT-99`, the remaining documentation-consolidation cards,
recovered TODO work, and all UNREFINED proposals remain outside this package.

The user resumed the whole residual-convergence campaign after the LIB-02I
lifecycle close and publication; continue one JIT package at a time through the
final residual-layout audit unless a genuine escalation condition is reached.

Before continuing, verify the exact branch, `HEAD`, lack or identity of an
upstream, cleanliness including untracked files, and recovery/lock state. The
explicit whole-campaign approval covers routine one-card-at-a-time migration,
validation, commits, and publication inside the `PLAN-03A` boundary; scope,
semantic, evidence, safety, or destructive-action expansion still stops.
