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

- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent architecture/reliability/usability reviews must be incorporated.

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

- [`CHOICE-SIZE-01`](../../design/QUESTIONS.md#choice-size-01--step-08-r-decomposition-or-explicit-exception).

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

Not started. Select this card for read-only planning; implementation requires
separate approval.
