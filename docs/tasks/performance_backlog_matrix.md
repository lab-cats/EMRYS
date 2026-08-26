# EMRYS performance campaign matrix

> **PROVISIONAL CAMPAIGN RANKING — NOT AN IMPLEMENTATION BACKLOG**

Last ranked: **2026-08-25**

This is a scoped planning view of the candidate cards in the
[performance campaign](performance_campaign.md). The
[findings matrix](backlog_matrix.md) remains the sole durable owner of accepted
tasks, implementation status, outcomes, acceptance, and dispositions.

The scores support just-in-time experiment selection. They do not establish a
fixed sequence, authorize a dependency or format, or turn a timing into
acceptance. Every score must be reconsidered when its candidate is bounded.

## Scoring

All scores use `5` as the highest value.

### Importance

| Score | Meaning |
|---:|---|
| `5` | Systemic scaling defect, measurement prerequisite, or major stage bottleneck |
| `4` | Major recurring time, space, I/O, or utilization opportunity |
| `3` | Meaningful follow-on or workload-specific opportunity |
| `2` | Useful localized improvement |
| `1` | Retained exploratory companion outside current integration scope |

### Complexity

| Score | Meaning |
|---:|---|
| `5` | Cross-cutting lifecycle, cache, format, scheduler, or scientific-kernel implementation |
| `4` | Multi-owner behavior with demanding integration evidence |
| `3` | Bounded multi-module implementation and retained benchmark |
| `2` | Localized implementation or measurement extension |
| `1` | Straightforward local correction |

### Correctness/evidence risk

| Score | Meaning |
|---:|---|
| `5` | Artifact authority, recovery, cache, format, or numerical implementation requiring adversarial or independent proof |
| `4` | Multi-owner concurrency or exact artifact-contract change |
| `3` | Resource/process behavior needing integration evidence |
| `2` | Localized validation or I/O behavior |
| `1` | Measurement-only change with unchanged outputs |

The three scores are independent and are not multiplied into a composite.

## Campaign-card matrix

| Card | Track | Importance | Complexity | Risk | Scaling target | Benchmark | Parity | Main routing |
|---|---|---:|---:|---:|---|---|---|---|
| `PC-PERF-02` | Measurement | `5` | `3` | `1` | Make stage, task-boundary, and full-E2E cost inspectable | Null; Steps 02–09; 100k E2E; independent read/sample/partition/candidate axes | Existing outputs unchanged; schema-versioned measurement only | `PERF-02` |
| `PC-PERF-03` | Validation | `5` | `1` | `2` | `O(B)` BAM/BAI signature read to `O(1)` | Increasing sparse and real file sizes; bytes read and RSS | Exact acceptance, rejection, race handling, and diagnostics | `PERF-03` |
| `PC-PERF-04` | Reference | `2` | `1` | `2` | Quadratic contig membership to linear | Increasing contig counts | Exact order, duplicate identity, and diagnostics | `PERF-04` |
| `PC-PERF-05` | Artifact identity | `5` | `5` | `5` | Repeated full-byte proof to one admitted digest/identity | Artifact count/size; cold/warm; replacement, retarget, truncation, and mutation | Exact receipts, identities, mutation rejection, recovery | `PERF-05`; coordinate `ARCH-01`, `AC-SLICE-07` |
| `PC-PERF-06` | Step 06 | `5` | `4` | `5` | Many BAM passes and temporary subsets to one routing pass | Retained exact 100k owner comparison; future 1m/10m wall/RSS/I/O/peak-scratch qualification | Headers, records, flags, order, counts, indexes, downstream Step 07 | `PERF-06` |
| `PC-PERF-07` | Step 02 | `4` | `3` | `4` | Consolidate canonicality/RG/count/validation scans | Canonical and noncanonical BAMs by size | Exact BAM/BAI/RG/count/validation behavior | `PERF-07` |
| `PC-PERF-08` | Steps 04–05 | `4` | `3` | `4` | Reuse producer sidecar indexes | Existing/missing/stale/mismatched Picard/GATK sidecars | Exact sidecar admission, fallback, and downstream artifacts | `PERF-08` |
| `PC-PERF-09` | Step 07 | `5` | `4` | `4` | Remove `P*B` proof amplification and skew stragglers | `S=1/4/16`, `P=1/8/32`, uniform/skewed, concurrency | Exact VCF/evidence ordering, attribution, and failures | `PERF-09`; depends on `PERF-05` identity boundary |
| `PC-PERF-10` | Step 08 | `5` | `5` | `5` | Full expansion/materialization to bounded deterministic chunks | `C=10k/100k/1m`, samples, ALT multiplicity, one-large/many-file | Exact tables, order, hashes, malformed-input behavior | `PERF-10` |
| `PC-PERF-11` | Annotation | `3` | `3` | `4` | Rebuild annotation model per analysis to compatible reuse | Repeated analyses over representative full GTF | Exact annotations; invalidation on GTF/runtime/policy/schema | `PERF-11` |
| `PC-PERF-12` | Validation | `4` | `3` | `4` | Redundant full-table copies to streaming/global minimum | Wide/long Step 08–09 tables and malformed positions | Exact validity, global checks, and actionable diagnostics | `PERF-12` |
| `PC-PERF-13` | Step 09 | `4` | `5` | `5` | Per-row R allocation to exact batched/chunked kernel | 10k/100k/1m candidates; varied replicates | Independent oracle; exact family/order/selections; accepted numeric tolerance | `PERF-13`; coordinate `AC-SLICE-16` |
| `PC-PERF-14` | Formats | `3` | `4` | `5` | Reduce bytes and parse cost | VCF/BCF, TSV/columnar, BAM/CRAM, compression levels | Decoded semantic identity plus export/evidence/recovery contract | `PERF-14` |
| `PC-PERF-15` | Scheduling | `4` | `4` | `4` | Serial/whole-workflow reservations to measured stage resources | Threads/processes/RSS; local and Slurm-shaped workloads | Exact artifacts, receipts, failures, ceilings | `PERF-15`; `PERF-01` remains cross-node |
| `PC-PERF-16` | Storage | `4` | `5` | `5` | Reduce shared I/O and retained ephemeral space | Shared versus local scratch; injected failure/recovery | No premature deletion; exact publication/recovery/evidence | `PERF-16`; coordinate `AC-SLICE-07/17` |
| `PC-PERF-17` | STAR/input | `4` | `3` | `3` | Amortize index loading and decompression | Samples per node; serial/shared index; decompression threads | Exact STAR scientific outputs and safe lifecycle | `PERF-17`; index admission remains `FUT-INDEX-01` |
| `PC-PERF-18` | Startup | `3` | `4` | `4` | Reduce process/interpreter/JVM/scheduler startup across `J` | Many small tasks; persistent workers; batching | Exact attribution, isolation, cleanup, and results | `PERF-18` |
| `PC-PERF-19` | Logs | `3` | `2` | `3` | Unbounded captured streams to bounded streaming | Large output, slow consumer, failure, cancellation | Complete ordered forensic evidence and lifecycle behavior | `PERF-19`; role-facing adoption remains `LOG-05` |
| `PC-PERF-20` | Reuse | `4` | `5` | `5` | Avoid compatible repeated computation/I/O | Repeated runs/analyses; corruption, mutation, policy changes | Exact cache-key authority, provenance, invalidation, recovery | `PERF-20`; coordinate `ANALYSIS-01`, `ARCH-01`, `AC-SLICE-07` |
| `PC-PERF-21` | Integration | `5` | `3` | `3` | Admit only proven improvements without cross-stage regression | Affected retained matrix and 100k E2E after each admitted win | Aggregate parity, logical commit attribution, honest evidence ceiling | `PERF-21` |

## Interpretation

- `PC-PERF-02` is the enabling measurement surface, not a user-facing setup
  benchmark and not a performance result by itself.
- `PC-PERF-05` is intentionally separate from cross-run content-addressed
  reuse. Proving one artifact once inside an admitted lifecycle should not
  silently settle the final Artifact Store or cache architecture.
- `PC-PERF-06`, `10`, and `13` are high-value but require stronger parity than
  ordinary refactors because they replace computational implementations.
- `PC-PERF-21` is the integration vehicle, never a competing status registry.
- Cross-node work remains deferred until per-job resources and single-node
  storage behavior are understood; distributing waste is not optimization.
