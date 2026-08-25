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
contracts and libraries, reporting, local-pilot intake/control, and
reference/runtime/storage evidence occupy separate cross-cutting owners.
Numeric step labels are historical aliases rather than a complete execution
order.

EMRYS currently exposes owner-local commands, SLURM entry points, read-only
local-pilot admission, dry-run-first public run/resume/inspection commands, and
one fixed source-checkout-bound Snakemake graph for local execution. The static
graph invokes public owners through hash-bound closed dispatch records,
schedules only content-bound verified-task records, and feeds the existing
artifact-index, run-summary, and HTML-report transactions. An internal
filesystem-first lifecycle owns the run lock, immutable workflow attempts,
terminal receipts, durable producer-entry ledgers, between-task resume, and
read-only state inspection. The production materializer projects the fixed
profile to the exact public owner commands and publishes attempt state only
under the aggregate lifecycle lock. Real science-tool and cluster execution
remain outside the proven boundary.

| Component group | Implemented owners | Principal inputs | Principal outputs |
| --- | --- | --- | --- |
| Input admission | `src/emrys/ingestion/sample_manifest_admission/` | Explicit sample manifest and optional declared FASTQ paths | Schema/admission result and paired-FASTQ diagnostics |
| Local-pilot orchestration | `src/emrys/orchestration/local_pilot/`, `src/emrys/contracts/orchestration/`, and `workflow/` | Explicit YAML request, ordered TSV manifests, exact runtime profile, reviewed fixed-profile record, canonical execution/config snapshots, and hash-bound task dispatches | Dry-run plans, create-absent run/attempt materialization, canonical execution/reporting identity, semantic all-pass evidence, durable task/reporting start records, task-attempt and verified records, immutable workflow attempts, public derived inspection, and between-task resume; no real-tool or cluster proof |
| Reference preparation | Owners `00a`, `00b`, and `00c` under `src/emrys/stages/` | Reference FASTA, GTF, and tool parameters | STAR index, BED12, and FASTA sidecars |
| Per-sample processing and evidence | Owners `01`–`06` under `src/emrys/stages/` plus evidence owners `02b` and `03` | Declared reads, references, and preceding owner artifacts | Aligned/canonical/duplicate-marked/split BAMs plus QC and orientation evidence |
| Cohort transformation and analysis | Stage owners `07` and `08`, then analysis owners `09` and `10` | Declared partitions, sample order, reference context, registered PUM motif, and upstream receipts | Cohort VCFs, annotated candidates, paired-CMH ranked candidates, and hash-bound sequence/motif context projections |
| Reporting | `src/emrys/reporting/` | Admitted source checkout, explicit artifact inventory, and validated computational receipts | Artifact index, canonical run summary, separate self-contained scientific and evidence HTML views, summary TSV, and v4 report receipt |
| Neutral contracts and libraries | `src/emrys/contracts/` and `src/emrys/libraries/` | Owner-declared records or values | Shared schemas, vocabularies, validation, and narrowly reviewed primitives |
| Operational evidence | Runtime-availability inspection (`runtime_availability`), reference provenance, and storage inventory under `src/emrys/evidence/` | Explicit profiles, reference inventories, storage roots, and retention declarations | Bounded operational observations and receipts |

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
| Project scientific context | `project_candidate_scientific_context` | Attach mechanically oriented continuous genomic windows and one registered PUM motif analysis after Step `09`, without reopening alignments, changing calls, discovering motifs, or inferring biological strand. | Receipt-last candidate-context, exact motif-hit, logo-frequency, and motif-statistic tables for bounded report presentation. |

### Exact continuing inputs

| Input or artifact contract | Where it continues to be consumed |
| --- | --- |
| Reference FASTA and its FAI | Reference preparation, split-N-cigar handling, cohort observation, and Step `10` scientific-context projection. |
| Reference GTF | STAR-index construction, BED12 conversion, and Step `08` annotation. |
| BED12 | RSeQC paired-orientation inference. |
| Sample manifest | Steps `07`, `08`, and `09`. |
| Partition manifest | Steps `07`, `08`, and `09`. |
| Analysis declarations | Step `09` thresholds and optional background inputs. |

Read-only artifact adapters and the canonical run-summary builder project
explicit native outputs and validation records into reporting inputs. Static
rendering publishes separate self-contained scientific and operational
evidence/provenance HTML views plus a deterministic summary TSV and a
validated, identity-bound v4 receipt last.
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
publish the static scientific and evidence HTML report transaction from a
validated canonical summary.

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
    -> static report rendering
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

Static reporting follows that rule through the private
[`_run_report/`](../../src/emrys/reporting/_run_report/README.md) package.
The installed `python -X pycache_prefix=/dev/null -I -m emrys build report` route is owned directly by
[`report.py`](../../src/emrys/reporting/report.py). Its admitted source checkout
governs code and renderer identity, while the separately admitted artifact root
governs contract-relative run inputs. Private owners separate
immutable models, explicit input/context validation, two structured view
projections, fixed Matplotlib/Logomaker SVG figures, Jinja rendering, v4
receipt projection, and one receipt-last transaction. The locked Python
renderer plus the single packaged HTML template and CSS resource are the
complete rendering runtime; reporting has no PDF, external renderer,
compatibility facade, shell wrapper, or format-selection surface.

The local lifecycle consumes only the direct public reporting-transaction
validator in `reporting/transaction_validation.py`; it does not import a
reporting-private package or turn rendering into completion authority. Source
checkout identity and the independent artifact-source root are admitted by the
neutral `libraries/source_authority.py` seam. Completion is derived only after
every required owner scope has a complete durable start-to-verification chain
and all three reporting transactions are semantically revalidated through the
same irreversible-entry policy. An entered but incomplete scope blocks
automatic resume; an unentered scope remains pending.

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
2. Read-only adapters inspect an explicit inventory and publish versioned
   artifact records, an ordered index, and a receipt.
3. The run-summary owner consumes one committed adapter receipt and publishes
   canonical JSON with deterministic TSV projections.
4. The static report owner consumes that canonical summary under distinct
   admitted code and artifact roots, then publishes scientific HTML,
   evidence/provenance HTML, summary TSV, and the v4 receipt last.
5. The local lifecycle independently re-admits the exact required task-start
   and verified-task roster plus all three reporting start/completion chains,
   then publishes the immutable workflow-attempt receipt last.

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
