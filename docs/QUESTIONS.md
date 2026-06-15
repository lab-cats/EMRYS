# Questions and answers

This file tracks project questions that were open during pipeline reconstruction, what has been answered, and what remains unresolved.

## Still open / unresolved

### GATK availability

* `module avail gatk` did not show a visible GATK module.
* Need to determine whether GATK is:

  * installed under a different module name,
  * available as a jar,
  * available through conda/mamba,
  * available through a container,
  * or should be installed into a project environment.

This blocks final implementation of:

```text
Step 05: SplitNCigarReads
```

### Full-scale execution across all samples

Only `ABE_EV_2` has been carried through Steps `01`, `02`, `02b`, and `03`.

Need to decide whether to:

1. Continue developing downstream steps on `ABE_EV_2`, or
2. Generalize/run Steps `01` through `03` across all six samples before implementing further downstream logic.

Current recommendation: continue developing on `ABE_EV_2`, but confirm strandedness across all six samples before making final global assumptions.

### Storage quotas

Storage is being used successfully under project/storage paths, but exact quotas have not been documented.

Need to determine:

* quota for home directory
* quota for `/mnt/stor-pool-01/users/2609214`
* whether there is scratch storage
* whether scratch should be used for temporary files

### Final deliverables

The broad final deliverables are expected to be RNA-editing / variant-like site summaries and CMH result tables/plots, but the exact final table/plot formats are not yet specified.

Need to define expected Step `09` outputs before porting the old R scripts.

### Future artifact and reporting design

Structured artifacts and reporting are planned, deferred, and non-runnable. Open questions:

* What is the exact versioned JSON schema for per-step sidecars?
* What are the run ID semantics across dry-runs, execute runs, reruns, and partial reruns?
* How should provenance and git commit capture work on local machines and CSU SLURM?
* Should artifacts describe failed and incomplete runs, or only successful runs?
* How should reruns, schema-version conflicts, and pipeline-version conflicts be represented?
* What are the exact HTML, PDF, and TSV report deliverables?
* Which responsibilities belong to Jinja2 versus Quarto or R Markdown?
* What final CMH/editing-site results, plots, and interpretation notes belong in the report?

## Cluster

### What is the correct login node?

Answered operationally.

The user is able to connect to CSU HPC and work from:

```text
/mnt/stor-pool-01/users/2609214/norad
```

The shell helper assumes the cluster repo is available at:

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Is VPN required?

Answered operationally.

VPN was needed/used to access the cluster. The user found the correct VPN instructions and successfully connected.

### What are the exact module names?

Partially answered.

Known usable modules:

```text
star/2.7.11b
samtools/1.19.2
bedtools/2.31.1
picard/3.1.1
python39
java/17.0.10
```

RSeQC is available through the project virtual environment:

```text
.venv/bin/infer_experiment.py
```

Unresolved:

```text
GATK
R
bcftools
```

`bcftools` and `R` have not yet been validated in the rebuilt pipeline.

### Where should full data live?

Answered operationally.

Raw Novogene data live outside the repo and are linked into the repo:

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

The working repo and generated outputs live under:

```text
/mnt/stor-pool-01/users/2609214/norad
```

Do not copy full raw data into Git.

### What partition/account should jobs use?

Partially answered.

Known partition behavior:

```text
short: approximately 3 hour max walltime
long: approximately 3 day max walltime
```

Current implemented jobs use `short` where appropriate.

Known working examples:

* STAR alignment completed on `short`
* samtools sort/index completed on `short`
* BAM QC completed on `short`
* RSeQC infer_experiment completed on `short`

No special account setting has been required so far.

### Cluster quirks

Known:

* `logs/` must exist before `sbatch` when jobs write to `logs/%x-%j.out`.
* Use/export `TMPDIR=/tmp`.
* Cluster may warn:

```text
slurmstepd: error: TMPDIR [/local/tmp] is not writeable
slurmstepd: error: Setting TMPDIR to /tmp
```

This has not been fatal when the job itself logs `TMPDIR: /tmp`.

* `module list` writes to stderr, so scripts should use:

```bash
module list 2>&1 || true
```

## Reference files

### Genome build

Partially answered.

The Novogene reference is GRCh38-like.

Exact annotation release/version has not yet been documented.

### Annotation version

Still open.

The GTF came from the Novogene `04.Ref` delivery, but the exact annotation version has not yet been recorded.

### STAR index path

Answered.

```text
refs/novogene_star_index/
```

Built successfully with:

```text
sjdbOverhang=149
```

because reads are 150 bp.

### FASTA path

Answered.

Prepared reference FASTA path:

```text
refs/novogene_ref/genome.fa
```

Original compressed Novogene FASTA:

```text
genome.fa.gz
```

### GTF/GFF path

Answered.

Prepared GTF path:

```text
refs/novogene_ref/genome.gtf
```

Original compressed Novogene GTF:

```text
genome.gtf.gz
```

### BED12 annotation path

Answered.

RSeQC BED12 annotation:

```text
refs/novogene_ref/genome.bed
```

Generated by:

```text
scripts/gtf_to_bed12.py
```

Cluster validation wrote 206,601 transcript BED12 records.

### Chromosome naming

Answered.

Reference uses numeric-style chromosome names such as:

```text
1
2
3
```

not:

```text
chr1
chr2
chr3
```

The FASTA and GTF naming match.

## Sequencing data

### Paired-end or single-end?

Answered.

The data are paired-end.

RSeQC confirmed:

```text
This is PairEnd Data
```

### Strandedness?

Answered for `ABE_EV_2`.

RSeQC `infer_experiment.py` output:

```text
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

Still open:

* Confirm strandedness across all six samples once their canonical BAMs exist.

### Read length?

Answered.

Reads are 150 bp.

STAR index was built with:

```text
sjdbOverhang=149
```

### Sample manifest source?

Answered.

Manifest file:

```text
samples.tsv
```

Validated by:

```text
scripts/validate_manifest.py
```

### Naming convention?

Answered for current data.

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

Note that `ABE_EV4` lacks the underscore before `4`, unlike `ABE_EV_2` and `ABE_EV_3`.

## Pipeline

### Which steps are already done?

Implemented and cluster-proven:

```text
00a  Build STAR index
00b  Convert GTF to BED12
01   STAR alignment for ABE_EV_2
02   Sort/index canonical BAM for ABE_EV_2
02b  BAM QC for ABE_EV_2
03   RSeQC strandedness/orientation inference for ABE_EV_2
```

Scaffolded only / pending:

```text
04   MarkDuplicates
05   SplitNCigarReads
06   Split BAM by read orientation
07   bcftools mpileup by chromosome and orientation/strand
08   VCF preprocessing
09   CMH editing-site calling
```

### Which steps need to be reproduced from the reference workflow?

The uploaded/reference workflow indicates these downstream steps still need clean reimplementation:

```text
MarkDuplicates
SplitNCigarReads
Split BAM by read orientation
bcftools mpileup by chromosome and strand/orientation
VCF preprocessing
CMH editing-site calling
```

The reference workflow should not be run directly because it is hardcoded and not manifest-driven.

### Expected final deliverables?

Partially answered.

Expected broad deliverables:

```text
CMH/editing-site result tables
editing-site summary tables
plots from downstream R analysis
```

Still needs definition:

* exact output file names
* exact columns
* expected comparison structure
* whether final outputs are per chromosome, per strand/orientation, per condition, or combined
* plotting requirements

### What is the next implementation target?

Likely next target:

```text
Step 04: Picard MarkDuplicates
```

Expected input:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Likely outputs:

```text
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai
results/qc/markdup/ABE_EV_2.markdup.metrics.txt
```

Implementation assumption:

* Mark duplicates, do not remove duplicates, unless there is a specific documented reason to change that.

### What needs special care later?

Step `06` and downstream interpretation need special care.

The old workflow split read orientation using samtools flags similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Because Step `03` indicates reverse-stranded / first-strand behavior for `ABE_EV_2`, future steps must document the difference between:

```text
read orientation labels
biological transcript strand
editing interpretation
```

Do not silently assume old `FWD` / `REV` labels equal biological sense / antisense.
