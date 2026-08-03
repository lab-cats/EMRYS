# REVIEW-ARCH-03E — Review `construct_FASTA_sidecars` migration architecture

## Objective

Challenge `MIG-03E` for dependency-valid selection, one-owner placement,
complete caller cutover, temporary reference-provenance bridging, test
ownership, and reversible removal of all three flat native-asset paths.

## Why this exists

The job embeds the producer path, the validator combines a final neutral report
library with an ambient flat reference-provenance import, artifact evidence
hashes the producer, and public CLI/tests assume flat placement. A relocation
could introduce a hidden package/import dependency, duplicate an owner, or
silently promote a deferred shared-library decision.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen semantic DAG, target home, and direct-migration mechanics
  without reopening descriptors, packaging, reference-library extraction,
  transactions, or reference policy.
- Reject peer-stage imports, global path mutation, runtime discovery, duplicate
  assets, speculative wrappers, symlinks, compatibility copies, and another
  migration owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03E](../TODO/REVIEW-REL-03E-review-construct-fasta-sidecars-migration.md) — Fully: reliability review requires an architecture-corrected owner, import, caller, and rollback boundary.

## Prerequisites

- Review committed `MIG-03E` against frozen parent `5259acb` without running or
  changing executable/test files.

## Required context

- `MIG-03E`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `00c` contract/inventory; producer,
  validator, job, exact invocation/import graph, tests, reference-provenance
  implementation/consumers, artifact evidence, coverage identity, and every
  proposed current/final path.

## Questions owned by this card

- None.

## In scope

- DAG eligibility; final-owner fitness; job delegation; neutral report loading;
  temporary exact-file reference-provenance loading; separation from the
  public provenance CLI and Step `05` consumer; artifact producer evidence;
  owner-local versus independent tests; explicit mixed-layout maps; wrapper
  necessity; atomic cutover; permissible path-only source edits; one-owner
  invariant; and rollback order.

## Out of scope

- Reliability fault detail except where ownership obscures it, code changes,
  package/descriptor/schema design, reference-provenance extraction, scheduler
  hardening, validator redesign, another stage, or a future unit.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact
  `MIG-03E` corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved source/test owner, dependency direction, import identity, path
  consumer, wrapper, duplicate, atomicity, evidence identity, or rollback
  question.
- Every finding is incorporated into `MIG-03E` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03E`, roadmap/handoff only if current status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, moving or
  modifying `reference_provenance.py`, a second owner, or a supported caller
  that cannot cut over atomically.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `79af085` and JIT-definition checkpoint `3c6aaf0`.

One high finding makes the temporary reference-provenance dependency fully
explicit and testable. The final validator uses private identity
`_norad_reference_provenance`, resolves only the unchanged
`scripts/reference_provenance.py`, verifies exact `__file__` and the four-symbol
API (`ProvenanceError`, `parse_fasta`, `parse_fai`, `parse_dict`), removes only
its owned partial cache on execution failure, preserves foreign cache state and
`sys.path`, and emits one path-bearing fail-closed diagnostic. The separate
module has no readiness sentinel, so the migration may not edit it to create
one. This bridge is accepted only as bounded mixed-layout debt; it does not
approve a neutral extraction, package identity, or Step `05` change.

A second high finding freezes the atomic executable/test cutover to exactly
fourteen tracked files: five native/test moves and nine explicit Make,
artifact, CLI, SLURM, roster, loader, coverage, and literal-expansion callers.
The moved tests receive only root/path corrections plus later review-approved
parity oracles. Any fifteenth path reopens architecture review before mutation.

One medium finding routes the non-flat final validator through the existing
shared path-validating test loader while still-flat validators retain module-
name imports. Another keeps all scheduler behavior in the independent
parametrized wrapper suite; only the two direct owner tests move. No wrapper,
duplicate, package marker, descriptor, schema, runtime discovery, global path
mutation, or future-owner change is justified.

The no-predecessor DAG eligibility, final homes, artifact identities, direct
cutover, one-owner invariant, documentation-after-executable order, and reverse
rollback otherwise pass. The DAG and public artifact flow do not change, so no
diagram edit is justified. The same campaign agent authored/reconciled and
reviewed the plan; independent authorship is not claimed. No executable/test
file changed and no computational test ran.
