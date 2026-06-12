# NORAD / CSU HPC RNA-seq Workflow

This repository contains code, tests, documentation, and SLURM job wrappers for a NORAD / PUM1 / rABE-related Novogene Remora RNA-seq workflow.

The project is being rebuilt as a maintainable, manifest-driven, dry-run-first pipeline for:

* local development on macOS
* full-scale execution on CSU’s SLURM cluster
* RNA-seq preprocessing
* strandedness/orientation inference
* downstream RNA-editing / variant-like site calling

The uploaded legacy workflow is treated as a protocol reference, not as production code.

## Current status

The pipeline is being developed one validated step at a time.

Current development/validation sample:

```text
ABE_EV_2
```

Implemented and cluster-proven for `ABE_EV_2`:

| Step  | Purpose                                   | Status                        |
| ----- | ----------------------------------------- | ----------------------------- |
| `00a` | Build Novogene STAR index                 | cluster-proven                |
| `00b` | Convert GTF to BED12 for RSeQC            | cluster-proven                |
| `01`  | STAR alignment                            | cluster-proven for `ABE_EV_2` |
| `02`  | Create canonical sorted/indexed BAM       | cluster-proven for `ABE_EV_2` |
| `02b` | BAM QC with samtools                      | cluster-proven for `ABE_EV_2` |
| `03`  | Infer strandedness/orientation with RSeQC | cluster-proven for `ABE_EV_2` |

Pending scaffold-only steps:

| Step | Purpose                                               |
| ---- | ----------------------------------------------------- |
| `04` | Picard MarkDuplicates                                 |
| `05` | GATK SplitNCigarReads                                 |
| `06` | Split BAMs by read orientation                        |
| `07` | bcftools mpileup by chromosome and orientation/strand |
| `08` | VCF preprocessing                                     |
| `09` | CMH editing-site calling                              |

Future scaffold jobs are intentionally non-runnable until implemented.

## Biological and computational goal

This repository supports RNA-seq / RNA-editing workflow reconstruction for NORAD / PUM1 / rABE-related analysis.

The high-level intended workflow is:

```text
FASTQ(.gz)
    ↓
STAR alignment
    ↓
canonical sorted/indexed BAM
    ↓
BAM QC
    ↓
RSeQC strandedness/orientation inference
    ↓
Picard duplicate marking
    ↓
GATK SplitNCigarReads
    ↓
read-orientation BAM splitting
    ↓
bcftools mpileup
    ↓
VCF preprocessing
    ↓
CMH/editing-site calling
```

This is not currently a simple gene-count differential-expression workflow. The downstream reference workflow points toward RNA-editing / variant-like site analysis.

## Key result so far

RSeQC `infer_experiment.py` for `ABE_EV_2` produced:

```text
This is PairEnd Data
Fraction of reads failed to determine: 0.0828
Fraction of reads explained by "1++,1--,2+-,2-+": 0.0432
Fraction of reads explained by "1+-,1-+,2++,2--": 0.8740
```

Interpretation:

```text
ABE_EV_2 appears strongly reverse-stranded / first-strand-style.
```

Common equivalent settings:

```text
featureCounts -s 2
HTSeq stranded=reverse
fr-firststrand
```

This has only been confirmed for `ABE_EV_2`. Confirm strandedness across all six samples before treating it as a global library-prep assumption.

## Development model

The intended development loop is:

```text
implement locally
    ↓
run local tests
    ↓
commit and push
    ↓
pull on cluster
    ↓
submit SLURM dry-run
    ↓
inspect logs
    ↓
submit SLURM execute job
    ↓
inspect outputs
    ↓
proceed to next step
```

The cluster login node should not be used for heavy computation. It is for editing, Git operations, small file transfers, light checks, file inspection, and submitting jobs.

Full analysis should run through SLURM jobs in `jobs/`.

## Quick start: local development

Clone the repo:

```bash
git clone https://github.com/Glen-Cocoa/norad.git
cd norad
```

Create and activate a local Python environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Record dependency changes in `requirements.txt`, `environment.yml`, or another project-specific setup file rather than leaving them implicit.

Run the local validation gate:

```bash
git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
```

Shortcut for the Makefile-covered checks:

```bash
make all-checks
```

Validate the example manifest:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv
```

To also check file existence:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv \
  --base-dir . \
  --check-files
```

## Quick start: cluster execution

On the cluster:

```bash
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Run a dry-run job first:

```bash
sbatch jobs/<step>.slurm
```

Inspect the job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

If the dry-run looks correct, run execute mode:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Then inspect outputs before proceeding.

Optional cluster helper commands may exist in `~/.bashrc`:

```bash
norad
nlogs
sqme
sj <JOBID>
sjtail <JOBID>
sjcheck <JOBID>
```

These helpers are convenience only; the repo does not depend on them.

## Repository layout

```text
scripts/        # Python, shell, and later R scripts
jobs/           # SLURM job wrappers
tests/          # local tests and pending test plans
configs/        # optional config files
data/test/      # tiny local test fixtures only
data/raw/       # large/raw data symlinks; not committed
data/full/      # optional full-scale data paths; not committed
results/        # generated outputs; not committed
logs/           # SLURM stdout/stderr logs; not committed
docs/           # project documentation
```

Large data files and generated outputs should stay out of Git.

## Important documentation files

```text
docs/HANDOFF.md        big project-state handoff
docs/PIPELINE_PLAN.md  tactical step map and validation status
docs/QUESTIONS.md      answered/open project questions
docs/RUNBOOK.md        operational commands and cluster procedure
DECISIONS.md           decisions and reasons
README.md              entrypoint / overview
```

## Data and reference locations

### Local repo

```text
/Users/elisteiger/dev/norad
```

### Cluster repo

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Raw data symlink on cluster

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs live under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### Manifest

```text
samples.tsv
```

Known samples:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Conditions:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Note that `ABE_EV4` lacks the underscore before `4`.

### Reference files

Prepared reference files:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

Reference notes:

* Novogene-provided GRCh38-like reference.
* Chromosome names are numeric-style, for example `1`, `2`, `3`, not `chr1`, `chr2`, `chr3`.
* FASTA and GTF chromosome names match.
* STAR index was built with `sjdbOverhang=149` for 150 bp reads.
* BED12 annotation was generated from the GTF for RSeQC.

## Implemented pipeline steps

### Step 00a: build STAR index

Job:

```text
jobs/step_00a_build_novogene_star_index.slurm
```

Output:

```text
refs/novogene_star_index/
```

Status:

```text
implemented / cluster-proven
```

### Step 00b: GTF to BED12

Script:

```text
scripts/gtf_to_bed12.py
```

Job:

```text
jobs/step_00b_gtf_to_bed12.slurm
```

Output:

```text
refs/novogene_ref/genome.bed
```

Validated output:

```text
206,601 transcript BED12 records
```

Status:

```text
implemented / cluster-proven
```

### Step 01: STAR alignment

Script:

```text
scripts/step_01_star_align.sh
```

Job:

```text
jobs/step_01_star_align.slurm
```

Validated output for `ABE_EV_2`:

```text
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
results/star/ABE_EV_2/ABE_EV_2.Log.final.out
results/star/ABE_EV_2/ABE_EV_2.Log.out
results/star/ABE_EV_2/ABE_EV_2.Log.progress.out
results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

### Step 02: canonical sort/index BAM

Script:

```text
scripts/step_02_sort_index_bam.sh
```

Job:

```text
jobs/step_02_sort_index_bam.slurm
```

Validated output for `ABE_EV_2`:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

### Step 02b: BAM QC

Script:

```text
scripts/step_02b_bam_qc.sh
```

Job:

```text
jobs/step_02b_bam_qc.slurm
```

Expected output for `ABE_EV_2`:

```text
results/qc/bam/ABE_EV_2.quickcheck.txt
results/qc/bam/ABE_EV_2.flagstat.txt
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

### Step 03: strandedness/orientation inference

Script:

```text
scripts/step_03_infer_strandedness_and_orientation.sh
```

Job:

```text
jobs/step_03_infer_strandedness_and_orientation.slurm
```

Validated output for `ABE_EV_2`:

```text
results/qc/strandedness/ABE_EV_2.infer_experiment.txt
```

Status:

```text
implemented / cluster-proven for ABE_EV_2
```

## Pending pipeline steps

The following are scaffold-only and should not be treated as implemented:

```text
jobs/step_04_mark_duplicates.slurm
jobs/step_05_split_n_cigar_reads.slurm
jobs/step_06_split_bam_by_read_orientation.slurm
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
jobs/step_08_vcf_preprocessing.slurm
jobs/step_09_cmh_editing_site_calling.slurm
```

Next likely implementation target:

```text
Step 04: Picard MarkDuplicates
```

Expected Step 04 input:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Likely Step 04 outputs:

```text
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai
results/qc/markdup/ABE_EV_2.markdup.metrics.txt
```

## Confirmed tools on CSU

Known modules/tools:

```text
star/2.7.11b
samtools/1.19.2
bedtools/2.31.1
picard/3.1.1
python39
java/17.0.10
```

Picard is invoked through the jar path set by the module:

```bash
module load picard/3.1.1
java -jar "$PICARD" MarkDuplicates ...
```

RSeQC is available through the project virtual environment:

```text
.venv/bin/infer_experiment.py
```

Still unresolved:

```text
GATK
R / Rscript
bcftools
```

## Bioinformatics glossary

### File formats

`FASTQ` / `.fastq.gz`: raw sequencing reads. For paired-end data, `R1` is the first read and `R2` is the second read.

`SAM`: human-readable alignment format.

`BAM`: compressed binary alignment format.

`BAI`: BAM index file.

### Tools

`STAR`: splice-aware RNA-seq aligner used here to align FASTQs to the reference and produce SAM/BAM-style alignment outputs.

`samtools`: alignment-file toolkit used for operations such as sorting, indexing, filtering, and inspecting BAMs.

`Picard`: preprocessing/QC toolkit; current expected use is duplicate marking with `MarkDuplicates`.

`GATK`: genomics toolkit; current expected use is RNA-seq preprocessing with `SplitNCigarReads`, pending cluster availability.

`R`: downstream analysis, statistics, visualization, and tables.

## Git and data policy

Use Git for:

* source code
* SLURM job wrappers
* configuration files
* documentation
* small safe test fixtures

Do not commit:

* FASTQ / FASTQ.GZ
* SAM / BAM / CRAM / BAI
* large TSV/CSV outputs
* logs
* results directories
* credentials or tokens
* `.env` files
* private SSH keys
* large raw reference/data files

Tiny test fixtures may be committed only if they are small, safe, and non-sensitive.

## Script and job conventions

Scripts should:

* accept explicit command-line arguments
* avoid hardcoded local or cluster paths where practical
* provide useful `--help`
* fail with clear errors
* print resolved context in dry-run mode
* support `--execute`
* validate required inputs and outputs
* be testable locally with small fixtures or mocks

SLURM wrappers should:

* default to dry-run mode
* use `EXECUTE=1` for execute mode
* fail on invalid `EXECUTE` values
* create/log into `logs/`
* export/use `TMPDIR=/tmp`
* log job ID, job name, node, working directory, TMPDIR, modules, inputs, and outputs
* call the corresponding script rather than duplicating logic

## Notes

The goal is not to develop directly on the cluster. The goal is to make scripts work locally on small data, then submit reproducible SLURM jobs for full-scale execution.

Keep the workflow boring, gated, and reproducible.
