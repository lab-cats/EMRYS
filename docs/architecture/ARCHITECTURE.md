# Current architecture

This map explains how EMRYS turns a scientific Analysis into an immutable Run
and inspectable Results. The [stage map](../../src/emrys/contracts/STAGE_MAP.md)
defines scientific steps and their dependencies; [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md)
defines permitted imports. Each implementation's contract defines its exact
interface and failure behavior.

## Public application model

```text
Project -> Analysis -> Run -> Results
                         |
                         +-- Attempt(s), when operationally relevant
```

A Project supplies one shared Dataset and Reference plus one or more named
Analyses. EMRYS validates the selected Analysis and records its execution plan
as an immutable Run. A changed plan creates a new Run; retrying an unchanged
plan creates another Attempt. Results is the read-only home of completed
scientist-facing outputs and reports.

The Project root owns `project.yaml`, `runs/`, `logs/`, and `runtime/`.
Execution profiles live beneath `runtime/profiles/`; the checked runtime
inventory lives at `runtime/runtime.tsv`. EMRYS generates the lower-level
records and workflow settings. Scientists do not have to author or transfer
those implementation details.

The deterministic two-word Run name is used for ordinary selection and display.
The content-derived Run ID remains authoritative and appears in advanced views.
Reporting runs automatically after a successful full scientific Attempt unless
disabled, and can be requested independently. It is not a scientific stage
and changes neither Run nor Attempt identity.

## Responsibility boundaries

| Responsibility | Current owner | Boundary |
|---|---|---|
| Interaction | Installed `emrys` CLI | Composes supported capabilities; contains no scientific semantics. |
| Project and Run coordination | `src/emrys/orchestration/run_coordinator/` | Admits Project intent, binds immutable Runs, selects placement, materializes Attempts, derives status, and invokes reporting. It does not own science or report rendering. |
| Scientific transformations and analyses | `src/emrys/stages/`, `src/emrys/analyses/` | Own algorithms, declared inputs/outputs, native validation, publication, and recovery behavior. |
| Operational evidence | `src/emrys/evidence/` | Observes runtime, reference, storage, QC, and orientation facts without promoting their meaning. |
| Results and reporting | `src/emrys/reporting/` plus selected reporter | Indexes admitted artifacts, builds the canonical summary, and publishes one bespoke scientific view plus the fixed evidence/operations view. It never reruns science. |
| Neutral records and primitives | `src/emrys/contracts/`, `src/emrys/libraries/` | Provide versioned schemas, identity facts, validation, and narrowly proven shared mechanics. |
| Scheduling and placement | `workflow/`, Snakemake, and the private whole-Run Slurm transport | Schedule the admitted graph and expose attributable execution facts; they are not scientific, completion, or recovery authority. |

Source imports, runtime/control invocation, and artifact/evidence flow are
separate dependency graphs. A permitted relationship in one does not grant a
relationship in another. Public owners exchange declared records and artifacts,
not peer-private implementation.

## Scientist-facing workflow

The built-in paired-CMH path groups fourteen scientific owners into nine phases.
Historical step numbers do not express the complete dependency order. The
[`current_user_pipeline.mmd`](diagrams/current_user_pipeline.mmd) diagram is a
non-authoritative visual projection.

| Phase | Purpose | Main output |
|---|---|---|
| Prepare reference | Build the STAR index, BED12 annotation, and FASTA sidecars. | Admitted index and reference-derived files. |
| Align reads | Align each declared paired library. | Coordinate-sorted STAR BAM. |
| Canonicalize | Sort, index, and attach stable read groups. | Canonical BAM/BAI boundary. |
| Inspect alignment evidence | Collect non-gating BAM QC and mechanical orientation evidence. | QC and orientation reports. |
| Prepare read evidence | Mark duplicates, split N-cigar reads, and partition by mechanical orientation. | Analysis-ready BAM/BAI pairs. |
| Observe cohort | Count bases for every declared sample, partition, and orientation. | Partitioned multi-sample VCFs. |
| Normalize candidates | Validate, expand, filter, and annotate the declared VCF set. | Deterministic candidate and QC tables. |
| Analyze | Run the selected module; the built-in module performs paired CMH ranking. | Module-declared final scientific Results. |
| Add scientific context | Optionally run the module's Step 10; the built-in path projects sequence and PUM-motif context. | Context and motif tables. |

Compatible Steps 00–06 processing may be completed once and referenced by a
separate downstream Run whose selected samples are an exact subset and whose
processing semantics and Reference remain compatible. Source artifacts stay in
place and are re-admitted by content; they are not copied into an Artifact
Store.

An installed collaborator module may declare closed configuration, typed
inputs and outputs, dependencies, minimum threads and memory, one Step 09 task,
and optional Step 10. It uses the existing dispatch, validation, publication,
recovery, logging, and Results authorities. Its separately selected reporter
owns bespoke scientific presentation. There is no universal Stage hierarchy,
workflow language, report DSL, installer DSL, or mutable plugin registry.

## Execution, lifecycle, and evidence

Planning does not write anything. Interactive execution shows the immutable
plan and asks before starting; automation uses `--execute`. Direct and
single-node Slurm execution use the same Snakemake workflow. Slurm only places
the whole Run on a compute node.

Each task records its start, runs its scientific owner, validates the outputs,
and records completion only after every required check passes. The Run
lifecycle owns locking, immutable Attempts, failure and interruption records,
and resume between completed tasks. Inspection reads those records and the
owner evidence instead of guessing from timestamps, logs, scheduler state, or
Snakemake's private files.

After a successful full Attempt, reporting publishes views of the findings,
their input and validation evidence, and how execution proceeded. This evidence
does not replace scientific review or biological interpretation. The
[Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
defines exact lifecycle behavior; the [reporting owner](../../src/emrys/reporting/README.md)
defines report admission and publication.
