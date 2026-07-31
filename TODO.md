# TODO

This file contains only prioritized pending work and current blockers. The
authoritative status matrix and branch lineage are in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and evidence boundary are in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Complete and push the Phase `01` measured baseline and public-contract
   matrix package.
2. Add the six evidence-derived characterization packages in the exact
   descendant order owned by
   [`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).
3. Record the measured test-sufficiency decision on the final Phase `01`
   gate.
4. Continue through the separately reviewed Phase `02` plan before changing
   production structure.

## Engineering gaps for the refactor gate

- Add independent Step `09` validator recomputation of the CMH statistic,
  p-value, odds ratio, and estimability from DP/AD counts before any compatible
  correction.
- Add high-risk characterization for shared validation publication/recheck
  faults and exact validation check rosters.
- Complete public CLI/exit, SLURM-wrapper, and independent-golden
  characterization without changing production contracts.

## Runtime and scientific blockers

- Establish the immutable production sample manifest, explicit replicate
  values, persistence location, and SHA-256 before downstream promotion.
- Populate the explicit runtime profile with approved CSU paths and
  expectations, execute it inside the actual batch/compute context, and
  inspect every required status without installing software.
- Record storage quotas, scratch availability, and an approved retention
  policy before large downstream runs.
- Populate and execute the reference-provenance inventory against production
  references; recover the exact Novogene annotation release if possible and
  inspect contig agreement, including the mitochondrial contig.
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
