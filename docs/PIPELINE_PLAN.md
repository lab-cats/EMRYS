# NORAD Pipeline Plan

This is a high-level handoff map for the local-first, SLURM-scaled workflow.
Future steps are scaffolding only until their scripts, wrappers, and tests are
implemented.

| Step | Purpose | Expected inputs | Expected outputs | Status | Main tool(s) |
| --- | --- | --- | --- | --- | --- |
| 00a | Build the Novogene STAR index. | Novogene reference FASTA/GTF under `data/raw/` | STAR index under `refs/novogene_star_index/` | implemented | STAR |
| 00b | Convert reference GTF to sorted BED12 for strandedness checks. | `refs/novogene_ref/genome.gtf` | `refs/novogene_ref/genome.bed` | implemented | Python, bedtools |
| 01 | Align paired-end FASTQs to the reference. | FASTQ R1/R2 files, STAR index | STAR alignment output under `results/star/` | implemented | STAR |
| 02 | Sort and index canonical BAMs. | STAR SAM/BAM alignment | `results/bam/<sample_id>/<sample_id>.sorted.bam` and index | implemented | samtools |
| 02b | Run BAM integrity/QC checks. | `results/bam/<sample_id>/<sample_id>.sorted.bam` | QC summaries under `results/qc/bam/` | implemented | samtools |
| 03 | Infer strandedness and read orientation. | sorted BAM, `refs/novogene_ref/genome.bed` | `results/qc/strandedness/<sample_id>.infer_experiment.txt` | pending | RSeQC `infer_experiment.py` |
| 04 | Mark PCR/optical duplicates. | `results/bam/<sample_id>/<sample_id>.sorted.bam` | duplicate-marked BAM and Picard metrics | pending | Picard MarkDuplicates |
| 05 | Run RNA-seq SplitNCigarReads. | duplicate-marked BAM | `results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.bam` | pending | GATK SplitNCigarReads |
| 06 | Split processed BAMs by read orientation. | split-N-cigar BAM | FWD/REV orientation-specific BAMs and indexes | pending | samtools |
| 07 | Run mpileup by chromosome and strand. | FWD/REV BAMs, chromosome BEDs, reference FASTA | per-chromosome/per-strand VCF files | pending | bcftools |
| 08 | Preprocess mpileup VCFs for editing-site statistics. | Step 07 VCF files | cleaned/annotated VCF-like TSV/table files | pending | R |
| 09 | Call CMH editing sites and write summaries. | Step 08 preprocessed tables | CMH/editing-site result tables and plots | pending | R |

## Reference Workflow Alignment

Steps 04-09 are based on the uploaded/reference RNA-editing workflow:
MarkDuplicates -> SplitNCigarReads -> split BAM by read orientation -> bcftools
mpileup -> VCF preprocessing -> CMH editing-site calling.

This repository is rebuilding that workflow in a cleaner SLURM/script/testable
structure rather than using the hardcoded original scripts directly.
