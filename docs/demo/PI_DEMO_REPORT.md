# Preliminary PI Demo Report

This is a preliminary pipeline validation and handoff/demo report for the NORAD / Novogene Remora RNA-seq workflow rebuild. It is not a final biological analysis report.

This report reflects the already-documented project state only. It does not inspect live cluster job status or rerun generated-output checks.

For a short demo path, see `docs/demo/DEMO_WALKTHROUGH.md`. For a visual system map, see `docs/architecture/ARCHITECTURE.md`. Standalone Mermaid diagrams live in `docs/architecture/diagrams/pipeline.mmd` and `docs/architecture/diagrams/reliability.mmd`.

## Executive Summary

This project rebuilds a legacy hardcoded RNA-editing / RNA-seq workflow into a local-first, SLURM-scaled, dry-run-first, testable pipeline.

The biological context is NORAD / PUM1 / rABE-related RNA-seq. The downstream goal is RNA-editing / variant-like site analysis, not simple gene-count differential expression.

Reference preparation steps `00a` through `00c` are cluster-proven. Sample-processing steps `01` through `06` are cluster-proven across all six samples. Step `06` read-orientation BAM splitting is cluster-proven across the cohort and preserves mechanical read-orientation groups without making biological strand claims. Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`, but it has no real-bcftools runtime or cluster evidence and is not cluster-proven. Step `08` is implemented locally at commit `90335d8` and its shell/fake-R tests pass; because this workstation has no `Rscript`, the authored real-R fixtures remain runtime-blocked and pending. Step `08` also has no cluster dry-run, execute run, or inspected output evidence and is not cluster-proven. Step `09` remains pending / not implemented / not cluster-proven and is the next local implementation boundary, while Step `07` remains the first later cluster-promotion gate.

## PI Decision Brief

### Current validated boundary

The preprocessing and read-orientation backbone is cluster-proven through Step `06` across all six samples. Steps `07` and `08` now have locally implemented, fake-tool-tested contracts, but neither has real-runtime or cluster evidence. Step `08` real-R fixture execution is specifically blocked by the absence of `Rscript` on this workstation. Step `09` remains unimplemented, and no downstream editing-site stage is cluster-proven.

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
| `06` read-orientation split | SplitNCigarReads BAM/BAI | `FWD_like` and `REV_like` BAM/BAI plus orientation counts TSV | All six jobs completed 0:0; quickcheck passed; counts TSVs present; assigned_fraction = 1.000000 and unassigned_records = 0 for all six; cluster validation showed no Step 06 scratch files remaining in the checked Step 06 artifact paths | cluster-proven across all six samples |
| `07` cohort mpileup | Step `06` FWD_like/REV_like BAM/BAI pairs, sample manifest, partition manifest, FASTA/FAI | `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf`, `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.REV_like.mpileup.vcf`, and `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.step07_outputs.tsv` | implementation commit `e68b00c`; local Bash 3.2 and mocked-bcftools shell tests | implemented and locally tested; real-bcftools and cluster validation pending; not cluster-proven |
| `08` VCF preprocessing | exact partition-manifest × `{FWD_like,REV_like}` Step `07` VCF/receipt set, sample manifest, Novogene GTF | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, `results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv`, and `results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv` | implementation commit `90335d8`; local shell/fake-R suite passes; real-R fixtures authored but not run because `Rscript` is unavailable | implemented and locally shell/fake-R tested; real-R runtime and cluster validation pending; not cluster-proven |
| `09` CMH editing-site calling | Step `08` sites/input receipt, paired-replicate sample manifest, partition manifest | approved all-sites/significant/summary/spectrum tables and plots under `results/editing/<analysis>/` | not yet implemented | pending / not cluster-proven |

### PI scientific/QC questions

- Are the high duplicate rates expected, especially in `ABE_EV4` and `ABE_PUM1_4`, or should they trigger sample-level QC concern?
- Is `ABE_EV_2`'s lower unique mapping / higher multimapping acceptable for the intended downstream analysis?
- Should the legacy `FWD_like` / `REV_like` orientation split be preserved exactly through first reproduction before changing biological interpretation?
- What should count as the first biologically useful MVP: orientation-split BAMs, mpileup VCFs, preprocessed editing tables, or CMH-ranked candidate sites?
- Which filters/thresholds should be treated as legacy-preservation constraints versus PI-guided analysis choices?

### Proposed next 48 hours / next week

Next 48 hours:

1. Complete the Step `08` repository-wide docpatch, clean-status check, and push gate.
2. Create `step-09-cmh` from the clean, docpatched Step `08` branch and implement only Step `09`.
3. Preserve Step `07` as the first later cluster-promotion gate; do not execute Step `08` on the cluster before Step `07` is cluster-proven.

Next week:

1. Complete the Step `09` implementation/test commit and separate repository-wide docpatch.
2. Begin sequential cluster promotion with Step `07` dry-run, narrow pilot, and primary-contig execution before downstream execute runs.
3. Resolve an R-capable environment and run the Step `08` and Step `09` real-R fixtures before claiming real-R runtime validation.
4. Review QC and candidate sites with PI before interpreting biology.

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
| `06` | read-orientation BAM split | cluster-proven across all six samples |
| `07` | bcftools mpileup | implemented locally and locally tested with mocked bcftools; no real or cluster runtime; not cluster-proven |
| `08` | VCF preprocessing | implemented locally at `90335d8`; shell/fake-R tested; real-R runtime blocked and cluster validation pending; not cluster-proven |
| `09` | CMH editing-site calling | pending / not implemented / not cluster-proven |

Step 06: cluster-proven across all six samples.

Steps `05` and `06` are cluster-proven/cohort-proven across all six samples based on documented final output inspection and user-provided Step `06` cohort validation evidence.

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
| `06` read-orientation split | per sample | about 25-34 minutes per sample; slower EV samples about 33-34 minutes | Preliminary ADAM operational runtimes from the current validation run, not formal benchmarks. |
| `07` cohort mpileup | per cohort partition, both mechanical orientations | no real runtime measured | Local mocked-bcftools execution only. The long-partition, 8-hour, 1-CPU job request is unvalidated configuration, not observed runtime evidence. |
| `08` VCF preprocessing | one cohort across all declared partitions and both orientations | no real-R runtime measured | Local shell/fake-R execution only; the real-R fixture runner reported an explicit skip because `Rscript` is unavailable. |

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

Step `06` completed across the cohort in about 25-34 minutes per sample on ADAM; the slower EV samples took about 33-34 minutes. These are preliminary operational runtimes from the current ADAM validation run, not formal benchmarks.

Observed Step `06` preliminary ADAM operational runtimes:

| Sample | Runtime |
| ------ | ------: |
| `ABE_EV_2` | 00:33:09 |
| `ABE_EV_3` | 00:25:27 |
| `ABE_EV4` | 00:34:07 |
| `ABE_PUM1_2` | 00:27:17 |
| `ABE_PUM1_3` | 00:26:29 |
| `ABE_PUM1_4` | 00:29:34 |

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

## Step 06 Read-Orientation Split Results

Step 06 splits each validated SplitNCigarReads BAM into mechanical read-orientation groups (`FWD_like` and `REV_like`) needed by the legacy orientation-aware downstream editing workflow.

All six Step 06 jobs completed with ExitCode 0:0. Published `FWD_like` and `REV_like` BAM/BAI outputs and orientation-count TSVs were present for all six samples; `samtools quickcheck` passed silently; assigned_fraction was 1.000000 with zero unassigned records for all six samples.

Cluster validation showed no Step 06 scratch files remaining in the checked Step 06 artifact paths.

| Sample | Input records | FWD_like records | REV_like records | Assigned fraction | Runtime | Status |
| ------ | ------------: | ---------------: | ---------------: | ----------------: | ------: | ------ |
| `ABE_EV_2` | 88,863,298 | 21,689,836 | 67,173,462 | 1.000000 | 00:33:09 | cluster-proven |
| `ABE_EV_3` | 67,725,992 | 26,943,032 | 40,782,960 | 1.000000 | 00:25:27 | cluster-proven |
| `ABE_EV4` | 98,078,863 | 29,765,372 | 68,313,491 | 1.000000 | 00:34:07 | cluster-proven |
| `ABE_PUM1_2` | 75,761,468 | 27,371,848 | 48,389,620 | 1.000000 | 00:27:17 | cluster-proven |
| `ABE_PUM1_3` | 76,522,917 | 31,559,320 | 44,963,597 | 1.000000 | 00:26:29 | cluster-proven |
| `ABE_PUM1_4` | 81,011,913 | 24,998,144 | 56,013,769 | 1.000000 | 00:29:34 | cluster-proven |

`FWD_like` and `REV_like` are mechanical read-orientation groups based on SAM flag filters. They are not biological sense/antisense, transcript-strand, or edit-direction labels.

`samtools view -f FLAG` means records have all bits in `FLAG`; it is not exact flag equality.

Demo meaning: the reusable preprocessing backbone is rebuilt and cluster-validated through Step `06` across the full six-sample cohort. Steps `07` and `08` extend the local code boundary with mocked/fake-runtime-tested contracts, but the cluster-proven boundary has not moved. Step `09` is the next local implementation boundary.

## Step 08 Local VCF Preprocessing Contract

Step `08` consumes the exact partition-manifest × `{FWD_like,REV_like}` set of Step `07` VCFs and receipts; it does not glob whichever files are present. Before R execution, the shell wrapper verifies receipt paths, both manifest hashes, sample order, declared VCF record counts, and the complete declared input set.

The published output set is:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The deterministic wide sites table retains partition and candidate IDs; mechanical orientation; genomic coordinates and ALT index; genomic and RNA-normalized alleles; compatible annotation strand; gene/transcript IDs; CDS, UTR, exon, and intron flags; QUAL/FILTER; INFO alternate depth; and `orientation_policy`. It then appends manifest-ordered `DP__<sample>`, `AD__<sample>`, and `AF__<sample>` column groups. The input receipt reconciles every declared VCF's observed records, ALT alleles, supported SNVs, skipped symbolic/non-SNV alleles, and published candidates with the cohort summary. The complete input receipt is published last as the output-set commit marker.

The implemented legacy-preservation mapping is:

```text
FWD_like -> legacy neg -> compatible + transcripts -> complement DNA REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain DNA REF/ALT
orientation_policy=legacy_provisional_v1
```

The table retains genomic alleles alongside RNA-normalized alleles so this transformation remains auditable. The policy is provisional and is not biologically validated.

Current evidence is limited to implementation commit `90335d8`, passing shell/fake-R wrapper tests, and static/local repository checks. The real-R fixture suite exists but could not execute because this workstation has no `Rscript`. No cluster job, real-R output table, or biological candidate result has been inspected.

## Engineering And Reproducibility Features

The rebuilt pipeline emphasizes:

- local-first development
- SLURM execution at scale
- dry-run by default
- explicit `EXECUTE=1`
- scope-owned locking, including Step `07` cohort/partition and Step `08` cohort locks
- run-token temp files
- validation before publish
- rollback protection
- local fake-tool smoke tests
- clear docs and troubleshooting

This design is meant to make the workflow reproducible, reviewable, and handoff-safe rather than dependent on one-off interactive commands.

## What This Demonstrates

- The legacy workflow has been translated into explicit, testable pipeline steps rather than one-off scripts.
- Each implemented step has defined inputs, outputs, validation checks, and cluster execution gates.
- The pipeline has already produced useful QC signals across all six samples.
- Real cluster failure modes are being captured as durable troubleshooting/engineering decisions, not ad hoc fixes.
- The current state is honest: preprocessing and read-orientation splitting are cluster-proven through Step `06`; Step `07` is mocked-bcftools tested locally; Step `08` is shell/fake-R tested locally but its real-R fixture runtime is blocked; neither has cluster evidence; downstream CMH calling remains pending.

## Near-Term Roadmap

### Phase 1 — Rebuild and validate preprocessing backbone

Status: cluster-proven through Step `06` across all six samples. Steps `07` and `08` are implemented and locally fake-tool tested but await their real-runtime and cluster gates; Step `09` is the next local implementation boundary.

- Reference prep and STAR index
- STAR alignment across six samples
- Canonical BAM generation and QC
- RSeQC strandedness confirmation
- Picard MarkDuplicates
- GATK SplitNCigarReads
- Read-orientation BAM split

Current boundary:
Step `06` is the final cluster-proven preprocessing/read-orientation split step and is proven across all six samples. Step `08` is the local code boundary but is not real-R runtime-validated or cluster-proven; Step `09` is the next local implementation boundary.

### Phase 2 — Reproduce legacy editing-site calling workflow

Status: in progress locally. Step `07` is mocked-bcftools tested locally; Step `08` is implemented and shell/fake-R tested locally with real-R runtime validation blocked; Step `09` and Step `07` cluster execution remain pending.

- Step `07`: cohort bcftools mpileup per declared partition and mechanical read-orientation group, implemented locally but not run with real bcftools
- Step `08`: preprocess the exact Step `07` receipt set into deterministic candidate/input/QC tables, implemented locally but not run with real R
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

1. Complete the Step `08` docpatch/clean-push gate, then create the descendant `step-09-cmh` branch.
2. Apply the same implementation-commit, docpatch-commit, clean-push gate to Step `09`.
3. During later cluster promotion, validate Step `07` first with dry-run, narrow pilot, and inspected primary-contig outputs before executing downstream stages.
4. Run the real-R fixture suites in an R-capable environment before claiming real-R runtime validation.

## Demo Talking Points

- We are rebuilding the legacy workflow into maintainable research software with explicit inputs, outputs, dry-runs, and tests.
- The current pipeline has been validated through read-orientation splitting across all six samples.
- The cohort is consistently reverse-stranded / first-strand-style by RSeQC.
- STAR and duplicate-marking summaries already provide useful preliminary QC observations.
- Step `05` exposed a real cluster temp-space issue and was hardened rather than papered over.
- Step `05` is now cohort-proven after final BAM/BAI output inspection.
- Step `06` preserves read-orientation groups without making unsupported biological strand claims and is cluster-proven across all six samples.
- Step `07` has local implementation and mocked-test evidence only; no cluster VCFs or biological results are presented.
- Step `08` has local implementation and shell/fake-R evidence only; no real-R tables, cluster outputs, or biological results are presented.
- Step `08` uses `orientation_policy=legacy_provisional_v1`, which preserves a legacy mapping but is not biologically validated.
