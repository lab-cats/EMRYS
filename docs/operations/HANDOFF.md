# Project handoff

This is the canonical current takeover snapshot. The roadmap and acceptance
criteria live in [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
commands live in [`RUNBOOK.md`](RUNBOOK.md).

## Checkout

- Branch:
  `refactor-01a-step09-independent-cmh-oracle`
- Parent:
  `refactor-01-test-baseline`
- Verified parent HEAD:
  `4fc32e08121e541f489ede32f25d59c2626a60e0`
- Parent implementation:
  `b124e96 add Python coverage baseline gate`
- Parent documentation patch:
  `4fc32e0 add test baseline traceability docpatch`
- Current implementation:
  `bef0f97 test: characterize Step 09 CMH independently`
- Current package: independent test-only Step `09` CMH, estimability, and
  global-BH characterization from paired DP/AD counts
- Package type: test/fixture implementation plus separate documentation patch
- Remote and cluster work: paused

The Phase `01a` branch was created only after inspecting the canonical
takeover documents, running the applicable parent gate, refreshing the
remote, and verifying a clean, pushed, upstream-equal predecessor and absent
target.

## Completed boundary

The local descendant sequence has implemented:

- Steps `00a` through `09`;
- Step `09c` scientific-evidence validation;
- versioned artifact/scientific-review/run-summary/report-receipt schemas;
- explicit read-only artifact indexing;
- canonical run-summary assembly and report-table approvals;
- atomic, receipt-last HTML/PDF/summary-TSV reporting;
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
- Shared validator publication faults, exact check rosters, complete public
  CLI/exit behavior, early and utility SLURM behavior, and independent
  serialized/state goldens remain the measured Phase `01` characterization
  gaps.

## Immediate resume point

The `refactor-01a-step09-independent-cmh-oracle` implementation and
documentation content are complete. Its complete computational gate applies
to the executable state at `bef0f97`; the subsequent documentation-only patch
requires the documentation gate rather than another unchanged computational
run. After confirming this branch is clean, pushed, and upstream-equal, create
`refactor-01aa-validation-efficiency`.

That package must preserve existing public Make targets while separating
non-overlapping validation lanes, adding quiet failure-first per-lane logs and
a serial fallback, and measuring safe bounded parallelism. It may pin
developer-only `pytest-xdist` only through the normal dependency gate. Exact
serial/parallel pass, skip, and coverage evidence must agree before a parallel
default is enabled.

The one-time Phase `00` dependency exception is exhausted and does not
authorize future changes outside the normal development gate. Do not change
production structure before the final Phase `01` sufficiency gate and all
three Phase `02` reviews. Do not begin production, cluster, scientific-policy,
or biological-interpretation work.

The authoritative continuation sequence is in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md).
