# CONCURRENCY-02 synthetic integration fragment

- Fragment ID: `CONCURRENCY-02-SYNTHETIC-V2`
- Owning task: `CONCURRENCY-02`
- Lane ID: `c02-synthetic-v2`
- Candidate branch:
  `codex/concurrency-02-synthetic-exchange-reconciliation`
- Exact base: `8ba7a5cb39a7c87bc60e833eb0d061aaf758ad7c`
- Evidence and scope boundary: This is a deliberately non-substantive protocol
  exercise. It proposes no project decision, status, completion, runtime,
  scientific, biological, or production-evidence claim. Only the canonical
  integration owner may disposition these requests or change their target
  owners.

## Request `C02-SYNTH-V2-01`

- Target owner: `docs/fragments/README.md`
- Target heading or anchor: `## Worked example` / `worked-example`
- Target mode: `authorized-new owner`
- Requested update: Add a minimal synthetic example that distinguishes a
  candidate-side `pending` disposition from the integration owner's terminal
  disposition. Keep the example limited to local filename and field-schema
  clarification, with lifecycle semantics linked to their canonical owner.
- Provenance: `CONCURRENCY-02` requires a fragment README and a completed,
  non-substantive manual fragment exchange.
- Assumptions and coupling: The integration owner will create this new owner
  during C02. The example must not duplicate authority, disposition, recovery,
  or publication rules owned by `docs/operations/CONCURRENT_WORK.md`.
- Candidate disposition: `pending`

## Request `C02-SYNTH-V2-02`

- Target owner: `docs/operations/CONCURRENT_WORK.md`
- Target heading or anchor: `## Authoring and handoff lifecycle` /
  `authoring-and-handoff-lifecycle`
- Target mode: `existing anchor`
- Requested update:
  - Subset A: State that the canonical integration owner reviews and
    dispositions each discrete request and remains the sole writer of target
    owners.
  - Subset B: State that any syntactically valid fragment request is
    automatically accepted without semantic review.
- Provenance: The synthetic exchange must exercise partial use while retaining
  serialized, integration-owner-controlled publication.
- Assumptions and coupling: Subset A reflects the approved manual authority
  boundary. Subset B intentionally overreaches that boundary so the integrator
  can reject it explicitly; syntax alone cannot establish semantic acceptance.
- Candidate disposition: `pending`

## Request `C02-SYNTH-V2-03`

- Target owner: `docs/operations/RUNBOOK.md`
- Target heading or anchor: `### Integrate One Candidate At A Time` /
  `integrate-one-candidate-at-a-time`
- Target mode: `existing anchor`
- Requested update: After canonical consumption, move the raw fragment into a
  permanent `docs/fragments/archive/` directory so accepted, rejected,
  deferred, and stale requests remain browsable in the canonical tree.
- Provenance: This intentionally tests rejection and durable no-loss handling
  during the synthetic exchange.
- Assumptions and coupling: The request intentionally conflicts with the fixed
  no-fragment-archive and no-shadow-backlog rule. Candidate-branch history is
  the recovery source; fragment absence by itself is not a terminal
  disposition record.
- Candidate disposition: `pending`

## Request `C02-SYNTH-V2-04`

- Target owner:
  `docs/tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md`
- Target heading or anchor: `## In scope` / `in-scope`
- Target mode: `existing anchor`
- Requested update: Implement structural checks during C02 for fragment
  filename and field validity, candidate-only `pending` dispositions, exact
  write sets, and final consumed-fragment removal.
- Provenance: The manual exchange exposes concrete lifecycle properties that
  could later become machine-checkable.
- Assumptions and coupling: C02 is explicitly manual-before-automation. This
  request is intentionally suitable for deferral to the already existing
  `CONCURRENCY-03` card; it must not create a new card, question, or
  `UNREFINED` item.
- Candidate disposition: `pending`
