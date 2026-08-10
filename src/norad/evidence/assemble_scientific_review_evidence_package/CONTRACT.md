# `assemble_scientific_review_evidence_package` evidence contract

This is the observed contract of historical Step `09c` for `ARCH-02A`. It is a
scientific-evidence governance and review operation, not a computational
transformation or analysis rerun. The exact public identity and historical
alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug and is now the implemented source location.

## Responsibility and execution dependencies

Validate one explicitly declared scientific-review plan, the complete Step
`08`/`09` lineage, and source-backed scientific evidence; reconcile reviewer
decisions and candidate adjudication; enforce allowable evidence states; and
publish a deterministic 13-table review package. It does not run R, recompute
CMH statistics, infer reviewer decisions, discover substitute inputs, mutate
upstream artifacts, or execute requested reruns.

Required inputs are a safe review ID, exact sample and partition manifests,
all three outputs from the final
[`preprocess_and_annotate_cohort_candidates`](../../stages/cohort_candidate_preprocessing/CONTRACT.md)
owner, the Step `09` analysis directory produced by the final
[`rank_cohort_candidates_with_paired_CMH`](../../analyses/paired_cmh_candidate_ranking/CONTRACT.md)
owner and named by the plan's `primary_analysis_id`, a one-row review plan, an
evidence manifest plus every declared evidence payload, and an output root.
The analysis directory must contain all six exact Step `09` files. Inputs and
evidence sources are bound by path, SHA-256, and row count and are rechecked
during publication.

## Evidence and state contract

Every scientific domain must be represented explicitly:

- orientation/locus and annotation audits;
- QC funnel and replicate effects;
- sensitivity and leave-one-pair-out analyses;
- candidate selection and adjudication;
- decisions and limitations; and
- computational validation as separately declared evidence.

Evidence status is `missing`, `incomplete`, `complete`, or `not_applicable`.
Source-backed evidence requires declared identity, owner/reviewer, policy and
date, schema-conforming rows, exact path/hash/count, and compatible review and
analysis IDs. Missing evidence has no source; `not_applicable` requires a
reason. Decisions may record a required rerun and bounded rerun scope, but this
operation only records that decision.

The requested science state is never inferred or automatically promoted:

```text
evidence_incomplete
science_review_complete_exploratory
```

An exploratory-complete review requires every scientific category complete or
justifiably not applicable, all decision dimensions explicitly completed,
every selected candidate adjudicated, and a completion date. An incomplete
review must keep that date `NA`. `science_review_complete_exploratory` remains
provisional. `biological_interpretation_ready` is reserved and rejected.

Implementation, local-test, runtime-validation, cluster-dry-run, and cluster-
proof states remain independent axes. A declared `proven` cluster state
requires passed runtime and dry-run states plus complete explicit
computational-validation evidence. Package publication does not itself prove
any computational or scientific claim.

## Thirteen-output transaction

Under `<output-root>/<review-id>/`, the exact outputs are:

```text
<review>.step09c_review_plan.tsv
<review>.step09c_evidence_index.tsv
<review>.step09c_orientation_locus_audit.tsv
<review>.step09c_annotation_audit.tsv
<review>.step09c_qc_funnel.tsv
<review>.step09c_replicate_effects.tsv
<review>.step09c_sensitivity_matrix.tsv
<review>.step09c_leave_one_pair_out.tsv
<review>.step09c_candidate_selection.tsv
<review>.step09c_candidate_adjudication.tsv
<review>.step09c_decisions.tsv
<review>.step09c_limitations.tsv
<review>.step09c_review_summary.tsv
```

The review summary records requested states and policy versions, evidence-
category states, decisions, counts, and exact path/hash/row-count provenance
for every primary input. It is published last as the native commit marker.
`computational_validation` is retained through the evidence index and its
external source; it has no dedicated normalized table among the 13 outputs.

[`step_09c_scientific_validation.py`](step_09c_scientific_validation.py)
owns all validation, normalization, state gating, locking, and publication.
Dry-run validates fully but creates no output directory. Execute mode acquires
an exclusive review lock, requires all 13 previous outputs or none, stages and
rereads every table, rechecks input hashes, removes a predecessor summary
marker first, publishes 12 payloads then the new summary, revalidates final
content/hashes, and rechecks inputs.

Failure removes a partial first publication or restores a byte-identical
predecessor with its summary last. Incomplete rollback retains the lock and
recovery paths and writes a recovery notice. The summary still becomes visible
before final post-publication checks and does not hash its 12 siblings; later
consumers must validate the entire package rather than trust marker presence.

[`step_09c_scientific_validation.sh`](step_09c_scientific_validation.sh)
is a thin public launcher. It validates CLI shape, resolves Python, delegates
all behavior, and preserves the implementation's exit status.

## Consumers and protected evidence

- The artifact index requires all 13 exact adapters and treats
  `step09c_review_summary_v1` as the failure marker while reconciling package
  rows, identities, decisions, evidence states, and upstream provenance.
- Run-summary science normalization accepts one explicit committed review
  summary, validates the complete public package and explicitly referenced
  evidence against indexed records, treats private source inputs as committed
  descriptors, and rejects ad hoc or glob-selected substitutes.
- Reporting consumes that normalized science record. Raw Step `09` candidates
  or a Step `09c` marker alone do not become biological conclusions.
- Direct shell/Python tests protect CLI delegation, incomplete and exploratory
  states, non-promotion, reserved-state rejection, evidence mutation,
  computational-claim gates, exact publication, locks, rollback, and recovery.
- Neutral
  [`test_review_package.py`](../../../../tests/contracts/scientific_evidence/test_review_package.py)
  independently protects the public roster, headers, vocabularies, bindings,
  state reduction, standard-library-only boundary, and shared package identity.
- Artifact, run-summary, report, and schema-parity tests protect downstream
  package-integrity, projection, and presentation boundaries.

This is local synthetic-fixture characterization. No production Step `09c`
package, completed production review, cluster proof, or biological-
interpretation readiness is established in this checkout.

## Current ownership boundaries and deferred decisions

- The review implementation imports neutral
  [`step08.py`](../../contracts/scientific_evidence/step08.py) for the public
  Step `08` manifest/table contract and shared `ContractError`/`Table`
  identity, and neutral
  [`step09.py`](../../contracts/scientific_evidence/step09.py) for the public
  Step `09` output contract. The Step `09` validator consumes both neutral
  owners directly; Step `09c` retains ten evidence domains, state policy, and
  transaction machinery.
- Public review-package roster, headers, vocabularies, bindings, and state
  reduction belong to neutral
  [`review_package.py`](../../contracts/scientific_evidence/review_package.py).
  This implementation, artifact indexing, and run-summary science import
  that standard-library-only package module.
- Artifact indexing and run-summary science no longer load this private
  implementation. Run-summary science uses a reporting-local reader/projection
  over the committed public package, explicitly referenced evidence, and
  validated artifact-index records; private review/input and publication policy
  remains here.
- Policy and evidence-input rules outside the neutral public contract remain
  owner-local across publication, artifact reconciliation, science
  normalization, and tests. Review-plan Git/software/runtime values are
  declared metadata, not independently observed environment facts.
- Separate modules for retained private schemas/policy, recovery tooling,
  reviewer workflow, and migration mechanics remain deferred.
