# SIZE-07E — Resolve Step 08 R module size

## Objective

Resolve the Step `08` R module's mandatory size-policy conflict through proven
non-algorithmic decomposition or an explicit time-bounded exception.

## Why this exists

The roughly 1,900-line module exceeds the mandatory threshold, while the
existing refactor audit forbids changing Steps `07`–`09` scientific algorithms
without runtime evidence and separate authorization. Line-count policy cannot
silently override scientific safety.

## Fixed decisions

- Do not alter Step `08` orientation, allele, filtering, annotation, or
  transformation semantics without separate scientific/runtime authorization.
- Prefer extraction only when a seam is demonstrably non-algorithmic and exact
  parity is independently proven.
- Otherwise record an explicit exception with owner, rationale, expiry/recheck
  trigger, and future evidence requirement.

## Blocked by

- None.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- At task start, refresh only
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.R`:
  record its live line count, responsibilities, callers, scientific/contract
  risks, and mandatory disposition. Do not run or require a repo-wide size
  inventory.
- Inspect guarded real-R coverage, committed fixtures, function boundaries,
  runtime/cluster evidence, and scientific authorization state.

## Required context

- `RA-008`, `RA-025`, Step `08` R source, shell/real-R/Python validation layers,
  orientation decisions, output schemas, and size policy.

## Questions owned by this card

- Resolved [`CHOICE-SIZE-01`](../../design/QUESTIONS.md#resolved-index).

## In scope

- Scientific-neutrality analysis, exact parity plan, non-algorithmic extraction
  if authorized, or explicit exception and recheck trigger.

## Out of scope

- Statistical/scientific changes, production reruns, module rewrites for style,
  or claiming runtime/cluster proof from local fixtures.

## Deliverables

- One approved disposition, evidence supporting it, and bounded implementation
  cards if neutral extraction requires more than one concern.

## Acceptance evidence

- The completion record captures the target-only starting and resulting size,
  responsibility/caller map, extracted seam or approved exception, and final
  size disposition.
- Extraction path: exact shell/real-R/Python output, error, ordering, hash, and
  transaction parity passes with scientific functions unchanged.
- Exception path: explicit user approval, scope, rationale, owner, expiry, and
  recheck evidence are canonical.

## Canonical documentation updates

- `DECISIONS.md` for an exception, `REFACTOR_AUDIT.md` disposition,
  `QUESTIONS.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop unless neutrality is demonstrable; any algorithmic seam requires
  inspected runtime evidence and explicit scientific authorization.

## Completion record

Completed in the explicitly approved PI-readiness tranche through the
non-algorithmic extraction path; no size exception was required. The
target-only refresh measured
`src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.R`
at 1,939 lines and 69,505 bytes. The public R program owns declared Step `07`
input admission, annotation and feature handling, allele/orientation and VCF
processing, Step `07` receipt reconciliation, deterministic three-table
serialization, and main orchestration. Its direct callers are the adjacent
shell transaction owner, the SLURM wrapper through that shell, the guarded
real-R fixtures, and explicit diagnostic direct invocation.

The exact original `ARGUMENT_NAMES` plus the 22-function argument, path,
manifest, selector, region, and partition-admission block now live unchanged in
the adjacent 524-line owner-private `_step_08_input_contract.R`. The public
facade is 1,454 lines and resolves the required sibling from Rscript's exact
`--file=` path before `main`, with no working-directory search/change or
package-loading side effect. The shell's `--r-script` and `STEP08_R_SCRIPT`
routes remain whole-program diagnostic replacements.

All annotation, allele, orientation, VCF transformation, serialization,
reconciliation, and main bodies remain text-identical in the public file. The
remaining facade exceeds the 1,000-line planning threshold but is retained as
one cohesive scientifically sensitive implementation/serialization boundary:
further extraction would enter algorithms explicitly barred from this slice,
while the file is now below the mandatory 1,500-line threshold. The helper is
below 600 lines.

Focused local evidence passed on the final tree: the guarded `NORAD_USE_RENV`
real-R semantic, deterministic-output, and negative-fixture suite; the fake
shell/transaction suite; 17 Python validator tests; 16 targeted SLURM cases;
both R parses; Bash syntax; root and foreign-CWD help; no-argument and missing-
sibling errors; exact moved-block/scientific-suffix parity; mode checks; and
`git diff --check`. This is local fixture/runtime parity only and adds no
production-scale, cluster, scientific-review, or biological proof.
