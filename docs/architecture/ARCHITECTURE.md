# Current architecture

This document owns the conceptual map of the implemented EMRYS system within
the [`architecture index`](README.md). Exact semantic identities and DAG edges belong in
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md); current public
surfaces and direct protection belong in the
[`functional-owner inventory`](FUNCTIONAL_OWNER_INVENTORY.md); and each
owner-local `CONTRACT.md` owns exact interface and failure behavior.

Current projections:

- the [scientist-facing workflow](#scientist-facing-workflow) and its
  [Mermaid source](diagrams/current_user_pipeline.mmd) provide the phase view;
- [`pipeline.mmd`](diagrams/pipeline.mmd) provides the grouped system
  projection; and
- [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) remains the exact
  machine-independent dependency authority.

## Implemented system shape

All fourteen numbered workflow, analysis, and evidence owners occupy their
functional homes under `src/emrys/`. Sample-manifest admission, neutral
contracts and libraries, reporting, run-coordinator intake/control, and
reference/runtime/storage evidence occupy separate cross-cutting owners.
Numeric step labels are historical aliases rather than a complete execution
order.

EMRYS currently exposes owner-local commands, read-only run-coordinator admission,
dry-run-first public run/resume/report/inspection commands, one private
whole-Run Slurm transport, and one source-checkout-bound Snakemake graph for
one-host execution. Planning composes the common processing profile with one
immutable explicitly admitted analysis-module tail. The resulting graph
invokes public owners through hash-bound closed dispatch records,
schedules only content-bound verified-task records, and stops at the complete
scientific/evidence owner closure. After its v2 Attempt receipt, public control
invokes the artifact-index, run-summary, and HTML-report transactions by default
as a separate downstream operation. An internal
filesystem-first lifecycle owns the run lock, immutable workflow attempts,
terminal receipts, durable producer-entry ledgers, between-task resume, and
read-only state inspection. The production materializer projects the composed
profile to the exact public owner commands and publishes Attempt state only
under the aggregate lifecycle lock. Hosted 130-pair real-tool
direct/disposable-single-node-Slurm outcome parity is proven; 100,000-pair,
institutional site/module and collaborator dependency provisioning,
failure/recovery, multi-node, production,
scientific-review, and biological-validation evidence remain outside that
boundary.

| Component group | Implemented owners | Principal inputs | Principal outputs |
| --- | --- | --- | --- |
| Input admission | `src/emrys/ingestion/sample_manifest_admission/` | Explicit sample manifest and optional declared FASTQ paths | Schema/admission result and paired-FASTQ diagnostics |
| Run-coordinator orchestration | `src/emrys/orchestration/run_coordinator/`, `src/emrys/contracts/orchestration/`, and `workflow/` | Project-v1, ordered TSV manifests, Project-owned runtime inventory, one Project-local execution profile, common processing profile, selected installed module/configuration, canonical execution/config snapshots, and hash-bound task dispatches | Dry-run plans, create-absent Run/Attempt materialization, canonical execution/reporting identity, semantic all-pass evidence, durable task/reporting start records, task-attempt and verified records, immutable workflow attempts, public derived inspection, between-task resume, processing reuse across compatible module selections, and hosted 130-pair direct/disposable-single-node-Slurm successful-outcome parity for the built-in profile; no collaborator-module, institutional-site, production, scientific-review, or biological-validation proof |
| Reference preparation | Owners `00a`, `00b`, and `00c` under `src/emrys/stages/` | Reference FASTA, GTF, and tool parameters | STAR index, BED12, and FASTA sidecars |
| Per-sample processing and evidence | Owners `01`–`06` under `src/emrys/stages/` plus evidence owners `02b` and `03` | Declared reads, references, and preceding owner artifacts | Aligned/canonical/duplicate-marked/split BAMs plus QC and orientation evidence |
| Cohort transformation and analysis | Stage owners `07` and `08`, then one selected `emrys.analysis_modules` provider; built-in owners `09` and `10` remain paired CMH plus context projection | Declared partitions, sample order, selected module configuration, typed upstream artifacts, and receipts | Cohort VCFs and annotated candidates followed by module-declared final Results and validation evidence |
| Reporting | Fixed reporting core plus one selected `emrys.analysis_reporters` provider under `src/emrys/reporting/` | Admitted source checkout/provider, descriptor-derived artifact inventory, and validated computational receipts | Artifact index, canonical run summary, module-specific scientific HTML, fixed evidence/operations HTML, summary TSV, and v4 or v5 report receipt |
| Neutral contracts and libraries | `src/emrys/contracts/` and `src/emrys/libraries/` | Owner-declared records or values | Shared schemas, vocabularies, validation, and narrowly reviewed primitives |
| Operational evidence | Runtime-availability inspection (`runtime_availability`), reference provenance, and storage inventory under `src/emrys/evidence/` | Explicit profiles, reference inventories, storage roots, and retention declarations | Bounded operational observations and receipts |

Exact files, direct execution surfaces, validators, and tests are linked from
the [functional-owner inventory](FUNCTIONAL_OWNER_INVENTORY.md).

## Current-to-target responsibility crosswalk

This is a descriptive mapping of the implemented tree to the
[ratified responsibility model](../design/decisions/platform-direction.md#ratified-responsibility-and-dependency-model).
It is not a target package map. `Aligned` means the current owner already fits
the durable responsibility direction in its declared scope; `transitional`
means protected current behavior spans responsibilities whose final interface
or owner remains with a later slice; `unresolved` means the target decision has
not selected a representation. No status authorizes a source move.

| Current owner | Responsibility represented today | Graph(s) | Status | Later decision or exit condition |
|---|---|---|---|---|
| Package root `__main__.py` | Installed-command composition over owner validation, inspection, onboarding, and Run/report control | Source import and invocation | Aligned | The Project-root ordinary-command cutover is complete. Low-level reporting builders are private; the installed CLI reaches only the Run-oriented reporting operation. |
| `ingestion/` | External sample/input admission and diagnostics | Import and emitted declarations | Aligned | Public configuration and setup slices may simplify intake without giving ingestion execution or scientific authority. |
| `contracts/` | Closed schemas, vocabularies, identity facts, and cross-owner records | Import and artifact/evidence contracts | Aligned | The neutral role and every exact implementation exception are permanently justified and mechanically ratcheted in `SOURCE_TOPOLOGY.md`. |
| `libraries/` | Narrow implementation shared only across demonstrated consumers | Import | Aligned | Every seam stays independently justified and acyclic; the closeout audit found no duplicated policy pair that qualified for another shared layer. |
| Semantic behavior under `stages/`, `analyses/`, and `evidence/` | Recognizable transformation, analysis, and evidence semantics with adjacent contracts and tests; the bounded analysis-module descriptor declares typed inputs/outputs, exact dependencies, minimum resources, and producer/validator plans | Import, invocation, and semantic artifact/evidence flow | Aligned | The collaborator-module boundary is complete without a universal Stage hierarchy or workflow language. |
| Owner-local cross-cutting mechanics under `stages/`, `analyses/`, and `evidence/` | Current shell producers, runtime resolution, filesystem operations, and publication transactions adjacent to the semantic owner | Import and runtime/control invocation | Aligned | Caller-complete Python migrations retired the qualifying shell owners; distinct trust and mutation boundaries retain their owner-local checks. No universal lifecycle abstraction qualified. |
| Runtime, reference, and storage evidence owners | Explicit operational observations that do not become computation or admission authority | Import and invocation | Aligned | The application composes the exact capabilities ratified in `SOURCE_TOPOLOGY.md`; no edge may broaden by analogy. |
| `orchestration/run_coordinator/` and `contracts/orchestration/` | Project admission, planning, application coordination, composed-profile materialization, execution/reuse admission, lifecycle, inspection, and resource decisions | Import and invocation | Aligned | This is the final private application owner, not a Run god object. Module discovery and profile composition do not give it scientific or reporting-renderer authority. |
| `reporting/` | Profile-derived artifact adaptation, canonical summary, one module-specific scientific view, fixed evidence/operations view, and receipt-last report publication | Import and artifact/evidence flow | Aligned | Reporting is default-on but disable-able, independently regenerable through one Run-oriented operation, and separate from scientific Attempt authority. Reporter identity is receipt-only; exact historical reports remain read-only compatible. |
| Root `workflow/` and the composed profile | Snakemake scheduling of the common processing graph plus one immutable selected-module tail through hash-bound task records | Runtime/control invocation | Aligned | Snakemake remains the sole backend and a mechanism, not scientific, admission, module-discovery, or recovery authority; Slurm is whole-Run transport around it. |
| Repository `scripts/`, tests, Git, Make, CI, and environments | Development, validation, restoration, and delivery controls | Outside the product graphs except as test or build consumers | Aligned | These remain repository controls and never become scientific-workflow owners or evidence promotion. |
| OS, R, Python, filesystem, Snakemake, and SLURM mechanisms | External effects and observations reached through current owner code | Runtime/control invocation | Aligned | Existing owner-local adapters retain attributable effects and observations. No generalized backend or mechanism layer is justified without a concrete extension or net-negative replacement. |

The source-import projection and its exact current transitions live in
[`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md). Runtime
invocation remains visible here and in the orchestration/owner contracts. Exact
functional-owner semantic artifact and evidence edges remain in
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md); lifecycle, admission,
orchestration, and reporting flows remain with their current contracts and this
architecture. Permission in one projection does not grant permission in
another.

## Scientist-facing workflow

This view groups the built-in paired-CMH owners into nine explanatory phases.
An explicitly selected collaborator module retains the common path through
candidate preprocessing and supplies its own typed Step `09` plus optional
Step `10` tail. The
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
| Project scientific context | `project_candidate_scientific_context` | Attach mechanically oriented continuous genomic windows and one registered PUM motif analysis after Step `09`, without reopening alignments, changing calls, discovering motifs, or inferring biological strand. | Receipt-last candidate-context, exact motif-hit, logo-frequency, and motif-statistic tables for bounded report presentation. |

### Exact continuing inputs

| Input or artifact contract | Where it continues to be consumed |
| --- | --- |
| Reference FASTA and its FAI | Reference preparation, split-N-cigar handling, cohort observation, and Step `10` scientific-context projection. |
| Reference GTF | STAR-index construction, BED12 conversion, and Step `08` annotation. |
| BED12 | RSeQC paired-orientation inference. |
| Sample manifest | Steps `07`, `08`, and `09`. |
| Partition manifest | Steps `07`, `08`, and `09`. |
| Analysis declarations | The selected module identifier and closed module configuration; for the built-in paired-CMH provider, Step `09` thresholds and optional background inputs. |

Read-only artifact adapters derive the expected roster from the admitted module
profile and project native outputs and validation records into reporting
inputs. The canonical run-summary builder publishes v2 for the existing flat
paired-CMH path or v3 for an explicit module. The selected reporter publishes
bespoke scientific HTML while fixed EMRYS reporting publishes the
evidence/operations view, deterministic summary TSV, and a validated v4 or v5
receipt last.
Reporting does not discover inputs, execute analysis, repair artifacts, or
promote runtime, cluster, scientific-review, or biological evidence.

In prose: EMRYS prepares a shared reference universe, aligns each declared
read pair, and converts the alignment into a canonical BAM. QC and mechanical-
orientation evidence branch from that boundary while the main BAM continues
through duplicate marking, RNA-aware splitting, and neutral mechanical-
orientation partitioning. Manifest-declared samples and partitions then enter
cohort mpileup; the exact VCF set is normalized and annotated before paired-
CMH ranking. The bounded context owner then projects those fixed calls onto one
exact indexed reference and registered PUM motif. Read-only reporting may then
publish the selected scientific and fixed evidence/operations HTML report
transaction from a validated canonical summary.

### Scientific boundary

Computational completion is not a biological conclusion. `FWD_like` and
`REV_like` are mechanical labels. EMRYS produces CMH-ranked computational
candidates and provenance; candidate review, adjudication, and biological
interpretation are external work-process records, not pipeline steps, gates,
artifacts, or completion states.

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
    -> selected scientific report plus fixed evidence/operations rendering
```

Approved shared seams remain narrow: validation-report publication, BAM
validation, reference-contig parsing, executable-value resolution, artifact
contracts, and the neutral Step `08`, Step `09`, and scientific-context
contracts. Their exact
consumer rosters and allowed dependency directions live
in [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md).
Private bridges and colocated helper packages remain part of their public
owner; they do not create additional pipeline components or a generic utility
layer.

Module-aware reporting follows that rule through the private
[`_run_report/`](../../src/emrys/reporting/_run_report/README.md) package.
The installed `emrys report [RUN]` route admits one successful Project Run
Run and plans, generates, or reuses the fixed artifact-index → run-summary →
HTML sequence. Its admitted source checkout and selected installed providers
govern code and renderer identity,
while the Run governs the separately admitted artifact root and report output.
Private owners separate
immutable models, explicit input/context validation, module-specific scientific
projection, the fixed evidence/operations projection, Jinja rendering, v4/v5
receipt projection, and one receipt-last transaction. The built-in paired-CMH
reporter retains its Matplotlib/Logomaker figures. The locked Python renderer
plus packaged templates and CSS are the complete rendering runtime; reporting
has no generic report DSL, PDF selector, external rendering service, shell
wrapper, or format-selection surface. The three low-level builders remain
implementation details rather than public recovery commands.

The scientific lifecycle ends after every required owner scope has a complete
durable start-to-verification chain, releases the Run lock, and publishes a v2
Attempt receipt. Reporting is then invoked by public control unless disabled;
it creates neither a Run nor an Attempt and cannot alter that receipt. The
dedicated reporting operation is the only orchestration owner that composes the
three private builders. It generates only from fully empty reporting state,
reuses only a semantically complete transaction, and fails closed on partial or
ambiguous state. Receipt-v1 Runs remain exactly readable and may reuse complete
reports, but cannot originate new reports.

## Identity, inputs, and outputs

Sample identity, condition, order, and replicate pairing come from the
declared sample manifest. Partition selection, reference identity, analysis
pairing, and thresholds are also explicit inputs. Owners consume declared
paths, artifacts, and receipts
rather than infer them from filenames, globs, neighboring source directories,
or numeric step order.

Native owner outputs and validation artifacts remain authoritative for their
own stage or evidence boundary. Downstream consumers reference those outputs
through declared contracts; reporting does not become the owner of upstream
computation or external interpretation.

## Publication and evidence flow

The downstream product flow is one-way:

1. Native owners publish their declared artifacts and owner-local validation
   evidence.
2. Read-only adapters derive the inventory from the admitted module profile and
   publish versioned artifact records, an ordered index, and a receipt.
3. The run-summary owner consumes one committed adapter receipt and publishes
   canonical v2 or v3 JSON with deterministic TSV projections.
4. The selected scientific reporter and fixed reporting core consume that
   canonical summary under distinct admitted code and artifact roots, then
   publish scientific HTML, evidence/operations HTML, summary TSV, and the v4
   or v5 receipt last. Reporter identity is report metadata, not Run identity.
5. The scientific lifecycle independently re-admits the exact required
   task-start and verified-task roster, releases the Run lock, and publishes the
   immutable v2 workflow-attempt receipt last. Public control then invokes the
   reporting flow by default as a separate downstream operation.

Operational evidence owners sit beside this product flow. Runtime, reference,
and storage observations can inform execution or review, but do not become
computational pipeline stages. The exact evidence ceilings and current proof
state are deliberately outside this architecture map.

## Canonical detail routes

| Question | Canonical owner |
| --- | --- |
| What are the exact semantic owners, inputs, outputs, and DAG edges? | [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) |
| Where are public commands, jobs, validators, Make surfaces, and tests? | [`FUNCTIONAL_OWNER_INVENTORY.md`](FUNCTIONAL_OWNER_INVENTORY.md) |
| What does one operation validate, publish, or preserve on failure? | Its adjacent `CONTRACT.md` linked from the inventory |
| Which source homes and dependency directions are allowed? | [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| Which commands and operational procedures are supported? | [`RUNBOOK.md`](../operations/RUNBOOK.md) |
| Where are recovery procedures and symptom diagnosis? | [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| Where do reporting, scientific, execution, and evidence rules live? | [`DECISIONS.md`](../design/DECISIONS.md), owner-local contracts, and [`TEST_BASELINE.md`](../design/TEST_BASELINE.md) |
| What is implemented or currently checked? | Live Git plus checks and retained artifacts for the exact commit |
| What accepted work remains? | [`backlog_matrix.md`](../tasks/backlog_matrix.md) |

The standalone [reliability flow](diagrams/reliability.mmd) is a concise
non-authoritative view of validation and publication boundaries.
