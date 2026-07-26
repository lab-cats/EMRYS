# Decisions

This file records project decisions that should not be casually re-litigated unless new evidence appears.

## TSV Is The Canonical Manifest Format

Decision: the manifest is tab-separated.

Reason: TSV is simple, robust with file paths, easy to parse in Python/R/shell, and avoids CSV quoting issues.

Current manifest:

```text
samples.tsv
```

The manifest is the source of truth for sample IDs, conditions, FASTQ paths,
and optional replicate metadata. Earlier steps remain compatible with
manifests that omit `replicate`; Step `09` requires it and uses it as the only
pairing source.

## The Workflow Is Local-First And Cluster-Scaled

Decision: develop and test locally, then execute full data jobs on CSU SLURM.

Workflow:

```text
stage branch
-> local implementation and validation
-> implementation commit
-> repository-wide docpatch and documentation-only commit
-> clean status/history and push
-> next descendant local stage
-> upstream-first cluster dry-run and execute promotion
-> inspected evidence and validation docpatch
```

Reason: this keeps large cluster jobs reproducible, reviewable, and gated.

## Major Stages Use Descendant Branches And Documentation Gates

Decision: each major implementation or validation stage must use a dedicated
branch created from the latest clean, docpatched parent branch.

The completion gate is:

```text
implement only the stage and its required contracts
-> run focused tests and the complete repository validation gate
-> commit implementation and tests
-> reread the nine required project documents
-> perform a repository-wide documentation consistency pass
-> commit documentation separately as "step NN docpatch"
-> rerun diff/status/history checks and require a clean worktree
-> push the completed stage branch
-> create the next descendant branch
```

If implementation changes after a docpatch, the gate reopens: retest, commit
the fix, and add another separate documentation-only commit before branching.
Any inserted work package follows the same pattern on a sequentially named
descendant branch.

Documentation must distinguish:

```text
implemented locally
locally tested
runtime validation blocked
cluster dry-run validated
cluster-proven
```

Only inspected cluster evidence can support a `cluster-proven` claim.

Reason: linear stage ancestry plus a documentation-only gate makes the state,
interfaces, evidence, and remaining validation requirements reviewable at every
handoff boundary.

## SLURM Wrappers Are Dry-Run By Default

Decision: pipeline job wrappers default to dry-run mode.

Execute mode must be explicit:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Reason: this prevents accidental large jobs, makes command construction testable, and supports a one-step-at-a-time workflow.

## Script-Level Execution Uses `--execute`

Decision: scripts should print resolved context and commands by default, and only run tool commands when passed `--execute`.

Reason: this keeps behavior consistent between local tests and SLURM wrappers.

## Future Steps Remain Non-Runnable Until Implemented

Decision: scaffolded future steps must be clearly pending/non-runnable.

Pending steps should not look submit-ready. Placeholder jobs should not load modules, call tools, or define realistic resource use until implemented.

Reason: this prevents accidentally submitting placeholder jobs and mistaking scaffolding for working pipeline logic.

Current application: Steps `07`, `08`, and `09` are implemented locally and
locally tested at their available local boundaries, but none is
cluster-proven. After `step-09b1-real-r-fixes`, the Step `08` and Step `09`
real-R fixtures both pass without `SKIP` under the guarded local runtime. No
currently scoped Step `07`-`09` entry point is a non-runnable scaffold.

## Active Tests Live Under `tests/shell/`; Future Test Plans Live Under `tests/pending/`

Decision: implemented steps get active tests under `tests/shell/`.

Future steps may have comment-only test plans under `tests/pending/`, but pending tests must not be wired into `Makefile` or active test runners.

Reason: this prevents known-failing future tests from breaking current validation while still preserving implementation plans.

## Uploaded Legacy Workflow Is A Protocol Reference

Decision: uploaded old scripts are reference/protocol fossils, not code to run directly.

Reason: the old workflow is hardcoded and not manifest-driven. This repo is rebuilding the workflow into a cleaner SLURM/script/testable structure.

The reference workflow informs Steps `04` through `09`:

```text
MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

## Use The Novogene-Provided Reference

Decision: use the Novogene-provided reference FASTA/GTF as the reference basis for this pipeline unless there is a strong reason to change.

Prepared reference paths:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

Reason: the data delivery and original workflow were built around this reference. Using it avoids coordinate/name mismatches.

Known reference behavior:

```text
chromosome names are numeric-style, e.g. 1, 2, 3
not chr1, chr2, chr3
```

## STAR Index Uses `sjdbOverhang=149`

Decision: build the STAR index with:

```text
sjdbOverhang=149
```

Reason: reads are 150 bp, and STAR convention is read length minus 1.

## BED12 Is Generated From The GTF For RSeQC

Decision: use a generated BED12 annotation for RSeQC strandedness checks.

Output:

```text
refs/novogene_ref/genome.bed
```

Reason: RSeQC `infer_experiment.py` expects BED-style gene/transcript models, not raw GTF.

## GATK Reference Sidecars Are Step 00c

Decision: reference FASTA sidecars are a dedicated Step `00c`, not hidden per-sample Step `05` work.

Expected outputs:

```text
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Reason: `SplitNCigarReads` needs the FASTA index and sequence dictionary, and shared reference files should be prepared and validated once instead of silently created inside per-sample jobs.

Current evidence: an ad hoc cluster prep task generated both sidecars successfully with exit code `0:0`; FAI, DICT, and BAM header contig counts all matched at 194, and the reference/BAM SQ check passed. Step `00c` is implemented with a dry-run-first script, SLURM wrapper, reference-level lock, temp-file publication, and shell tests; the formal Step `00c` job is cluster-proven.

## STAR Outputs Feed Canonical Step 02 BAMs

Decision: even though STAR can output coordinate-sorted BAM directly, Step `02` creates the canonical downstream BAM path.

STAR output example:

```text
results/star/<sample_id>/<sample_id>.Aligned.sortedByCoord.out.bam
```

Canonical Step `02` output:

```text
results/bam/<sample_id>/<sample_id>.sorted.bam
results/bam/<sample_id>/<sample_id>.sorted.bam.bai
```

Reason: downstream steps should depend on a stable canonical path, not STAR-specific output naming.

## Step 02 Enforces Canonical Read-Group Metadata

Decision: Step `02` is the boundary that creates canonical downstream BAMs. Those BAMs must be coordinate sorted, indexed, and carry exactly one read group for the current one-sample-per-BAM contract.

Read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

`LB=<sample_id>` is provisional until true Novogene library, lane, or platform-unit metadata is recovered.

Reason: Picard and downstream tools require records to resolve to a valid `@RG`. Missing read groups caused Picard MarkDuplicates to fail, so Step `04` must not work around missing canonical metadata.

Implementation requirement: Step `02` validates the replacement BAM and index before publishing, uses a per-sample lock, and restores the previous canonical BAM/BAI pair if publication fails after backups begin.

## Step 02 Publication Is Validation-First And Rollback-Protected

Decision: stable canonical BAM and BAI paths are replaced only after temporary replacement files pass validation.

Reason: downstream jobs should never consume a half-published canonical BAM/BAI pair.

## All Six Libraries Are Reverse-Stranded / First-Strand-Style

Decision: all six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.

Confirmed dominant RSeQC orientation group:

```text
1+-,1-+,2++,2--
```

The dominant reverse-stranded orientation ranges from 0.8562 to 0.8740 across the cohort.

Tool-specific examples that commonly correspond to this orientation include:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

Do not present tool-specific options as universally interchangeable without naming the tool.

## Step 03 And Step 04 Are Parallel Consumers Of Canonical Step 02 BAMs

Decision: Step `03` and Step `04` both consume the canonical Step `02` BAM. Step `03` does not require the duplicate-marked BAM from Step `04`.

Reason: strandedness inference depends on the canonical alignment and annotation, not duplicate-marked output.

## Read Orientation Labels Must Be Separated From Biological Strand Interpretation

Decision: future orientation-splitting steps must document the distinction between read-orientation labels, mechanical flag groups, and biological interpretation.

Reason: the old workflow used FWD/REV-like read orientation splits, but the rebuilt pipeline should preserve them as `FWD_like` / `REV_like` mechanical flag groups because the cohort is reverse-stranded / first-strand-style.

Old workflow used samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

`samtools view -f FLAG` means a read has all bits in `FLAG`, not exact flag equality. Do not silently assume `FWD_like` / `REV_like` labels equal biological sense / antisense, transcript strand, or biological strand.

## Picard Is Invoked Through `$PICARD`

Decision: invoke Picard through the jar path set by the CSU module:

```bash
module load picard/3.1.1
java -jar "$PICARD" <PicardCommand>
```

Reason: CSU exposes Picard as a jar path through the `picard/3.1.1` module rather than as a standalone `picard` executable.

## Step 04 Validates The Actual Java Runtime

Decision: Step `04` must select and validate Java before Picard starts.

Resolution order:

```text
1. JAVA_BIN_OVERRIDE, when explicitly provided
2. $JAVA_HOME/bin/java, only if the path exists and is executable
3. command -v java
```

The wrapper logs `JAVA_HOME`, the selected executable, and the actual `java -version`, then fails before Picard starts if the runtime is below Java 17.

Reason: the cluster has shown inconsistent Java availability across compute nodes, and `JAVA_HOME` or module name alone is not proof of the effective runtime.

## Step 04 Marks Duplicates, Not Removes Them

Decision: Step `04` uses Picard MarkDuplicates with:

```text
REMOVE_DUPLICATES=false
```

Reason: the legacy workflow appears to mark duplicates, and marking preserves reads for downstream inspection while still encoding duplicate status.

Expected Step `04` outputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
results/qc/markdup/<sample_id>.markdup.metrics.txt
```

## Node Pinning Is Temporary Mitigation

Decision: pinning Step `04` to `node003` is a temporary operational workaround, not a durable architecture choice.

Reason: `node002` has provided Java 17 and completed the GATK/bcftools probe, `node003` has provided working Java 17 for Step `04`, while `node007` exposed Java 11 and a missing advertised Java 17 `JAVA_HOME`. The durable fix is an HPC-supported cluster-wide Java 17 executable/path or administrator remediation.

Do not copy a JDK from another compute node or from the head node.

## RSeQC Is Run Through The Project Virtual Environment

Decision: Step `03` prefers the project-local RSeQC executable:

```text
.venv/bin/infer_experiment.py
```

Reason: RSeQC was available in the project `.venv`, and relying on it avoids needing a global RSeQC module.

## SLURM Jobs Export `TMPDIR=/tmp`

Decision: SLURM jobs should export/use:

```text
TMPDIR=/tmp
```

Reason: CSU default `/local/tmp` was observed to be non-writable on compute nodes. Jobs may emit a warning and fall back to `/tmp`; this has not been fatal when the job logs show `TMPDIR: /tmp`.

## Step 05 GATK Temp Files Use Project Storage

Decision: Step `05` must route GATK `SplitNCigarReads` Java/HTSJDK temp files to a per-run project-storage temp directory, not node-local `/tmp`.

Required mechanism:

```text
--java-options -Djava.io.tmpdir=<project temp dir>
--tmp-dir <project temp dir>
TMPDIR=<project temp dir> for the GATK process
```

Reason: GATK/HTSJDK `SortingCollection` spill files can exceed safe node-local `/tmp` capacity during `SplitNCigarReads`. Project-storage temp space keeps large temporary spill files with the pipeline run instead of relying on node-local scratch capacity.

## `logs/` Must Exist Before `sbatch`

Decision: create `logs/` before submitting jobs.

```bash
mkdir -p logs
```

Reason: jobs use `#SBATCH --output=logs/%x-%j.out` and `#SBATCH --error=logs/%x-%j.err`; SLURM can fail if the directory does not exist.

## `module list` Output Should Be Captured With stderr

Decision: scripts should use:

```bash
module list 2>&1 || true
```

Reason: Environment Modules writes `module list` output to stderr, which can otherwise make logs confusing or interact badly with strict shell settings.

## Step 05 Uses The Confirmed GATK Path And Split-N-Cigar Layout

Decision: Step `05` uses the validated CSU GATK path in its SLURM wrapper and writes split-N-cigar outputs under `results/split_ncigar/<sample_id>/`.

Confirmed evidence:

```text
node: node002
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
GATK path: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
tool probe exit code: 0:0
```

Expected outputs:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

Step `05` consumes validated `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` sidecars as prerequisites, fails clearly if they are missing, and must not create shared reference sidecars inside per-sample jobs. It is cluster-proven across all six samples after final BAM/BAI output inspection.

## Step 07 Is A Cohort-Wide, Manifest-Partitioned mpileup

Decision: Step `07` runs every sample in manifest order together for one
declared partition and publishes both neutral mechanical orientations:

```text
FWD_like
REV_like
```

The analysis partition manifest is the declared correction universe and has the
schema:

```text
partition_id    selector_type    selector_value
```

`region` maps to bcftools `-r`; `regions_file` maps to `-R`. Pilots use a
separate one-row manifest rather than changing the approved full-analysis
manifest.

Step `07` preserves these legacy mpileup/filter defaults:

```text
maximum depth: 10000000
skip indels
FORMAT annotations: DP, AD, ADF, ADR, SP
INFO annotations: AD, ADF, ADR
filter: INFO/AD[1-]>2 & MAX(FORMAT/DP)>20
plain VCF output
no bcftools call stage
```

Reason: cohort-wide multi-BAM mpileup preserves the manifest-defined sample
universe and order for downstream paired analysis, while explicit partition
manifests prevent accidental glob-based changes to the multiple-testing
universe. Neutral orientation names avoid claiming biological strand meaning.

## Step 07 Publishes VCFs Atomically With A Receipt Commit Marker

Decision: one Step `07` transaction owns the cohort/partition output scope,
validates both orientation VCFs, and publishes the receipt last.

Expected paths:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

The receipt records the cohort, partition selector, orientation, VCF path,
manifest hashes, manifest sample count, and VCF record count. Its presence is
the transaction commit marker. Header-only VCFs are valid when their structure
and exact manifest-ordered sample columns pass validation.

Reason: publishing the receipt last prevents downstream steps from accepting a
partial pair of VCFs as a complete partition. Owned locks, run-token scratch
paths, validation-before-publication, rollback, and cleanup preserve the
reliability contract established by Steps `05` and `06`.

For the approved primary manifest, the durable completion unit is 25 committed
partition transactions: 25 receipts and 50 VCFs. The separate pilot
transaction is validation evidence only and never counts toward, mutates, or
enters that primary correction universe.

## The Confirmed bcftools Path Is The Step 07 Cluster Default

Decision: use the validated CSU bcftools path as the Step `07` SLURM-wrapper
default:

Confirmed evidence:

```text
node: node002
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

Current status: Step `07` is implemented locally and locally tested with mocked
bcftools. It has not run against real bcftools on this workstation, has not
completed a cluster dry-run or execute job, has no inspected cluster output,
and is not cluster-proven. The tracked primary-contig manifest includes `MT`;
its exact presence/spelling in the Novogene FASTA index must be confirmed
during cluster dry-run validation.

## Step 08 Consumes Only The Declared Step 07 Transaction Set

Decision: Step `08` consumes the exact partition-manifest Cartesian product
with the two neutral orientations in fixed order:

```text
FWD_like
REV_like
```

It must not glob whatever VCFs happen to exist. For every declared partition it
requires the Step `07` receipt commit marker and validates the receipt schema,
cohort, selector, orientation order, exact VCF paths, sample-manifest and
partition-manifest hashes, sample count, exact manifest-ordered VCF sample
columns, and declared VCF record counts. The sample manifest, partition
manifest, annotation GTF, receipts, and VCFs must remain byte-stable throughout
processing.

Decision: semantic preprocessing uses `VariantAnnotation` for VCF parsing and
ALT expansion and uses `rtracklayer` plus `GenomicRanges` to import and query
the Novogene GTF directly. Every alternate allele is expanded by ALT index, and
the corresponding FORMAT/AD and INFO/AD alternate value is extracted.
Symbolic and non-SNV alternate alleles are counted and excluded rather than
truncated. Overlapping partition selectors, duplicate candidate IDs, missing
or incorrect required FORMAT/INFO definitions, malformed or negative counts,
partial DP/AD missingness, and AD greater than DP are hard failures.

Decision: validate raw count lexemes before semantic VCF parsing.
FORMAT/DP must contain exactly one non-negative integer or `.`;
FORMAT/AD and present INFO/AD values may be a single `.` when the whole vector
is missing. Otherwise they must contain exactly one token for REF plus one for
every ALT, and every token must be a non-negative integer or `.`. This lexical
preflight streams through the VCF before `VariantAnnotation` parses it.

The orientation mapping is explicitly provisional:

```text
FWD_like -> legacy neg -> compatible + transcripts -> complement DNA REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain DNA REF/ALT
orientation_policy=legacy_provisional_v1
```

Step `08` retains the genomic and RNA-normalized alleles, mechanical
orientation, and compatible annotation strand. This policy reproduces the
approved legacy behavior; it is not a biologically validated strand or editing
interpretation.

Reason: a declared, hash-checked input universe prevents stale or extra VCFs
from silently changing candidate membership, while semantic ALT/count parsing
avoids the legacy failure modes of positional truncation and implicit strand
interpretation. Raw lexical validation is also required because a semantic
parser may coerce malformed count tokens into parsed numeric values and erase
the distinction between valid missingness and invalid input. The additional pass
is bounded-memory but adds one full VCF read; benchmark its I/O cost on the
first supported Step `08` pilot and primary-universe cluster runs before
claiming acceptable production scaling.

## Step 08 Publishes Deterministic Wide Tables As One Transaction

Decision: Step `08` publishes:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The sites table begins with this fixed metadata order:

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

Those fields are followed by manifest-ordered `DP__<sample>`,
`AD__<sample>`, and `AF__<sample>` groups. Supported intergenic SNVs remain
published with missing gene/transcript IDs and false annotation flags.
Candidate order follows partition-manifest order, then `FWD_like`,
`REV_like`, then original VCF record and ALT order.

The input-receipt columns are:

```text
cohort_id
partition_id
selector_type
selector_value
orientation
step07_receipt_path
step07_receipt_sha256
vcf_path
vcf_sha256
sample_manifest_sha256
partition_manifest_sha256
annotation_gtf
annotation_gtf_sha256
sample_count
declared_vcf_record_count
observed_vcf_record_count
observed_alt_allele_count
supported_snv_count
skipped_symbolic_count
skipped_non_snv_count
published_candidate_count
orientation_policy
```

The summary columns are:

```text
cohort_id
partition_count
step07_receipt_count
input_vcf_count
sample_count
observed_vcf_record_count
observed_alt_allele_count
supported_snv_count
skipped_symbolic_count
skipped_non_snv_count
published_candidate_count
sample_manifest_sha256
partition_manifest_sha256
annotation_gtf
annotation_gtf_sha256
orientation_policy
```

Observed alternate alleles must equal supported SNVs plus counted symbolic and
non-SNV exclusions; supported and published candidate counts must equal the
combined sites row count. A header-only sites table is valid when all counts
reconcile.

Execute mode accepts only a complete prior three-file set or no prior set,
uses an owned cohort lock and run-token scratch/backup paths, validates all
temporary outputs, publishes sites then summary, and publishes
`step08_inputs.tsv` last as the transaction commit marker. A failed replacement
restores the prior complete set.

Reason: fixed schemas and ordering make Step `09` consumption deterministic,
and receipt-last rollback publication prevents a partial cohort table set from
being mistaken for a committed Step `08` result.

For the approved 25-partition universe, the durable Step `08` input-receipt
contract is exactly 50 rows in partition-manifest order, with `FWD_like` then
`REV_like` for each partition. A different row count or order is a different
or incomplete transaction, not a harmless presentation change.

Current evidence: this contract is implemented locally at commit `90335d8`.
The fake-R shell suite passes. Hardening commit `eae5eca` adds the raw lexical
preflight and reason-specific negative-fixture assertions; the complete
real-R suite passes without `SKIP` in the guarded local environment. The
earlier generic fixture failure was misattributed to partition overlap, which
already rejected correctly; malformed raw DP/AD/INFO AD coercion was the
actual defect. There is no cluster dry-run, execute, log, or output evidence,
and Step `08` is not cluster-proven.

## Step 09 Pairing Comes Only From Explicit Manifest Replicates

Decision: the generic sample manifest may include an optional `replicate`
column without breaking earlier manifests. Step `09` requires it and accepts
only one control and one treatment per replicate, identical replicate sets,
and at least two strata. Pairing must never be inferred from sample names.

The approved current reference mapping is:

```text
ABE_EV_2 / ABE_PUM1_2 -> replicate 2
ABE_EV_3 / ABE_PUM1_3 -> replicate 3
ABE_EV4  / ABE_PUM1_4 -> replicate 4
```

`configs/step_09_pairs.NORAD_EV_PUM1.tsv` documents those relationships but is
not a runtime input or overlay. The full sample manifest remains the source of
truth. Its hash must match the complete Step `08` input receipt, so replicate
metadata must be present before Step `07` produces the upstream receipt chain.

Reason: explicit pairing is reviewable and resistant to the inconsistent sample
name spelling already present in the cohort. Reusing one full manifest and one
hash across Steps `07`-`09` prevents a late metadata overlay from silently
changing the analysis contract.

## Step 09 Uses One Paired CMH And BH Family

Decision: for every successfully testable target candidate, Step `09` builds a
2-by-2 table of treatment/control by edited/unedited counts for every
manifest-defined replicate and runs:

```text
mantelhaen.test(..., alternative="two.sided", correct=TRUE, exact=FALSE)
```

The common odds ratio direction is treatment relative to control. BH is
applied once across all successfully tested target candidates from every
declared partition and both orientations. Missing counts, low coverage,
degenerate tables, and non-target mutations remain in the all-sites table with
explicit statuses. Mean depth, optional background, FDR, and effect thresholds
are call filters; mean depth does not shrink the BH family.

The defaults are:

```text
control: EV
treatment: PUM1
RNA change: A>G
minimum per-sample DP: 1
mean analysis DP: strictly >50
BH FDR: strictly <0.05
common OR: strictly >1.2 or <1/1.2
absolute treatment-control fraction difference: strictly >0.005
```

Decision: background filtering is disabled by default. If an explicit
condition different from control and treatment is selected, every background
sample must have adequate depth and an edited fraction strictly below `0.01`
by default. EV must not be repurposed as a missing no-dox cohort.

Reason: this preserves the approved paired legacy analysis while making the
comparison direction, multiple-testing universe, threshold boundaries, and
missing/degenerate behavior explicit and testable.

## Step 09 Publishes One Six-Output Transaction

Decision: Step `09` publishes:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

All-sites preserves every Step `08` candidate and order; significant-sites is
the deterministic `significant_up`/`significant_down` subset. Both tables use
42 fixed fields followed by manifest-ordered `DP__`, `AD__`, and `AF__`
groups. The summary uses 39 fixed provenance/count/threshold fields. The
mutation table always emits all 12 canonical substitutions, and both base-R
PDFs use a fixed 7-by-5-inch device with signature/EOF validation.

Execute mode accepts only all six existing outputs or none, uses an
analysis-scoped owned lock plus run-token temporary/backup paths, verifies
immutable inputs and exact output reconciliation, and publishes the summary
last as the commit marker. A failed replacement restores the previous complete
set. If rollback is incomplete, the owned lock remains for explicit operator
recovery.

Reason: the six files jointly describe one analysis result. A summary-last,
rollback-protected boundary keeps downstream readers from treating a partial
set as committed while retaining recoverable evidence when restoration itself
fails.

Current evidence: this contract is implemented locally at commit `e4371de`.
The shell/fake-R suite passes. Hardening commit `eae5eca` replaces the
locale-sensitive raw-to-text PDF assertion with raw-byte signature matching;
the complete real-R suite passes without `SKIP` in the guarded local
environment. The prior failure was a fixture defect, not evidence of a
corrupt PDF. There is no cluster dry-run, execute, log, or inspected output
evidence, and Step `09` is not cluster-proven. It retains
`orientation_policy=legacy_provisional_v1`, which is not biologically
validated.

Durable cluster-proof reconciliation requires one successful six-output
transaction whose all-sites row count equals Step `08`, whose significant
table contains the exact ordered rows whose `call_status` is `significant_up`
or `significant_down`, whose summary has one row, whose mutation spectrum has
12 rows, and whose PDFs have valid signatures/EOF
markers, together with matching upstream hashes/status totals, inspected
scheduler/log evidence, and no owned lock or scratch residue. This
computational proof does not convert `legacy_provisional_v1` or
`significant_up`/`significant_down` into biological validation.

## Local R Is Pinned, Guarded, And Never Bootstrapped By Compute Wrappers

Decision: local development uses the official signed and notarized
Apple-silicon CRAN R `4.6.1` package. Its published SHA-1
`fc9f4ada15589e8e037b9bf05563d21e97181635` must match before installation.
Do not use or repair the damaged Homebrew checkout for this runtime.

The repository pins `renv` `1.2.3` and Bioconductor `3.23`. Its lock records
the eight direct Step `08` namespaces and their transitive closure:
`VariantAnnotation`, `GenomicRanges`, `IRanges`, `S4Vectors`,
`SummarizedExperiment`, `GenomeInfoDb`, `BiocGenerics`, and `rtracklayer`.
Project-library activation occurs only when `NORAD_USE_RENV=1`; otherwise the
guarded `.Rprofile` is inert.

Explicit local interfaces are `make r-restore`, `make r-check`, and
`make local-real-r-test`, with `RSCRIPT_BIN` selecting the executable.
Restoration/installation is an operator action. Analysis scripts, SLURM
wrappers, and report renderers must fail clearly when dependencies are absent
and must never bootstrap or install them. Step `09` uses only base R
(`stats`, `graphics`, and `grDevices`).

Local acceptance evidence includes normal restore, an empty cache-disabled
binary restore, all required namespace loads, `BiocManager::valid()`,
`renv::status()`, headless PDF creation, and both real-R suites passing without
`SKIP` after `step-09b1-real-r-fixes`.

This decision does not select a CSU module or batch-visible `Rscript`.
Cluster runtime and package availability remain unresolved and must be proven
separately.

## Computational Proof And Scientific Interpretation Are Separate Gates

Decision: `cluster-proven` means a declared computation completed on the
cluster and its scheduler state, logs, inputs, outputs, hashes, and stage
contracts were inspected. It does not mean its biological orientation,
annotation interpretation, thresholds, candidate identity, or causal
interpretation is validated.

Decision: implement `step-09c-scientific-validation` locally before remote
promotion as dry-run-first tooling that validates and summarizes explicit
evidence. It must not rerun CMH, infer human decisions, or claim that synthetic
fixtures constitute production scientific review. Later production review
must still inspect orientation, annotation provenance and semantics,
predeclared threshold/replicate sensitivity, candidate adjudication, and the
background-cohort decision. A>G enrichment can support but cannot
independently prove the orientation mapping. PI review and report generation
do not constitute orthogonal experimental validation.

Reason: computational reproducibility and biological validity answer different
questions. Keeping the gates distinct prevents a technically correct run from
being overstated as a validated scientific conclusion.

Decision: Step `09c` may publish only these overall science states:

```text
evidence_incomplete
science_review_complete_exploratory
```

`evidence_incomplete` means required evidence or decisions are absent or
incomplete. `science_review_complete_exploratory` means evidence and decisions
are recorded while the result remains provisional; it permits only
exploratory reporting, not biological candidate claims.
`biological_interpretation_ready` is reserved and Step `09c` must reject it
until a separately approved scientific-policy branch defines and unlocks all
stricter exit criteria. Reports must render state and limitations explicitly;
they never infer validation from review completion.

Evidence categories use `missing`, `incomplete`, `complete`, or justified
`not_applicable`; orientation uses `provisional`, `validated`, or
`replacement_required`. Background, matched-DNA, orthogonal-evidence,
annotation, threshold, and adjudication decisions remain independent
dimensions.

## Local Engineering Uses The Approved Report-First Descendant Order

Decision: remote promotion remains paused while local implementation proceeds
through this exact descendant order:

```text
step-09b-local-r-runtime
-> step-09b1-real-r-fixes
-> step-09c-scientific-validation
-> artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
-> post09-runtime-preflight
-> post09-reference-provenance
-> post09-storage-inventory-retention
-> post09-validation-report-00a
-> post09-validation-report-00b
-> post09-validation-report-00c
-> post09-validation-report-01
-> post09-validation-report-02
-> post09-validation-report-02b
-> post09-validation-report-03
-> post09-validation-report-04
-> post09-validation-report-05
-> post09-validation-report-06
-> post09-validation-report-07
-> post09-validation-report-08
-> post09-validation-report-09
```

The completed local `step-09b1-real-r-fixes` package makes Step `09c` the next
descendant after its docpatch and clean/push gate. Structured run summaries
and HTML/PDF reports are immediate, before the three foundational engineering
packages.
Each foundation publishes an atomic read-only TSV, adds an artifact adapter,
and appears in report fixtures. Each step-specific validator publishes the
fixed `step_id`, `scope_id`, `check_id`, `status`, `observed`, `expected`,
`detail` schema, adds its adapter, and is proven through the consolidated
summary/report fixture.

No package adds a generic dispatcher, job array, automatic installation,
automatic cleanup, native compute-side artifact retrofit, report globbing, or
analysis rerun. Targeted reruns, analysis config, module wrapping, broad
refactors, and public-data ingestion remain deferred.

Reason: the report-first slice makes missing and incomplete evidence visible
early without blocking on remote production evidence, while the later
validators progressively strengthen the same explicit artifact model.

## Future Refactors Must Preserve Proven Interfaces

Decision: future helper-library, orchestration, validation-reporting, and admin-utility refactors must preserve existing step command-line interfaces, output paths, dry-run/execute semantics, and proven cluster contracts unless a later task explicitly decides otherwise.

Reason: the current pipeline is intentionally gated and handoff-oriented. Deferred engineering improvements should reduce duplication and improve operability without changing the behavior that downstream steps and cluster runbooks already depend on.

Candidate helper names, config filenames, validator names, Makefile targets, and admin utilities remain roadmap ideas until separately implemented and tested.

## Reporting Is Decoupled From Computation Through Structured Artifacts

Decision: compute steps and report rendering should remain decoupled.

The immediate artifact slice uses JSON Schema Draft 2020-12 for artifact
records, scientific-review records, run summaries, and report receipts. An
explicit expected-artifact inventory supplies every adapter and source path;
neither adapters nor renderers discover inputs by glob.

```text
artifact-schema-v1
-> read-only artifact-adapters-v1 over existing outputs
-> artifact-run-summary
```

A `run_id` identifies one immutable
manifest/reference/partition/primary-analysis contract. Retries with identical
inputs receive different `attempt_id` values; input or policy hash changes
require a new `run_id`. Records model attempts, implementation, local tests,
runtime validation, cluster validation, warnings/errors, provenance, metrics,
and scientific state independently. Missing, failed, incomplete, and
externally unavailable evidence must be represented, not omitted.

Canonical, stably ordered `<run_id>.run_summary.json` is the report layer's
single structured input. It is assembled by read-only adapters over existing
Step `00a`-`09` and Step `09c` receipts/summaries. Existing compute CLIs and
paths remain unchanged; native per-step JSON emission is not added.

Decision: reports use checksum-pinned Quarto `1.9.38` with bundled Pandoc and
Typst. The approved Quarto archive SHA-256 is
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6f18a`.
`make quarto-restore` is an explicit operator action into ignored local tool
storage; rendering never installs software. One static QMD consumes the
validated run summary, runs no analysis code, and produces a self-contained
HTML report followed by a consolidated HTML/PDF/TSV bundle. The PDF uses
bundled Typst. Renderers never rerun STAR, samtools, Picard, GATK, bcftools,
R preprocessing, or CMH and never use external network assets.

Reports must keep computational and scientific status separate and render a
persistent applicable state banner. `evidence_incomplete` forbids biological
interpretation; `science_review_complete_exploratory` remains explicitly
provisional. Candidate rows are “CMH-ranked candidates,” never validated
editing sites. Full-table truncation records the explicit full-table path and
hash, and every PDF page carries the state banner. Report generation itself
is never validation evidence.

At the Step `09b1` boundary these packages are approved but unimplemented.
Only schemas, templates, and synthetic fixtures will be committed; generated
production reports remain ignored.

## Documentation Files Have Different Purposes

Decision: keep documentation roles distinct.

```text
docs/operations/       handoff, runbook, and troubleshooting
docs/design/           pipeline plan, questions, and decisions
docs/demo/             PI demo walkthrough and report
docs/architecture/     visual pipeline/dataflow architecture and diagrams
TODO.md                tactical next work
README.md              entrypoint / overview
```

Reason: avoids turning one file into an everything-bucket.
