# REVIEW-ARCH-03C — Review `convert_GTF_to_BED12` migration architecture

## Objective

Challenge `MIG-03C` for one-owner placement, same-owner dependency direction,
complete caller cutover, test ownership, and reversible removal of all three
flat source paths.

## Why this exists

The validator imports normalization logic from its producer, the scheduler
embeds that producer's repository path, artifact evidence hashes the producer,
and several exact inventories assume mixed placement. A path-only-looking move
could create an accidental package, stage import, duplicate owner, weakened
roster, or permanent compatibility surface.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen semantic DAG, target home, and migration mechanics without
  reopening descriptor/package/reference-materialization design.
- Reject cross-owner imports, global path mutation, runtime discovery, duplicate
  assets, speculative wrappers, symlinks, compatibility copies, and another
  migration owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03C](REVIEW-REL-03C-review-convert-gtf-to-bed12-migration.md) — Fully: reliability review requires an architecture-corrected owner, caller, and rollback boundary.

## Prerequisites

- Review committed `MIG-03C` against frozen parent `1b82e4f` without running or
  changing executable/test files.

## Required context

- `MIG-03C`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `00b` contract/inventory; producer,
  validator, job, exact import/invocation graph, tests, artifact evidence,
  coverage identities, and every proposed current/final path.

## Questions owned by this card

- None.

## In scope

- Final-owner fitness; typed-external-input root selection; sibling producer
  import; scheduler-to-producer path; neutral report loading; artifact producer
  evidence; owner-local versus independent tests; explicit mixed-layout maps;
  wrapper necessity; atomic cutover; one-owner invariant; and rollback order.

## Out of scope

- Reliability fault detail except where ownership obscures it, code changes,
  package/descriptor/schema design, producer-independent validation,
  reference-materialization extraction, another stage, or a future unit.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact
  `MIG-03C` corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved source/test owner, dependency-direction, path consumer,
  wrapper, duplicate, atomicity, evidence identity, or rollback question.
- Every finding is incorporated into `MIG-03C` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03C`, roadmap/handoff only if current status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, a separate
  neutral extraction, or a supported caller that cannot cut over atomically.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `17ef13d` and JIT-definition checkpoint `44e3393`. One
high finding closes the sibling-import/test-loader gap: production retains its
same-owner bare import, while the shared exact-file test loader must bind and
path-validate the final producer module without `sys.path` mutation, reject a
foreign cache, and reproduce both sibling files in copied fault layouts. One
medium finding makes the job/producer atomicity explicit: the job's only source
change is its delegated final producer path, so the old job hash is rollback
evidence while the byte-identical producer hash remains artifact evidence.
Another medium finding requires every mixed-layout inventory to retain literal
basename/semantic-ID path maps and exact one-owner equality, and keeps Step
`00b` mocked behavior owner-local while independent scheduler assertions remain
cross-owner. The typed-external-input root selection, neutral-report dependency,
artifact path transition, no-wrapper decision, final homes, reverse rollback,
and no-package/descriptor/schema boundary otherwise pass. The DAG and public
artifact flow do not change, so no diagram edit is justified. The same campaign
agent authored/reconciled and reviewed the plan; independent authorship is not
claimed. No executable/test file changed and no computational test ran.
