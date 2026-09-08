# EMRYS optimization campaign

Reduce pipeline and operator command wall time, peak and retained disk usage,
I/O, and memory while preserving scientific results, provenance, recovery, and
supported behavior.
Prefer eliminating repeated work and unnecessary allocations over adding
machinery or changing computational methods.

This document owns the optimization audit and proposed measurement approach.
The [backlog matrix](backlog_matrix.md) remains the only authority for accepted
work, status, and acceptance. Candidate numbers below are discussion references,
not backlog IDs or an execution sequence. Documenting a candidate does not
authorize implementation, benchmarking, cluster execution, runtime changes,
artifact deletion, or adoption of an existing PR. Select each bounded outcome
through the [workflow kernel](../operations/WORKFLOW.md).

## Audit basis and evidence limits

The read-only audit examined GitHub master
[`fdf76760311e6c8076320a289ef3956d754c190d`][audit-tree] on 2026-09-07.
It covered processing, analysis, validation, orchestration, reporting, resource
configuration, and retention. Source citations below are pinned to that revision;
recheck the relevant production path and adjacent owners before selecting work.
Open-PR observations are also an audit-time snapshot.

The second read-only pass used the same source revision and added candidates
11–13 for inspection, source attribution, and runtime startup. It reconciled
the existing campaigns and overlapping work without running new experiments.
These additions identify costs to measure, not established redundant defenses
or completed optimization designs.

No new tests, benchmarks, cluster jobs, or production-artifact inventory ran in
the audit. Static repetition and allocation findings establish mechanisms, not
speedup percentages or reclaimed GiB. Historical fixtures and site observations
do not establish current whole-Run performance. Existing benchmark results are
qualified separately below.

The four objectives can conflict. More concurrency can shorten wall time while
raising peak memory and storage contention. Smaller heaps can increase spill
I/O. Compression can reduce storage while increasing CPU time. Moving scratch
can relieve shared storage without reducing total bytes written. Select an
explicit primary objective and acceptable tradeoffs for each experiment.

## Candidate observations

The order is an initial value-and-risk assessment, not a dependency graph.
Reference streaming and Step 06 count consolidation are the recommended first
implementation proposals; execution-profile tuning is the first measurement
proposal. Step 08 retention and Step 07 hashing merit larger investigations.

| Discussion | Candidate | Primary opportunity | Initial behavior classification |
|---|---|---|---|
| 1 | Consolidate Step 06 scans and subgroup materialization | Wall time, logical I/O; temporary disk in a later slice | Preserve count and partition semantics; direct-output replacement remains undecided until parity is demonstrated. |
| 2 | Stream reference observation and FASTA parsing | Memory | Preserve input acceptance, hashes, sizes, and mutation detection. |
| 3 | Tune existing resource profiles | Wall time and allocation efficiency | Environment-deferred; measure on the selected allocation and storage. |
| 4 | Produce or reuse native BAM indexes | Wall time and I/O | Preserve indexed retrieval, validation, and publication. |
| 5 | Bound Step 08 retained candidate tables | Memory; potentially wall time | Preserve candidate construction, order, counts, and serialized outputs. |
| 6 | Reduce repeated whole-cohort hashing around Step 07 | Wall time and read I/O | Guarantee decision remains undecided across distinct mutation boundaries. |
| 7 | Bind JVM heaps to admitted stage budgets | Memory and execution reliability | Environment-deferred; preserve successful processing and failure semantics. |
| 8 | Use qualified fast scratch for GATK spill | Shared-storage I/O and wall time | Environment-deferred; preserve capacity and recovery protections. |
| 9 | Reduce Step 09 validation allocations | Memory | Preserve AF validation, pairing, global BH correction, and reconciliation. |
| 10 | Evaluate compressed retained VCFs and tables | Persistent disk; potentially physical I/O | Undecided representation contract, requiring complete consumer migration. |
| 11 | Measure inspection, resume, and report startup hashing | Operator command wall time and read I/O | Preserve content verification; reuse across mutation windows remains undecided. |
| 12 | Audit source attribution before task entry | Startup wall time, filesystem work, and subprocess overhead | Preserve package/commit attribution and distinct publication boundaries. |
| 13 | Measure R runtime-probe startup overhead | Readiness and execution-startup wall time | Preserve probe isolation and admitted dependency closure; execution changes need evidence. |

None of these resource costs alone establishes a scientific defect.

### 1. Consolidate Step 06 scans and subgroup materialization

[Count collection][step06-counts] performs five input BAM scans: one total and
four flag-mask counts. [Extraction and publication][step06-execution] perform
four more input extraction scans, write four subgroup BAMs, merge them into two
orientation BAMs, and index both. Output count scans and digest checks add work.

First evaluate collecting total and four mask counts in one streaming
observation while leaving extraction and merging intact. A separate proposal
can investigate producing the two final partitions without four materialized
subgroups, reducing their combined peak temporary footprint.

The [orientation contract][step06-contract] preserves permissive `-f` masks.
Do not replace them with exact flag equality or a naive union: unusual records
can satisfy multiple masks, and multiplicity matters. Preserve coordinate ties,
read-group/program-header handling, exact counts, input identity checks, indexed
outputs, and the five-file publication/recovery transaction. Benchmark full
producer and validator execution, including overlapping masks, secondary and
supplementary records, tied coordinates, empty groups, and publication failure.
Fewer traversals can still lose to additional parsing overhead.

### 2. Stream reference observation and FASTA parsing

[Reference observation][reference-observation] reads each entire reference/index
member into bytes to calculate SHA-256 and length. [FASTA parsing][fasta-parser]
also retains complete text and a split-line list despite an existing iterable
parser. Reuse existing streaming hash and parsing mechanisms to remove
file-sized transient allocations.

Preserve the [two reference observations][reference-rechecks]: the later one
detects changes during inspection. Preserve report bytes, file lengths, contig
ordering, symlink rejection, and malformed-input behavior. Measure a full-size
FASTA and STAR Genome file; do not extrapolate from tiny fixtures. This overlaps
whole-reference-read discovery 11 in the [compression intake][compression].
Any separately selected empty-header correction is a distinct behavior decision.

### 3. Tune existing resource profiles

The [default profile][default-profile] reserves the entire workflow memory for
every stage, preventing simultaneous tasks even when the DAG and CPU capacity
permit them. The [Viking example][viking-profile] requests 256 CPUs but permits
12 workflow cores. That is a configuration distinction, not measured CPU
utilization; a large node may have been selected for memory.

Measure concurrent samples versus threads per task, realistic per-stage memory
reservations, and Step 07 partition concurrency. Use existing profile controls
and admission constraints rather than another scheduler or tuning service.
Evaluate queue delay separately from execution time where site measurements
exist. More concurrency may increase actual memory, CPU use, and shared-storage
traffic. Lower reservations alone do not lower observed RSS. Apply revised
plans through the immutable Run contract; never edit an existing Run in place.

### 4. Produce or reuse native BAM indexes

[Step 04][step04-index] writes a BAM with Picard and subsequently rereads it
with `samtools index`. Evaluate index creation during native output writing,
using the [pinned runtime][runtime-pins]. Verify the emitted index name,
readability, count reconciliation, and indexed-region retrieval before retiring
the separate pass. Preserve metrics, staging, ownership, and atomic publication.

Step 05 native GATK index reuse and removal of redundant final no-clobber scans
already have an implementation proposal in [PR44][pr44]. Reconcile that exact
proposal with current master, recovery fixes, and representative measurements;
do not duplicate it or treat its fixture results as demonstrated speedup.
Step 04 and Step 05 remain separately bounded owner changes. Any Step 06
write-time indexing extension also needs verification against the pinned tools.

### 5. Bound Step 08 retained candidate tables

[VCF processing][step08-processing] materializes complete VCFs, expanded alleles,
DP/AD/AF matrices, and candidate tables. The parent retains worker results and
then [combines the cohort with `rbind`][step08-aggregation]. This exposes memory
amplification and copying, but their share of wall time is unmeasured.

Evaluate bounded batches or ordered worker fragments. An existing unmerged
prototype, commit `032572186`, must be reviewed before recreating that work;
it is not present in the audited master. Bound each proposal across the R
producer, Python admission, validator, and consumers so an earlier improvement
does not merely move the peak into validation. Preserve sample/partition/
orientation order, candidate uniqueness, allele/count checks, annotation,
exact TSV bytes, and transactional rollback. Measure candidates x samples x
workers with realistic partition skew and a full annotation, including any
extra temporary I/O introduced by fragments.

### 6. Reduce repeated whole-cohort hashing around Step 07

Every partition task [binds all cohort orientation BAMs and indexes][step07-inputs],
plus shared reference inputs. The task wrapper hashes inputs
[twice before production][task-entry] and [once afterward][task-exit]. For `P`
partitions and `B` bytes of common inputs, these observations alone request
approximately `3 * P * B` logical bytes: 75 complete shared-input traversals for
25 partitions. Producer, validator, output, and resume observations add work.
Cache hits mean this is not a claim of 75 physical disk reads.

First determine whether adjacent pre-entry observations can be consolidated
without opening their mutation window. Broader reuse across tasks requires an
equal-or-stronger demonstrated content-stability guarantee or a separately
approved guarantee change. A cached digest, read-only pathname, or size/mtime
comparison does not by itself enforce immutable bytes. Avoid introducing a
generic cache or Artifact Store to bypass this decision. Preserve input changes
detected before entry and during execution, and measure cold/warm behavior on
the actual storage class. Existing Step 07 aggregate input-identity reuse does
not eliminate these wrapper observations.

### 7. Bind JVM heaps to admitted stage budgets

The [Picard invocation][step04-index] supplies no explicit heap bound;
[GATK Java options][gatk-scratch] set temporary storage but not heap size.
Snakemake memory reservations are scheduling admission, not per-process heap
limits. No claim about the effective JVM maximum or observed RSS follows from
the absence of an explicit command-line setting.

Evaluate native heap limits derived from admitted budgets with headroom for
nonheap/native allocations. Measure representative concurrent jobs, spill
volume, garbage collection, peak memory, and task wall time. Smaller heaps may
increase disk traffic or fail otherwise successful processing. Keep resource
authority with the existing profile and owner command construction; avoid a
second independent resource policy.

### 8. Use qualified fast scratch for GATK spill

[Slurm already establishes private temporary storage][slurm-scratch], but
[Step 05][gatk-scratch] deliberately places GATK spill under the output directory
because CSU `/tmp` can be too small. Evaluate sufficiently large fast scratch
for disposable tool spill while keeping final-output staging and publication
on their required filesystem.

Preserve capacity qualification, headroom, ownership, interruption handling,
and recovery. Do not blindly redirect to `/tmp`; a memory-backed filesystem
can worsen memory pressure. Compare spill-heavy workloads on the intended
institutional storage. This can reduce shared-storage traffic and wall time
without reducing total bytes written or persistent output size. PR44 does not
implement this scratch-placement change.

### 9. Reduce Step 09 validation allocations

[R validation][step09-af] allocates and returns complete DP, AD, and AF matrices.
At the audited revision no production consumer reads `counts$af` afterward.
Validate each sample's AF vector and discard that vector rather than retaining
the dense AF matrix. Keep lexical, missingness, and AD/DP consistency checks
and preserve emitted AF columns. The matrix payload is `8 * candidates * samples`
bytes, or 128 MB for one million candidates and 16 samples; this is an allocation
opportunity, not a measured reduction in peak RSS.

A separate proposal can stream the [Python validator's][step09-validator]
upstream, all-sites, and significant-sites reconciliation instead of retaining
three wide row-dictionary tables. Keep the candidate IDs, counters, and p-value
state necessary for global checks. Existing streaming projections do not
include every upstream/BH check and cannot replace this validator unchanged.
Measure both proposals independently with exact output and rejection parity.

### 10. Evaluate compressed retained VCFs and tables

[Step 07 explicitly writes uncompressed VCF][step07-vcf], and downstream
candidate tables use plain TSV. Lossless compression may reduce retained
storage and physical I/O at the cost of CPU and a representation migration.
Evaluate a bounded VCF proposal before any broader format change.

This is not a drop-in output flag: exact filenames, receipt paths and hashes,
Python text readers, R admission, workflow declarations, validators, inventories,
reporting, and historical readers must be considered together. Preserve
scientific values and ordering and explicitly approve changed representation
and identity contracts. Do not keep parallel permanent formats by default, or
silently remove retained originals to obtain a favorable disk result.

### 11. Measure inspection, resume, and report startup hashing

[Run inspection][inspection-admission] admits every expected task, and
[verified-task admission][verified-reuse] hashes every recorded input and
output. The same task admission runs during
[Snakemake graph construction][workflow-reuse]; [resume][resume-inspection] and
[reporting][report-inspection] also invoke full inspection. Their latency can
therefore grow with scientific data volume and repeated shared inputs, beyond
the number of status records.
This operator command cost is distinct from candidate 6's producer-entry
observations, although measurements must avoid counting the same work twice.

Measure complete `emrys inspect`, resume planning, and report startup across
sample count, partitions, retained Attempts, and cold/warm storage. Identify
which files are read repeatedly within one invocation and whether those reads
guard different mutation windows. Investigate sharing an admitted observation
only where an existing owner can preserve equal-or-stronger change detection
and retire the duplicate work. Preserve current verified-state meaning,
historical admission, deterministic diagnostics, and recovery. Do not introduce
a persistent digest cache, second status registry, or silently weaker inspect
mode. Separating recorded status from fresh integrity verification would be a
distinct product decision. Reconcile active reporting-predecessor work before
selecting any report-startup slice.

### 12. Audit source attribution before task entry

The [normal task-entry path][task-source-entry] calls source attestation four
times before scientific production, including the call made while constructing
the task-start record. Each [attestation][source-attestation] performs two
working/package comparisons and a [Git-object comparison][source-object-check].
Together with its top-level and HEAD observations, this makes six Git
subprocess calls per successful attestation, or 24 per normal task entry, plus
repeated package-tree traversal and byte reads. These are source-derived call
counts, not measured startup time or evidence that the checks are redundant.

Measure task-start latency, Git invocations, and filesystem work on the selected
local or institutional storage. Map each observation to its exact trust and
publication boundary before proposing consolidation. The
[package comparison][source-package-check] also reads both sides when their
canonical roots are the same; determine whether that case can be simplified
without losing a currently detected change. Retire only equivalent work inside
the existing source-authority owner. Preserve executing-package bytes, exact
commit binding, changed HEAD/package detection, and task-start publication
checks. An immutable Run does not make its source filesystem immutable and
does not authorize caching across those boundaries. Related assurance work
remains in the [polish campaign](polish-campaign.md).

### 13. Measure R runtime-probe startup overhead

The [packaged runtime policy][runtime-probe-policy] declares ten R namespace
checks. [Probe dispatch][runtime-probe-dispatch] runs them sequentially, and
each [namespace check][runtime-namespace-probe] launches a separate `Rscript`.
One examination of that inventory therefore starts R ten times for namespace
checks in addition to its R-version probe; module dependencies can add checks.
This establishes process multiplicity, not how much of Doctor or execution
startup it consumes.

Measure the complete readiness path and separate interpreter startup,
namespace loading, and package-identity I/O. Compare bounded concurrency of
independent probes before considering a combined R process, which changes
fresh-process isolation and namespace load-order behavior. Preserve per-check
attribution, report order, deadlines, failure isolation, selected-library/root/
version checks, and read-only dependency state. Use the existing probe owner
and established process facilities; add no runtime service or probe framework.
Reconcile Doctor assembly and runtime-model work before selection. Existing
[`RUNTIME-CLOSURE-01`](backlog_matrix.md#reliability-and-qualification) owns the
recursive R dependency closure and automatic-snapshot policy; this performance
candidate must preserve that outcome rather than redefine its acceptance.

## Prior work and scope boundaries

- STAR/canonical BAM handling already avoids unnecessary sorting and uses
  hard-link reuse when admission permits it. Count distinct physical data,
  not two path sizes, when estimating savings from hard-linked files.
- [Processing reuse][processing-reuse] already avoids compatible upstream
  recomputation and copying. The pipeline already uses Snakemake inside one
  whole-Run Slurm allocation; neither is a new optimization proposal.
- [PR45][pr45] narrows Step 08 VCF field materialization. Retained
  [run 33090518708][pr45-run], head
  `195a78d1c2d7a25d2d66368d760b16b907d2e4df`, used the misleading reused artifact
  name `step08-fragments-1`; the run revision identifies the experiment.
  All recorded artifact comparisons matched. The million-candidate cases had
  only one baseline/candidate pair each: observed wall-time improvements were
  about 0.7% and 2.4%, with at most 5.4% RSS reduction. Smaller cases were mixed.
  These results did not establish its gate of 10% median wall improvement or
  15% peak-RSS reduction without material regression. Do not promote this
  proposal as a demonstrated optimization or confuse it with the fragment
  prototype in candidate 5.
- The standalone FASTQ helper's repeated scans are outside the normal DAG.
  Existing `OPS-03` first decides whether that helper remains useful. Its
  optimization cannot be counted as pipeline savings unless the measured
  operator journey actually includes it.
- `SETUP-02` owns portable advisory benchmarking; `FUT-INDEX-01` owns explicit
  prebuilt STAR-index admission; `PERF-01` retains the separate cross-node
  experiment. Refer to their current [backlog outcomes](backlog_matrix.md),
  rather than creating duplicate acceptance or status here.

[Verified-task reuse][verified-reuse] requires bound inputs and outputs to
remain present and hash-identical. Deleting consumed BAMs or VCFs, or marking
them automatically temporary, would break current resume verification. Initial
disk work should avoid producing redundant temporary data. Persistent-output
retention changes need their own explicit recovery and evidence decision.

Do not lower mpileup depth, change duplicate-marking methods, prefilter the CMH
population, split global BH correction by partition, drop annotations, or
reduce scientific-context coverage as neutral performance changes.

## Measurement and adoption

Use the existing [resource benchmark helper][benchmark-helper] where sufficient,
and established allocation/OS/storage accounting for missing measurements.
Avoid a parallel benchmark framework. The helper times its producer command;
its separately invoked validator is not included in that timing. Its child RSS
and filesystem block counters do not establish aggregate concurrent memory,
network-filesystem traffic, or peak allocated disk occupancy. Failed repetitions
must not disappear from a recommendation based only on successful rows.

For operator command candidates, time the complete public invocation and
attribute its admission, subprocess, hashing, and rendering costs separately;
a producer-only benchmark cannot establish inspection or readiness latency.

For each selected experiment, record:

| Dimension | Required observation |
|---|---|
| Identity | Exact baseline/candidate commits, input hashes, reference/annotation, tool versions, node, storage, and resource profiles. |
| Wall time | Complete task, whole-Run, or selected public-command elapsed time; distinguish producer, admission, validation, publication, rendering, and queue delay where applicable. |
| Memory | Individual process peaks and aggregate concurrent usage; distinguish reserved memory from consumption. |
| I/O | Logical traversal counts, physical bytes/operations, cache conditions, and storage/network counters appropriate to the filesystem. |
| Disk | Peak temporary occupancy and retained allocated bytes, accounting for hard links and comparing equivalent artifact sets. |
| Correctness | Exact bytes where the contract requires them, explicit semantic equivalence for approved representation changes, independent checks, and relevant failure/recovery cases. |
| Repeatability | Paired baseline/candidate trials with balanced order; retain every raw trial and failure. Use at least three pairs as a starting proposal and increase repetition when variability prevents a decision. |

Linux [cgroup accounting][cgroup-accounting] can provide aggregate memory and
local block-I/O observations where available; it does not replace appropriate
network-filesystem measurement. Do not flush shared system caches or alter site
configuration merely to manufacture a cold trial.

Before running, approve the primary metric, representative workload, material
improvement threshold, allowed regressions in other dimensions, and execution
authority. There is no universal speedup threshold for this campaign: PR45's
gate belongs to that experiment. A result is adoptable only when its improvement
is repeatable at the stated evidence level, correctness/recovery checks pass,
all repetitions are accounted for, and the complete implementation meets the
[architecture guardrails][guardrails]. Long checks belong in selected CI;
institutional storage or allocation claims require separately authorized site
evidence.

## Bounded delivery

Select one owner outcome at a time. Before implementation, recheck current
source, competing PRs, callers, consumers, contracts, tests, and duplicated
mechanics. Replace or retire superseded loops, allocations, scans, and paths
across the complete touched vertical. Reuse existing owners and mature tools.
Report product, tests/protections, configuration, documentation, and retained
evidence changes separately; unrelated deletion does not offset growth.

A selected outcome needs its own approved plan and acceptance in the existing
backlog or explicit bounded objective. Adopted outcomes and their contract
changes belong with their owners; exact benchmark evidence remains bound to
the tested revision. Refresh superseded observations here when needed, without
adding a progress ledger or duplicating backlog statuses.

[audit-tree]: https://github.com/lab-cats/EMRYS/tree/fdf76760311e6c8076320a289ef3956d754c190d
[step06-counts]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/mechanical_orientation/producer.py#L358-L387
[step06-execution]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/mechanical_orientation/producer.py#L406-L449
[step06-contract]: ../../src/emrys/stages/mechanical_orientation/CONTRACT.md
[reference-observation]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/evidence/reference_provenance/_reference_contigs.py#L20-L48
[fasta-parser]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/libraries/references/contigs.py#L18-L47
[reference-rechecks]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/evidence/reference_provenance/reconciler.py#L133-L163
[compression]: compression_campaign.md#discovery-findings-for-selection
[default-profile]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/resources/default_execution.yaml#L4-L41
[viking-profile]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/configs/execution_profile.csu_viking_ev_pum1.yaml
[step04-index]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh#L237-L259
[runtime-pins]: ../../src/emrys/resources/runtime/pixi.toml
[pr44]: https://github.com/lab-cats/EMRYS/pull/44
[step08-processing]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/cohort_candidate_preprocessing/_step_08_vcf_processing.R#L46-L179
[step08-aggregation]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R#L196-L239
[step07-inputs]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/materialization.py#L874-L946
[task-entry]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/task.py#L1838-L1864
[task-exit]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/task.py#L1967-L1977
[gatk-scratch]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh#L147-L169
[slurm-scratch]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/slurm_submission.py#L100-L125
[step09-af]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R#L227-L278
[step09-validator]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/analyses/paired_cmh_candidate_ranking/validator.py#L149-L279
[step07-vcf]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/stages/partitioned_cohort_mpileup/producer.py#L395-L418
[processing-reuse]: ../../src/emrys/orchestration/run_coordinator/CONTRACT.md
[pr45]: https://github.com/lab-cats/EMRYS/pull/45
[pr45-run]: https://github.com/lab-cats/EMRYS/actions/runs/33090518708
[verified-reuse]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/task.py#L1605-L1617
[inspection-admission]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/_inspection_evidence.py#L183-L215
[workflow-reuse]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/workflow/Snakefile#L485-L503
[resume-inspection]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/control.py#L286-L307
[report-inspection]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/reporting_operation.py#L298-L311
[task-source-entry]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/task.py#L1828-L1908
[source-attestation]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/libraries/source_authority.py#L531-L597
[source-object-check]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/libraries/source_authority.py#L297-L357
[source-package-check]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/libraries/source_authority.py#L449-L527
[runtime-probe-policy]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/resources/runtime/runtime_policy.tsv#L18-L27
[runtime-probe-dispatch]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/evidence/runtime_availability/_probes.py#L339-L387
[runtime-namespace-probe]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/evidence/runtime_availability/_probes.py#L153-L203
[benchmark-helper]: ../../scripts/benchmark_stage_resources.py
[cgroup-accounting]: https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
[guardrails]: ../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails
