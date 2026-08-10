# Durable decisions

This index records current decisions that are not safely inferred from code or
filenames. Detailed rationale remains grouped by responsibility; exact behavior
belongs to the applicable owner contract. Current state belongs in
[`HANDOFF.md`](../operations/HANDOFF.md), roadmap in
[`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), and unresolved design in
[`QUESTIONS.md`](QUESTIONS.md).

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
- Keep active tests separate from non-runnable future scaffolds; coverage is a
  regression signal, not a substitute for behavioral or scientific evidence.
- Update documentation when its subject changes and keep exact operator detail
  with its functional owner.

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
- Reporting consumes explicit versioned artifacts and authorized tables; it
  never discovers inputs, reruns analysis, installs tools, or promotes state.

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

## Architecture

Detailed rationale: [`platform-direction.md`](decisions/platform-direction.md).

- Organize source vertically by functional owner; keep native implementation,
  contracts, commands, diagnostics, recovery, and tests together.
- Use semantic identities and explicit artifact DAG edges rather than numeric
  aliases or filenames for order.
- Prohibit peer private-implementation imports. Promote shared code only after
  equivalent reuse is proved and only to the narrowest neutral owner.
- Keep repository controls, public starter inputs, and runtime product domains
  distinct. Source placement alone creates no installed package or evidence.

Future intake, orchestration, logging, report profiles, acquisition, analysis
extensions, and installable control-plane ideas remain explicitly
unimplemented in [`FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md)
and [`QUESTIONS.md`](QUESTIONS.md).
