# Durable decisions

This index records current decisions that are not safely inferred from code or
filenames. Detailed rationale remains grouped by responsibility; exact behavior
belongs to the applicable owner contract. Live Git owns checkout state, exact
checks and retained artifacts own validation observations, the
[findings matrix](../tasks/backlog_matrix.md) owns accepted work and acceptance,
and the temporary [architecture campaign](../tasks/architecture_campaign.md)
owns unsliced alternatives.

## Repository and delivery

Detailed rationale: [`repository-and-delivery.md`](decisions/repository-and-delivery.md).

- Use explicit ordered TSV manifests for repeated scientific and evidence
  records; a future YAML request may reference rather than replace the sample
  manifest.
- Develop with local fixtures and run heavy production computation through
  SLURM.
- Keep executable logic in tested source, not Markdown.
- Deliver bounded semantic changes, validate the final affected state
  proportionally, and publish only under separate authority.
- Record future test work in the findings matrix rather than non-runnable
  scaffolds; coverage is not a substitute for behavioral or scientific evidence.
- Update documentation when its subject changes and keep exact operator detail
  with its functional owner.
- Follow the accepted
  [2026-08-25 documentation audit](decisions/repository-and-delivery.md#repository-documentation-audit-2026-08-25):
  legacy sources are not current authority, and their durable content moves in
  bounded retirement packages before deletion.

## Execution, evidence, and reporting

Detailed rationale:
[`execution-evidence-and-reporting.md`](decisions/execution-evidence-and-reporting.md).

- Default supported mutating interfaces to an inspectable dry-run where their
  established contract permits it.
- Publish multi-file results as validated owned transactions with stable-input
  checks, no-clobber rules, rollback, recovery, and a receipt/summary last.
- Preserve ambiguous locks, partials, backups, and recovery evidence; a
  characterized defect is not an approved contract.
- Restore R and report dependencies explicitly. Runtime-availability
  inspection, reference reconciliation, and storage inventory observe declared
  state without repair or mutation.
- Keep implementation, runtime, cluster, scientific-review, and biological
  evidence distinct. Missing and failed expected evidence remains visible.
- Reporting consumes explicit versioned computational artifacts; it
  never discovers inputs, reruns analysis, installs tools, or promotes state.
- A full run invokes downstream reporting by default after upstream admission,
  with an explicit opt-out. Reports are independently regenerable; report
  failure remains visible but does not invalidate completed scientific work.
- Scientific HTML figures use the locked private Matplotlib/Logomaker renderer
  only for deterministic presentation of admitted scientific records. Figure
  provenance stays in the evidence HTML; existing owner-generated scientific
  PDFs remain native analysis artifacts.

## Scientific pipeline

Detailed rationale: [`scientific-pipeline.md`](decisions/scientific-pipeline.md).

- Keep the declared Novogene reference family coherent; derive BED12 from GTF,
  treat FASTA sidecars as an explicit owner, and use Step `02` as the canonical
  read-group-tagged BAM boundary.
- Mark rather than remove duplicates, validate the effective Java runtime, and
  use owned project storage for large GATK temporary data.
- Keep BAM QC and orientation evidence separate from downstream transformation.
  Mechanical orientation is not biological strand interpretation.
- Step `07` is cohort-wide and manifest-partitioned; Step `08` consumes only
  the complete declared transaction universe.
- Pair Step `09` only through explicit replicate metadata and use the declared
  paired CMH method with one global BH family. Results are CMH-ranked
  candidates, not validated editing sites.
- Project report-ready sequence and known-motif context in one bounded
  post-Step09 owner. Version 1 uses mechanically RNA-change-oriented continuous
  genomic windows, one registered `PUM_UGUANA`/`TGTANA` model, significant-up
  foreground, tested non-significant background, two-sided Fisher enrichment,
  no single-model BH value, and upstream-owned deterministic top-eight display
  ranks. These are context projections, not editing, binding, or biological
  validation.

## Architecture

Detailed rationale: [`platform-direction.md`](decisions/platform-direction.md).

- Organize source vertically by functional owner; keep native implementation,
  contracts, commands, diagnostics, recovery, and tests together.
- Apply the [ratified architectural invariant constitution](decisions/platform-direction.md#ratified-architectural-invariant-constitution).
  Its **Preserved** entries are scoped current contracts; its **Target** entries
  are binding campaign requirements with named gaps, not implementation claims.
- Apply the
  [ratified responsibility and dependency model](decisions/platform-direction.md#ratified-responsibility-and-dependency-model):
  responsibility bands are not packages, source imports, runtime invocation,
  and artifact flow are separate graphs, and only durable negative directions
  are enforced before later slices select concrete APIs.
- Keep every effective operational value and source inspectable, expose only
  owner-defined safe overrides, and keep the science needed for review visible
  across operational abstractions.
- Migrate in bounded slices. Temporary compatibility has an owner, scope,
  parity protection, and retirement condition; superseded paths retire after
  caller migration and parity. Existing direct, adversarial, seeded-fault, and
  synthetic end-to-end defenses require mapped equal-or-stronger replacement.
- Roll out application logging incrementally through separately approved
  application-operation slices with exactly one semantic attempt owner and an
  explicit disposition for transitional or retiring surfaces; do not
  blanket-retrofit the legacy control surface.
- Make every architecture audit record concrete compression opportunities and
  apply the campaign's full category-separated
  [per-slice protocol](../tasks/architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol).
  Default implementation slices to net-negative maintained product code and no
  product-file growth; an exception requires explicit user approval of
  quantified growth and its justification, plus a retirement condition when
  temporary.
- Treat boundary values as immutable by default. A `Run` is an immutable plan;
  changing it creates a distinct `Run`. Apply the
  [ratified application model and Run boundary](decisions/platform-direction.md#ratified-application-model-and-run-boundary):
  the compact public model is `Project -> Analysis -> Run -> Results`, with
  `Attempt` progressively disclosed; each Run binds one immutable admitted
  Analysis revision to one immutable inspectable internal Execution Plan.
  Exact fields, identity composition, persistence, recovery ownership, APIs,
  backends, policy interfaces, storage, compatibility, and migration remain
  unresolved.
- Distinguish executable/static protections from retained evidence. An existing
  surviving defense may satisfy equal-or-stronger replacement. Evidence may be
  marked as a deletion candidate, but deleting the exact artifacts or class
  requires separate explicit user approval and its own commit, and cannot
  offset implementation growth.
- Use semantic identities and explicit artifact DAG edges rather than numeric
  aliases or filenames for order.
- Prohibit peer private-implementation imports. Promote shared code only after
  equivalent reuse is proved and only to the narrowest neutral owner.
- Keep repository controls, public starter inputs, and runtime product domains
  distinct. Source placement alone creates no installed package or evidence.
- Use Snakemake's local executor for the first fixed CMH profile; it schedules
  public owner commands but does not own science, validation meaning, recovery,
  or evidence promotion.
- Normalize one explicit YAML request plus ordered TSV manifests into a
  content-bound canonical JSON execution contract. Keep that identity distinct
  from the narrower existing reporting run contract.
- Treat an owner task as reusable only after producer success, complete native
  outputs, owner validation, and an explicit all-pass check of every validation
  row. Snakemake metadata and output presence are never completion authority.
- Expose the fixed local profile only through dry-run-first public run/resume/
  inspection commands that materialize immutable attempt state under the
  aggregate lock and expose no raw engine or recovery controls.
- Keep candidate review, adjudication, and biological interpretation outside
  every computational profile. They are external work-process records, not
  pipeline steps, gates, artifacts, or completion states.

The implemented source-checkout local lifecycle is defined by
[`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md). Accepted open outcomes
remain in the [findings matrix](../tasks/backlog_matrix.md); unsliced
architecture alternatives remain in the temporary
[architecture campaign](../tasks/architecture_campaign.md).
