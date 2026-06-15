# Questions And Answers

This file tracks project questions that were open during pipeline reconstruction, what has been answered, and what remains unresolved.

## Still Open / Unresolved

### Step 04 Cohort Validation

Step `04` is implemented and cluster-proven for `ABE_EV_2`; cohort-wide validation remains pending.

Promotion requires, for each remaining sample:

```text
confirmed scheduler completion
exit code 0:0
nonempty BAM/BAI/metrics
samtools quickcheck PASS
retained coordinate sorting
retained sample-specific read group
```

Remaining samples:

```text
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

### Step 04 Duplication Interpretation

`ABE_EV_2` has an elevated duplication fraction:

```text
PERCENT_DUPLICATION = 0.664166
```

Need to determine whether this is a cohort outlier after all six Step `04` metrics are available. Do not label it a pipeline failure without cohort context.

### Step 02b Final-BAM QC Refresh

Step `02b` is implemented and useful for BAM QC/provenance, but a clean refresh against the final hardened Step `02` BAMs remains pending.

Do not assume older Step `02b` reports all correspond to the final published BAMs.

### Java 17 Availability

Step `04` validates the actual selected Java runtime, but cluster-wide Java 17 availability remains unresolved.

Need one durable answer:

```text
HPC-supported Java 17 module that works consistently across nodes
administrator-provided cluster-wide Java 17 path
explicit verified executable supplied through JAVA_BIN_OVERRIDE
administrator remediation of inconsistent node images
```

Temporary node pinning to `node003` is not a durable architecture decision.

### GATK Availability

`module avail gatk` did not show a visible GATK module.

Need to determine whether GATK is:

```text
installed under a different module name
available as a jar
available through conda/mamba
available through a container
or should be installed into a project environment
```

This blocks final implementation of:

```text
Step 05: SplitNCigarReads
```

### R / Rscript And bcftools Availability

Unresolved:

```text
R
Rscript
bcftools
```

These are needed for Steps `07`, `08`, and `09`.

### Storage Quotas

Storage is being used successfully under project/storage paths, but exact quotas have not been documented.

Need to determine:

```text
home directory quota
/mnt/stor-pool-01/users/2609214 quota
scratch storage availability
whether scratch should be used for temporary files
```

### Exact Annotation Version

The GTF came from the Novogene `04.Ref` delivery, but the exact annotation version has not yet been recorded.

### Final Deliverables

The broad final deliverables are expected to be RNA-editing / variant-like site summaries and CMH result tables/plots, but the exact final table/plot formats are not yet specified.

Need to define expected Step `09` outputs before porting the old R scripts:

```text
exact output file names
exact columns
expected comparison structure
whether outputs are per chromosome, per orientation, per condition, or combined
plotting requirements
```

### Future Artifact And Reporting Design

Structured artifacts and reporting are planned, deferred, and non-runnable.

Open questions:

```text
exact versioned JSON schema for per-step sidecars
run ID semantics across dry-runs, execute runs, reruns, and partial reruns
provenance and git commit capture on local machines and CSU SLURM
whether artifacts describe failed and incomplete runs, or only successful runs
rerun, schema-version conflict, and pipeline-version conflict representation
exact HTML, PDF, and TSV report deliverables
Jinja2 versus Quarto/R Markdown responsibilities
final CMH/editing-site results, plots, and interpretation notes
```

### Read-Group Library Metadata

Step `02` currently uses the provisional read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

Need to determine whether true Novogene library, lane, or platform-unit metadata can be recovered from delivery records and should replace provisional `LB=<sample_id>` later.

## Answered / Resolved

### What Is The Correct Login Node?

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

### Is VPN Required?

Answered operationally.

VPN was needed/used to access the cluster. The user found the correct VPN instructions and successfully connected.

### What Are The Known Module Names?

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

Known caveat: module names and `JAVA_HOME` are not sufficient proof of effective Java runtime on every compute node.

### Where Should Full Data Live?

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

### Sample Manifest Source

Answered.

Manifest file:

```text
samples.tsv
```

Validated by:

```text
scripts/validate_manifest.py
```

### What Partition / Account Should Jobs Use?

Partially answered.

Known partition behavior:

```text
short: approximately 3 hour max walltime
long: approximately 3 day max walltime
```

No special account setting has been required so far.

### Reference Files

Answered:

```text
STAR index: refs/novogene_star_index/
FASTA: refs/novogene_ref/genome.fa
GTF: refs/novogene_ref/genome.gtf
BED12: refs/novogene_ref/genome.bed
```

The BED12 annotation was generated by:

```text
scripts/gtf_to_bed12.py
```

Cluster validation wrote 206,601 transcript BED12 records.

### Chromosome Naming

Answered.

The reference uses numeric-style chromosome names such as:

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

### Paired-End Or Single-End?

Answered.

The data are paired-end. RSeQC confirmed paired-end behavior across all six samples.

### Read Length

Answered.

Reads are 150 bp.

STAR index was built with:

```text
sjdbOverhang=149
```

### Strandedness?

Answered.

All six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.

Confirmed Step `03` results:

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| ------ | ------------------: | ----------------: | ----------------: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

### Which Steps Are Already Done?

Cluster-proven:

```text
00a  Build STAR index
00b  Convert GTF to BED12
01   STAR alignment across all six samples
02   Hardened canonical sort/read-group/index BAM across all six samples
03   RSeQC strandedness/orientation inference across all six samples
```

Implemented and useful, with refresh pending:

```text
02b  BAM QC against final hardened BAMs
```

Implemented and single-sample cluster-proven:

```text
04   Picard MarkDuplicates for ABE_EV_2
```

Scaffolded / not implemented / not cluster-proven:

```text
05   SplitNCigarReads
06   Split BAM by read orientation
07   bcftools mpileup by chromosome and orientation/strand
08   VCF preprocessing
09   CMH editing-site calling
```

### Which Steps Need Clean Reimplementation From The Reference Workflow?

The uploaded/reference workflow indicates these downstream steps still need clean reimplementation:

```text
SplitNCigarReads
Split BAM by read orientation
bcftools mpileup by chromosome and strand/orientation
VCF preprocessing
CMH editing-site calling
```

The reference workflow should not be run directly because it is hardcoded and not manifest-driven.

### What Needs Special Care Later?

Step `06` and downstream interpretation need special care.

The old workflow split read orientation using samtools flags similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Because the cohort is reverse-stranded / first-strand-style, future steps must document the difference between:

```text
read orientation labels
biological transcript strand
editing interpretation
```

Do not silently assume old `FWD` / `REV` labels equal biological sense / antisense.
