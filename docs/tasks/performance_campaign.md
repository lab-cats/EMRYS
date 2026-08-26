# EMRYS computational performance campaign

> **TEMPORARY CAMPAIGN SOURCE — NOT A SECOND BACKLOG**
>
> This document preserves computational-scaling diagnoses, proposed end states,
> experiment rules, alternatives, and slicing context. The
> [findings matrix](backlog_matrix.md) alone owns accepted task IDs, status,
> required outcomes, acceptance, and dispositions. The provisional
> [performance campaign matrix](performance_backlog_matrix.md) supports
> comparison and routing only.

Status: **Active temporary campaign**  
Opened: **2026-08-25**

## Purpose

Reduce the time, memory, shared-storage traffic, and scratch-space cost of the
existing computational pipeline without weakening scientific behavior,
artifact identity, provenance, recovery, or fail-closed validation.

The central diagnosis is narrower than “every scientific algorithm is naive.”
STAR, samtools, bcftools, interval overlap, and the current statistical method
already contain appropriate indexed or near-linear kernels. The largest proven
waste is the software around those kernels repeatedly hashing, parsing,
validating, copying, and materializing the same large artifacts.

For large scientific data, reducing fourteen linear passes to two can matter as
much as an asymptotic improvement. This campaign therefore tracks both:

- true complexity changes;
- pass, allocation, process, compression, storage, and scheduling reductions;
- amortized reuse across samples, partitions, and analyses; and
- space reductions through streaming and bounded working sets.

## Non-goals and excluded scientific-equivalence campaigns

This campaign does not authorize:

- removing SplitNCigarReads or another scientific stage;
- replacing Picard with an implementation that has different duplicate or
  optical-duplicate semantics;
- replacing STAR or changing alignment policy;
- changing candidate eligibility, CMH meaning, multiple-testing family, FDR
  policy, or another statistical method;
- weakening mutation detection, receipts, no-clobber behavior, rollback,
  recovery, or evidence language merely to improve a timing; or
- treating local, hosted-CI, scheduler, or synthetic evidence as scientific or
  biological validation.

An exact implementation of the already accepted method may be evaluated only
when its parity boundary and independent oracle are explicit. Scientifically
different alternatives require separately approved scientific-review work.

## Scaling vocabulary

| Symbol | Quantity |
|---|---|
| `B` | Bytes in large immutable input and produced artifacts |
| `R` | Reads or alignment records |
| `S` | Samples or libraries |
| `P` | Cohort partitions |
| `C` | Expanded candidate or alternate-allele rows |
| `G` | Reference and annotation size or feature count |
| `A` | Compatible analyses over one processed dataset |
| `J` | Independently scheduled tasks or workers |

The benchmark for a change must vary the dimensions that exercise its claimed
benefit. Increasing read pairs alone cannot establish sample, partition,
candidate, annotation, skew, concurrency, or startup scaling.

## Evidence and integration rule

Every candidate follows the same short loop:

1. State one scaling hypothesis and its expected time/space/I/O effect.
2. Freeze baseline and candidate SHAs and run both in one retained CI job.
3. Establish output and failure parity before interpreting timing.
4. Use a warm-up followed by repeated cyclic baseline/candidate pairs.
5. Retain raw measurements, environment identity, and a machine-readable
   summary.
6. Admit the candidate only if it produces either:
   - a deterministic reduction in bytes, passes, allocations, processes, or
     peak space with no material counter-regression; or
   - a repeatable timing/resource improvement larger than observed noise.
7. Record a parity failure, regression, or no-signal result as experiment
   evidence and exclude its code from performance integration.

Hosted GitHub runners are appropriate for paired screening. Their heterogeneous
hardware and cache state do not support hard release thresholds until repeated
measurements establish variance. Stable-runner and cluster/shared-filesystem
qualification are higher evidence rungs, not substitutes for local correctness.

## Required measurements

Where the platform exposes them, retained summaries record:

- wall and CPU time;
- peak resident memory;
- input and output blocks or bytes;
- peak scratch and final output size;
- process, task, and subprocess count;
- dataset/profile and scaling dimensions;
- tool, package, runtime, runner, and cache-state identity;
- baseline and candidate SHAs;
- parity method and result; and
- the evidence ceiling.

The full 100k E2E is an integration/correctness screen. Focused retained cases
attribute a result to one owner or cross-cutting boundary. Existing successful
100k runs are reused and are not repeated merely to reproduce pass/fail.

The initial `sample-stages` case reuses the exact verified 100k Step 01 BAM to
exercise Step 02's canonical hard-link/index/publication path. Retained-evidence
admission necessarily hash-verifies and therefore warms the BAM; per-trial setup
adds only metadata-identity checks. Paired producer wall and CPU time are the
primary signal, and hosted block counters must not be interpreted as cold-I/O
evidence. Exact BAM/BAI identities plus an indexed query form parity; the
trial-owned large outputs are unlinked after validation while the compact
fingerprint, validation report, logs, and phase-resource evidence are retained.

The `step06-mechanical-orientation` case reuses the exact verified 100k Step 05
BAM/BAI and compares each archived Step 06 owner with the exact verified Step 06
five-output reference for `control_pair_01`. Admission hash-verifies the retained
input and reference publications before timing, so this is a warm-cache screen;
per-trial setup performs metadata-identity checks and creates only the
EMRYS-shaped result directories. Paired producer wall and CPU time remain the
primary hosted-run signals, and hosted block counters do not establish cold-I/O
or shared-filesystem behavior.

Outside the timer, the case requires the current mechanical-orientation validator
and all-pass gate, samtools quickcheck, reconciled idxstats, indexed traversal,
exact counts-TSV bytes, narrowly canonicalized headers, and decoded SAM records
in exact retained order. An independent oracle recomputes the four flag-group,
orientation, assigned, and unassigned counts from the retained Step 05 records.
Only admitted run-root and run-token substrings may be normalized. The compact
parity bundle is retained and the trial BAM/BAI publications are removed. Its
evidence ceiling is paired, real-tool, single-node synthetic 100k performance and
semantic artifact parity; it is not cold-cache, shared-storage, cluster,
production-scale, scientific-review, or biological evidence.

The `step04-duplicate-marking` case similarly times only the archived Picard
owner for the exact verified 100k Step 02 pair and admitted Java, Picard,
samtools, Bash, and SHA-256 authorities. Admission warms the exact Step 02 and
Step 04 publications; per-trial setup is metadata-only. Outside the timer, the
current duplicate-marking validator and all-pass gate are followed by decoded
BAM/header/index parity, exact Picard metrics body and histogram parity, and an
independent Step 02-to-04 duplicate-bit, PG-tag, and metrics reconciliation.
Only the stage-owned command path, run-token, timestamp, TMPDIR, and index-policy
metadata are normalized. Large trial publications are removed and residue is
rejected. The evidence ceiling is paired real-tool, single-node synthetic 100k
warm-cache performance and semantic parity, not raw BAI byte identity,
cold-cache, shared-storage, cluster, production-scale, scientific-review, or
biological evidence.

## Proven scaling defects

### Bounded signature checks are not bounded

The BAM/BAI helpers request four bytes but currently call a whole-file reader,
making a constant-size signature check `O(B)` in both I/O and memory. The target
is a no-follow, descriptor-bound fixed-prefix read that preserves exact
short-file, replacement, and mutation rejection.

### Immutable artifacts are repeatedly reproved

The task boundary hashes declared inputs multiple times and produced outputs
multiple times. Native owners frequently add before/after hashes of the same
objects. The target is one authoritative digest when bytes enter or are
produced within an admitted lifecycle, followed by cheap descriptor/path
identity checks while the object remains under that lifecycle. Rehashing
remains mandatory when authority is absent or identity changes.

The transition must reject replacement, retargeting, truncation, same-mtime
mutation, incomplete writes, and recovery ambiguity. A path/mtime cache is not
an acceptable substitute for content identity.

### Partition proof currently scales with the complete cohort

Each Step 07 partition declares and rehashes the full cohort BAM/BAI roster.
The proof layer therefore tends toward `O(PB)` even though bcftools uses indexed
regional access. The target is one admitted cohort identity plus per-partition
metadata and accessed-work validation, approximately `O(B + P*S)` outside the
scientific indexed reads.

### Shared reference work scales per sample

The complete STAR index and other shared reference artifacts are repeatedly
hashed and loaded per sample. Qualified immutable reference identity should
change proof overhead from `O(SG)` to `O(G + S)`. Co-located work may then test
safe shared loading, node-local staging, and decompression amortization.

### Some validation contains quadratic membership work

Reference-contig duplicate detection uses a linear membership scan for each
contig. A set-backed membership owner can preserve order and diagnostics while
changing that check from quadratic to linear in contig count.

The retained `reference-contig-membership` identity case compares exact
`origin/master` and `HEAD` source archives at 1,000, 4,000, and 16,000
fixed-width one-base contigs. Setup is outside producer timing; one warmup and
four balanced measured repetitions include parsing and canonical-result
publication. An independent formula validates every ordered name and length
plus the exact count before parity is accepted. A direct equality/hash-operation
oracle remains part of the implementation acceptance boundary so heterogeneous
hosted-runner timing is not the sole complexity proof. These measurements are
synthetic hosted-runner identity evidence, not representative reference,
full-E2E, cluster, production, scientific-review, or biological evidence.

### Step 08 and strict table validation materialize complete datasets

Step 08 validates, parses, expands, aggregates, writes, and in some paths
rereads complete VCF/table objects. The strict Python TSV reader retains raw
bytes, decoded text, raw rows, and dictionary rows. The target is deterministic
bounded chunks and only the explicitly necessary global state. Output volume
may remain `O(C*S)` while working memory becomes chunk-bounded.

### Compatible analyses repeat invariant upstream work

The broader reuse target remains owned by `ANALYSIS-01`: content-bound Steps
00–06 artifacts are produced once, then separately identified analyses rerun
only cohort-dependent work. Performance evidence should vary `A` and establish
the amortized benefit without creating a second reuse authority.

## Stage and systems opportunity inventory

### Measurement and attribution

- Extend retained cases across Steps 02–09 and task-boundary/inspection paths.
- Add machine-readable full-E2E timing and available scheduler accounting.
- Record bytes/passes and peak scratch, not wall time alone.
- Keep null comparisons as harness validation.
- Separate direct-owner timing from orchestration, resume, reporting, and
  end-to-end measurements.

### Steps 01–03

- Admit and hash the STAR index once; coordinate compatibility with
  `FUT-INDEX-01`.
- Test safe node-local or shared-memory STAR loading for co-located samples.
- Sweep parallel FASTQ decompression against STAR threads without
  oversubscription.
- Consolidate Step 02 count, read-group, canonicality, and validation scans.
- Stream the noncanonical Step 02 transformation path to avoid an unnecessary
  compressed intermediate.
- Determine whether RSeQC cost is read-depth or annotation-startup bound before
  changing its execution shape.

### Steps 04–05

- Reuse valid current-attempt Picard/GATK sidecar indexes with fail-closed
  fallback to samtools.
- Eliminate redundant publication scans only when staging and final paths are
  proven to be the same admitted inode.
- Measure JVM heap, spill, and scratch envelopes before applying resource
  profiles.
- Compare node-local and project-storage scratch without moving final
  publication off its required filesystem.

Stage removal and scientifically different duplicate-marking implementations
remain excluded.

### Step 06

The current owner performs four full flag filters, two merges, multiple count
scans, two indexes, repeated hashes, and four flag-specific temporary BAMs.

The intended end state is one compiled htslib-backed dispatcher that:

- decodes each alignment once;
- applies the exact accepted flag-mask membership;
- routes records directly to FWD-like or REV-like output;
- accumulates component and aggregate counts during routing;
- preserves header, read-group, coordinate order, and failure behavior; and
- indexes the two final outputs using measured resources.

The accepted runtime currently has no htslib language binding and samtools does
not provide multi-output flag routing. A pure text/FIFO workaround is not an
accepted substitute. Dependency/tool ownership must be explicitly selected
before this implementation proceeds.

The retained 100k Step 06 case supplies the first attributable screening rung
for existing materialized-count and publication candidates and future owner
implementations. Its decoded parity boundary does not settle the dispatcher
dependency, production-scale qualification, or scientific-equivalence campaign.

### Step 07

- Remove full-cohort proof amplification through the accepted artifact-identity
  boundary.
- Retain indexed scientific access and exact sample/partition identity.
- Estimate partition work from accepted BAM-index/read-density evidence rather
  than equal base count alone when it improves skew.
- Test dynamic partition scheduling and explicit storage-reader budgets.
- Test FWD/REV execution concurrently with explicit core and memory ownership.
- Evaluate BCF/bgzip only as a versioned representation experiment.

### Step 08

- Combine lexical/header/count validation and extraction into one streaming
  pass.
- Process deterministic bounded VCF chunks, including the one-large-VCF case.
- Have workers publish ordered fragments and return counts/hashes rather than
  complete data frames.
- Preserve manifest order independently of completion order.
- Cache the compiled annotation interval model by exact GTF, runtime/package,
  schema, and policy identity.
- Stream independent TSV validation while retaining only required global
  counters and identities.
- Test dynamic scheduling on skewed and uniform inputs separately.

### Step 09

- Vectorize deterministic coverage, frequency, eligibility, and background
  calculations.
- Evaluate only eligible target candidates with the expensive CMH kernel.
- Test deterministic chunking and a batched exact implementation against the
  independent numerical oracle.
- Preserve the global BH family, candidate universe, numeric behavior, order,
  and selected candidates.
- Reduce working memory to chunks plus the minimum global p-value/identity
  state, using an external deterministic pass if required.

No alternative statistic or multiple-testing policy may enter through the
performance campaign.

### Orchestration, resume, reporting, and logs

- Share one deep artifact validation within an inspect operation rather than
  repeating it through task and ledger views.
- Make ordinary resume proportional to admitted records/metadata while keeping
  an explicit deep-scrub path.
- Reuse one immutable admitted artifact snapshot across downstream reporting
  transactions instead of recursively reconstructing it.
- Stream subprocess stdout/stderr to durable logs with incremental hashing,
  bounded memory, and backpressure.
- Preserve cancellation, failure, receipt-last, fsync, and forensic ordering.

### Resource scheduling and storage

- Derive per-stage CPU, RSS, thread, process, JVM, and scratch envelopes.
- Replace serial defaults and whole-workflow memory reservations only after
  those envelopes exist.
- Model shared-storage bandwidth and maximum simultaneous readers as resources.
- Separate internal tool threads from independent-job concurrency.
- Test sample, partition, and orientation fan-out before cross-node work.
- Batch many small tasks or reuse compatible workers only when task isolation,
  attribution, cleanup, and failure semantics remain exact.

### Formats, retention, and cross-run reuse

- Compare BCF/bgzip, columnar internal tables, compression levels, and other
  representations using decoded semantic parity and explicit export contracts.
- Mark intermediates as durable/reusable or ephemeral; delete only after the
  accepted downstream and recovery boundary proves them unnecessary.
- Evaluate content-addressed reuse with hierarchical keys over scientific
  inputs/policy, runtime/tools, source/package identity, and relevant execution
  contract.
- Keep cache authority subordinate to the accepted artifact lifecycle and
  `ANALYSIS-01`; no competing identity system may emerge.

## Benchmark matrix

Minimum representative axes include:

| Concern | Required shapes |
|---|---|
| Artifact traversal | 10 MB, 100 MB, 1 GB+; warm and cold where controllable |
| Reads | 100k, 1m, 5m or 10m+ pairs |
| Samples | 1, 4, 16, and a larger cohort where feasible |
| Partitions | 1, 8, 32; sparse/dense; uniform and heavy skew |
| Candidates | 10k, 100k, 1m; samples and ALT multiplicity varied independently |
| Annotation | small synthetic and representative full annotation |
| Scheduling | workers/threads/processes varied independently; many-small and one-large jobs |
| Failure | mutation, replacement, malformed data, partial output, rollback, cancellation, and resume |

Exact byte parity is required where serialization is part of the contract.
When compression, native writers, or internal representation legitimately
change bytes, the card must name a stronger decoded semantic oracle plus exact
schema, ordering, identity, evidence, and failure requirements.

## Existing experiment inventory

The current-master rebuild produced nine isolated candidates:

| Candidate | Intended effect | Current disposition rule |
|---|---|---|
| Step 02 publication fast path | Avoid duplicate final-path scans under proven inode identity | Admit only after focused large-BAM evidence |
| Step 04 native index | Reuse a valid Picard-produced index | Admit only with real-runtime producer and fallback proof |
| Step 05 native index | Reuse a valid GATK-produced index | Reconcile with Step 05 publication fast path |
| Step 05 publication fast path | Avoid duplicate final-path scans | Reconcile with native-index candidate |
| Step 06 materialized counts | Avoid four full-input count scans | Interim only; a one-pass dispatcher supersedes it |
| Step 06 publication fast path | Avoid duplicate final-path checks | Fold into the eventual one-pass owner if that owner is accepted |
| Step 07 publication rescans | Remove one cohort hash pass and final VCF rescans | Partial solution; require retained partition evidence |
| Step 08 dynamic scheduling | Reduce skew stragglers | Skew must improve without material uniform regression |
| Step 08 output rereads | Avoid rereading just-written TSVs | Require retained large-table evidence |

Existing successful 100k runs establish synthetic end-to-end correctness for
their exact commits. They did not publish attributable stage resource metrics
and therefore do not, by themselves, establish a performance win.

The older draft PR chain `#16` → `#17` → `#19` → `#20` → `#21` is obsolete.
It depends on the closed/unmerged `#15`, whose resource-policy capability later
landed independently. The chain must not be merged or replayed wholesale; only
corrected current-master isolated commits may be considered.

## Routing and deduplication

- `SETUP-02` owns the user-facing portable advisory benchmark; `PERF-02` owns
  internal CI measurement.
- `PERF-01` remains the later cross-node experiment after resource modeling.
- `FUT-INDEX-01` owns compatible prebuilt STAR-index admission.
- `ANALYSIS-01` owns Steps 00–06 reuse across analyses.
- `ARCH-01` and `AC-SLICE-06/07/17` own broader policy, artifact lifecycle, and
  retirement architecture.
- `AC-SLICE-09` owns public inspect/explain UX, not engineering telemetry.
- `AC-SLICE-15/16` own scientific review and numerical oracles; performance
  cards consume but do not close them.
- `LOG-05` owns role-facing logging; bounded subprocess memory is separate.

## Retirement condition

Retire this campaign and its provisional matrix only after every durable
hypothesis, invariant, risk, benchmark requirement, and accepted end state has
either moved to an accepted findings-matrix item and its subject owner or
received an explicit discard disposition. Experiment chronology and routine
timings remain in Git and retained CI artifacts rather than becoming permanent
architecture prose.
