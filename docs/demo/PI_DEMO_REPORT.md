# Preliminary PI Demo Report

This is a preliminary pipeline validation and handoff/demo report for the NORAD / Novogene Remora RNA-seq workflow rebuild. It is not a final biological analysis report.

This report reflects the already-documented project state only. It does not inspect live cluster job status or rerun generated-output checks.

For a short demo path, see `docs/demo/DEMO_WALKTHROUGH.md`. For a visual system
map, see `docs/architecture/ARCHITECTURE.md`. The current-state standalone
Mermaid diagrams are `docs/architecture/diagrams/pipeline.mmd` and
`docs/architecture/diagrams/reliability.mmd`; the proposed roadmap and future
diagrams are linked from `docs/architecture/FUTURE_ARCHITECTURE.md`, including
`future_roadmap_sequence.mmd`.

## Executive Summary

This project rebuilds a legacy hardcoded RNA-editing / RNA-seq workflow into a local-first, SLURM-scaled, dry-run-first, testable pipeline.

The biological context is NORAD / PUM1 / rABE-related RNA-seq. The downstream goal is RNA-editing / variant-like site analysis, not simple gene-count differential expression.

Reference preparation steps `00a` through `00c` are cluster-proven.
Sample-processing steps `01` through `06` are cluster-proven across all six
samples. Step `06` read-orientation BAM splitting preserves mechanical groups
without making biological strand claims. Step `07` is implemented locally and
mocked-bcftools tested at commit `e68b00c`, but it has no real-bcftools or
cluster evidence. Step `08` is implemented locally at `90335d8` and
shell/fake-R tested. Step `09` is implemented locally at `e4371de` and
shell/fake-R tested. Signed/notarized Apple-silicon CRAN R `4.6.1` and a
repository `renv` environment locked to Bioconductor `3.23` are now installed
locally; activation is guarded by `NORAD_USE_RENV=1`. Namespace, lock,
headless-PDF, and empty cache-disabled binary restore checks pass.

Both real-R suites now pass locally without `SKIP` after the corrective
implementation at `eae5eca`. Step `08` preflights raw DP/AD/INFO AD lexemes
before semantic parsing; its partition-overlap validator was already correct,
and a generic fixture message had misattributed the later malformed-count
failure. Step `09` validates PDF EOF bytes without locale-sensitive text
conversion. Steps `07`-`09` still have no remote dry-run, execute, log, or
inspected production-output evidence and are not cluster-proven. Remote
validation is paused while the approved local scientific-validation,
artifact/report, foundation, and per-step validator sequence is implemented.

## PI Decision Brief

### Current validated boundary

The preprocessing and read-orientation backbone is cluster-proven through Step
`06` across all six samples. Steps `07`-`09` now have locally implemented,
fake-tool-tested contracts, but none has cluster evidence. The local R
environment itself passes its restore, namespace, lock, and PDF checks. Step
`08` and Step `09` real-R fixtures also pass locally without skipping after
`eae5eca`. No downstream editing-site stage has production or cluster
evidence, and none is cluster-proven.

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
| `08` VCF preprocessing | exact partition-manifest × `{FWD_like,REV_like}` Step `07` VCF/receipt set, sample manifest, Novogene GTF | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, `results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv`, and `results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv` | implementation commit `90335d8`, corrective commit `eae5eca`; shell/fake-R and guarded real-R suites pass; raw count preflight active | implemented and locally tested; cluster validation pending; not cluster-proven |
| `09` CMH editing-site calling | Step `08` sites/input receipt, paired-replicate sample manifest, partition manifest | four TSVs and two PDFs under `results/editing/<analysis>/` | implementation commit `e4371de`, fixture correction `eae5eca`; shell/fake-R and guarded real-R suites pass; PDF EOF validation is raw-byte based | implemented and locally tested; cluster validation pending; not cluster-proven |

### PI scientific/QC questions

- Are the high duplicate rates expected, especially in `ABE_EV4` and `ABE_PUM1_4`, or should they trigger sample-level QC concern?
- Is `ABE_EV_2`'s lower unique mapping / higher multimapping acceptable for the intended downstream analysis?
- Should the legacy `FWD_like` / `REV_like` orientation split be preserved exactly through first reproduction before changing biological interpretation?
- What should count as the first biologically useful MVP: orientation-split BAMs, mpileup VCFs, preprocessed editing tables, or CMH-ranked candidate sites?
- Which filters/thresholds should be treated as legacy-preservation constraints versus PI-guided analysis choices?

### Approved immediate local sequence

The `step-09b1-real-r-fixes` branch is complete and pushed; both Step `08` and
Step `09` real-R suites pass locally without `SKIP`.

1. Implement the dry-run-first `step-09c-scientific-validation` evidence
   package. Its fixture statuses are `evidence_incomplete` or
   `science_review_complete_exploratory`; it must reject the reserved
   `biological_interpretation_ready` value.
2. Implement the immediate reporting slice:
   `artifact-schema-v1`, `artifact-adapters-v1`, `artifact-run-summary`,
   `report-html-v1`, and `report-exports-v1`. The synthetic reports must label
   incomplete/exploratory state and never imply validation.
3. Implement read-only runtime, reference-provenance, and storage-retention
   foundations, then one validation-report branch for every pipeline step from
   `00a` through `09`.
4. Stop local work at `post09-validation-report-09`. Remote Step `07`-`09`
   promotion remains paused until then.

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
| `08` | VCF preprocessing | implemented locally at `90335d8`, hardened at `eae5eca`; shell/fake-R and guarded real-R suites pass; not cluster-proven |
| `09` | CMH editing-site calling | implemented locally at `e4371de`; shell/fake-R and guarded real-R suites pass after `eae5eca`; not cluster-proven |

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
| `08` VCF preprocessing | one cohort across all declared partitions and both orientations | accepted synthetic fixture runtime only; no production or cluster runtime measured | The real-R fixture suite passes locally without `SKIP`, including raw-count and partition-overlap failures. |
| `09` paired CMH calling | one analysis across the complete Step `08` candidate universe | accepted synthetic fixture runtime only; no production or cluster runtime measured | The real-R fixture suite passes locally without `SKIP`, including raw-byte PDF signature/EOF checks. |

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

Step `09` pairs only from explicit full-manifest metadata:

| Replicate | EV control | PUM1 treatment |
| --------- | ---------- | -------------- |
| `2` | `ABE_EV_2` | `ABE_PUM1_2` |
| `3` | `ABE_EV_3` | `ABE_PUM1_3` |
| `4` | `ABE_EV4` | `ABE_PUM1_4` |

`configs/step_09_pairs.NORAD_EV_PUM1.tsv` records this approved mapping for
reference only. It is not a runtime overlay, and pairing is never inferred
from sample names. The replicate-bearing full sample manifest must be used
before Step `07` so one manifest hash flows through the Steps `07`-`09` chain.

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

Demo meaning: the reusable preprocessing backbone is rebuilt and
cluster-validated through Step `06` across the full six-sample cohort. Steps
`07`-`09` extend the local code boundary with mocked/fake-runtime-tested
contracts, but the cluster-proven boundary has not moved.

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

Current evidence includes implementation commit `90335d8`, corrective commit
`eae5eca`, passing shell/fake-R wrapper tests, the guarded local R environment,
and a real-R suite that passes without `SKIP`. The correction validates raw
DP/AD/INFO AD lexemes before `VariantAnnotation`; the partition-overlap
validator was already correct. No production Step `08` table, cluster job, or
biological candidate result has been inspected.

## Step 09 Local Paired-CMH Contract

Step `09` consumes only the exact Step `08` sites table and complete input
receipt for the declared cohort. It verifies manifest hashes, the complete
partition/orientation set, row and candidate uniqueness, receipt counts, and
manifest-ordered `DP__`, `AD__`, and `AF__` sample columns. Pairing comes only
from explicit full-manifest replicates, with one EV and one PUM1 sample per
stratum and at least two strata.

For every successfully testable RNA `A>G` candidate, the base-R engine runs a
two-sided, continuity-corrected paired CMH test. The common odds ratio is
treatment relative to control. BH is applied once across all successfully
tested target candidates from all partitions and orientations before call-level
depth/background/effect filters. Defaults require per-sample DP at least `1`,
mean DP strictly above `50`, FDR strictly below `0.05`, common OR above `1.2`
or below `1/1.2`, and absolute treatment-control fraction difference above
`0.005`. Optional background filtering is disabled by default; EV is never
recast as no-dox.

Missing, low-coverage, degenerate, and non-target rows are retained with
explicit statuses. The six-output transaction is:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The summary publishes last as the commit marker. The outputs preserve
`orientation_policy=legacy_provisional_v1` where applicable; the policy is not
biologically validated.

Current evidence includes implementation commit `e4371de`, passing
shell/fake-R wrapper tests, 23 passing Python tests, the guarded local R
environment, and a real-R suite that passes without `SKIP` after the
`eae5eca` fixture correction. PDF EOF matching is now raw-byte based and
locale-independent. No production Step `09` CMH output, cluster job, plot, or
biological candidate result has been inspected.

## Engineering And Reproducibility Features

The rebuilt pipeline emphasizes:

- local-first development
- SLURM execution at scale
- dry-run by default
- explicit `EXECUTE=1`
- scope-owned locking, including Step `07` cohort/partition, Step `08` cohort, and Step `09` analysis locks
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
- The current state is honest: preprocessing and read-orientation splitting
  are cluster-proven through Step `06`; Step `07` is mocked-bcftools tested
  locally; the Step `08` and Step `09` real-R suites pass locally without
  `SKIP`; none has downstream production, cluster, or biological-result
  evidence.

## Near-Term Roadmap

### Phase 1 — Rebuild and validate preprocessing backbone

Status: cluster-proven through Step `06` across all six samples. Steps `07`-`09`
are implemented and locally fake-tool tested. The local R environment is now
installed and checked, and Step `08`/`09` semantic real-R fixture suites pass
locally after `eae5eca`. Cluster gates remain paused.

- Reference prep and STAR index
- STAR alignment across six samples
- Canonical BAM generation and QC
- RSeQC strandedness confirmation
- Picard MarkDuplicates
- GATK SplitNCigarReads
- Read-orientation BAM split

Current boundary:
Step `06` is the final cluster-proven preprocessing/read-orientation split
step and is proven across all six samples. Step `09` is the compute-code
boundary; Steps `07`-`09` remain not cluster-proven.

### Phase 2 — Reproduce legacy editing-site calling workflow

Status: locally implemented. Step `07` is mocked-bcftools tested; Steps `08`
and `09` are shell/fake-R tested and their real-R suites pass locally. All Step
`07`-`09` production and remote execution remains pending.

- Step `07`: cohort bcftools mpileup per declared partition and mechanical read-orientation group, implemented locally but not run with real bcftools
- Step `08`: preprocess the exact Step `07` receipt set into deterministic candidate/input/QC tables; raw count lexemes are preflighted before semantic parsing
- Step `09`: paired CMH calling across explicit manifest-defined strata; the real-R PDF fixture uses locale-independent raw-byte validation
- Preserve/control strand and read-orientation assumptions
- Runtime-validate and cluster-promote each downstream stage in upstream order

### Phase 3 — Scientific review and refinement

Status: activated as local `step-09c-scientific-validation` tooling immediately
after the real-R fixes. It records explicit evidence and decisions without
rerunning CMH or claiming a production scientific review.

- Validate the flag-group/transcript-strand/RNA-allele mapping independently
  at predeclared plus-strand and minus-strand transcript loci; A>G enrichment
  is supporting evidence, not proof.
- Record the Novogene GTF path/checksum/delivery provenance and exact release
  when recoverable; otherwise retain the release as an explicit limitation.
- Reconcile the Step `07` -> `08` -> `09` candidate funnel by partition and
  orientation.
- Predeclare threshold sensitivity and leave-one-pair-out analyses under
  distinct analysis IDs; review the unweighted mean-sample-AF effect metric,
  replicate-direction discordance, `ABE_EV_2`, and replicate `4`.
- Adjudicate deterministic top, discordant, and near-threshold candidates
  with explicit pass/flag/reject evidence and limitations.
- Decide whether an eligible distinct background cohort exists. EV is not
  no-dox; adding a background changes the manifest hash and reruns Steps
  `07`-`09`.

Before viewing results, freeze the selection rules, sample sizes, sensitivity
grid/decision thresholds, hashes, git commit, commands/versions, reviewer/date/
owner, and analysis IDs. `science_review_complete_exploratory` records a
finished review but keeps results provisional.
Step `09c` accepts `evidence_incomplete` or
`science_review_complete_exploratory`; it must reject the reserved
`biological_interpretation_ready` value until a separately approved policy
branch unlocks its stricter exit criteria. This gate is not Step `10` and does
not itself provide orthogonal experimental validation.

### Phase 4 — Immediate artifacts and reports

Status: activated after Step `09c`, but not implemented yet.

The approved order is artifact schema, read-only adapters, canonical run
summary, self-contained HTML, then bundled-Typst PDF/TSV exports. Reports use
explicit inventory paths, represent missing/incomplete evidence, and carry a
persistent scientific-state banner. Candidate rows are “CMH-ranked
candidates,” never validated editing sites. Report generation is not evidence
of computational or biological validation.

### Phase 5 — Foundations and per-step validators

Status: activated after report exports, but not implemented yet.

Read-only runtime preflight, reference provenance, and storage
inventory/retention tooling precede one validation-report branch for each of
`00a`, `00b`, `00c`, `01`, `02`, `02b`, `03`, `04`, `05`, `06`, `07`, `08`,
and `09`. Remote validation resumes only after
`post09-validation-report-09`. Analysis config, module extraction, arrays,
generic dispatchers, automatic cleanup, and public-data ingestion remain
deferred.

## Questions For PI Discussion

- Are the high duplication rates expected for this dataset/prep, especially ABE_EV4 and ABE_PUM1_4?
- Should ABE_EV_2’s lower unique mapping / higher multimapping be treated as a sample QC concern or acceptable cohort variation?
- Should the first biologically useful MVP output be orientation-split BAMs, mpileup VCFs, preprocessed candidate tables, or CMH-ranked editing sites?
- Should we preserve the legacy `FWD_like` / `REV_like` read-orientation split exactly before changing biological interpretation?
- What evidence would approve or replace `legacy_provisional_v1`, and what
  annotation version/semantics should be authoritative?
- Is unweighted mean sample AF the intended effect metric, and which primary
  thresholds/sensitivity analyses should be predeclared?
- Is there a genuine eligible background cohort, and what candidate
  adjudication or orthogonal evidence is required before biological claims?

## Next Steps

The `step-09b1-real-r-fixes` branch is complete and pushed; both real-R suites
pass locally without `SKIP`.

1. Implement Step `09c`, the artifact schema/adapters/run summary, and the
   immediate HTML/PDF reporting slice in separate gated descendant branches.
2. Implement read-only foundations and one validator branch per pipeline step;
   stop local work at `post09-validation-report-09`.
3. Resume remote validation later in upstream order. Even then, keep
   computational proof independent from biological readiness.

## Demo Talking Points

- We are rebuilding the legacy workflow into maintainable research software with explicit inputs, outputs, dry-runs, and tests.
- The current pipeline has been validated through read-orientation splitting across all six samples.
- The cohort is consistently reverse-stranded / first-strand-style by RSeQC.
- STAR and duplicate-marking summaries already provide useful preliminary QC observations.
- Step `05` exposed a real cluster temp-space issue and was hardened rather than papered over.
- Step `05` is now cohort-proven after final BAM/BAI output inspection.
- Step `06` preserves read-orientation groups without making unsupported biological strand claims and is cluster-proven across all six samples.
- Step `07` has local implementation and mocked-test evidence only; no cluster VCFs or biological results are presented.
- Step `08` real-R fixtures pass locally without `SKIP`; raw count lexical
  validation and partition-overlap rejection are covered. No
  production/cluster table or biological result is presented.
- Step `09` real-R fixtures pass locally without `SKIP`, including
  locale-independent raw-byte PDF EOF validation. No production/cluster CMH
  table, plot, or biological result is presented.
- Steps `08` and `09` use `orientation_policy=legacy_provisional_v1`, which preserves a legacy mapping but is not biologically validated.
- The signed local R `4.6.1` and guarded `renv`/Bioconductor `3.23`
  environment pass namespace, lock, headless-PDF, and empty binary restore
  checks; Step `09b1` fixes are complete locally and Step `09c` is next.
- Scientific-validation tooling and immediate consolidated HTML/PDF reporting
  are activated next, but neither is implemented at this boundary and neither
  can establish validation.
- Future cluster proof establishes computation, not biological truth;
  orientation, annotation, robustness, candidate evidence, and background
  eligibility remain a separate science gate.
