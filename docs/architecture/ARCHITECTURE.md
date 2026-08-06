# Current architecture

This document is the canonical conceptual map of the implemented NORAD
system. Exact semantic identities and DAG edges belong in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md); current public
surfaces and direct protection belong in the
[`functional-owner inventory`](FUNCTIONAL_OWNER_INVENTORY.md); and each
owner-local `CONTRACT.md` owns exact interface and failure behavior.

Canonical current views:

- [`PIPELINE_OVERVIEW.md`](PIPELINE_OVERVIEW.md) and its
  [Mermaid source](diagrams/current_user_pipeline.mmd) provide the
  scientist-facing phase view;
- [`pipeline.mmd`](diagrams/pipeline.mmd) provides the grouped system
  projection; and
- [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) remains the exact
  machine-independent dependency authority.

## Implemented system shape

All fourteen numbered workflow, analysis, and evidence owners occupy their
functional homes under `src/norad/`. Sample-manifest admission, neutral
contracts and libraries, reporting, and reference/runtime/storage evidence
occupy separate cross-cutting owners. Numeric step labels are historical
aliases rather than a complete execution order.

NORAD currently exposes owner-local commands and SLURM entry points; it has no
implemented one-command pipeline orchestrator. Operators select the applicable
entry point and supply its declared inputs. Deferred orchestration profiles do
not change that boundary.

| Component group | Implemented owners | Principal inputs | Principal outputs |
| --- | --- | --- | --- |
| Input admission | `src/norad/ingestion/sample_manifest_admission/` | Explicit sample manifest and optional declared FASTQ paths | Schema/admission result and paired-FASTQ diagnostics |
| Reference preparation | Owners `00a`, `00b`, and `00c` under `src/norad/stages/` | Reference FASTA, GTF, and tool parameters | STAR index, BED12, and FASTA sidecars |
| Per-sample processing and evidence | Owners `01`–`06` under `src/norad/stages/` plus evidence owners `02b` and `03` | Declared reads, references, and preceding owner artifacts | Aligned/canonical/duplicate-marked/split BAMs plus QC and orientation evidence |
| Cohort transformation and analysis | Stage owners `07` and `08`, then analysis owner `09` | Declared partitions, sample order, reference context, and upstream receipts | Cohort VCFs, annotated candidates, and paired-CMH ranked candidates |
| Scientific-review evidence | Evidence owner `09c` | Explicit review plan, declared evidence, and Step `09` products | Versioned review package and review summary |
| Reporting | `src/norad/reporting/` | Explicit artifact inventory, validated receipts, review summary, and table approvals | Artifact index, canonical run summary, HTML/PDF bundle, and report receipt |
| Neutral contracts and libraries | `src/norad/contracts/` and `src/norad/libraries/` | Owner-declared records or values | Shared schemas, vocabularies, validation, and narrowly reviewed primitives |
| Operational evidence | Runtime preflight, reference provenance, and storage inventory under `src/norad/evidence/` | Explicit profiles, reference inventories, storage roots, and retention declarations | Bounded operational observations and receipts |

Exact files, scheduler wrappers, validators, and direct tests are linked from
the [functional-owner inventory](FUNCTIONAL_OWNER_INVENTORY.md).

## Ownership and dependency direction

Cross-owner flow uses declared artifacts and neutral contracts. A functional
owner does not import another owner's private implementation. The allowed
direction is:

```text
caller inputs
    -> ingestion/reference/stage/evidence/analysis owners
    -> owner validation and receipts
    -> neutral artifact adaptation
    -> canonical run summary
    -> static report rendering
```

Approved shared seams remain narrow: validation-report publication, BAM
validation, reference-contig parsing, executable-value resolution, artifact
contracts, and the neutral Step `08`, Step `09`, and review-package
contracts. Their exact consumer rosters and allowed dependency directions live
in [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).
Private bridges and colocated helper packages remain part of their public
owner; they do not create additional pipeline components or a generic utility
layer.

## Identity, inputs, and outputs

Sample identity, condition, order, and replicate pairing come from the
declared sample manifest. Partition selection, reference identity, analysis
pairing, review plans, evidence attachments, and report-table approvals are
also explicit inputs. Owners consume declared paths, artifacts, and receipts
rather than infer them from filenames, globs, neighboring source directories,
or numeric step order.

Native owner outputs and validation artifacts remain authoritative for their
own stage or evidence boundary. Downstream consumers reference those outputs
through declared contracts; reporting does not become the owner of upstream
computation or review evidence.

## Publication and evidence flow

The downstream product flow is one-way:

1. Native owners publish their declared artifacts and owner-local validation
   evidence.
2. Read-only adapters inspect an explicit inventory and publish versioned
   artifact records, an ordered index, and a receipt.
3. The run-summary owner consumes one committed adapter receipt plus explicitly
   supplied scientific-review and report-table inputs and publishes canonical
   JSON with deterministic TSV projections.
4. Static renderers consume that canonical summary and authorized supplemental
   tables to publish selected report formats and a receipt.

Operational evidence owners sit beside this product flow. Runtime, reference,
and storage observations can inform execution or review, but do not become
computational pipeline stages. The exact evidence ceilings and current proof
state are deliberately outside this architecture map.

## Canonical detail routes

| Question | Canonical owner |
| --- | --- |
| What are the exact semantic owners, inputs, outputs, and DAG edges? | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) |
| Where are public commands, jobs, validators, Make surfaces, and tests? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| What does one operation validate, publish, or preserve on failure? | Its adjacent `CONTRACT.md` linked from the inventory |
| Which source homes and dependency directions are allowed? | [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md) |
| How is a future direct move performed safely? | [`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md) |
| Which commands and operational procedures are supported? | [`RUNBOOK.md`](../operations/RUNBOOK.md) |
| Where are recovery procedures and symptom diagnosis? | [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| Where do reporting, scientific, execution, and evidence rules live? | [`DECISIONS.md`](../design/DECISIONS.md), owner-local contracts, and [`TEST_BASELINE.md`](../design/TEST_BASELINE.md) |
| What is currently proved, blocked, or awaiting external execution? | [`HANDOFF.md`](../operations/HANDOFF.md) and [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |
