# Decisions

This is the stable index for durable NORAD decisions and rationale. Detailed
records are grouped by responsibility under [`decisions/`](decisions/).
Current status belongs in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), task state in
[`../tasks/`](../tasks/), evidence in
[`HANDOFF.md`](../operations/HANDOFF.md), commands in
[`RUNBOOK.md`](../operations/RUNBOOK.md), and open choices in
[`QUESTIONS.md`](QUESTIONS.md).

## Development and repository

### Use TSV manifests

[Decision and rationale.](decisions/repository-and-delivery.md#use-tsv-manifests)

### Develop locally and scale through SLURM

[Decision and rationale.](decisions/repository-and-delivery.md#develop-locally-and-scale-through-slurm)

### Use descendant branches and separate docpatch gates

[Decision and rationale.](decisions/repository-and-delivery.md#use-descendant-branches-and-separate-docpatch-gates)

### Keep executable programs out of Markdown

[Decision and rationale.](decisions/repository-and-delivery.md#keep-executable-programs-out-of-markdown)

### Permit isolated concurrent authoring with serialized integration

[Decision and rationale.](decisions/repository-and-delivery.md#permit-isolated-concurrent-authoring-with-serialized-integration)

### Use transient integration fragments for cross-owner proposals

[Decision and rationale.](decisions/repository-and-delivery.md#use-transient-integration-fragments-for-cross-owner-proposals)

### Run one complete computational gate per executable state

[Decision and rationale.](decisions/repository-and-delivery.md#run-one-complete-computational-gate-per-executable-state)

### Prefer failure-first validation output

[Decision and rationale.](decisions/repository-and-delivery.md#prefer-failure-first-validation-output)

### Route task context by revision and impact

[Decision and rationale.](decisions/repository-and-delivery.md#route-task-context-by-revision-and-impact)

### Use proportional planning categories and bounded approval envelopes

[Decision and rationale.](decisions/repository-and-delivery.md#use-proportional-planning-categories-and-bounded-approval-envelopes)

### Make documentation consistency impact-directed

[Decision and rationale.](decisions/repository-and-delivery.md#make-documentation-consistency-impact-directed)

### Keep active and future tests separate

[Decision and rationale.](decisions/repository-and-delivery.md#keep-active-and-future-tests-separate)

### Treat legacy scripts as protocol references

[Decision and rationale.](decisions/repository-and-delivery.md#treat-legacy-scripts-as-protocol-references)

## Execution and publication

### Default to dry-run

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#default-to-dry-run)

### Publish validated transactions

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#publish-validated-transactions)

### Preserve recovery evidence

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#preserve-recovery-evidence)

### Characterize unsafe publication states before correcting them

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#characterize-unsafe-publication-states-before-correcting-them)

## Reference and BAM pipeline

### Use the Novogene-provided reference

[Decision and rationale.](decisions/scientific-pipeline.md#use-the-novogene-provided-reference)

### Build STAR with the declared read-length overhang

[Decision and rationale.](decisions/scientific-pipeline.md#build-star-with-the-declared-read-length-overhang)

### Generate BED12 from GTF

[Decision and rationale.](decisions/scientific-pipeline.md#generate-bed12-from-gtf)

### Treat FASTA sidecars as Step `00c`

[Decision and rationale.](decisions/scientific-pipeline.md#treat-fasta-sidecars-as-step-00c)

### Make Step `02` the canonical BAM boundary

[Decision and rationale.](decisions/scientific-pipeline.md#make-step-02-the-canonical-bam-boundary)

### Keep QC and downstream transformation as separate consumers

[Decision and rationale.](decisions/scientific-pipeline.md#keep-qc-and-downstream-transformation-as-separate-consumers)

### Mark rather than remove duplicates

[Decision and rationale.](decisions/scientific-pipeline.md#mark-rather-than-remove-duplicates)

### Validate the effective Java runtime

[Decision and rationale.](decisions/scientific-pipeline.md#validate-the-effective-java-runtime)

### Use project storage for large GATK temporary files

[Decision and rationale.](decisions/scientific-pipeline.md#use-project-storage-for-large-gatk-temporary-files)

## Orientation and downstream analysis

### Separate mechanical orientation from biological strand

[Decision and rationale.](decisions/scientific-pipeline.md#separate-mechanical-orientation-from-biological-strand)

### Run Step `07` cohort-wide and manifest-partitioned

[Decision and rationale.](decisions/scientific-pipeline.md#run-step-07-cohort-wide-and-manifest-partitioned)

### Consume only declared Step `07` transactions in Step `08`

[Decision and rationale.](decisions/scientific-pipeline.md#consume-only-declared-step-07-transactions-in-step-08)

### Keep the orientation policy provisional

[Decision and rationale.](decisions/scientific-pipeline.md#keep-the-orientation-policy-provisional)

### Pair Step `09` samples only through manifest replicates

[Decision and rationale.](decisions/scientific-pipeline.md#pair-step-09-samples-only-through-manifest-replicates)

### Use one paired CMH and global BH family

[Decision and rationale.](decisions/scientific-pipeline.md#use-one-paired-cmh-and-global-bh-family)

## Runtime environments

### Guard the repository-local R environment

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#guard-the-repository-local-r-environment)

### Restore report tooling explicitly

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#restore-report-tooling-explicitly)

### Probe runtime availability from explicit profiles

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#probe-runtime-availability-from-explicit-profiles)

### Reconcile references without repair

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#reconcile-references-without-repair)

### Measure storage without acting on retention policy

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#measure-storage-without-acting-on-retention-policy)

## Evidence and scientific state

[Responsibility record.](decisions/execution-evidence-and-reporting.md#evidence-and-scientific-state)

### Separate computational proof and scientific interpretation

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#separate-computational-proof-and-scientific-interpretation)

### Preserve two post-review states

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#preserve-two-post-review-states)

### Require explicit evidence relationships

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#require-explicit-evidence-relationships)

## Structured artifacts and reporting

[Responsibility record.](decisions/execution-evidence-and-reporting.md#structured-artifacts-and-reporting)

### Decouple reporting from computation

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#decouple-reporting-from-computation)

### Use versioned closed schemas

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#use-versioned-closed-schemas)

### Inventory physical artifacts explicitly

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#inventory-physical-artifacts-explicitly)

### Bind run identity to immutable analysis inputs

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#bind-run-identity-to-immutable-analysis-inputs)

### Represent missing and failed evidence

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#represent-missing-and-failed-evidence)

### Adapt step validation reports without promotion

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#adapt-step-validation-reports-without-promotion)

### Authorize supplemental report tables explicitly

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#authorize-supplemental-report-tables-explicitly)

### Render deterministic, static reports

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#render-deterministic-static-reports)

## Measure Python coverage without replacing scenario gates

[Decision and rationale.](decisions/repository-and-delivery.md#measure-python-coverage-without-replacing-scenario-gates)

## Documentation ownership

[Decision and rationale.](decisions/repository-and-delivery.md#documentation-ownership)

## Approved architecture direction (2026-07-31)

[Durable platform-direction decisions.](decisions/platform-direction.md)

### Protect behavior before architectural mutation

[Decision and rationale.](decisions/platform-direction.md#protect-behavior-before-architectural-mutation)

### Govern future work through a file-backed task registry

[Decision and rationale.](decisions/platform-direction.md#govern-future-work-through-a-file-backed-task-registry)

### Use an architecture runway with rolling vertical delivery

[Decision and rationale.](decisions/platform-direction.md#use-an-architecture-runway-with-rolling-vertical-delivery)

### Target a vertical package with direct contract-preserving migrations

[Decision and rationale.](decisions/platform-direction.md#target-a-vertical-package-with-direct-contract-preserving-migrations)

### Converge cross-cutting source without misclassifying repository surfaces

[Decision and rationale.](decisions/platform-direction.md#converge-cross-cutting-source-without-misclassifying-repository-surfaces)

### Identify stages semantically and order them with a DAG

[Decision and rationale.](decisions/platform-direction.md#identify-stages-semantically-and-order-them-with-a-dag)

### Promote shared libraries only from proven reuse

[Decision and rationale.](decisions/platform-direction.md#promote-shared-libraries-only-from-proven-reuse)

### Apply risk-based source-size thresholds

[Decision and rationale.](decisions/repository-and-delivery.md#apply-risk-based-source-size-thresholds)

### Use YAML run requests with TSV sample manifests

[Decision and rationale.](decisions/platform-direction.md#use-yaml-run-requests-with-tsv-sample-manifests)

### Prioritize local FASTQ and registered references before public acquisition

[Decision and rationale.](decisions/platform-direction.md#prioritize-local-fastq-and-registered-references-before-public-acquisition)

### Preserve an extension path for preprocessing profiles and analysis modules

[Decision and rationale.](decisions/platform-direction.md#preserve-an-extension-path-for-preprocessing-profiles-and-analysis-modules)

### Keep an installable control plane as a later capability

[Decision and rationale.](decisions/platform-direction.md#keep-an-installable-control-plane-as-a-later-capability)

### Make science reporting the future default and retain comprehensive reporting

[Decision and rationale.](decisions/platform-direction.md#make-science-reporting-the-future-default-and-retain-comprehensive-reporting)

### Separate concise console output from durable detailed logs

[Decision and rationale.](decisions/execution-evidence-and-reporting.md#separate-concise-console-output-from-durable-detailed-logs)

### Treat documentation and maintainer context as architecture

[Decision and rationale.](decisions/repository-and-delivery.md#treat-documentation-and-maintainer-context-as-architecture)

### Defer repository skills until the underlying practice is proven

[Decision and rationale.](decisions/repository-and-delivery.md#defer-repository-skills-until-the-underlying-practice-is-proven)

### Keep optional-analysis success and request archival future-only

[Decision and rationale.](decisions/platform-direction.md#keep-optional-analysis-success-and-request-archival-future-only)

### Decision-capture crosswalk

[Canonical-owner routing.](decisions/platform-direction.md#decision-capture-crosswalk)

## Deferred engineering

[Durable guardrail.](decisions/platform-direction.md#deferred-engineering)
