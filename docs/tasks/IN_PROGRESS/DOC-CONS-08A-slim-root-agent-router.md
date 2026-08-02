# DOC-CONS-08A — Slim the root agent router

## Objective

Reduce `AGENTS.md` to automatically needed project guardrails and canonical
routes while relocating every detailed repository convention without loss.

## Why this exists

The root instructions currently combine approval and safety guards with
operations procedure, topology, current-layout detail, and cross-language
engineering conventions. Automatic loading protects critical rules but makes
every task pay for unrelated detail and leaves several facts with two owners.

## Fixed decisions

- Follow the rule-by-rule disposition in
  [`DOCUMENTATION_OWNERSHIP.md`](../../sitemap/DOCUMENTATION_OWNERSHIP.md#agentsmd-rule-disposition).
- Keep approval, destructive-action, shared-worktree, local/cluster/data,
  evidence-language, and biological-interpretation guards automatically
  reachable from the root file.
- Create `docs/operations/ENGINEERING_CONVENTIONS.md` as the neutral owner for
  cross-language current-workflow conventions; stage-specific detail remains
  in colocated contracts.
- Move content, repair links, and remove the old copy in the same coherent
  change. Do not leave a permanent compatibility copy.
- Generic reusable preferences remain in the repository until a separately
  authorized global owner is verified.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: every current rule needs an approved destination and reachability boundary.

## Completion unblocks

- None.

## Prerequisites

- Compare the live `AGENTS.md` rule by rule with the frozen disposition; do not
  rely on historical line numbers alone.

## Required context

- `AGENTS.md`, the ownership map's responsibility and rule-disposition
  sections, `TASK_START.md`, `TASK_DELIVERY.md`, `CONCURRENT_WORK.md`, and only
  the directly affected contract or operations owner needed for one rule.

## Questions owned by this card

- None.

## In scope

- Creating the neutral engineering-conventions owner.
- Relocating repository layout, script/publication, R, and SLURM convention
  detail to that owner or an exact functional contract.
- Replacing moved root detail with concise canonical routes.
- Verifying the DOC-IA corrections to the universal thin-wrapper and target-
  owner claims remain accurate while their surrounding detail moves.
- Repairing direct inbound links and checking the proposed root file is
  materially shorter.

## Out of scope

- Editing global agent guidance, executable behavior, public interfaces,
  scientific policy, current state, task lifecycle, or source layout.
- Relocating `TOP_LEVEL.md` temporary blocks or cleaning `TASK_START.md` stubs;
  those remain the exact scope of `DOC-SITEMAP-01`.

## Deliverables

- A concise root `AGENTS.md`, one neutral engineering-conventions owner, and an
  updated no-loss disposition tied to the final live rules.

## Acceptance evidence

- Every input rule is retained, relocated, intentionally repeated, or removed
  only after its verified owner exists.
- Critical approval, safety, evidence, destructive-action, and scientific
  guards remain automatically reachable.
- No detailed command, mutable status, topology table, or duplicate ownership
  roster remains in the root router.
- All affected links and the documentation gate pass.

## Canonical documentation updates

- `AGENTS.md`, `docs/operations/ENGINEERING_CONVENTIONS.md`, the documentation
  ownership map, affected direct routes, and this card.

## Escalation conditions

- Stop if a rule has no durable owner, the root and a destination disagree, or
  relocation weakens an automatically loaded safety/scientific guard.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
