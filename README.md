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

Steps `00a`-`00c` are cluster-proven reference prep. Steps `01`-`06` are cluster-proven across all six samples. Step `06` preserves the legacy read-orientation split without claiming biological strand interpretation. Step `07` is implemented locally and locally tested with mocked bcftools, but real-bcftools runtime validation is unavailable on this workstation and no Step `07` cluster dry-run or execute evidence has been inspected. Step `08` is implemented locally at implementation commit `90335d8` and its wrapper/publication behavior is locally tested with a fake `Rscript`; this workstation has no `Rscript`, so the real-R fixture suite has not run, and no Step `08` cluster evidence exists. Step `09` is implemented locally at implementation commit `e4371de`; its shell/fake-R wrapper, manifest, transaction, and output-validation contracts are locally tested, while its real-R fixture runner reports `SKIP` because this workstation has no `Rscript`. No Step `09` cluster dry-run, execute, log, or output evidence exists. Steps `07`-`09` are therefore not cluster-proven. The Step `09` implementation/docpatch gate is complete and pushed at `9ac8307`; the documentation-only descendant `step-09a-roadmap-docpatch` is the required clean/pushed base for sequential cluster promotion beginning with Step `07`.

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
| `09` | paired CMH editing-site calling | implemented locally; shell/fake-R tests pass; real-R runtime and cluster validation pending; not cluster-proven |

### Promotion, Scientific Review, And Roadmap Gates

The approved descendant history is:

```text
step-09-cmh
└── step-09a-roadmap-docpatch
    └── validate-step-07
        └── validate-step-08
            └── validate-step-09
                └── step-09b-scientific-validation
```

Before `validate-step-07`, establish the production runtime six-sample
replicate-bearing `samples.tsv` and record its SHA-256; that file is absent
from this checkout and its cluster provisioning has not been inspected. The
same manifest bytes and hash must flow through Steps `07`-`09`. Also resolve
the compute-node-visible `Rscript`, required Step `08` packages and hash
utilities, run both real-R fixture suites in that environment, verify all
twelve Step `06` BAM/BAI pairs, confirm the FASTA/FAI primary contigs including
`MT`, and inspect storage/quota before production mpileup.

If resolving the manifest requires a tracked repository/config change, insert
a separately gated descendant package such as
`step-07a-runtime-manifest` before `validate-step-07`; do not mix a config
implementation into the evidence-only validation branch. A byte-identical
cluster-local copy needs provenance evidence, not a fabricated implementation
commit.

Runtime promotion exits are deliberately numeric:

* Step `07`: pilot and chromosome-1 gates first, then the remaining 24 primary
  partitions, completing 25 primary receipts and 50 valid primary VCFs; the
  pilot receipt/two VCFs remain outside the correction universe.
* Step `08`: one three-file transaction with exactly 50 input-receipt rows in
  partition order and `FWD_like`, then `REV_like`, order, with hashes, schemas,
  candidate uniqueness, and counts reconciled.
* Step `09`: one six-file transaction whose all-sites count equals Step `08`,
  significant table is the exact ordered rows whose `call_status` is
  `significant_up` or `significant_down`, summary has one row, mutation
  spectrum has 12 rows, and both PDFs pass signature/EOF checks.

Each validation branch requires inspected scheduler/log/output evidence, an
evidence docpatch, a clean worktree, and a push before its descendant is
created. Even after Step `09` becomes computationally cluster-proven,
`legacy_provisional_v1` and the CMH-ranked candidate sites remain
scientifically provisional. The separate `step-09b-scientific-validation`
gate covers orientation, annotation provenance/semantics, predeclared
threshold sensitivity, replicate robustness, candidate adjudication, and the
background-cohort decision. It is not Step `10`. Evidence may close as
`science_review_complete_exploratory`, which leaves all biological claims
provisional, or as `biological_interpretation_ready`, which additionally
requires a validated orientation policy and every stricter scientific exit.
Exploratory completion may unblock operational/artifact tooling, but not
biological candidate claims.

Only after runtime proof and the scientific gate should the ordered
post-proof packages begin: reusable runtime-environment audit tooling,
reference-registry/provenance tooling,
storage/retention, step-specific validation reports, targeted reruns, artifact
schema and adapters, run-summary aggregation, HTML then PDF/TSV reporting,
analysis config, and finally a thin `rna_editing_cmh` module. Generic job
arrays, broad helper-library refactors, automatic R installation, public-data
ingestion, and report generation remain deferred until their stated
prerequisites are met. The canonical details are in
`docs/design/PIPELINE_PLAN.md` and `TODO.md`.

The promotion-specific environment, reference, and storage evidence is
collected manually now using the runbook. The later packages productize those
checks for repeatable future runs/cohorts; they are not excuses to defer the
current prerequisites. Their package labels remain candidates until each
package is separately activated, while the dependency order is fixed.

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
`make real-r-test` runs both semantic R fixture suites when `Rscript` is
available; on this workstation both runners report `SKIP`, which is not
real-R validation.

### Step 09 Local Implementation

Implemented entry points, tests, and reference pairing:

```text
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
jobs/step_09_cmh_editing_site_calling.slurm
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

The full sample manifest is the only runtime pairing source. Its optional
`replicate` column becomes required for Step `09`: each replicate must contain
exactly one control and one treatment, the two conditions must have identical
replicate sets, and at least two strata are required. The tracked Step `09`
pairing file documents the approved `2`, `3`, and `4` relationships only; it is
not a runtime overlay, and pairing is never inferred from sample names. The
same replicate-bearing sample manifest must be used before Step `07` so its
hash propagates through the complete Steps `07`-`09` chain.

Step `09` validates the Step `08` sites table and complete input-receipt contract,
runs two-sided continuity-corrected paired CMH tests with treatment-relative-
to-control common odds ratios, and applies BH once across all successfully
tested target candidates before call-level depth/effect filtering. Defaults
are EV control, PUM1 treatment, RNA `A>G`, per-sample depth at least `1`, mean
analysis depth strictly greater than `50`, FDR strictly less than `0.05`,
common odds ratio strictly above `1.2` or below `1/1.2`, and absolute
treatment-control fraction difference strictly above `0.005`. Optional
background filtering is disabled unless an explicit, distinct condition is
provided; EV is never repurposed as a missing no-dox cohort.

One validated transaction publishes four TSVs and two 7-by-5-inch PDFs:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The all-sites table retains missing, low-coverage, degenerate, and non-target
candidates with explicit statuses and preserves
`orientation_policy=legacy_provisional_v1`; that policy is not biologically
validated. The summary is published last as the six-output transaction commit
marker. Owned locks, immutable input hashes, run-token temporary and backup
paths, exact output reconciliation, cleanup, and rollback protect the set. The
real-R fixtures are implemented but have not run on this workstation because
`Rscript` is unavailable.

For demo details, start with `docs/demo/DEMO_WALKTHROUGH.md`, then use `docs/architecture/ARCHITECTURE.md` for the visual pipeline/dataflow architecture, `docs/demo/PI_DEMO_REPORT.md` for preliminary validation and QC summary, `docs/design/PIPELINE_PLAN.md` as the tactical map, `docs/operations/HANDOFF.md` for current state, `docs/operations/RUNBOOK.md` for safe inspection commands, the operations troubleshooting guide for known failure modes, and `TODO.md` for the next gates. Standalone Mermaid sources live under `docs/architecture/diagrams/`, including current pipeline/reliability diagrams and `future_roadmap_sequence.mmd`.

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
    ->
scientific evidence and decision gate
```

This is not currently a simple gene-count differential-expression workflow. The downstream reference workflow points toward RNA-editing / variant-like site analysis.

Step `06` splits Step `05` BAMs into `FWD_like` and `REV_like` read-orientation groups using the legacy mechanical flag groups and writes an orientation counts TSV. These labels are not biological sense/antisense claims.

The final arrow is a review gate, not another computational pipeline step.
Cluster execution can produce CMH-ranked candidate sites, but it does not by
itself validate the provisional orientation mapping or establish biological
truth.

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

An operator-validated `Rscript` plus the required Step `08` Bioconductor
packages is needed to run both real-R fixture suites and later cluster
promotion. Step `09` otherwise uses base R, including `stats`,
`graphics`, and `grDevices`. The implemented wrappers do not install packages
or guess an R module.

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
