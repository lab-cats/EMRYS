# FUT-AGENT-01 — Evaluate persistent agent identity, context, and state

State: [`UNREFINED` proposal](README.md). File presence preserves this distinct
question; it authorizes no agent, service, memory store, identity, or spike.

## Proposal

Evaluate whether durable agent identity, context, or state could add measurable
value beyond explicit repository files, bounded skills and reviewer roles,
context packets, and stateless adapters. A later time-boxed experiment remains
an open choice rather than an assumed next step.

## Why preserve it

Continuity and specialization may reduce repeated work, but hidden persistence
can also retain stale context, obscure provenance and authority, or leak state
between projects. That tradeoff is separate from reusable skills or bounded
reviewer personas.

## Settled boundaries

- Persistent identity or memory cannot become canonical project state. Useful
  state must be explicit, inspectable, attributable, versioned, correctable,
  replaceable, and rebuildable from authorized sources where feasible.
- Persistence grants no standing authority to edit, integrate, push, publish,
  delete, promote evidence, or make architectural or scientific decisions.
- Privacy, secrets, operator identity, retention, expiry, reset, provenance,
  model-version drift, and cross-project isolation require an explicit policy
  before experimentation.
- Bounded personas and independent reviewer roles remain distinct and do not
  require persistent identity.
- This proposal neither approves nor rejects a spike.

## Questions before refinement

- What repeated failure or coordination cost cannot be solved by files,
  context packets, skills, or a stateless library, CLI, or MCP adapter?
- What would persist, where, for how long, and how would users inspect, reset,
  correct, or revoke it?
- How would permissions, provenance, model changes, operator identity, privacy,
  secrets, and project isolation be represented?
- How would the system fail closed when its state is unavailable, stale,
  contradictory, or ahead of canonical Git state?
- What comparison would justify or reject a small reversible experiment?

## Related proposals

- `FUT-AIDEV-01` owns the broader file-first kernel, project-profile, and live-
  state concept; an adapter must never become a hidden authority.
- Existing task-start, context-routing, and concurrent-lane practices, plus any
  later reviewed intake mechanism, are the nonpersistent comparison baseline.

These are refinement inputs, not dependency relationships.

## Promotion conditions

- Document repeated evidence that explicit files, bounded roles, and stateless
  adapters are insufficient for a named outcome.
- Define state, authority, privacy, expiry, reset, provenance, isolation, and
  fail-closed contracts.
- Decide explicitly whether a narrowly time-boxed experiment is warranted.
- Convert the result into a complete reviewed TODO card before any experiment.
