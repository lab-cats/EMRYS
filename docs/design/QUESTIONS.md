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

### CSU Batch R / Rscript Availability

The local runtime question is resolved: the official signed and notarized
Apple-silicon CRAN R `4.6.1` package is installed, and its published SHA-1
`fc9f4ada15589e8e037b9bf05563d21e97181635` was verified before installation.
The repository uses guarded `renv` `1.2.3`, Bioconductor `3.23`, and opt-in
activation through `NORAD_USE_RENV=1`.

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

Those eight namespaces and their transitive closure are locked. Normal restore,
an empty cache-disabled binary restore, namespace loading,
`BiocManager::valid()`, `renv::status()`, and headless PDF creation passed.
After `step-09b1-real-r-fixes`, the Step `08` and Step `09` suites both pass
without `SKIP` in the guarded local environment. Step `08` now performs
fail-closed lexical validation before semantic parsing, and the Step `09` PDF
fixture checks its signatures as raw bytes rather than locale-sensitive text.

Still unresolved:

```text
supported CSU compute-node/batch-visible Rscript path
compatible cluster package library and versions
whether that environment passes the restored Step 08 and Step 09 suites
```

The workflow does not install packages from compute or SLURM wrappers. Step
`09` itself uses base R (`stats`, `graphics`, and `grDevices`) and adds no
Bioconductor dependency.

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

### Runtime Sample-Manifest Provisioning And Persistence

The runtime contract is known, but the production file is not yet established
from this checkout:

```text
samples.tsv is absent from the current Git checkout
the cluster-local full manifest has not been inspected
the six approved replicate assignments must exist before Step 07
one byte-identical manifest/hash must flow through Steps 07-09
```

Determine whether the runtime manifest is intentionally cluster-local or can
be safely tracked, where its durable copy lives, how operators obtain it in a
fresh checkout, and where its SHA-256 is recorded. Never edit downstream
receipt hashes to mask a changed manifest; regenerate affected stages.
If the answer requires a tracked config change, use a separately gated
`step-07a-runtime-manifest`-style descendant before `validate-step-07`; do not
mix config implementation into the evidence-only validation branch.

### Post-Step 09 Scientific Evidence And Decisions

The local `step-09c-scientific-validation` package is implemented at
`b674a31` and synthetic-fixture-tested. It validates and summarizes explicit
evidence but does not answer these questions by itself, rerun CMH, or infer
human decisions. With production evidence unavailable, the production overall
state remains `evidence_incomplete`. Later inspected evidence can support
`science_review_complete_exploratory`; the reserved
`biological_interpretation_ready` value must be rejected until a separate
approved policy branch unlocks its exit criteria.

These scientific questions remain open even after a future computationally
`cluster-proven` Step `09`:

```text
What independent protocol/RSeQC/BAM-locus evidence is sufficient to retain
  legacy_provisional_v1, and what evidence requires a versioned replacement?
Can the exact Novogene GTF release be recovered after its path/identity/
  SHA-256 and delivery provenance are fixed; if not, can the unresolved
  release be accepted explicitly as a limitation? How should multiple
  transcript/gene assignments be represented, and what discrepancy rate is
  acceptable in the predeclared annotation audit?
Is unweighted mean sample AF the intended treatment-control effect metric?
Which primary thresholds will be approved before results are reviewed, and
  which sensitivity and leave-one-pair-out analyses are predeclared?
Does a genuine distinct, comparable no-dox/rABE-negative background cohort
  exist, and is the legacy every-background-sample AF <0.01 rule intended?
What coverage, quality/bias, repeat/multimapping, polymorphism, and annotation
  criteria define candidate pass/flag/reject adjudication?
What orthogonal evidence, if any, is required before a candidate is described
  as biologically validated rather than CMH-ranked?
```

A>G enrichment may support an orientation decision but cannot independently
prove the mapping that created the A>G labels. PI review and candidate
adjudication are also not substitutes for orthogonal experimental validation.
Record answers in `docs/design/DECISIONS.md` only after the underlying
evidence has been inspected.

### Immediate Artifact And Reporting Implementation

The design questions for the immediate artifact/report vertical slice are
resolved. Step `09c` is implemented and fixture-tested locally.
`artifact-schema-v1` is implemented and locally fixture-tested at `5f4d3b4`;
`artifact-adapters-v1` is implemented and locally fixture-tested at
`4dbd32d`; `artifact-run-summary` is implemented and locally fixture-tested
at `209bb19`; and `report-html-v1` is implemented and locally fixture-tested
at `117ba26`. Producer-side report-table approvals and final PDF/TSV/receipt
exports remain approved but unimplemented:

```text
artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-html-v1a-report-table-approvals
-> report-exports-v1
```

Implemented schema decisions:

```text
JSON Schema Draft 2020-12
shared common schema plus four public record schemas
67-row synthetic inventory of explicit physical artifacts; no glob discovery
immutable-contract run_id plus distinct attempt_id retries
explicit missing/failed/incomplete evidence records
typed local/runtime/cluster evidence and independent scientific state
reserved biological_interpretation_ready is rejected
read-only schema/inventory validation; no source inspection or output creation
artifact-record remains 1.0.0
scientific-review-record, run-summary, and report-receipt are 1.1.0
```

Implemented adapter decisions:

```text
49 exact read-only adapters cover all 67 declared Step 00a-09c artifacts
no glob discovery and no native compute-output retrofit
required strict six-field run-contract JSON plus explicit inventory
run_id binds the immutable run contract, not the revisionable inventory
inventory-only revisions create distinct superseding adapter attempts
records/index/receipt publish atomically with the receipt last
missing, failed, incomplete, unavailable, and unknown evidence remain explicit
adapter completion alone creates or promotes no runtime, cluster, science, or readiness state
a valid native Step 09c science state may be propagated after reconciliation
```

Implemented run-summary decisions:

```text
canonical run-summary JSON as the report layer's sole structured entry point
one exact complete adapter receipt and optional exact Step 09c summary
no glob discovery, analysis execution, or status promotion
deterministic artifact and QC TSV views
rollback-protected four-file transaction with the receipt published last
distinct summary attempt IDs under one unchanged immutable run contract
explicit missing, failed, incomplete, and unavailable evidence remains visible
```

Implemented HTML-report decisions:

```text
Quarto 1.9.38 with bundled Typst
official macOS archive SHA-256
  47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a
checksum-verified repository-local ignored restore via make quarto-restore
one canonical run-summary JSON and only explicitly approved TSVs
dry-run-first HTML-only CLI; --formats accepts only html
self-contained script-free HTML; no executable cells or external active assets
wrapper prefers .venv/bin/python and honors authoritative PYTHON_BIN_OVERRIDE
report generation never runs analysis and never proves validation
state banners preserve incomplete or exploratory/provisional meaning
```

Fixed decisions for the remaining report packages:

```text
report-html-v1a-report-table-approvals adds a normal producer authorization path
report-exports-v1 adds PDF, exported summary TSV, and final report receipt
PDF uses Quarto bundled Typst and repeats the state banner on every page
```

The current gate has 58 schema tests, 50 adapter tests, 108 combined
schema/adapter tests, 39 run-summary tests, 147 combined artifact-layer tests,
and 65 focused report tests. The focused report target passes with real pinned
Quarto required. The full Python gate reports `277 passed, 1 skipped`; the
expected skip is its opt-in real-Quarto case. Synthetic fixtures exercise
explicit native-source inspection, adapter and summary receipt-last
publication, and deterministic HTML rendering. No production source has been
inspected by these artifact-layer packages, and no production artifact index,
run summary, or report exists. Production reports and biological conclusions
remain unavailable because production Steps `07`-`09` evidence and production
Step `09c` review evidence have not been generated or inspected.

The separate longer-term module/refactor questions remain deferred:

```text
whether Step 06 is a universal core stage or an optional orientation-aware prerequisite
whether the first analysis module is named rna_editing_cmh
the future analysis-config interface
public-dataset ingestion through the same manifest/config/provenance boundary
```

### Remaining Engineering Roadmap Decisions

The immediate sequence is now fixed: artifacts/run summary and HTML/PDF reports
precede runtime preflight, reference provenance, storage/retention, and one
validator branch per Step `00a`-`09`. These packages are approved for local
implementation; remote validation remains paused until the final validator.

Still-deferred questions beyond that sequence:

```text
when repeated execution makes SLURM arrays useful
how stale-lock inspection and cleanup should prove safety before changing anything
the exact targeted-rerun planner interface
the analysis-config and module-wrapping contracts
whether cluster tool paths eventually need a shared config
when second-cohort evidence justifies broader refactoring
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

Contract answered; runtime provisioning remains open above.

Manifest file:

```text
samples.tsv
```

Validated by:

```text
scripts/validate_manifest.py
```

The generic schema accepts optional `replicate` metadata so earlier manifests
remain valid. Step `09` requires `replicate` for its control/treatment samples
and uses the full sample manifest as the only pairing source. The manifest must
carry the approved pairs before Step `07` so the same hash propagates through
the downstream receipt chain. This does not establish that a production
`samples.tsv` is present in the current checkout or that its cluster-local
copy has been inspected.

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
09   Paired CMH editing-site calling from the committed Step 08 tables
09c  Explicit scientific-evidence validation and 13-TSV review transaction
```

Implemented local infrastructure package:

```text
artifact-schema-v1  Draft 2020-12 contracts, explicit synthetic inventory,
                    read-only validator, and fixtures
artifact-adapters-v1 49 read-only Step 00a-09c adapters, explicit immutable
                     run contract, and receipt-last artifact transaction
artifact-run-summary Canonical JSON, deterministic artifact/QC TSV views, and
                     a receipt-last summary transaction
report-html-v1       Checksum-pinned Quarto restore and one static,
                     self-contained script-free HTML report
```

Step `07` passed its mocked-bcftools focused tests and the complete local
repository validation gate. It has not run against real bcftools on this
workstation, has not completed a cluster dry-run or execute job, and has no
inspected cluster output. It is not cluster-proven.

Step `08` is implemented locally at commit `90335d8`, and its fake-R wrapper
and shell tests pass. Its `step-09b1-real-r-fixes` hardening is at `eae5eca`,
and the complete real-R fixture suite passes without `SKIP` under the guarded
local runtime. Step `08` has no cluster dry-run, execute, log, or output
evidence and is not cluster-proven.

Step `09` is implemented locally at commit `e4371de`, and its shell/fake-R
suite passes. After the raw-byte PDF assertion fix at `eae5eca`, its complete
real-R fixture suite also passes without `SKIP`. Step `09` has no cluster
dry-run, execute, log, or output evidence and is not cluster-proven.

Step `09c` is implemented locally at `b674a31`. Its active Python/shell
fixtures cover dry-run, exact summary-last publication, missing/incomplete and
exploratory states, reserved-state rejection, hashes, locks, cleanup, and
rollback. It has no production evidence package or completed production
science review, and it is not a cluster computation or biological-readiness
gate.

`artifact-schema-v1` is implemented locally at `5f4d3b4`. It contains one
shared and four public schemas, a 67-row synthetic explicit inventory, a
read-only validator, and fixtures covered by the current 58 focused tests. It is not a
compute step and has not inspected production artifacts or changed any
runtime, cluster, scientific-review, or biological-readiness status.

`artifact-adapters-v1` is implemented locally at `4dbd32d`. It contains 49
explicit adapters covering the full 67-row inventory; 50 focused tests pass.
Its synthetic fixtures inspect representative native outputs and publish
records/index/receipt transactions. No production source has been inspected
or indexed, and no runtime, cluster, scientific-review, or
biological-readiness status has changed.

`artifact-run-summary` is implemented locally at `209bb19`. It publishes
canonical JSON, deterministic artifact/QC TSV views, and a receipt-last
four-file transaction from exact synthetic adapter inputs. All 39 focused
tests pass. Synthetic fixture summaries exist; no production artifact
transaction or production run summary has been generated, and no evidence
status has been promoted.

`report-html-v1` is implemented locally at `117ba26`. Its 65-test focused
target passes with real pinned Quarto required, and the complete Python gate
reports `277 passed, 1 skipped`. Synthetic/incomplete fixture reports render
deterministically, but no production report has been generated and no
computational, scientific, or biological state has been promoted.

### Which Steps Need Clean Reimplementation From The Reference Workflow?

Steps `07`, `08`, and `09` have now been cleanly reimplemented as
parameterized, manifest-driven stages. Step `07` real-bcftools and cluster
validation remain pending. Steps `08` and `09` pass their complete local
real-R semantic suites; all cluster validation remains pending.

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
to replace it remains an open question, and Step `09` preserves that
qualification in its result tables and summary.

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

Before `VariantAnnotation` semantic parsing and ALT expansion, Step `08`
streams through the raw VCF and validates FORMAT/DP, FORMAT/AD, and present
INFO/AD tokens lexically. DP has exactly one non-negative integer or `.`;
an AD value may be a single `.` when its whole vector is missing, but otherwise
has exactly one token for REF plus one for every ALT. Every token is a
non-negative integer or `.`. This prevents a semantic parser from coercing
malformed raw tokens into parsed numeric values. `rtracklayer` plus
`GenomicRanges` provide direct parsing and strand-aware use of the Novogene
GTF. Every multiallelic record is expanded by ALT index, and the matching
FORMAT/AD and INFO/AD alternate value is retained. Symbolic and non-SNV
alternate alleles are counted and excluded. Missing or incorrect required
FORMAT/INFO definitions, malformed or negative counts, partial DP/AD
missingness, and AD greater than DP fail rather than being truncated or
repaired.

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

This contract is implemented locally at commit `90335d8`, hardened at
`eae5eca`, and locally tested through both the fake-R shell suite and passing
real-R suite without `SKIP`. The earlier generic negative-fixture failure was
misattributed to partition overlap; reason-specific assertions confirmed that
overlap rejection already worked. The actual defect was malformed raw
DP/AD/INFO AD coercion, now rejected by the streaming lexical preflight. That
preflight adds one bounded-memory streaming pass over each VCF; its I/O cost
still requires a future pilot benchmark and primary-universe cluster
measurement. No cluster evidence has been inspected, and Step `08` is not
cluster-proven.

### What Is The Step 09 Paired CMH Contract?

Answered for local implementation.

The full sample manifest is the only runtime pairing source. It must include
`replicate`, with exactly one control and one treatment for each replicate,
identical replicate sets for the two conditions, and at least two strata.
Pairing is never inferred from sample names. The current approved relationships
are:

```text
ABE_EV_2 / ABE_PUM1_2 -> replicate 2
ABE_EV_3 / ABE_PUM1_3 -> replicate 3
ABE_EV4  / ABE_PUM1_4 -> replicate 4
```

`configs/step_09_pairs.NORAD_EV_PUM1.tsv` is a reference record of that mapping,
not a runtime overlay. Because Step `09` requires the current sample-manifest
hash to match every Step `08` input-receipt row, the replicate-bearing full
manifest must be established before Step `07`.

Step `09` validates the current manifest and partition hashes, the complete
Step `08` receipt order and counts, the exact sites-table schema and
manifest-ordered sample columns, candidate uniqueness, count/AF consistency,
and immutable input hashes. For each successfully testable target row, it builds
treatment/control by edited/unedited tables across the manifest-defined strata
and calls two-sided `mantelhaen.test(..., correct=TRUE, exact=FALSE)`. The
common odds ratio is treatment relative to control. BH is applied once across
all successfully tested target candidates from all partitions and both
orientations before mean-depth, background, or effect filters.

Default call thresholds are:

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

Optional background filtering is disabled by default. When an explicit
condition distinct from control and treatment is supplied, every background
sample must have adequate depth and AF strictly below `0.01` by default. EV is
never repurposed as a missing no-dox cohort.

The all-sites and significant-sites tables begin with 42 fixed
analysis/annotation/statistic fields and then manifest-ordered
`DP__<sample>`, `AD__<sample>`, and `AF__<sample>` groups. Exact status
vocabularies are:

```text
test_status:
  not_target_change | missing_counts | low_coverage | degenerate_table | tested
call_status:
  not_tested | below_mean_dp | background_not_passed | fdr_not_met |
  effect_not_met | significant_up | significant_down
background_status:
  disabled | pass | missing_counts | low_coverage | fail_fraction
```

The summary has 39 fixed provenance, count, threshold, method, and policy
columns. The mutation table has nine fixed columns and exactly 12 ordered
canonical substitutions:

```text
A>C A>G A>T C>A C>G C>T G>A G>C G>T T>A T>C T>G
```

The complete output transaction is:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

Both plots use a fixed 7-by-5-inch base-R device, are signature/EOF validated,
and remain valid for an empty candidate table. Execute mode uses an owned
analysis lock, run-token
temporary and backup paths, validation before publication, exact output
reconciliation, and rollback. The summary is published last as the transaction
commit marker. An incomplete rollback retains the owned lock for explicit
operator recovery.

This contract is implemented locally at commit `e4371de`, its fixture was
hardened at `eae5eca`, and it is locally tested through the shell/fake-R suite
and passing real-R suite without `SKIP`. The fixture now searches for the PDF
header and EOF marker as raw bytes; the prior failure was a locale-sensitive
test assertion, not a corrupt-PDF finding. No Step `09` cluster evidence has
been inspected, and the step is not cluster-proven. The workflow preserves
`orientation_policy=legacy_provisional_v1`; the all-sites,
significant-sites, and summary tables record it. The policy is not
biologically validated.

### What Is The Step 09c Scientific-Evidence Contract?

Answered for local implementation.

Step `09c` is explicit-input, dry-run-first Python/shell tooling implemented at
`b674a31`. It validates the named sample/partition manifests, Step `08`
three-file transaction, Step `09` six-file analysis directory, one-row review
plan, and evidence manifest. It does not discover inputs by glob, rerun CMH,
infer reviewer decisions, or act as a SLURM/compute stage.

The run-summary package hardens this contract without changing its allowed
science states. Human reviewer, decision-owner, and evidence-owner names are
retained as human-readable text while machine identifiers and policy versions
remain safe IDs. Complete or incomplete source evidence requires a date;
source-free missing/not-applicable evidence may normalize with a null date.
Primary, superseded, and sensitivity analysis sets must be disjoint, and
category-specific evidence must belong to the declared analysis role.
Pending decisions cannot cite supporting evidence; recorded decisions require
complete or justified-not-applicable support, and rerun booleans/scopes must
agree. Passed/failed/proven computational claims require their defined
complete evidence roles; runtime and cluster roles additionally require
explicit underlying paths/hashes. Blocked/not-run states are not proof and
must not be given invented claim evidence. The tracked example declares
`local_test_status=not_run` because it attaches no computational evidence;
that declaration is separate from the repository tooling's passing fixture
tests.

Execute mode publishes 13 TSVs under
`results/scientific_validation/<review_id>/`, with
`<review_id>.step09c_review_summary.tsv` last. It validates schemas, paths,
SHA-256 hashes, row counts, identities, policies, dates, computational claims,
scientific statuses, and cross-table evidence relationships. Publication uses
an owned review lock, run-token scratch/backup paths, immutable-input rechecks,
validation before publication, rollback, and cleanup.

The only permitted overall science states are:

```text
evidence_incomplete
science_review_complete_exploratory
```

The second remains provisional. `biological_interpretation_ready` is reserved
and rejected. Active Python and shell synthetic fixtures pass, but no
production review evidence is recorded or supported by inspected evidence;
production science remains `evidence_incomplete`.

### What Is The Artifact Adapters V1 Contract?

Answered for local implementation.

`scripts/build_artifact_index.py` is dry-run-first, explicit-input-only, and
read-only with respect to Step `00a`-`09c` sources. Its 49 exact adapter IDs
cover all 67 rows in the tracked synthetic inventory. It never discovers
sources by glob, invokes analysis code, or requires native JSON emitters.

The interface requires:

```text
--run-id RUN_ID
--run-contract RUN_CONTRACT_JSON
--inventory INVENTORY_TSV
--output-root OUTPUT_ROOT
[--execute]
```

The strict run-contract JSON contains the declared run-contract hash plus
sample-manifest, reference-contract, partition-manifest, primary-analysis ID,
and primary-analysis-policy identity. Those fields define immutable run
identity. An inventory-only revision is a new `adapter_attempt_id` under the
same run; changing an identity component requires a new `run_id`.

Execute mode publishes `records/<artifact_id>.json`,
`<run_id>.artifacts.tsv`, then `<run_id>.artifact_receipt.tsv` last under
`results/artifacts/<run_id>/`. A complete receipt commits the adapter
transaction even when individual records explicitly report missing,
incomplete, failed, unavailable, or unknown evidence. Runtime, cluster, and
scientific status remain independent.

This contract is implemented at `4dbd32d`. All 50 focused adapter tests and
108 combined schema/adapter tests pass on synthetic fixtures. No production
source or artifact transaction has been inspected. The run-summary package is
implemented separately. Static HTML rendering is also implemented;
producer-side report-table approvals and PDF/TSV/receipt exports remain
pending.

### What Is The Artifact Run Summary Contract?

Answered for local implementation.

`scripts/build_run_summary.py` is dry-run-first and explicit-input-only:

```text
--run-id RUN_ID
--artifact-receipt ARTIFACT_RECEIPT
--output-root OUTPUT_ROOT
[--science-review-summary REVIEW_SUMMARY_TSV]
[--execute]
```

The artifact receipt must be the exact complete receipt under the declared
`OUTPUT_ROOT/<run_id>/` adapter transaction. The optional Step `09c` summary
is an exact committed path and is never discovered. Dry-run validates the
complete adapter transaction, immutable run identity, receipt/run-contract/
inventory/index/record hashes, ordering, attempt lineage, and optional science
evidence without writing. It carries native-source hashes recorded by the
adapter but does not rehash native Step `00`-`09` sources. Execute mode
publishes:

```text
results/artifacts/<run_id>/
  <run_id>.run_summary.json
  <run_id>.run_summary.tsv
  <run_id>.qc_summary.tsv
  <run_id>.run_summary_receipt.tsv
```

Canonical, stably ordered JSON is the report layer's sole structured entry
point. The two TSVs are deterministic artifact and QC views, and the receipt
is published last. A complete summary transaction can legitimately retain
missing, failed, incomplete, or unavailable evidence. Retries receive
distinct run-summary attempt IDs under the unchanged immutable run contract.
Owned locking, adapter transaction-member and optional Step `09c` input
rechecks, output-directory identity checks, validation-before-publication,
rollback, and recovery protect publication.
The builder never invokes analysis or promotes computational, scientific, or
biological status.

This contract is implemented at `209bb19`. All 39 focused tests and 147
combined artifact-layer tests pass on synthetic fixtures. No production
adapter transaction or run summary exists, and no validation claim was
created.

### What Is The Static HTML Report Contract?

Answered for local implementation.

The public wrapper is explicit-input-only and dry-run-first:

```text
scripts/render_run_report.sh
  --run-summary RUN_SUMMARY_JSON
  --output-root OUTPUT_ROOT
  --quarto-bin QUARTO_BIN
  [--formats html]
  [--execute]
```

It requires the canonical `<run_id>/<run_id>.run_summary.json` name, pinned
Quarto `1.9.38`, and one explicit output root. The wrapper prefers the
repository `.venv/bin/python`, then `python3`, unless an authoritative
`PYTHON_BIN_OVERRIDE` is supplied. Dry-run validates the summary, renderer,
templates, prior output, and every explicitly approved report table without
creating output, lock, or scratch paths.

Execute mode disables document execution and publishes only:

```text
results/reports/<run_id>/<run_id>.run_report.html
```

The file is self-contained, script-free, and free of external active assets.
It escapes input content, preserves computational/scientific separation and
the applicable state banner, and calls candidates only “CMH-ranked
candidates.” It never invokes analysis or establishes validation. PDF,
exported report TSVs, and the report receipt are not part of this contract.

`make quarto-restore` verifies the official macOS Quarto archive with
SHA-256
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a`
before publishing ignored local tooling. `make report-test` then requires
that real pinned executable. All 65 focused tests pass, while the complete
Python gate reports `277 passed, 1 skipped`; the one expected skip is the
opt-in real-Quarto test executed by the focused target. This is local
synthetic/incomplete fixture evidence only, not a production report or
runtime, cluster, scientific-review, or biological-readiness claim.

The renderer accepts only tables named by `approved_report_tables`, but the
current normal run-summary producer emits that list empty. The resolved next
package is therefore `report-html-v1a-report-table-approvals`, followed by
`report-exports-v1`. Operators must not hand-edit canonical summary JSON.

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
