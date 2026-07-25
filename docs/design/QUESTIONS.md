# Questions And Answers

This file tracks project questions that were open during pipeline reconstruction, what has been answered, and what remains unresolved.

## Still Open / Unresolved

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

### R / Rscript Availability

Unresolved:

```text
R
Rscript
```

Step `08` is implemented locally at commit `90335d8`, and its wrapper behavior
is covered by shell tests with a fake R executable. `Rscript` is not available
on the current local workstation, so the committed real-R fixture suite has not
run and semantic runtime validation remains pending. Step `09` also requires R.

Step `08` declares these R package dependencies:

```text
VariantAnnotation
GenomicRanges
IRanges
S4Vectors
SummarizedExperiment
GenomeInfoDb
BiocGenerics
rtracklayer
```

The supported local/cluster `Rscript` path, compatible package versions, and
package availability in that environment remain unresolved. The workflow does
not install packages automatically.

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

### Exact Step 07 Primary-Contig Membership

The tracked Step `07` primary-contig partition manifest declares:

```text
1 through 22
X
Y
MT
```

The exact Novogene FASTA-index spelling and presence of `MT` has not been
inspected on this workstation. Step `07` validates every selector against the
runtime FASTA index and will fail rather than silently omit a missing contig.
Confirm the full tracked manifest against
`refs/novogene_ref/genome.fa.fai` during the first cluster dry-run.

### Step 09 Final Deliverable Schemas

The Step `08` paths and schemas are fixed by its local implementation and are
recorded under the answered Step `08` contract below. The approved Step `09`
paths remain planned:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

Still to finalize while implementing Step `09`:

```text
exact column order and status vocabulary for every Step 09 TSV
the complete mutation-spectrum schema
plot labels, dimensions, and deterministic rendering details
which summary fields carry runtime and exclusion counts
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
whether Step 06 orientation splitting remains part of the core preprocessing boundary or becomes an optional prerequisite requested by orientation-aware analysis modules
whether the first analysis module should be named rna_editing_cmh or preserve legacy workflow terminology
whether assay selection should live only in an analysis YAML config or whether the sample manifest can optionally point to a default analysis config
what metadata should be required before an analysis module is allowed to make biological comparisons
what evidence is required to replace the approved provisional
  orientation_policy=legacy_provisional_v1 mapping with a biologically
  validated policy
what artifact index format the reporting layer should consume
whether future public-dataset ingestion should be handled as a separate import layer that produces the same manifest/config inputs as lab-generated ADAM FASTQs
```

### Deferred Engineering Roadmap Decisions

The deferred engineering roadmap is tracked canonically in `TODO.md`. These questions do not block Step `00c`, Step `05`, or the remaining compute pipeline.

Open questions:

```text
when to activate manifest-driven submission and validation helpers
whether future sample selection helpers should be step-specific or generic
when SLURM arrays become useful enough to replace manual cohort loops
which reference files need checksums and where provenance should be recorded
which generated outputs are long-term retained versus disposable
whether validation reports should be per-step scripts, a generic dispatcher, or both
whether cluster tool paths need a config file, and which paths belong there
how stale-lock inspection and cleanup should prove safety before changing anything
which failure categories belong in a troubleshooting taxonomy
which Makefile conveniences are worthwhile after underlying commands exist
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

GATK and bcftools have confirmed direct paths:

```text
GATK 4.6.1.0: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
bcftools 1.21: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

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
FASTA index: refs/novogene_ref/genome.fa.fai
GTF: refs/novogene_ref/genome.gtf
BED12: refs/novogene_ref/genome.bed
sequence dictionary: refs/novogene_ref/genome.dict
```

The BED12 annotation was generated by:

```text
scripts/gtf_to_bed12.py
```

Cluster validation wrote 206,601 transcript BED12 records.

The GATK reference sidecars were generated successfully by an ad hoc cluster prep task with exit code `0:0`. FAI, DICT, and BAM header contig counts all matched at 194, and the reference/BAM SQ check passed.

Step `00c` is now cluster-proven as the formal sidecar preparation/validation step.

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
00c  GATK reference sidecars / reference FASTA index and sequence dictionary
01   STAR alignment across all six samples
02   Hardened canonical sort/read-group/index BAM across all six samples
02b  BAM QC refreshed across all six final hardened Step 02 BAMs
03   RSeQC strandedness/orientation inference across all six samples
04   Picard MarkDuplicates across all six samples
05   SplitNCigarReads across all six samples
06   Read-orientation BAM split across all six samples
```

Implemented locally and locally tested:

```text
07   Cohort bcftools mpileup by manifest partition and neutral orientation
08   VCF preprocessing of the declared Step 07 receipt set
```

Step `07` passed its mocked-bcftools focused tests and the complete local
repository validation gate. It has not run against real bcftools on this
workstation, has not completed a cluster dry-run or execute job, and has no
inspected cluster output. It is not cluster-proven.

Step `08` is implemented locally at commit `90335d8`. Its fake-R wrapper and
shell tests pass, but this workstation has no `Rscript`, so the real-R fixture
suite has not executed. Step `08` has no cluster dry-run, execute, log, or
output evidence and is not cluster-proven.

Pending / not implemented / not cluster-proven:

```text
09   CMH editing-site calling
```

### Which Steps Need Clean Reimplementation From The Reference Workflow?

Steps `07` and `08` have now been cleanly reimplemented as parameterized,
manifest-driven stages. Step `07` real-bcftools and cluster validation remain
pending. Step `08` real-R and cluster validation remain pending.

The uploaded/reference workflow indicates this downstream step still needs
clean implementation:

```text
CMH editing-site calling
```

Steps `05` SplitNCigarReads and `06` read-orientation BAM splitting are already implemented and cluster-proven across all six samples. The reference workflow should not be run directly because it is hardcoded and not manifest-driven.

### What Needs Special Care Later?

Read-orientation and downstream interpretation need special care.

The old workflow split read orientation using samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

Because the cohort is reverse-stranded / first-strand-style, downstream steps
must document the difference between:

```text
read-orientation labels
mechanical flag groups
editing interpretation
```

`samtools view -f FLAG` means a read has all bits in `FLAG`, not exact flag equality. Do not silently assume `FWD_like` / `REV_like` labels equal biological sense / antisense.

Step `08` now records `orientation_policy=legacy_provisional_v1` and retains
both mechanical orientation and compatible annotation strand. That policy is a
provisional legacy mapping, not biological validation. The evidence required
to replace it remains an open question, and Step `09` must preserve that
qualification.

### What Is The Step 07 Cohort mpileup Contract?

Answered for local implementation.

One invocation selects one row from the analysis partition manifest and runs
all sample-manifest BAMs together, in manifest order, for both neutral
`FWD_like` and `REV_like` orientations. `region` maps to bcftools `-r`, while
`regions_file` maps to `-R`. The approved primary manifest defines the
correction universe, and pilots use a separate one-row manifest.

The implementation preserves maximum depth `10000000`, skips indels, requests
FORMAT `DP,AD,ADF,ADR,SP` and INFO `AD,ADF,ADR`, applies
`INFO/AD[1-]>2 & MAX(FORMAT/DP)>20`, writes plain VCF, and has no
`bcftools call` stage.

Each partition publishes the two VCFs plus
`<cohort>.<partition>.step07_outputs.tsv` under
`results/mpileup/<cohort>/<partition>/`. The receipt records the selector,
orientation, output path, manifest hashes, manifest sample count, and record
count, and is published last as the downstream commit marker.

This contract is implemented locally and locally tested with mocked bcftools.
Real-bcftools runtime and cluster validation remain pending; Step `07` is not
cluster-proven.

### What Is The Step 08 VCF Preprocessing Contract?

Answered for local implementation.

Step `08` consumes exactly the partition-manifest Cartesian product with
`FWD_like` and `REV_like`; it never discovers inputs by glob. Before processing,
it validates each Step `07` receipt, manifest hashes, exact VCF paths,
manifest-ordered sample columns, sample counts, and declared record counts.
Overlapping partitions and globally duplicate candidate IDs are errors.

The R implementation uses `VariantAnnotation` for semantic VCF parsing and ALT
expansion, and `rtracklayer` plus `GenomicRanges` for direct parsing and
strand-aware use of the Novogene GTF. Every multiallelic record is expanded by
ALT index, and the matching FORMAT/AD and INFO/AD alternate value is retained.
Symbolic and non-SNV alternate alleles are counted and excluded. Missing or
incorrect required FORMAT/INFO definitions, malformed or negative counts,
partial DP/AD missingness, and AD greater than DP fail rather than being
truncated or repaired.

The provisional mapping is:

```text
FWD_like -> legacy neg -> compatible + transcripts -> complement DNA REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain DNA REF/ALT
orientation_policy=legacy_provisional_v1
```

This mapping is not biologically validated. The deterministic sites-table
metadata columns are:

```text
partition_id
candidate_id
orientation
chromosome
position
alt_index
genomic_ref
genomic_alt
rna_ref
rna_alt
annotation_strand
gene_ids
transcript_ids
is_cds
is_five_prime_utr
is_three_prime_utr
is_exon
is_intron
qual
filter
info_alt_depth
orientation_policy
```

They are followed by manifest-ordered `DP__<sample>`, `AD__<sample>`, and
`AF__<sample>` column groups. Supported intergenic SNVs remain in the table
with missing gene/transcript IDs and false annotation flags.

The fixed outputs are:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The input receipt has one row per partition and orientation in declared order,
records Step `07` receipt/VCF hashes and observed/supported/skipped/published
counts, and must reconcile with the sites table and summary. Execute mode uses
an owned cohort lock, run-token temporary paths, validation before publication,
rollback of a prior complete set, and publishes `step08_inputs.tsv` last as the
transaction commit marker.

This contract is implemented locally at commit `90335d8` and locally tested
through the fake-R shell suite. Real-R fixture execution is blocked on this
workstation because `Rscript` is unavailable. No cluster evidence has been
inspected, and Step `08` is not cluster-proven.

### Step 02b Final-BAM QC Refresh

Answered.

Step `02b` is implemented and refreshed across all six final hardened Step `02` BAMs.

The first cohort attempt failed immediately because `samtools` was not found on `PATH`, despite module output listing `samtools/1.19.2`. The successful rerun prepended:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This was a cluster environment/PATH inconsistency, not a BAM/QC failure. The current Step `02b` script creates the requested output directory before dry-run exit, so do not describe that dry-run as side-effect-free.

### Step 04 Cohort Validation And Duplication Interpretation

Answered.

Step `04` is cluster-proven across all six samples.

Confirmed MarkDuplicates metrics:

| Sample | Read pairs examined | Duplicate read pairs | Optical duplicate pairs | Percent duplication | Estimated library size |
| ------ | ------------------: | -------------------: | ----------------------: | ------------------: | ---------------------: |
| `ABE_EV_2` | 17,663,180 | 11,731,288 | 120,669 | 0.664166 | 6,327,403 |
| `ABE_EV_3` | 18,867,589 | 11,371,887 | 130,069 | 0.602721 | 8,397,468 |
| `ABE_EV4` | 23,240,508 | 19,860,628 | 177,257 | 0.854569 | 3,383,587 |
| `ABE_PUM1_2` | 19,087,654 | 13,522,128 | 128,791 | 0.708423 | 5,783,576 |
| `ABE_PUM1_3` | 21,657,503 | 14,809,440 | 150,924 | 0.683802 | 7,214,041 |
| `ABE_PUM1_4` | 19,424,683 | 16,348,986 | 132,657 | 0.841660 | 3,081,584 |

Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size.

Observed Step `04` MaxRSS ranged from about 22.7-24.3 GB. This is observed evidence, not a guaranteed resource requirement.

### Step 05 Cohort Validation

Answered operationally.

Step `05` is implemented and cluster-proven across all six samples:

```text
jobs/step_05_split_n_cigar_reads.slurm
scripts/step_05_split_n_cigar_reads.sh
tests/shell/test_step_05_split_n_cigar_reads.sh
```

The output layout is:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

Step `05` treats the Step `00c` outputs `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` as prerequisites, fails clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

The first `ABE_EV_2` cluster execute attempt reached GATK `SplitNCigarReads` traversal pass 1 completion and traversal pass 2 startup before failing because HTSJDK `SortingCollection` spill files used node-local `/tmp` and hit `No space left on device`. Step `05` was hardened to route GATK temp files to project storage and to clean owned temp files, sidecars, temp directories, and locks on failure.

Six-sample cluster revalidation completed successfully. Output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

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

### GATK Availability

Answered.

GATK availability is confirmed on compute node `node002`:

```text
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
GATK path: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
tool probe exit code: 0:0
```

This resolves the GATK availability question. Step `05` uses this path by default in its SLURM wrapper and is cluster-proven across all six samples.

### bcftools Availability

Answered.

bcftools availability is confirmed on compute node `node002`:

```text
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

This resolves the bcftools availability question. Step `07` now uses this path
as the SLURM-wrapper default and is implemented locally and locally tested with
mocked bcftools. It has not been validated with the real executable, has not
completed a cluster dry-run or execute job, has no inspected cluster output,
and is not cluster-proven.
