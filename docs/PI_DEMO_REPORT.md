# Preliminary PI Demo Report

This is a preliminary pipeline validation and handoff/demo report for the NORAD / Novogene Remora RNA-seq workflow rebuild. It is not a final biological analysis report.

This report reflects the already-documented project state only. It does not inspect live cluster job status or rerun generated-output checks.

## Executive Summary

This project rebuilds a legacy hardcoded RNA-editing / RNA-seq workflow into a local-first, SLURM-scaled, dry-run-first, testable pipeline.

The biological context is NORAD / PUM1 / rABE-related RNA-seq. The downstream goal is RNA-editing / variant-like site analysis, not simple gene-count differential expression.

Reference preparation steps `00a` through `00c` are cluster-proven. Sample-processing steps `01` through `05` are validated across all six samples. Step `05` SplitNCigarReads is cluster-proven after temp-space hardening and output inspection. Step `06` read-orientation BAM splitting is the next implementation target.

## Pipeline Status

| Step | Purpose | Status |
| ---- | ------- | ------ |
| `00a` | STAR index | cluster-proven |
| `00b` | GTF to BED12 | cluster-proven |
| `00c` | GATK reference sidecars | cluster-proven |
| `01` | STAR alignment | cluster-proven across all six |
| `02` | canonical BAM | cluster-proven across all six |
| `02b` | BAM QC | cluster-proven across all six |
| `03` | strandedness | cluster-proven across all six |
| `04` | MarkDuplicates | cluster-proven across all six |
| `05` | SplitNCigarReads | cluster-proven across all six |
| `06` | read-orientation BAM split | next implementation target |
| `07` | bcftools mpileup | pending |
| `08` | VCF preprocessing | pending |
| `09` | CMH editing-site calling | pending |

Step `05` is cluster-proven/cohort-proven across all six samples based on final split-N-cigar BAM/BAI output inspection.

## Sample Set

| Condition | Samples |
| --------- | ------- |
| EV | `ABE_EV_2`, `ABE_EV_3`, `ABE_EV4` |
| PUM1 | `ABE_PUM1_2`, `ABE_PUM1_3`, `ABE_PUM1_4` |

Note that `ABE_EV4` lacks the underscore before `4`.

## Preliminary STAR Alignment Summary

| Sample | Input reads | Unique % | Multi % | Unmapped too short % |
| ------ | ----------: | -------: | ------: | -------------------: |
| `ABE_EV_2` | 21,358,987 | 58.50 | 24.19 | 16.55 |
| `ABE_EV_3` | 20,535,573 | 82.95 | 8.93 | 7.85 |
| `ABE_EV4` | 26,560,165 | 71.06 | 16.44 | 12.02 |
| `ABE_PUM1_2` | 21,136,837 | 77.51 | 12.80 | 9.32 |
| `ABE_PUM1_3` | 23,183,778 | 85.38 | 8.04 | 6.35 |
| `ABE_PUM1_4` | 22,474,725 | 70.96 | 15.47 | 13.12 |

`ABE_EV_2` has lower unique mapping and higher multimapping than the rest of the cohort. This is a QC observation, not automatically a pipeline failure.

## Strandedness Summary

Step `03` RSeQC results show all six samples are strongly reverse-stranded / first-strand-style.

| Sample | Reverse-group fraction |
| ------ | ---------------------: |
| `ABE_EV_2` | 0.8740 |
| `ABE_EV_3` | 0.8617 |
| `ABE_EV4` | 0.8658 |
| `ABE_PUM1_2` | 0.8562 |
| `ABE_PUM1_3` | 0.8639 |
| `ABE_PUM1_4` | 0.8672 |

Common tool-specific settings that often correspond to this orientation are:

```text
featureCounts -s 2
HTSeq stranded=reverse
Salmon-style ISR
```

These settings should be named in tool context rather than treated as universally interchangeable.

## Duplicate Marking Summary

Step `04` Picard MarkDuplicates is cluster-proven across all six samples. Duplicate reads are marked, not removed.

| Sample | Pct duplication | Estimated library size |
| ------ | --------------: | ---------------------: |
| `ABE_EV_2` | 0.664166 | 6,327,403 |
| `ABE_EV_3` | 0.602721 | 8,397,468 |
| `ABE_EV4` | 0.854569 | 3,383,587 |
| `ABE_PUM1_2` | 0.708423 | 5,783,576 |
| `ABE_PUM1_3` | 0.683802 | 7,214,041 |
| `ABE_PUM1_4` | 0.841660 | 3,081,584 |

Duplication is high across the cohort, especially `ABE_EV4` and `ABE_PUM1_4`. This is a preliminary QC observation and should be interpreted with PI guidance.

## Step 05 Validation And Hardening

Step `05` uses GATK `SplitNCigarReads` after duplicate marking.

The first `ABE_EV_2` execute attempt got through traversal pass 1, entered traversal pass 2, then failed during HTSJDK temporary spill/write/close behavior. The root cause was GATK/HTSJDK writing `SortingCollection` temp files to node-local `/tmp`, which was too small for this workload.

This failure did not indicate a known problem with the input BAM, reference sidecars, GATK availability, or Java version; it exposed a cluster temp-storage assumption that has now been made explicit in the workflow.

The Step `05` script was hardened to use a per-run project-storage GATK temp directory through:

```text
--java-options -Djava.io.tmpdir=...
--tmp-dir ...
TMPDIR for the GATK process
```

Cleanup was also hardened for owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

Six-sample Step `05` revalidation completed successfully. Output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

```text
PASS=6
PENDING_OR_RUNNING=0
FAIL=0
```

All six samples have final split-N-cigar BAM/BAI files, passing `samtools quickcheck`, `@HD` with `SO:coordinate`, sample-matching `@RG`, and no Step `05` scratch files remaining.

Confirmed final Step `05` output sizes:

| Sample | Split-N-cigar BAM size | BAI size |
| ------ | ---------------------: | -------: |
| `ABE_EV_2` | 4.4G | 2.0M |
| `ABE_EV_3` | 3.5G | 1.6M |
| `ABE_EV4` | 4.4G | 1.8M |
| `ABE_PUM1_2` | 3.7G | 1.6M |
| `ABE_PUM1_3` | 3.7G | 1.6M |
| `ABE_PUM1_4` | 3.8G | 1.8M |

## Engineering And Reproducibility Features

The rebuilt pipeline emphasizes:

- local-first development
- SLURM execution at scale
- dry-run by default
- explicit `EXECUTE=1`
- per-sample locking
- run-token temp files
- validation before publish
- rollback protection
- local fake-tool smoke tests
- clear docs and troubleshooting

This design is meant to make the workflow reproducible, reviewable, and handoff-safe rather than dependent on one-off interactive commands.

## What This Demonstrates

- The legacy workflow has been translated into explicit, testable pipeline steps rather than one-off scripts.
- Each step has defined inputs, outputs, validation checks, and cluster execution gates.
- The pipeline has already produced useful QC signals across all six samples.
- Real cluster failure modes are being captured as durable troubleshooting/engineering decisions, not ad hoc fixes.
- The current state is honest: preprocessing is through SplitNCigarReads, while read-orientation splitting and editing-site calling remain downstream.

## Near-Term Roadmap

### Phase 1 — Rebuild and validate preprocessing backbone

Status: mostly complete; currently at the Step `06` read-orientation boundary.

- Reference prep and STAR index
- STAR alignment across six samples
- Canonical BAM generation and QC
- RSeQC strandedness confirmation
- Picard MarkDuplicates
- GATK SplitNCigarReads
- Read-orientation BAM split

Current boundary:
Step `06` is the final preprocessing/read-orientation split step before variant-like/editing-site calling.

### Phase 2 — Reproduce legacy editing-site calling workflow

Status: next.

- Run bcftools mpileup by chromosome and read-orientation group
- Preprocess VCF-like outputs into analysis tables
- Preserve/control strand and read-orientation assumptions
- Run CMH/editing-site calling

### Phase 3 — Scientific review and refinement

Status: requires PI guidance.

- Interpret QC findings, including high duplication and mapping differences
- Decide what should count as the first biologically useful MVP output
- Review candidate editing sites and filters
- Decide whether to preserve legacy thresholds or revise them

## Questions For PI Discussion

- Are the high duplication rates expected for this dataset/prep, especially ABE_EV4 and ABE_PUM1_4?
- Should ABE_EV_2’s lower unique mapping / higher multimapping be treated as a sample QC concern or acceptable cohort variation?
- Should the first biologically useful MVP output be orientation-split BAMs, mpileup VCFs, preprocessed candidate tables, or CMH-ranked editing sites?
- Should we preserve the legacy `FWD_like` / `REV_like` read-orientation split exactly before changing biological interpretation?

## Next Steps

1. Implement Step `06` read-orientation BAM split.
2. Validate Step `06` locally and then on the cluster.
3. Continue to Step `07` bcftools mpileup, Step `08` VCF preprocessing, and Step `09` CMH calling.

## Demo Talking Points

- We are rebuilding the legacy workflow into maintainable research software with explicit inputs, outputs, dry-runs, and tests.
- The current pipeline has been validated through SplitNCigarReads across all six samples.
- The cohort is consistently reverse-stranded / first-strand-style by RSeQC.
- STAR and duplicate-marking summaries already provide useful preliminary QC observations.
- Step `05` exposed a real cluster temp-space issue and was hardened rather than papered over.
- Step `05` is now cohort-proven after final BAM/BAI output inspection.
- The next technical milestone is Step `06`, which will preserve read-orientation groups without making unsupported biological strand claims.
