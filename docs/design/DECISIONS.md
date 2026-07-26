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
Step `09c` is also implemented locally at `b674a31` and fixture-tested as an
explicit evidence validator; it is not a core compute or SLURM stage and has
no production-review evidence. `artifact-schema-v1` is implemented locally at
`5f4d3b4` with a read-only validator and synthetic fixtures.
`artifact-adapters-v1` is implemented locally at `4dbd32d` with explicit
read-only native adapters and receipt-last synthetic transactions. No
production artifact index exists. `artifact-run-summary` is implemented
locally at `209bb19` with exact-input, receipt-last synthetic transactions.
`report-html-v1` is implemented locally at `117ba26` and tested against
synthetic summaries with the real pinned Quarto runtime. No production
artifact index, run summary, or report exists. PDF/TSV export and the final
report receipt remain non-runnable.

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

Current evidence: the decision is implemented at `b674a31`. Active Python and
shell fixtures cover explicit-input validation, incomplete and exploratory
states, reserved-state rejection, exact 13-file summary-last publication,
immutable hashes, locks, cleanup, and rollback. This local synthetic evidence
does not establish a production science review, runtime or cluster proof, or
biological readiness.

Decision: scientific-review normalization must retain human context without
weakening machine contracts. Reviewer, decision-owner, and evidence-owner
names are human-readable text; identifiers and policy versions remain safe
machine IDs. Complete or incomplete source evidence requires a date.
Source-free missing/not-applicable TSV evidence uses `NA` (or a valid date);
v1.1 normalization maps `NA` to JSON `null`.

Decision: primary, superseded, and sensitivity analysis sets are disjoint.
Each evidence category has explicit analysis ownership, and non-sensitivity
payloads must bind to the primary analysis. Pending decisions cannot cite
supporting evidence. Recorded decisions require their own complete or
justified-not-applicable status plus nonempty complete/not-applicable support;
rerun booleans and scopes must agree.

Decision: passed/failed/proven computational-status claims require their
defined complete status-specific evidence roles. Runtime and cluster roles
additionally require explicit underlying paths/hashes. Blocked/not-run states
have no claim-role requirement and must never be represented as proof.
Local-test, runtime, cluster-dry-run, and cluster-proof claims are never
inferred from a wrapper summary, package installation, or prose. The tracked
example review plan therefore declares `local_test_status=not_run` because it
attaches no local-test evidence, even though the repository tooling itself is
fixture-tested. These stricter contracts preserve the existing science-state
and readiness lock.

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
-> report-html-v1a-report-table-approvals
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

The local `step-09b1-real-r-fixes` package is complete and pushed. Step `09c`
is implemented locally at `b674a31`. `artifact-schema-v1` is implemented and
locally fixture-tested at `5f4d3b4`. `artifact-adapters-v1` is implemented and
locally fixture-tested at `4dbd32d`. `artifact-run-summary` was introduced at
`209bb19`. `report-html-v1` is implemented and locally tested with the real
pinned renderer at `117ba26`. `report-html-v1a-report-table-approvals` is
implemented at `2a4b8f8`; after its docpatch/push gate, `report-exports-v1` is
the next descendant. PDF/TSV/final-receipt exports remain immediate, before
the three foundational engineering packages.
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

Candidate helper names, config filenames, Makefile targets, and admin
utilities remain roadmap ideas until separately implemented and tested. This
does not apply to the implemented
`scripts/validate_artifact_contracts.py`,
`configs/artifact_inventory.example.tsv`, or
`schemas/artifacts/v1/`, `scripts/build_artifact_index.py`, or
`configs/artifact_run_contract.example.json`,
`scripts/build_run_summary.py`, or
`scripts/_run_summary_science.py`,
`configs/report_table_approvals.example.tsv`,
`scripts/restore_quarto.py`,
`scripts/render_run_report.sh`, `scripts/render_run_report.py`,
`reports/run_report.qmd`, `reports/run_report.css`, `make quarto-restore`, or
`make report-test` interfaces. It still applies to pending report export work,
foundation tools, and per-step validators.

## Reporting Is Decoupled From Computation Through Structured Artifacts

Decision: compute steps and report rendering should remain decoupled.

The implemented `artifact-schema-v1` package uses JSON Schema Draft 2020-12.
It provides one shared common schema and four public record contracts:

```text
schemas/artifacts/v1/common.schema.json
schemas/artifacts/v1/artifact_record.schema.json
schemas/artifacts/v1/scientific_review_record.schema.json
schemas/artifacts/v1/run_summary.schema.json
schemas/artifacts/v1/report_receipt.schema.json
```

Decision: the common schema retains its `v1` URN, and the artifact-record
document remains `1.0.0`. Scientific-review-record, run-summary, and
report-receipt documents are explicitly `1.1.0`. Their closed shapes were
enriched during run-summary implementation to retain human review context,
decision/evidence provenance, limitations, and the report's required input
version. Advancing them to `1.1.0` avoids silently mutating the already closed
`1.0.0` contracts. The run-summary TSV, QC TSV, and run-summary receipt TSV
producer contracts remain `1.0.0`.

An explicit expected-artifact inventory supplies every future adapter and
source path; neither adapters nor renderers may discover inputs by glob. The
inventory header is exactly:

```text
artifact_id
step_id
scope_type
scope_id
adapter
source_path
required
```

Decision: an inventory row represents one physical expected artifact path.
`artifact_id` and physical source path are unique. Multiple physical artifacts
may share one `(step_id, scope_type, scope_id)` logical scope, and those rows
remain contiguous so downstream aggregation preserves stable first-seen
ordering. Source paths are explicit and normalized: no glob syntax, unresolved
templates, redundant separators, or `.` / `..` traversal components.
The tracked example uses repository-relative paths; an explicit runtime
inventory may instead use normalized absolute paths.

The tracked `configs/artifact_inventory.example.tsv` is a 67-row synthetic
inventory covering physical fixture artifacts from Steps `00a`-`09c`. It
defines and tests the inventory shape; it is not a production run inventory
and does not assert that any production source exists.

```text
artifact-schema-v1
-> read-only artifact-adapters-v1 over existing outputs
-> artifact-run-summary
```

A `run_id` identifies one immutable
manifest/reference/partition/primary-analysis contract. Artifact or adapter
retries with identical identity values receive different attempt IDs; changing
one of those identity values requires a new `run_id`. Records model attempts,
implementation, local tests, runtime validation, cluster validation,
warnings/errors, provenance, metrics, and scientific state independently.
Missing, failed, incomplete, externally unavailable, and unknown evidence must
be represented, not omitted.

Decision: `run_contract_sha256` is the SHA-256 of canonical compact,
key-sorted JSON over exactly the sample-manifest hash, reference-contract hash,
partition-manifest hash, primary analysis ID, and primary-analysis-policy
hash. The schema validator checks that relationship within each record.
Decision: the implemented adapter transaction performs output-root-local
stateful collision checking. Its strict run-contract input contains
`run_contract_sha256` plus the five canonical identity components. An existing
`run_id` bound to different values fails. This is not a global registry claim;
it is validation against the prior committed receipt in the selected output
root.

Decision: the expected-artifact inventory is revisionable adapter-attempt
metadata, not part of run identity. An execute-mode build always receives a
new `adapter_attempt_id`. Under an unchanged run contract, an inventory-only
revision may supersede the prior adapter attempt after that complete prior
transaction is independently validated. The receipt records the current
inventory path/hash, current attempt, superseded attempt, and ordered history.

Decision: strict JSON and semantic validation are required in addition to
schema shape. Duplicate object keys, `NaN`/`Infinity`, invalid dates, incoherent
attempt supersession, status claims without required evidence, mismatched
scientific-review inputs, and invalid report-receipt transactions fail
closed. Artifact retry chains are checked per artifact; a run summary may
contain multiple independent artifact attempt histories.

Decision: the current v1 schemas preserve the scientific-policy lock. They
admit only `evidence_incomplete` and
`science_review_complete_exploratory`, require readiness authorization to be
null, and reject `biological_interpretation_ready`. A future policy that
unlocks readiness must receive its own approved schema/version change.

The public validator is:

```text
scripts/validate_artifact_contracts.py
```

It is read-only and explicit-input-only. It validates schemas, individual
records, inventories, and supported record/inventory reconciliation. It does
not discover outputs, build artifact records, verify production source
contents, publish an artifact transaction, assemble a run summary, render a
report, or run analysis. Record/inventory reconciliation is defined only for
artifact records and run summaries; scientific-review and report-receipt
records validate independently of an inventory argument.

Canonical, stably ordered `<run_id>.run_summary.json` is the report layer's
single structured input. `artifact-adapters-v1` first inspects existing
Step `00a`-`09` and Step `09c` outputs and publishes per-artifact records,
`<run_id>.artifacts.tsv`, and `<run_id>.artifact_receipt.tsv`. The separate
`artifact-run-summary` package now assembles those validated adapter outputs
into the canonical summary plus deterministic artifact and QC TSV views.
Existing compute CLIs and paths remain unchanged; native per-step JSON
emission is not added.

Decision: one exact complete adapter receipt under
`OUTPUT_ROOT/<run_id>/` is the only required run-summary entry point. An
optional Step `09c` review summary is supplied by exact path and is never
discovered. An optional exact report-table approvals TSV may authorize only
complete active-review Step `09c` TSV artifacts after run-contract, role,
path, hash, row-count, display-limit, policy, approver, and approval-time
validation. It requires the exact committed Step `09c` summary, is never
discovered, and omission authorizes no tables.
Dry-run performs full validation without stable writes. Execute mode publishes
canonical JSON, artifact TSV, QC TSV, and the run-summary receipt last as one
transaction.

Decision: `summary_state=complete` means the four-file summary transaction was
validated and committed. It does not mean the underlying evidence is
complete. Missing, failed, incomplete, and externally unavailable artifacts
remain explicit, and no local, runtime, cluster, scientific, or biological
status is inferred or promoted.

Decision: report-table approvals do not change the run-summary receipt TSV
header or its `1.0.0` schema. The receipt's canonical JSON SHA-256 transitively
commits the approval-manifest descriptor and approved records.

Decision: each execute-mode publication under one unchanged immutable run
contract receives a distinct run-summary attempt ID and preserves ordered
supersession history. Existing summary transactions, adapter
receipt/run-contract/inventory/index/record members, optional Step `09c`
inputs, optional approval manifest and approved table snapshots, and
output-directory identity must validate before replacement. The builder
carries native-source hashes recorded by the adapter but does not rehash
native Step `00`-`09` sources. Owned locking, run-token temporary/backup
paths, validation-before-publication, rollback, and recovery protect the
receipt-last boundary.

Decision: adapter transaction completion and evidence completion are separate.
The adapter receipt is published last and may be complete while individual
records are missing, failed, incomplete, externally unavailable, or unknown.
Implementation and local-test evidence never imply runtime or cluster proof.
Adapter v1 populates implementation evidence but deliberately leaves every
generated record's local-testing, runtime-validation, cluster-dry-run, and
cluster-proof fields at `not_run`; there is no native-validation import path
in this package.

A Step `09c` science state is exposed only after the required 13-output
summary-last scope, plan/summary identity, all ten required published evidence
category declarations, and exact evidence-ID, payload, and count relationships
reconcile. An `evidence_incomplete` review may retain missing or incomplete
categories, pending decisions/adjudication, and
`review_completed_date=NA`. A
`science_review_complete_exploratory` review additionally requires every
required category to be `complete` or justified `not_applicable`, complete
decisions with every required decision recorded, exact equality between the
selected and adjudicated `(analysis_id, candidate_id)` identity sets, and a
present completion date.
Non-provisional orientation additionally requires a complete orientation
audit and a matching completed orientation decision. A Step `09c` source that
declares `cluster_proof_status=proven` additionally requires the optional
`computational_validation` category to be complete. These native science
checks do not promote the artifact records' validation fields.
`biological_interpretation_ready` remains rejected.

Decision: reports use checksum-pinned Quarto `1.9.38` with bundled Pandoc and
Typst. The approved Quarto archive SHA-256 is
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a`.
The earlier planned digest was incorrect. The official GitHub release asset
metadata and an independently downloaded official archive both produced the
value above; the restore therefore fails closed on any other digest.

`make quarto-restore` is an explicit macOS operator action into ignored local
tool storage and does not use Homebrew. It safely extracts the official
archive, verifies the exact executable version, and writes
`.norad-quarto-install.json` with the archive identity and a deterministic
installed-tree hash. Every subsequent restore or `make report-test` rechecks
the receipt, complete tree, and executable version. Rendering never installs
or repairs software.

The implemented HTML interface is:

```text
scripts/render_run_report.sh
  --run-summary RUN_SUMMARY_JSON
  --output-root OUTPUT_ROOT
  --quarto-bin QUARTO_BIN
  [--formats html]
  [--execute]
```

Dry-run is the default and creates no stable output, lock, or scratch path.
This stage publishes exactly:

```text
results/reports/<run_id>/<run_id>.run_report.html
```

One static QMD consumes the validated canonical run summary, contains no
executable cells, and uses Quarto with execution disabled. The rendered HTML
must be script-free and self-contained: active resources are embedded, no
`script`, `base`, refresh, `iframe`, object, embed, remote asset, or sidecar
resource tree is accepted. The renderer also validates document language and
title, the main landmark, heading order, table headers/captions, image
alternatives, accessible embedded figures, exact run/hash identity, and one
exact scientific-state banner. It never reruns STAR, samtools, Picard, GATK,
bcftools, R preprocessing, or CMH.

Only tables named by the run summary's `approved_report_tables` records may
enter the report, and their exact normalized paths, SHA-256 values, row
counts, widths, and snapshots must validate. The implemented optional
`--report-table-approvals` interface accepts a nonempty exact 14-column TSV,
binds every row to the current run ID and immutable run-contract hash, and
authorizes only exact complete active-review Step `09c` TSV artifacts with
matching adapter role, path, hash, row count, display limit, approval policy,
approver, and canonical UTC approval time. Omitting the input emits
`approved_report_tables: []`. Canonical run-summary JSON must not be
hand-edited to bypass this producer.

Execute mode treats the one HTML file as an atomic publication. It validates
any prior report, uses an owned lock plus run-token stage and backup paths,
rechecks every input, and refuses to clobber symlinked, mutated, late
foreign, or identity-changed paths. Quarto runs in its own process group; the
renderer handles HUP, INT, TERM, and timeout by terminating and reaping that
complete group. Failed publication restores the validated prior report when
possible. Incomplete rollback or cleanup retains the owned lock and
best-effort recovery marker for explicit operator inspection. This HTML-only
stage does not publish a report receipt; PDF, exported summary TSV, and the
final report receipt belong to `report-exports-v1`.

Reports must keep computational and scientific status separate and render a
persistent applicable state banner. `evidence_incomplete` forbids biological
interpretation; `science_review_complete_exploratory` remains explicitly
provisional. Candidate rows are “CMH-ranked candidates,” never validated
editing sites. Full-table truncation records the explicit full-table path and
hash, and every PDF page carries the state banner. Report generation itself
is never validation evidence.

Current evidence: `artifact-schema-v1` is implemented at `5f4d3b4`. The shared
schema, four public schemas, read-only validator, 67-row synthetic physical
inventory, valid fixtures, and current `58` focused tests pass locally.
`artifact-adapters-v1` is implemented at `4dbd32d`; its 49 adapters, synthetic
native fixtures, receipt-last transaction, and 50 focused tests pass locally.
`artifact-run-summary` was introduced at `209bb19`; its report-table approval
producer is implemented at `2a4b8f8`, and its 53 focused and 161 combined
artifact-layer tests pass on synthetic fixtures. `report-html-v1` is
implemented at `117ba26`; the current `make report-test` gate passes 119
Python tests plus its shell wrapper with the real pinned Quarto runtime, and
the complete Python gate passes 292 tests with one expected skip.
`make report-test` makes the real renderer mandatory and does not skip it.
These results prove local synthetic-fixture behavior and local renderer
execution only. No production source/index, canonical run summary, approval
manifest, HTML/PDF report, pipeline runtime or cluster evidence, completed
production scientific review, or biological readiness exists.
`report-exports-v1` is next; generated production outputs/reports remain
ignored.

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
