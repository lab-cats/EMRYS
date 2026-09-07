# Workflow kernel

This is the repository-development workflow. [`AGENTS.md`](../../AGENTS.md)
supplies safety and authority. A selected findings-matrix item or explicitly
bounded objective supplies scope and acceptance, never additional authority.

## Start

1. Read the current root safety guard.
2. Verify the repository root, branch, `HEAD`, changes, upstream relation, and
   relevant competing worktrees from live Git.
3. Read the selected row in
   [`backlog_matrix.md`](../tasks/backlog_matrix.md) and any approved package
   boundary in full.
4. Read the affected implementation, adjacent contract or orientation,
   callers, consumers, tests, and fixtures.
5. Load only the cross-cutting architecture, decision, operation, or evidence
   section directly needed for that boundary.

Do not infer current state from memory, old summaries, branch names, historical
test totals, or prior handoffs. Reuse prior context only when the exact revision
is known and the live diff proves the relevant source unchanged.

Broaden the review when it reveals a public or scientific contract, shared
code, schema, dependency, generated input, security, concurrency, persistence,
recovery, publication, evidence, destructive action, or impact that cannot be
confidently bounded.

State the outcome, touched owners, exclusions, local feedback, required CI,
evidence ceiling, and stopping condition. Obtain approval before mutation.

## Design and compression

Before implementation, audit the entire touched vertical for duplicate callers,
branches, adapters, validation, compatibility, scripts, configuration, docs,
tests, and mutable state. Check the existing owner, standard library, mature
libraries, and package managers before adding bespoke machinery. Apply the
permanent [architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).

New public commands/options, schemas, receipts, supported paths, dependencies,
workflow rules, owners, shared seams, recovery mechanisms, or other maintained
surfaces require explicit approval. An implementation defaults to a meaningful
net reduction in maintained product code and no product-file growth. Stop for
approval of a quantified exception; moving logic or deleting unrelated tests,
documentation, or evidence does not satisfy it.

## Deliver

- Work in one authoritative worktree. Keep a slice to one observable outcome
  and coherent owner boundary.
- Change implementation, direct protection, exact contract, and affected
  documentation together. One semantic commit is the default.
- Move ownership caller-completely. A temporary compatibility path needs an
  owner, parity protection, and retirement condition; it is not completion.
- Preserve immutable boundary values. Mutable draft, Attempt, lock, log, or
  transaction state remains inside its narrow owner and cannot alter a Run.
- Replace high-risk protection only with an equal-or-stronger defense at the
  same evidence level. Follow the explicit approval boundary in the
  architecture guardrails.
- Evidence deletion is never implied by implementation approval. It requires an
  exact proposal, explicit approval, and a separate commit.
- Use focused local checks for feedback. Run one deduplicated applicable gate
  on the final state; long lanes run in CI. Rerun only evidence invalidated by a
  later change.
- Stop for scope expansion, unresolved semantics, unsafe recovery, missing
  required evidence, or an external decision. Do not absorb unrelated findings.

## Documentation and tasks

Update documentation only when its subject changes. Keep purpose and durable
rationale in role or cross-cutting guides, exact behavior beside the owner, and
machine-verifiable detail in schemas and tests. Do not preserve routine progress,
branch names, repeated totals, superseded planning, or a second status registry.

The findings matrix owns stable IDs, status, required outcomes, acceptance,
scores, and terminal dispositions. When closing or retiring an item, update its
row and every live reference in the same change. Preserve durable contracts,
safety rules, defects, decisions, and evidence ceilings before deleting their
old home; Git retains chronology and deleted wording.

## Close and publish

Review the complete semantic diff, verify acceptance, and record what actually
ran with the correct evidence ceiling. For architecture work, report product,
tests/protections, configuration/docs, evidence, public concepts,
compatibility, and mutable-state changes separately. Commit the coherent result.
Push, merge, cluster execution, dependency installation, destructive cleanup,
and evidence promotion remain separate unless explicitly included in the
approved scope. After publication, verify the intended remote ref and exact
upstream equality.
