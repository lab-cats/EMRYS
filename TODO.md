# TODO

This file contains only prioritized pending work and current blockers. The
authoritative status matrix and branch lineage are in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and evidence boundary are in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Create `refactor-01-test-baseline` from the clean, pushed, upstream-equal
   `refactor-00-comprehensive-audit` predecessor.
2. Add an explicit developer-only Python
   line/branch baseline and the public-contract risk-to-test matrix.
3. Create one evidence-determined descendant per cohesive high-risk
   characterization gap, then record the test-sufficiency decision on
   `refactor-01z-test-sufficiency-gate`.
4. Continue through the separately reviewed Phase `02` plan before changing
   production structure.

## Engineering gaps for the refactor gate

- Characterize the Step `09` validator's missing independent recomputation of
  the CMH statistic, p-value, odds ratio, and estimability from DP/AD counts
  before any compatible correction.
- Measure Python line/branch coverage and complete the public CLI, transaction,
  schema, status, deterministic-output, and recovery traceability matrix.
- Add high-risk characterization for shared validation publication/recheck
  faults, exact check rosters, and uneven SLURM/dry-run behavior.

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
