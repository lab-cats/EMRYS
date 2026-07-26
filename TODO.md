# TODO

This file contains only prioritized pending work and current blockers. The
authoritative status matrix and branch lineage are in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and evidence boundary are in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Complete the documentation-responsibility consolidation package:
   - establish one canonical owner for each mutable fact;
   - remove duplicated live status, hashes, test totals, commands, and roadmap
     prose;
   - make standalone `.mmd` files the canonical diagram sources;
   - preserve unique scientific and inspected validation evidence;
   - pass the complete local and documentation validation gates;
   - push the clean branch and confirm upstream equality.
2. After explicit approval of that completed gate, implement the next package
   shown in the pipeline plan.
3. Continue the approved local-only descendant sequence one package at a time,
   stopping at the boundary defined in the pipeline plan.

## Runtime and scientific blockers

- Establish the immutable production sample manifest, explicit replicate
  values, persistence location, and SHA-256 before downstream promotion.
- Verify CSU batch-visible R, required namespaces, hash utilities, and tool
  paths without installing software during compute or validation.
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
