# Current architecture

This document owns the conceptual map of the implemented NORAD system within
the [`architecture index`](README.md). Exact semantic identities and DAG edges belong in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md); current public
surfaces and direct protection belong in the
[`functional-owner inventory`](FUNCTIONAL_OWNER_INVENTORY.md); and each
owner-local `CONTRACT.md` owns exact interface and failure behavior.

Current projections:

- the [scientist-facing workflow](#scientist-facing-workflow) and its
  [Mermaid source](diagrams/current_user_pipeline.mmd) provide the phase view;
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
| Operational evidence | Runtime-availability inspection (`runtime_availability`), reference provenance, and storage inventory under `src/norad/evidence/` | Explicit profiles, reference inventories, storage roots, and retention declarations | Bounded operational observations and receipts |

Exact files, scheduler wrappers, validators, and direct tests are linked from
the [functional-owner inventory](FUNCTIONAL_OWNER_INVENTORY.md).

## Scientist-facing workflow

This view groups the exact semantic owners into nine explanatory phases. The
phase labels are not machine identities, public slugs, or scheduling commands;
arrows mean data or contract dependency, not automatic execution. The
[conceptual Mermaid source](diagrams/current_user_pipeline.mmd) and detailed
[system projection](diagrams/pipeline.mmd) provide the visual routes.

| Phase | Canonical semantic owner(s) | Purpose and ordering reason | Principal outputs and branches |
| --- | --- | --- | --- |
| Prepare the reference | `construct_STAR_index`; `convert_GTF_to_BED12`; `construct_FASTA_sidecars` | Establish the alignment index, transcript intervals, and FASTA sidecars before consumers require their coordinate and annotation contracts. These owners share external reference inputs but do not form a three-step dependency chain. | STAR index, BED12, FAI, and sequence dictionary. |
| Align reads | `align_RNA_reads_with_STAR` | Place each declared paired RNA-read input against the prepared STAR index before BAM normalization. | Coordinate-sorted STAR BAM and owner-local logs. |
| Canonicalize alignments | `construct_canonical_BAM` | Create the stable, coordinate-sorted, read-group-tagged BAM/BAI boundary used by downstream transformations and evidence branches. | Canonical BAM/BAI. |
| Inspect alignment evidence | `collect_canonical_BAM_QC_evidence`; `collect_RSeQC_paired_orientation_evidence` | Record non-gating BAM QC and mechanical library-orientation evidence from the canonical BAM; RSeQC also consumes BED12. | QC metrics and neutral paired-orientation evidence. This branch does not gate the main BAM path. |
| Prepare read evidence | `mark_BAM_duplicates_with_Picard`; `split_N_cigar_reads_with_GATK`; `partition_BAM_by_mechanical_read_orientation` | Mark duplicates, perform RNA-aware split-N-cigar handling, then form neutral mechanical-orientation BAM pairs before cohort observation. | Duplicate-marked and split-N-cigar BAM/BAI pairs, then `FWD_like` and `REV_like` BAM/BAI pairs. These labels are mechanical, not biological strand calls. |
| Observe the cohort | `generate_partitioned_cohort_mpileup_VCFs` | Count bases across every declared sample, partition, and mechanical orientation while preserving manifest order. | Receipt-last partitioned multi-sample VCF transactions. |
| Normalize and annotate candidates | `preprocess_and_annotate_cohort_candidates` | Validate the declared VCF set, expand alternate alleles, apply the provisional orientation conversion, annotate candidates, and publish deterministic TSVs before statistical comparison. | Sites TSV, exact input receipt, and QC summary TSV; unsupported non-SNV alleles are counted and excluded. |
| Rank paired candidates | `rank_cohort_candidates_with_paired_CMH` | Compare declared RNA reference/alternate counts across manifest-defined replicate strata, applying depth, statistical, and effect thresholds plus one global BH adjustment. An independently declared background cohort is optional. | Six-output transaction with all candidates, significant subset, summaries, spectrum, and plots. Outputs are **CMH-ranked candidates**, not validated editing sites. |
| Assemble review evidence | `assemble_scientific_review_evidence_package` | Combine the complete Step `08` and Step `09` transactions with explicit manifests and any separately supplied review evidence without rerunning analysis. | Deterministic review-evidence package with recorded, pending, absent, or limitation states. Explicit scientific review is optional and does not unlock biological readiness. |

### Exact continuing inputs

| Input or artifact contract | Where it continues to be consumed |
| --- | --- |
| Reference FASTA and its FAI | Reference preparation, split-N-cigar handling, and cohort observation. |
| Reference GTF | STAR-index construction, BED12 conversion, and Step `08` annotation. |
| BED12 | RSeQC paired-orientation inference. |
| Sample manifest | Steps `07`, `08`, and `09`, plus review-evidence assembly. |
| Partition manifest | Steps `07`, `08`, and `09`, plus review-evidence assembly. |
| Analysis/review declarations | Step `09` thresholds and optional background inputs; review plans and declared evidence enter only the review-evidence owner. |

Read-only artifact adapters and the canonical run-summary builder project
explicit native outputs and validation records into reporting inputs. Static
rendering is conditional on the selected HTML and/or PDF formats and publishes
a deterministic summary TSV plus a validated, identity-bound receipt last.
Reporting does not discover inputs, execute analysis, repair artifacts, or
promote runtime, cluster, scientific-review, or biological evidence.

In prose: NORAD prepares a shared reference universe, aligns each declared
read pair, and converts the alignment into a canonical BAM. QC and mechanical-
orientation evidence branch from that boundary while the main BAM continues
through duplicate marking, RNA-aware splitting, and neutral mechanical-
orientation partitioning. Manifest-declared samples and partitions then enter
cohort mpileup; the exact VCF set is normalized and annotated before paired-
CMH ranking. Complete candidate transactions can flow into the review-evidence
package, while scientific review joins only when explicitly supplied.
Read-only reporting may then publish selected static formats from a validated
canonical summary.

Computational completion is not a biological conclusion. `FWD_like` and
`REV_like` are mechanical labels, `science_review_complete_exploratory` remains
provisional, and `biological_interpretation_ready` remains reserved pending a
separately authorized policy.

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

Static reporting follows that rule through the private
[`_run_report/`](../../src/norad/reporting/_run_report/README.md) package.
The two public Python renderer paths are compatibility facades; private owners
separate immutable models, input/context validation, HTML/PDF/receipt
projection, pinned runtime execution, transaction primitives, and HTML versus
receipt-last bundle publication. Bundle dispatch imports the private HTML
owner in one direction only, so reporting has no renderer import cycle and no
new public command surface.

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
| Which commands and operational procedures are supported? | [`RUNBOOK.md`](../operations/RUNBOOK.md) |
| Where are recovery procedures and symptom diagnosis? | [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| Where do reporting, scientific, execution, and evidence rules live? | [`DECISIONS.md`](../design/DECISIONS.md), owner-local contracts, and [`TEST_BASELINE.md`](../design/TEST_BASELINE.md) |
| What is currently proved, blocked, or awaiting external execution? | [`HANDOFF.md`](../operations/HANDOFF.md) and [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |

The standalone [reliability flow](diagrams/reliability.mmd) is a concise
non-authoritative view of validation and publication boundaries.
