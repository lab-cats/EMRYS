# Project handoff

This is the canonical current takeover snapshot. The roadmap and acceptance
criteria live in [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
commands live in [`RUNBOOK.md`](RUNBOOK.md).

## Checkout

- Branch:
  `report-html-v1b-docs-responsibility-consolidation`
- Parent:
  `report-html-v1a-report-table-approvals`
- Verified parent HEAD:
  `41df822b60cbe3af16c12fc6326b69adf54c9f69`
- Parent implementation:
  `2a4b8f8 implement report table approval producer`
- Package type: documentation-only
- Remote and cluster work: paused

The consolidation branch was created only after fetching remote refs and
verifying a clean, upstream-equal parent and an absent target branch.

## Completed boundary

The local descendant sequence has implemented:

- Steps `00a` through `09`;
- Step `09c` scientific-evidence validation;
- versioned artifact/scientific-review/run-summary/report-receipt schemas;
- explicit read-only artifact indexing;
- canonical run-summary assembly and report-table approvals;
- static, self-contained HTML reporting.

The current package consolidates documentation responsibilities. It changes no
executable behavior, schema, test, workflow contract, or generated output.

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
| Static HTML report | implemented and tested with the pinned local renderer; no production report |

Transaction completion means only that the declared transaction reconciled. It
does not establish that every source exists or passed, nor does it promote
runtime, cluster, scientific, or biological state.

No production artifact index, run summary, report-table approval manifest,
Step `09c` evidence package, or report bundle is recorded in this checkout.

The last predecessor snapshot recorded a complete local Python, shell,
guarded-R, environment, and real-renderer pass. Exact totals are historical and
must be regenerated for this branch rather than copied forward.

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

## Immediate resume point

Complete this documentation-only package:

1. finish the repository-wide ownership consolidation;
2. run the documentation checks and complete local validation gate;
3. commit once as `consolidate documentation responsibilities`;
4. push and verify upstream equality;
5. stop for review before creating the next descendant package.

The authoritative continuation sequence is in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md).
