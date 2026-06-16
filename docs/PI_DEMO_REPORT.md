# Preliminary PI Demo Report

This is a preliminary pipeline validation and handoff/demo report for the NORAD / Novogene Remora RNA-seq workflow rebuild. It is not a final biological analysis report.

This report reflects the already-documented project state only. It does not inspect live cluster job status or rerun generated-output checks.

For a short demo path, see `docs/DEMO_WALKTHROUGH.md`. For a visual system map, see `docs/ARCHITECTURE.md`. Standalone Mermaid diagrams live in `docs/architecture_pipeline.mmd` and `docs/architecture_reliability.mmd`.

## Executive Summary

This project rebuilds a legacy hardcoded RNA-editing / RNA-seq workflow into a local-first, SLURM-scaled, dry-run-first, testable pipeline.

The biological context is NORAD / PUM1 / rABE-related RNA-seq. The downstream goal is RNA-editing / variant-like site analysis, not simple gene-count differential expression.

Reference preparation steps `00a` through `00c` are cluster-proven. Sample-processing steps `01` through `05` are validated across all six samples. Step `05` SplitNCigarReads is cluster-proven after temp-space hardening and output inspection. Step `06` read-orientation BAM splitting is implemented and locally tested, cluster-validated on `ABE_EV_3`, and pending cohort validation.

## PI Decision Brief

### Current validated boundary

The preprocessing backbone is cluster-proven through Step `05` across all six samples. Step `06` has been implemented, locally tested, and cluster-validated on `ABE_EV_3`; cohort validation is pending. Downstream editing-site calling steps `07`-`09` remain the next implementation boundary.

### Evidence table

| Step | Input contract | Output contract | Validation evidence | Current status |
| ---- | -------------- | --------------- | ------------------- | -------------- |
| `00a` STAR index | reference FASTA/GTF | `refs/novogene_star_index/` | built with `sjdbOverhang=149` | cluster-proven |
| `00b` GTF -> BED12 | `genome.gtf` | `refs/novogene_ref/genome.bed` | 206,601 BED12 records | cluster-proven |
| `00c` GATK sidecars | `genome.fa` | `.fai` and `genome.dict` | 194-contig FAI/DICT/BAM match; SQ PASS | cluster-proven |
| `01` STAR alignment | paired FASTQs, STAR index | STAR coordinate-sorted BAMs | STAR summaries across six samples | six-sample cluster-proven |
| `02` canonical BAM | STAR BAM | `results/bam/<sample>/<sample>.sorted.bam` and `.bai` | quickcheck, coordinate sort, RG/index publication | six-sample cluster-proven |
| `02b` BAM QC | canonical BAM | quickcheck and flagstat summaries | refreshed across final Step `02` BAMs | six-sample cluster-proven |
| `03` strandedness | canonical BAM, BED12 | RSeQC strandedness report | reverse-stranded / first-strand signal across cohort | six-sample cluster-proven |
| `04` MarkDuplicates | canonical BAM | markdup BAM/BAI, Picard metrics | quickcheck, index, metrics rows | six-sample cluster-proven |
| `05` SplitNCigarReads | markdup BAM, FASTA/FAI/DICT | split-N-cigar BAM/BAI | `PASS=6`, quickcheck, RG, no scratch files | six-sample cluster-proven |
| `06` read-orientation split | split-N-cigar BAM | `FWD_like`/`REV_like` BAM/BAI, counts TSV | local tests; `ABE_EV_3` cluster validation; counts sanity | `ABE_EV_3` cluster-validated; cohort pending |
| `07`-`09` editing workflow | orientation BAMs, reference, VCF tables | mpileup VCFs, preprocessed tables, CMH outputs | not yet implemented | pending / not cluster-proven |

### PI scientific/QC questions

- Are the high duplicate rates expected, especially in `ABE_EV4` and `ABE_PUM1_4`, or should they trigger sample-level QC concern?
- Is `ABE_EV_2`'s lower unique mapping / higher multimapping acceptable for the intended downstream analysis?
- Should the legacy `FWD_like` / `REV_like` orientation split be preserved exactly through first reproduction before changing biological interpretation?
- What should count as the first biologically useful MVP: orientation-split BAMs, mpileup VCFs, preprocessed editing tables, or CMH-ranked candidate sites?
- Which filters/thresholds should be treated as legacy-preservation constraints versus PI-guided analysis choices?

### Proposed next 48 hours / next week

Next 48 hours:

1. Finish Step `06` cohort validation.
2. Patch docs/status once cohort validation is complete.
3. Begin Step `07` on a narrow validation scope before full-cohort execution.

Next week:

1. Implement Steps `07`-`09` as legacy-preserving, dry-run-first stages.
2. Generate first candidate editing-site tables.
3. Review QC and candidate sites with PI before interpreting biology.

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
| `06` | read-orientation BAM split | implemented and locally tested; cluster-validated on `ABE_EV_3`; cohort validation pending |
| `07` | bcftools mpileup | pending / not implemented / not cluster-proven |
| `08` | VCF preprocessing | pending / not implemented / not cluster-proven |
| `09` | CMH editing-site calling | pending / not implemented / not cluster-proven |

Step `05` is cluster-proven/cohort-proven across all six samples based on final split-N-cigar BAM/BAI output inspection.

## Approximate Runtime Profile

| Stage | Scope | Runtime profile | Notes |
| ----- | ----- | --------------- | ----- |
| `00a` STAR index | one-time reference prep | heavier one-time setup job; exact elapsed not recorded in this report | Builds the STAR genome index. |
| `00b` GTF -> BED12 | one-time reference prep | short one-time annotation conversion; exact elapsed not recorded in this report | Produces RSeQC-compatible BED12 annotation. |
| `00c` GATK reference sidecars | one-time reference prep | ~25 seconds | Creates/validates FASTA `.fai` and sequence dictionary sidecars. |
| `01` STAR alignment | per sample | alignment-heavy per-sample step; exact elapsed not recorded in this report | Produces coordinate-sorted STAR BAMs. |
| `02` canonical BAM | per sample | a few minutes; `ABE_EV_2` observed ~3 min 46 sec | Publishes stable sorted/indexed downstream BAMs. |
| `02b` BAM QC | per sample | short QC step; exact elapsed not recorded in this report | Runs samtools integrity/QC checks. |
| `03` strandedness | per sample | short QC/inference step; exact elapsed not recorded in this report | Runs RSeQC strandedness inference. |
| `04` MarkDuplicates | per sample | ~6-9 minutes per sample | Picard duplicate marking across all six samples. |
| `05` SplitNCigarReads | per sample | tens of minutes per sample; observed GATK elapsed examples ~33-40 minutes, with heavier samples longer | GATK-heavy and sensitive to temp-space configuration. |
| `06` read-orientation split | per sample | `ABE_EV_3` observed ~25 min 27 sec | I/O-heavy samtools filtering/merging/indexing; cluster-validated on `ABE_EV_3`; cohort validation pending. |

These timings are preliminary operational estimates from the current ADAM/CSU cluster validation runs. They are intended to communicate approximate computational scale, not benchmark performance. Exact runtimes vary by sample size, mapping complexity, node load, and storage I/O.

Exact Step `04` per-sample runtimes:

| Sample | Runtime |
| ------ | ------: |
| `ABE_EV_2` | 00:08:29 |
| `ABE_EV_3` | 00:06:06 |
| `ABE_EV4` | 00:08:52 |
| `ABE_PUM1_2` | 00:06:40 |
| `ABE_PUM1_3` | 00:06:33 |
| `ABE_PUM1_4` | 00:07:32 |

Recovered Step `05` GATK elapsed examples:

| Sample | GATK elapsed |
| ------ | -----------: |
| `ABE_EV_3` | ~32.96 min |
| `ABE_PUM1_2` | ~35.84 min |
| `ABE_PUM1_4` | ~39.71 min |

`ABE_EV_2` and `ABE_EV4` were heavier/slower Step `05` samples, but exact elapsed times are not recorded in this report.

Observed Step `06` example:

| Sample | Runtime |
| ------ | ------: |
| `ABE_EV_3` | 00:25:27 |

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
- The current state is honest: preprocessing is cluster-proven through SplitNCigarReads; read-orientation splitting has one cluster-validated sample and still needs cohort validation before downstream editing-site calling.

## Near-Term Roadmap

### Phase 1 — Rebuild and validate preprocessing backbone

Status: mostly complete; currently at the Step `06` cohort-validation boundary.

- Reference prep and STAR index
- STAR alignment across six samples
- Canonical BAM generation and QC
- RSeQC strandedness confirmation
- Picard MarkDuplicates
- GATK SplitNCigarReads
- Read-orientation BAM split

Current boundary:
Step `06` is the final preprocessing/read-orientation split step before variant-like/editing-site calling. It is implemented and locally tested, cluster-validated on `ABE_EV_3`, and pending cohort validation.

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

1. Finish Step `06` cohort validation.
2. Inspect Step `06` outputs and update status docs only after validation is complete.
3. Continue to Step `07` bcftools mpileup, Step `08` VCF preprocessing, and Step `09` CMH calling.

## Demo Talking Points

- We are rebuilding the legacy workflow into maintainable research software with explicit inputs, outputs, dry-runs, and tests.
- The current pipeline has been validated through SplitNCigarReads across all six samples.
- The cohort is consistently reverse-stranded / first-strand-style by RSeQC.
- STAR and duplicate-marking summaries already provide useful preliminary QC observations.
- Step `05` exposed a real cluster temp-space issue and was hardened rather than papered over.
- Step `05` is now cohort-proven after final BAM/BAI output inspection.
- Step `06` preserves read-orientation groups without making unsupported biological strand claims; it is cluster-validated on `ABE_EV_3`, with cohort validation still pending.
