# TODO

This file contains only prioritized pending work and current blockers. The
authoritative status matrix and branch lineage are in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and evidence boundary are in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Stop for review before creating or implementing
   `post09-reference-provenance`.
2. After explicit approval, implement that package from the clean, pushed
   `post09-runtime-preflight` branch using its pipeline-plan acceptance
   criteria.
3. Continue any approved local-only descendant sequence one package at a time,
   stopping at the boundary defined in the pipeline plan.

## Runtime and scientific blockers

- Establish the immutable production sample manifest, explicit replicate
  values, persistence location, and SHA-256 before downstream promotion.
- Populate the explicit runtime profile with approved CSU paths and
  expectations, execute it inside the actual batch/compute context, and
  inspect every required status without installing software.
- Record storage quotas, scratch availability, and an approved retention
  policy before large downstream runs.
- Recover the exact Novogene annotation release if possible and verify
  reference-contig agreement, including the mitochondrial contig.
- Validate real bcftools behavior and Step `07` outputs before promoting Steps
  `08` or `09`.
- Complete the explicit production scientific-evidence gate before making
  biological claims.

## Deferred

- Remote and cluster promotion.
- Targeted reruns after validator stabilization and evidence inspection.
- Analysis-configuration extraction, module wrapping, shared helper
  refactors, job arrays, dispatchers, public-data ingestion, publishing
  infrastructure, or automatic cleanup.
- Any policy that could unlock `biological_interpretation_ready`.

Do not mark an item complete until its outputs and evidence have been
inspected and the canonical documentation owner has been updated.
