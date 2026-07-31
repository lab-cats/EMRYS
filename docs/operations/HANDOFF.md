# Project handoff

This is the canonical current takeover snapshot. The roadmap and acceptance
criteria live in [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
commands live in [`RUNBOOK.md`](RUNBOOK.md).

## Checkout

- Branch:
  `codex/context-start-policy`
- Parent:
  `refactor-01-architecture-direction-docs`
- Verified parent HEAD:
  `d2ceb54e5a106b9a5dced7264a1bb5165b89dab6`
- Parent documentation commit:
  `d2ceb54 docs: capture architecture direction and task registry`
- Current documentation commit:
  `docs: define version-aware task start` (the branch commit containing this
  handoff; resolve its exact SHA from Git)
- Recorded package state: `CONTEXT-00` is complete and the documentation-only
  tree is ready for publication; verify live cleanliness, push state, and
  upstream equality from Git before takeover
- Current package: documentation-only version-aware task-start routing,
  selective phase-boundary inspection, impact-directed consistency review, and
  explicit documentation-only validation semantics
- Package type: one documentation commit; computational validation is not
  applicable because the predecessor-to-final diff changes no executable or
  test-affecting surface
- Remote and cluster work: paused

The context-policy branch descends directly from the clean, pushed, upstream-
equal architecture-direction documentation commit. The parent branch and live
remote both resolved to the verified parent HEAD before this branch was
created; the user's responsible-context instruction was preserved when the
descendant was created. Review before push reopened the package to remove
sequence-only dependency metadata, preserve completed-card history, and create
bounded follow-up cards for registry semantics and the embedded documentation
validator. The approved correction also records multiple isolated
documentation/card sidecars plus rolling-wave program planning as future
operating-model cards; neither policy is active until its own card completes.

## Completed boundary

The local descendant sequence has implemented:

- Steps `00a` through `09`;
- Step `09c` scientific-evidence validation;
- versioned artifact/scientific-review/run-summary/report-receipt schemas;
- explicit read-only artifact indexing;
- canonical run-summary assembly and report-table approvals;
- atomic, receipt-last HTML/PDF/summary-TSV reporting;
- `make demo-report`, which builds a complete synthetic 81-artifact,
  15-scope run with all 11 supported approved science-table roles, runs
  report dry-run before execute, and publishes beneath ignored
  `results/demo-report/`;
- a bounded, script-free HTML view with an initially open science-first
  Overview, broad native categories, and local scrolling for wide tables,
  plus a linear PDF with compact readable candidate records;
- explicit-profile, read-only runtime availability preflight;
- explicit read-only reference artifact, provenance, hash, and contig reconciliation;
- explicit read-only storage-root measurement and retention-policy recording;
- a Step `00a` STAR-index validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `00b` BED12/GTF validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `00c` FASTA/FAI/DICT validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `01` STAR-output validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `02` canonical-BAM validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `02b` persisted BAM-QC validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `03` RSeQC-fraction validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `04` marked-BAM/Picard-metrics validation report, typed artifact
  adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `05` split-N-cigar/reference-prerequisite validation report, typed
  artifact adapter, and
  summary/HTML/PDF propagation fixture.
- a Step `06` mechanical-orientation output/count validation report, typed
  artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `07` VCF/receipt/selector/manifest/count validation report, typed
  artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `08` three-TSV transaction/identity/schema/count validation report,
  typed artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `09` seven-check transaction/identity/semantics/subset/summary/
  spectrum/PDF validation report, typed artifact adapter, and summary/HTML/PDF
  propagation fixture.
- a pinned developer-only Python line/branch baseline, deterministic
  non-regression check, subprocess tracing, self-tests, and exhaustive
  public-contract risk-to-test matrix.
- a test-only Step `09` oracle that independently derives count-table
  estimability, the two-sided continuity-corrected stratified CMH statistic,
  p-value, common odds ratio, and one global BH family from paired DP/AD
  counts, with valid, zero-cell, all-zero, missing, low-coverage,
  infinite-odds, rounding, multi-stratum, and coordinated-corruption cases.
- a de-duplicated complete developer-validation gate with four independent
  lanes, quiet failure-first logs, explicit verbose and serial modes, bounded
  process-group cleanup, timing/result summaries, and exact coverage
  comparison.
- a test-only publication-fault matrix covering the one publisher shared by
  all 13 step validators plus the distinct provenance, preflight, and storage
  transactions, with protected success/rollback behavior and current unsafe
  recovery states clearly distinguished in test names and comments.
- a file-backed task registry with 51 cards in the current working tree,
  bounded acceptance evidence, and an explicit planning-before-implementation
  lifecycle; the legacy reciprocal dependency model remains unchanged pending
  the separately planned `TASK-REG-01` migration;
- durable architecture decisions and target constraints for behavior-first
  migration, vertical source/test ownership, semantic stages, YAML+TSV intake,
  report profiles, two-sink logging, documentation/local context, future
  analysis/public-data/package seams, the documentation-health skill,
  isolated concurrent authoring, and rolling-wave delivery;
- a version-aware task-start router with exact-revision context reuse,
  selective phase-boundary inspection, explicit expansion triggers, impact-
  directed manual documentation review, and a quiet repository-wide structural
  gate;
- explicit standalone documentation-package semantics: computational
  validation is not applicable when the complete diff has no executable or
  test-affecting consumer;
- an open-choice ledger and updated future Mermaid sources. Current executable
  topology, report behavior, logging behavior, numeric stage identifiers, and
  runtime/scientific evidence remain unchanged.

## Evidence boundary

| Step/package | Verified state |
| --- | --- |
| `00a` STAR index | cluster-proven |
| `00b` GTF to BED12 | cluster-proven |
| `00c` reference sidecars | cluster-proven |
| `01` STAR alignment | cluster-proven across all six samples |
| `02` canonical BAM | cluster-proven across all six samples |
| `02b` BAM QC | refreshed across all six final Step `02` BAMs |
| `03` RSeQC orientation inference | cluster-proven across all six samples |
| `04` MarkDuplicates | cluster-proven across all six samples |
| `05` SplitNCigarReads | cluster-proven across all six samples |
| `06` mechanical orientation split | cluster-proven across all six samples |
| `07` cohort mpileup | implemented and mocked-bcftools tested locally; no real-runtime or cluster proof |
| `08` VCF preprocessing | implemented; shell/fake-R and guarded real-R tested locally; no cluster proof |
| `09` paired CMH ranking | implemented; shell/fake-R and guarded real-R tested locally; no cluster proof |
| `09c` scientific-evidence tooling | implemented and synthetic-fixture tested; no production review |
| Artifact schemas/adapters/run summary | implemented and synthetic-fixture tested; no production transaction |
| Static report bundle | HTML/PDF/summary TSV/report receipt implemented and tested with the pinned local Quarto/Typst renderer and PDF reader; no production report |
| Populated demo report | full synthetic report transaction, native broad HTML categories, bounded wide-table layout, and compact PDF candidate projection implemented and locally tested; no production data or evidence |
| Runtime preflight | explicit tool, R-namespace, SHA-256, and path-visibility probes implemented and locally fixture-tested; no CSU batch report |
| Reference provenance | explicit FASTA/FAI/DICT/GTF/BED12/STAR inventory and reconciliation implemented and locally fixture-tested; no production reference report |
| Storage inventory and retention | explicit root size/capacity measurement and retention-policy recording implemented and locally fixture-tested; no production storage report or approved production policy |
| Step `00a` structured validation | index members, source identities, ordered contig names/lengths, and `sjdbOverhang` validator implemented and locally fixture/report tested; no new production execution |
| Step `00b` structured validation | BED12 structure, sorting, blocks, uniqueness, and exact GTF normalization agreement implemented and locally fixture/report tested; no new production execution |
| Step `00c` structured validation | FASTA, FAI, and DICT structure plus exact ordered contig-name/length agreement implemented and locally fixture/report tested; no new production execution |
| Step `01` structured validation | five explicit STAR outputs, BAM container signature, final-log structure, mapping percentages, and splice-junction rows implemented and locally fixture/report tested; no new production execution |
| Step `02` structured validation | BAM/BAI containers, samtools quickcheck, coordinate sorting, matching read-group header, and alignment RG coverage implemented and locally fixture/report tested; no new production execution |
| Step `02b` structured validation | exact quickcheck marker, flagstat structure, total/mapped counts, and count reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `03` structured validation | required RSeQC labels, finite paired-orientation fractions, failed-to-determine fraction, and sum reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `04` structured validation | BAM/BAI containers, quickcheck, coordinate sorting, read-group preservation, and bounded Picard duplication metrics implemented and locally fixture/report tested; no new production execution |
| Step `05` structured validation | BAM/BAI containers, quickcheck, coordinate/read-group preservation, and exact FASTA/FAI/DICT agreement implemented and locally fixture/report tested; no new production execution |
| Step `06` structured validation | two BAM/BAI output pairs, exact counts-table structure, per-flag mechanical-orientation sums, assigned/unassigned totals, and assigned-fraction reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `07` structured validation | exact two-row receipt, VCF structure, selector/FAI reconciliation, manifest hashes and sample order, and VCF paths/counts implemented and locally fixture/report tested; no real-bcftools or cluster execution |
| Step `08` structured validation | sites/input-receipt/summary transaction, manifest and annotation identity, ordered partition-orientation inputs, candidate uniqueness/sample fields, and aggregate counts implemented and locally fixture/report tested; no production execution |
| Step `09` structured validation | six native outputs, exact headers/basenames/shared parent/distinct files, explicit cohort and provisional policy, complete Step `08` candidate order, count-derived target/test/call/depth/AF/background plus BH-from-reported-p semantics, subset, summary, mutation spectrum, and PDFs implemented and locally fixture/report tested; CMH statistic/p-value/odds ratio and count-table estimability are not independently recomputed; no production execution |
| Guarded local R dependency | `bitops` updated from locked `1.0-9` to `1.1-0` in the repository-local environment under a one-time explicit authorization; upstream consistency tests, exact boundary-output comparison, synchronization/current-release checks, and the complete local gate passed |
| Comprehensive refactor audit | evidence inventory, ranked findings, test-first recommendations, and explicit do-not-abstract boundaries recorded; no NORAD workflow, schema, config, test, scientific method, or public-contract behavior changed |
| Phase `01` test baseline | measured developer-only Python line/branch baseline and public-contract matrix recorded in [`../design/TEST_BASELINE.md`](../design/TEST_BASELINE.md); the implementation gate passed with 432 Python tests passing, 17 expected skips, every shell suite passing, guarded R environment/current-release validation, Step `08`/`09` local real-R fixtures, and 143 pinned report-runtime tests; no production behavior or evidence state changed |
| Phase `01a` independent Step `09` oracle | 20 focused Python oracle tests and the committed real-R Step `09` corpus comparison passed; the complete implementation gate passed with 452 Python tests, 17 expected conditional skips, unchanged 80.8701% line/69.6956% branch coverage across 26 production Python modules, every shell suite, guarded R environment checks, guarded Step `08`/`09` real-R fixtures, and 143 pinned report-runtime tests; the production validator and Step `09` method were unchanged |
| Phase `01a1` populated demo report | post-rebase report gate passed with 145 pinned real-Quarto/Typst tests, the isolated wrapper contract passed, repeat publication and cleanup passed, and `make demo-report` published the ignored 81-artifact/15-scope/11-table synthetic bundle; this is local synthetic-fixture and renderer-runtime evidence only |
| Phase `01aa` validation efficiency | implementation commit `dd19f0f` passed the final serial fallback in 440.821246 seconds and three consecutive default parallel gates in 152.335875, 169.928159, and 168.979423 seconds; every run reported 463 Python passes, 17 Python skips, 17 pinned report-runtime passes, all shell and guarded-R checks passing, and exact equality across 26 coverage files, 8,542/10,551 lines, 3,074/4,404 branches, and coverage digest `a6a5f1d9c5d33de3c1fbae82bd540342298f35089df55c3a76b17d08db1abd7f`; controlled exit-7 failure and SIGINT-130 tests proved retained failure output, propagation, descendant cleanup, handler restoration, and no stale owned logs; this is developer-validation infrastructure evidence only |
| Phase `01b` validation-publication faults | implementation commit `f7e00e4` added 28 test-only fault cases: 18 for the publisher shared by all 13 step validators and 10 for provenance, preflight, and storage publishers; 56 directly affected tests passed five serial repetitions and one two-worker run, covered serial/parallel execution was exactly equal, the broader 132-test regression passed, and the canonical complete gate passed in 153.161 seconds with all Python, shell, guarded-R, and 17 pinned report-runtime checks passing; a separately retained identical Python lane recorded 491 passes, 17 skips, and 26 coverage files at 8,566/10,551 lines and 3,103/4,404 branches; production behavior and evidence state were unchanged |
| Architecture-direction documentation | task registry, decisions, open choices, target architecture, roadmap, handoff, and four future diagrams updated; documentation-only validation passed; no executable, dependency, schema, config, fixture, test-harness, scientific-method, runtime, cluster, or evidence-state change |
| Task-start context documentation | task-start router, context-freshness matrix, expansion triggers, impact-directed documentation review, and documentation-only validation semantics updated; `git diff --check`, the 71-document/51-card/6-diagram structural gate, and independent read-only consistency review passed; computational validation was not applicable because no executable, dependency, schema, config, fixture, report-template, test-harness, scientific-method, runtime, cluster, or evidence-state surface changed |

The measured parent serial workflow was approximately 554 seconds from its
successful component timings. Removing duplicate Python and report execution
reduced the final serial fallback to 440.821246 seconds. Python-worker medians
for one through four workers were 200, 110, 107, and 108 seconds; two workers
were selected as the smallest candidate within 5% of the fastest and improved
the Python lane by 45%. Top-level medians for one through four lane slots were
351.760131, 216.836257, 174.101133, and 170.702626 seconds; three slots were
selected as the smallest candidate within 5% of the fastest. The final
three-run default median was 168.979423 seconds, 61.667% faster than the final
serial fallback.

Phase `01b` preserved the Phase `01aa` defaults of three top-level lane slots
and two Python workers. Its successful gate lane timings were 0.110 seconds
for static preflight, 39.724 for shell contracts, 131.618 for Python coverage,
144.052 for guarded R, and 113.317 for pinned report runtime. A retained
Python-lane measurement finished in 107.22 seconds with coverage digest
`a59ee1897b4b8a0d02881c3c5070f12f47f0a6b1067cd883624db88ad8056137`.
The tracked non-regression baseline was not rewritten. An initial restricted-
network gate attempt reached guarded R and failed only because release
metadata DNS was unavailable; the identical gate passed when network access
was available.

The fault suite confirms protected first/replacement publication, validation,
rollback, symlink rejection, input mutation, fsync/move failure, and
interruption paths. It also freezes known unsafe states for later correction:
metadata-only snapshots miss same-size rewrites with restored mtime; a late
foreign final can be deleted; incomplete restoration can leave backups without
lock/marker protection; and runtime preflight has lock-fsync/descriptor and
lock-cleanup gaps. Passing these tests characterizes those states; it does not
approve them as safe recovery behavior.

Transaction completion means only that the declared transaction reconciled. It
does not establish that every source exists or passed, nor does it promote
runtime, cluster, scientific, or biological state.

No production artifact index, run summary, report-table approval manifest,
Step `09c` evidence package, or report bundle is recorded in this checkout.
The export evidence is local synthetic-fixture and real-renderer evidence
only.

No CSU runtime profile has been populated or executed in a batch allocation.
The tracked runtime profile is an example contract. Local tests and a
successfully published preflight report would establish only the checks
recorded in their declared context, not workflow runtime validation or
cluster proof.

No production storage-root contract or retention-policy approval has been
populated. The tracked contracts use illustrative paths and pending approvals.
The inventory tool is read-only; report publication does not authorize or
perform deletion, movement, archival, compression, or cleanup.

## Cohort and preserved scientific evidence

The paired-end cohort is:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Explicit paired strata:

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

The `FWD_like` and `REV_like` groups are mechanical flag groupings.
`legacy_provisional_v1` is a compatibility policy, not a validated biological
strand model.

Step `09` outputs are CMH-ranked candidates. No validated editing-site or
causal biological conclusion exists.

`science_review_complete_exploratory` remains explicitly provisional.
`biological_interpretation_ready` is reserved and rejected until a separately
approved policy defines and unlocks stricter exit criteria.

## Current blockers

- The full production `samples.tsv` is not in this checkout. Its immutable
  cluster copy, explicit replicate values, persistence, and hash require
  inspection.
- Step `07` lacks real-bcftools and cluster evidence.
- CSU batch-visible R and package availability remain unresolved.
- Storage quota, scratch capacity, and retention policy remain unresolved.
- The exact Novogene annotation release remains partially unresolved.
- No production scientific-evidence review has been completed.
- The Step `09` structured validator still does not independently recompute
  the CMH statistic, p-value, common odds ratio, or table estimability from
  DP/AD counts. Phase `01a` now supplies independent characterization evidence
  for a later separately reviewed compatible correction; it did not change
  production validation.
- Exact check rosters, complete public CLI/exit behavior, early and utility
  SLURM behavior, and independent serialized/state goldens remain the measured
  Phase `01` characterization gaps.
- Phase `01b` now characterizes shared and ancillary publication faults, but
  it intentionally does not correct the confirmed same-size rewrite,
  late-foreign-final, incomplete-rollback, descriptor, or stale-lock behavior.

## Immediate resume point

The documentation-only context-policy package changes task-start and review
instructions; it does not execute the active repository-spanning refactor. Its
predecessor executable state remains the completed Phase `01b` implementation
and its recorded computational evidence.

`CONTEXT-00` is complete. After confirming its package commit is clean,
published, and upstream-equal, select
[`CONCURRENCY-01`](../tasks/TODO/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
as the next documentation-only operating package. It must implement isolated
worktrees, at most one implementation-candidate or immutable-execution lane,
multiple documentation/card sidecars, single-owner integration, and combined
validation. Complete and push it, then pause for the required user discussion
about leverage and first-use strategy. Do not select
[`PROGRAM-01`](../tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
or begin concurrent delivery before that discussion.

`TEST-01C` remains the first uncompleted Phase `01` characterization card.
Maintenance and program order are roadmap guidance rather than technological
blockers; every selected card still requires its bounded planning and approval.

The one-time Phase `00` dependency exception is exhausted and does not
authorize future changes outside the normal development gate. Do not change
production structure before the final Phase `01` sufficiency gate and all
three Phase `02` reviews. Do not begin production, cluster, scientific-policy,
or biological-interpretation work.

The authoritative continuation sequence is in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); detailed future
scope and dependencies are in [`../tasks/`](../tasks/).
