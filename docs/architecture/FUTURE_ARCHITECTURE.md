# Future architecture

This document owns target-state topology and future constraints. It does not
describe the current flat repository as already migrated, authorize a task, or
track branch/test/runtime status. Current implementation truth remains in
[`ARCHITECTURE.md`](ARCHITECTURE.md); roadmap order remains in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); rationale remains
in the
[`approved architecture decisions`](../design/DECISIONS.md#approved-architecture-direction-2026-07-31).

Canonical future diagrams:

- [`diagrams/future_roadmap_sequence.mmd`](diagrams/future_roadmap_sequence.mmd)
- [`diagrams/future_modular_pipeline.mmd`](diagrams/future_modular_pipeline.mmd)
- [`diagrams/future_manifest_config_contracts.mmd`](diagrams/future_manifest_config_contracts.mmd)
- [`diagrams/future_reporting_layer.mmd`](diagrams/future_reporting_layer.mmd)

## Target qualities

- scientist-facing entry points with explicit versioned requests and contracts;
- semantic stages that are independently understandable and testable;
- typed, immutable inputs/outputs at every stage and analysis branch;
- deterministic identities, artifacts, validation records, reports, and
  publication receipts;
- concise default interaction plus complete durable diagnostic evidence;
- filesystem-inspectable run, attempt, scheduler, failure, and recovery state;
- independent local-fixture, real-runtime, cluster, scientific-review, and
  biological-interpretation evidence;
- extension seams that do not overclaim one universal DNA/RNA workflow;
- no implicit dependency installation, input discovery, cleanup, or repair.

## Target source and test topology

The approved conceptual target is:

```text
src/
└── norad/
    ├── cli/
    ├── orchestration/
    ├── scheduler/
    ├── contracts/
    ├── libraries/
    ├── evidence/
    ├── reporting/
    ├── ingestion/
    └── stages/
        └── <semantic-stage>/
            ├── README.md
            ├── stage implementation files
            ├── validator entry point or files
            ├── job template or files
            └── stage descriptor and local contracts

tests/
├── stages/<semantic-stage>/
├── cli/
├── orchestration/
├── scheduler/
├── contracts/
├── libraries/
├── evidence/
├── reporting/
├── ingestion/
├── <independent contract suites>/
└── <integration suites>/
```

This is a vertical package target, not a claim that every asset is Python.
Shell, R, scheduler, schema, style, template, and other runtime resources keep
their native form under an explicit owner. Packaging those resources is a later
distribution concern.

The named top-level domains and stage-local ownership are fixed. Exact
stage-descriptor filename/serialization, submodule filenames, schema placement,
and packaged-asset locations remain owned by the reviewed topology task; the
tree above is not a generated-files specification.

Stage-local contracts live with the stage. Cross-stage contracts, public
schemas, run identity, and shared state vocabularies live in neutral owners.
The test tree mirrors local ownership while independent contract and integration
suites remain separate enough to detect producer/consumer shared defects.

Reporting implementation belongs in `src/norad/reporting` because it is an
application domain, not a repository-level output directory. Current root
`reports/` assets remain current truth until an approved migration establishes
their final package/asset ownership. Ingestion implementation belongs in
`src/norad/ingestion`; configured operational inbox/run-state directories live
outside source code. A root `ingestion/` source directory is not the target.

## Stage identity, DAG, and black-box boundary

Every future stage has:

- a human display title;
- a public semantic slug;
- a stable versioned machine key;
- zero or more historical numeric aliases;
- declared typed inputs and outputs;
- explicit DAG predecessors and successors;
- a local README, validator, and focused tests.

Numeric identifiers remain useful provenance but do not define future ordering.
The execution DAG defines required sequence, parallel branches, and typed
analysis branch points. A separate concise user overview explains the general
scientific order and why it exists; the detailed technical diagram remains a
maintainer view.

A stage may depend on neutral contracts/libraries but never import another
stage's implementation. Orchestration navigates only declared DAG edges and
contracts. No stage discovers upstream data by glob, filename convention, or a
neighbor's private directory. Failures identify the stage, run, attempt,
contract, and next safe operator action without hiding filesystem state.

The exact identity map and DAG are intentionally unresolved until the live
functional inventory is reviewed.

## Direct migration model

The hybrid flat/packaged repository is temporary migration scaffolding, not an
end state. Each bounded migration:

1. refreshes applicable behavior and consumer characterization;
2. moves one concern directly to its final owner;
3. retains a temporary root wrapper only when needed for a known caller;
4. migrates imports, jobs, Make targets, tests, commands, and documentation;
5. compares old/new behavior and output contracts where feasible;
6. removes the wrapper after all named callers and parity gates pass.

There are no known external consumers that require an indefinite legacy-path
program. Migrations preserve behavior, scientific meaning, artifacts, evidence,
dry-run/execute, transaction, recovery, and exit contracts. An intentionally
changed interface/path is versioned or otherwise made explicit in the approved
task; it is not described as accidental compatibility.

## Intake, identity, attempts, and promotion

The target V1 operational intake will use one versioned YAML request that
references one versioned TSV sample manifest:

- YAML: run policy, explicit input/reference/partition identities, requested
  current analysis/report behavior, and output/state roots;
- TSV: repeated sample rows, explicit pairing/replicate/condition/order, and
  read paths.

V1 accepts local paired FASTQ or FASTQ.GZ reads plus registered FASTA/GTF
reference inputs. It does not acquire public data.

The ingestion boundary atomically claims one ready request before execution,
validates and resolves every declared input, hashes and normalizes an immutable
run contract, and creates an inspectable attempt. An identical normalized
contract identifies the same run; a retry creates a new attempt; changed input
or policy creates a new run. A failed request remains resumable with its failure
and recovery evidence.

Target V1 computational success will require the request's currently required
tasks, validators, evidence assembly, and requested report to complete. Only
then may request/run metadata be promoted to a completed/archive state. Raw
inputs do not move automatically. Current `data/raw` is a storage convention
for pre-staged data, not the future intake queue or state machine.

Exact YAML fields and operational directory names remain open. Future
required/optional analysis success and archival rules are deliberately separate
from the V1 design.

## Orchestration and filesystem-inspectable state

The orchestration layer owns DAG planning, declared contract resolution, run
and attempt state, scheduler submission/materialization, resume decisions, and
requested report coordination. It does not own scientific algorithms or install
dependencies.

Run state must remain inspectable from explicit files and directories even if a
future CLI is unavailable. At minimum, a maintainer must be able to locate:

- the immutable normalized request and referenced manifest;
- run and attempt identities;
- resolved stage inputs/outputs and contract versions;
- scheduler submission material and job IDs when applicable;
- concise status plus complete durable logs;
- locks, staging, receipts, failure, rollback, and recovery evidence;
- report profile requests and published report receipts.

State transitions use explicit validation-before-publication and never infer
success from file presence alone.

## Shared libraries and dependency direction

Code starts local. At a second use, compare complete semantics; promote at two
only for a safety-critical or sufficiently complex equivalent, otherwise
normally at the third equivalent use. Put shared code in the narrowest neutral
owner and require independent API and consumer tests.

`libraries` never depends on `stages`. Neutral contracts never import producers.
Cross-language repetition remains when it provides independent verification or
when a cross-language abstraction would obscure execution. There is no generic
`utils` package, universal transaction framework, or generic stage dispatcher
without separately reviewed evidence.

## Source-size and local-context constraints

Material changes above 600 lines trigger cohesion review; new files normally
stay below 600. Architectural work on a file above 1,000 lines requires a
decomposition plan or explicit justification. Files above 1,500 lines require
elimination during the active refactor or an explicit exception. These are
review thresholds, not instructions to split at arbitrary line boundaries.

Every mature stage/domain supplements the global
[`task-start router`](../operations/TASK_START.md) with local maintainer
context containing:

- purpose and scientific/operational boundary;
- file map and local ownership;
- typed input/output contracts;
- direct upstream/downstream interfaces;
- focused, independent, and integration test locations;
- safety, failure, recovery, and evidence cautions;
- links to canonical cross-cutting decisions and commands.

This context reduces routine repository-wide reading. Phase boundaries trigger
renewed ownership, interface, acceptance, and diff assessment. Cross-cutting
changes, contradictions, unknown revisions, and scientific, evidence, safety,
recovery, or public-contract uncertainty broaden inspection according to
impact; they do not impose an unrelated fixed corpus.

## Reporting target

Reporting exposes at least two versioned projections:

- science: the future default, containing the minimum evidence a scientist
  needs to understand the run and data;
- comprehensive: the retained full diagnostic report.

Exact public names and flags remain open until the current report is
characterized. The science field catalog begins with evidence state,
CMH-ranked findings, QC/filter funnel, sensitivity/replicate evidence,
decisions/limitations, and concise methods. Every field has a plain-language
title, description, authorized source, missing/failure behavior, and neutral
scientific language.

One versioned format-neutral view model feeds HTML and PDF so their semantic
content remains aligned. Layout may differ by medium. The science HTML view
does not place horizontal scrolling inside panels; wide information becomes
responsive records, summaries, or another reviewed accessible presentation.

Both profiles preserve explicit-input/table authorization, deterministic
serialization, no-clobber, stable-input rechecks, rollback, cleanup, and
receipt-last publication. Profile outputs coexist without overwriting existing
immutable bundles. Rendering remains a projection and never installs tools,
runs analysis, discovers inputs, or promotes evidence.

## Logging target

The future logging contract separates two audiences:

- console: concise, directly relevant default progress/result/failure output,
  with explicit verbose and debug modes;
- durable log: complete run/attempt-scoped resolved context, commands, tool/job
  information, diagnostics, and failure/recovery detail.

Machine-readable output uses stdout. Human-oriented logs use stderr. Scheduler
capture files and NORAD application logs have explicit distinct roles. A log
level changes presentation only; it cannot change artifacts, hashes, receipts,
evidence, validation, publication, rollback, cleanup, or exit behavior.

Exact public level names/flags, durable path layout, retention ownership, and
failure-tail policy remain open until current output is characterized. No log
retention rule authorizes automatic deletion.

## Analysis extension boundary

The long-term architecture supports multiple typed preprocessing profiles and
multiple typed analysis modules. It does not assume every DNA/RNA assay shares
one preprocessing trunk. A profile declares a DAG and produces typed artifacts;
an analysis module declares accepted artifact types, configuration, runtime
dependencies, outputs, validation, evidence limits, and report projections.

The current CMH analysis may become the first built-in module. A scientist-
authored R module is feasible only with explicit inputs/outputs, controlled
working/state paths, dependency declaration, deterministic identity,
validation, provenance, failure semantics, and no automatic evidence promotion.
Future trust may distinguish exploratory custom modules from registered modules.

No generic loader, registry, universal module schema, alternate assay, or
optional-analysis success state belongs in the current refactor. Current work
only preserves clean typed branch points.

## Public reference and read acquisition

Public acquisition remains future-only and follows this priority:

1. local paired FASTQ/FASTQ.GZ plus registered reference;
2. NCBI reference acquisition and registration;
3. SRA read acquisition/materialization;
4. later ENA, GEO, or BAM support if concrete use cases justify them.

Reference adapters handle accession/versioned FASTA/FNA sequences and
GTF/GFF3/GBFF annotations plus hashes/provenance. They never convert references
to FASTQ. Read adapters handle sequencing-read archives such as SRA and may
materialize validated FASTQ. The adapters remain separate because identity,
format, transfer, cache, retry, storage, and provenance semantics differ.

## Later installable control plane

After internal interfaces stabilize, an installable `norad` package may expose
a thin operational interface for validation, planning, run, status, resume,
reporting, and stage description. Command names are illustrative until a
separate public-interface design is approved.

The control plane coordinates contracts, DAG, scheduler, filesystem state, and
reports. It does not reimplement external compute tools or bootstrap R/system
dependencies. Packaging must explicitly include required non-Python assets.
Scheduler jobs are materialized as immutable, run-bound resolved copies before
submission so an installed package update cannot mutate an active run's job.

Versioning, wheel/build metadata, asset APIs, and public distribution are
deliberately deferred until the architecture and behavior contracts settle.

## Documentation and skill boundary

Target directories use concise `README.md` files where durable. Parent READMEs
explain child purpose but child READMEs own local detail. Opaque table, schema,
generated, lock, and byte-sensitive artifacts receive adjacent documentation,
not embedded comments that change their contract.

`docs/reference/GLOSSARY.md` will own abbreviations and project-specific terms.
Code files will carry conventional language-native module/header documentation
and only useful why/invariant/safety/scientific comments. Documentation cleanup
requires an audience map and source-to-destination ledger before relocation.

No `docs/skills` directory is planned. Once these practices are implemented and
proven, a proper documentation-health skill may audit deterministic structure
and semantic responsibility drift. It remains read-only by default and requires
approval before repair.

## Deferred capabilities and guardrails

The following remain outside the current repo-spanning refactor task set unless
a separate future card, live plan, and approval say otherwise:

- analysis-module registry and custom-analysis execution;
- public reference/read acquisition;
- installable/public package distribution;
- optional-analysis success and request archival;
- generic dispatchers and job arrays;
- targeted-rerun orchestration;
- publication infrastructure;
- automatic dependency restoration;
- automatic stale-lock deletion, log cleanup, or artifact cleanup;
- policy capable of unlocking biological readiness.

Every future capability enters through explicit contracts and preserves the
evidence boundaries in `AGENTS.md`. Target diagrams are constraints, not proof
that an implementation or migration exists.
