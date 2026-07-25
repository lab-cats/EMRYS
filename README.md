# NORAD / CSU HPC RNA-seq Workflow

This repository contains code, tests, documentation, and SLURM job wrappers for a NORAD / PUM1 / rABE-related Novogene Remora RNA-seq workflow.

The project rebuilds a hardcoded legacy RNA-editing/RNA-seq workflow into maintainable research software. The rebuilt pipeline is manifest-driven, local-first, SLURM-scaled, and dry-run-first for:

* local development on macOS
* full-scale execution on CSU's SLURM cluster
* RNA-seq preprocessing
* strandedness/orientation inference
* downstream RNA-editing / variant-like site calling

The uploaded legacy workflow is treated as a protocol reference, not as production code. Local implementation stages use descendant branches, focused and repository-wide tests, a separate documentation-only commit, and a clean push gate. Runtime promotion remains upstream-first through SLURM dry-run, execute, output inspection, and evidence docpatches.

A future decoupled reporting layer is planned to consume structured pipeline artifacts and render reusable HTML, PDF, and TSV outputs without rerunning computation. That layer is roadmap-only and not implemented.

## Current Status

Steps `00a`-`00c` are cluster-proven reference prep. Steps `01`-`06` are cluster-proven across all six samples. Step `06` preserves the legacy read-orientation split without claiming biological strand interpretation. Step `07` is implemented locally and locally tested with mocked bcftools, but real-bcftools runtime validation is unavailable on this workstation and no Step `07` cluster dry-run or execute evidence has been inspected. Step `08` is implemented locally at implementation commit `90335d8` and its wrapper/publication behavior is locally tested with a fake `Rscript`; this workstation has no `Rscript`, so the real-R fixture suite has not run, and no Step `08` cluster evidence exists. Step `09` remains pending / not implemented / not cluster-proven. After the Step `08` docpatch and push gate, the next local implementation boundary is Step `09`; later cluster promotion still begins with Step `07`.

| Step | Purpose | Status |
| ---- | ------- | ------ |
| `00a` | Build Novogene STAR index | cluster-proven |
| `00b` | Convert GTF to BED12 for RSeQC | cluster-proven |
| `00c` | GATK reference sidecars / reference FASTA index and sequence dictionary | cluster-proven |
| `01` | STAR alignment | complete and cluster-proven across all six samples |
| `02` | Canonical sorted/read-group/indexed BAM | hardened and cluster-proven across all six samples |
| `02b` | BAM QC with samtools | implemented and refreshed across all six final hardened Step 02 BAMs |
| `03` | Infer strandedness/orientation with RSeQC | cluster-proven across all six samples |
| `04` | Picard MarkDuplicates | cluster-proven across all six samples |
| `05` | SplitNCigarReads | implemented and cluster-proven across all six samples |
| `06` | read-orientation BAM split | cluster-proven across all six samples |
| `07` | cohort mpileup by declared partition and mechanical orientation | implemented locally; mocked-bcftools tests pass; runtime and cluster validation pending; not cluster-proven |
| `08` | deterministic VCF preprocessing and annotation | implemented locally; shell/fake-R tests pass; real-R runtime and cluster validation pending; not cluster-proven |
| `09` | paired CMH editing-site calling | pending / not implemented / not cluster-proven |

### Step 07 Local Implementation

Implemented entry points:

```text
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
```

Partition manifests:

```text
configs/step_07_partitions.primary_contigs.tsv  # approved correction universe: 1-22, X, Y, MT
configs/step_07_partitions.pilot.tsv            # one-row pilot: 1:1-100000
configs/step_07_partitions.example.tsv          # illustrative schema/example
```

One invocation selects one declared partition, passes every sample BAM to a cohort-wide mpileup in manifest order, and produces both neutral mechanical orientations:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

The receipt is published last as the output-set commit marker; downstream stages must require and validate it rather than globbing VCFs. Step `07` is dry-run-first, validates declared inputs and output structure, and uses owned locks, run-token scratch paths, validation-before-publication, cleanup, and rollback. These claims are locally tested with a fake bcftools executable only. See `docs/operations/RUNBOOK.md` for the exact CLI, SLURM variables, and future cluster-promotion sequence.

### Step 08 Local Implementation

Implemented entry points and tests:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

Step `08` consumes exactly the declared partition-manifest cross-product with
`FWD_like` and `REV_like`; it never discovers VCFs by glob. It verifies the
Step `07` receipts, hashes, paths, record counts, and exact manifest-ordered
sample columns before using `VariantAnnotation`, `GenomicRanges`, and
`rtracklayer` to expand alternate alleles and annotate the Novogene GTF.
Symbolic and non-SNV alleles are counted and excluded.

The orientation mapping is explicitly provisional:

```text
orientation_policy=legacy_provisional_v1
FWD_like -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> compatible - transcripts -> retain genomic REF/ALT
```

This is legacy compatibility behavior, not a biologically validated strand
policy. Step `08` publishes a validated three-file transaction:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The wide sites table has fixed metadata followed by manifest-ordered
`DP__<sample>`, `AD__<sample>`, and `AF__<sample>` columns. The inputs receipt
is published last as the commit marker. Owned locks, stable input hashes,
run-token temporary paths, validation-before-publication, cleanup, and rollback
protect the output set. The shell/fake-R suite tests that wrapper contract.
`make real-r-test` runs the semantic R fixtures when `Rscript` is available;
on this workstation it reports `SKIP`, which is not real-R validation.

For demo details, start with `docs/demo/DEMO_WALKTHROUGH.md`, then use `docs/architecture/ARCHITECTURE.md` for the visual pipeline/dataflow architecture, `docs/demo/PI_DEMO_REPORT.md` for preliminary validation and QC summary, `docs/design/PIPELINE_PLAN.md` as the tactical map, `docs/operations/HANDOFF.md` for current state, `docs/operations/RUNBOOK.md` for safe inspection commands, the operations troubleshooting guide for known failure modes, and `TODO.md` for the next gates. Standalone Mermaid sources live in `docs/architecture/diagrams/pipeline.mmd` and `docs/architecture/diagrams/reliability.mmd`.

Architecture/design docs:

- `docs/architecture/FUTURE_ARCHITECTURE.md` - deferred modular target architecture for core preprocessing, analysis modules, and reporting.

## Cohort And Key Results

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

All six libraries are paired-end and reverse-stranded / first-strand-style by Step `03`. Tool-specific examples that often correspond to this orientation are:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

Do not treat those options as universally interchangeable without naming the tool.

## Biological And Computational Goal

This repository supports RNA-seq / RNA-editing workflow reconstruction for NORAD / PUM1 / rABE-related analysis.

The intended workflow is:

```text
FASTQ(.gz)
    ->
STAR alignment
    ->
canonical sorted/read-group/indexed BAM
    ->
BAM QC
    ->
RSeQC strandedness/orientation inference
    ->
Picard duplicate marking
    ->
GATK reference sidecar validation
    ->
GATK SplitNCigarReads
    ->
read-orientation BAM splitting
    ->
bcftools mpileup
    ->
VCF preprocessing
    ->
CMH/editing-site calling
```

This is not currently a simple gene-count differential-expression workflow. The downstream reference workflow points toward RNA-editing / variant-like site analysis.

Step `06` splits Step `05` BAMs into `FWD_like` and `REV_like` read-orientation groups using the legacy mechanical flag groups and writes an orientation counts TSV. These labels are not biological sense/antisense claims.

## Development Model

The intended development loop is:

```text
create the stage branch from the latest clean docpatched predecessor
    ->
implement only that stage
    ->
run focused and complete local validation
    ->
commit implementation and tests
    ->
reread project docs and perform the repository-wide docpatch
    ->
commit documentation separately, require a clean worktree, and push
    ->
create the next descendant local stage when explicitly approved
    ->
promote runtime stages upstream-first through SLURM dry-run and execute
    ->
inspect logs and outputs, then commit the validation docpatch
    ->
proceed to next step
```

The cluster login node should not be used for heavy computation. It is for editing, Git operations, small file transfers, light checks, file inspection, and submitting jobs.

Full analysis should run through SLURM jobs in `jobs/`.

## Quick Start: Local Development

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

Record dependency or tooling changes in `requirements.txt`, `environment.yml`, or another project setup document rather than leaving them implicit.

Run the local validation gate:

```bash
git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
make real-r-test
git status --short
git diff --name-status
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

## Quick Start: Cluster Execution

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

## Operator Checklist

- **Default dry-run:** Workflow shell scripts and SLURM wrappers default to dry-run. Submit a dry-run first to verify resolved inputs, printed commands, and logs.
- **Submit execute jobs explicitly:** Use `EXECUTE=1` when ready, e.g.:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

- **Script-level execution flag:** Workflow shell scripts use `--execute` to run tool commands; include all required step arguments when invoking a script directly.
- **Validation locations:** Use `docs/operations/RUNBOOK.md` for per-step dry-run/execute checks, `docs/design/PIPELINE_PLAN.md` for step status, and the design decisions log for execution policy.
- **Quick checks after execute:** Confirm expected outputs under `results/`, inspect SLURM logs under `logs/`, and use `sacct` for job state.

## Repository Layout

```text
scripts/        # Python, shell, and R scripts
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

## Important Documentation Files

```text
docs/operations/       handoff, runbook, and troubleshooting
docs/design/           pipeline plan, questions, and decisions
docs/demo/             PI demo walkthrough and report
docs/architecture/     visual pipeline/dataflow architecture and diagrams
TODO.md                tactical next work
README.md              entrypoint / overview
```

## Data And Reference Locations

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

### Reference files

Prepared reference files:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

Reference notes:

* Novogene-provided GRCh38-like reference.
* Chromosome names are numeric-style, for example `1`, `2`, `3`, not `chr1`, `chr2`, `chr3`.
* FASTA and GTF chromosome names match.
* STAR index was built with `sjdbOverhang=149` for 150 bp reads.
* BED12 annotation was generated from the GTF for RSeQC.
* Step `00c` formalizes GATK sidecar prep with `scripts/step_00c_prepare_gatk_reference.sh` and `jobs/step_00c_prepare_gatk_reference.slurm`; it is cluster-proven.

## Confirmed Tools On CSU

Known modules/tools:

```text
star/2.7.11b
samtools/1.19.2
bedtools/2.31.1
picard/3.1.1
python39
java/17.0.10
GATK 4.6.1.0: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
bcftools 1.21: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

Picard is exposed through the jar path set by the module. Step `04` validates the selected Java executable and actual runtime version before Picard starts.

RSeQC is available through the project virtual environment:

```text
.venv/bin/infer_experiment.py
```

GATK and bcftools were validated on compute node `node002`; the tool probe completed successfully with exit code `0:0`.

Still unresolved:

```text
R / Rscript
```

An operator-validated `Rscript` plus the required Bioconductor packages is
needed to run the Step `08` real-R fixture suite and later cluster promotion.
The implemented wrapper does not install packages or guess an R module.

## Beginner Glossary

`FASTQ` / `.fastq.gz`: raw sequencing reads. For paired-end data, `R1` is the first read and `R2` is the second read.

`SAM`: human-readable alignment format.

`BAM`: compressed binary alignment format.

`BAI`: BAM index file.

`STAR`: splice-aware RNA-seq aligner used here to align FASTQs to the reference.

`samtools`: alignment-file toolkit used for sorting, indexing, filtering, and inspecting BAMs.

`Picard`: preprocessing/QC toolkit; current use here is duplicate marking with `MarkDuplicates`.

`GATK`: genomics toolkit; Step `05` uses `SplitNCigarReads` for RNA-seq preprocessing after duplicate marking.

`R`: downstream analysis, statistics, visualization, and tables.

## Git And Data Policy

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
