# LOG-03 — Build two-sink logging foundation

## Objective

Implement the neutral logging foundation that separates concise console output
from complete operation-attempt durable logs.

## Why this exists

Per-script print edits would drift and could alter stream contracts. A small
foundation is needed before bounded domain adoption, but it must remain neutral
and avoid becoming a hidden orchestration framework.

## Fixed decisions

- Follow the approved level, stream, durable-log, and invariance contract.
- Machine output stays on stdout; human output stays on stderr.
- Durable detail is retained for every adopted application operation attempt;
  established help, parser/control-failure, and valid dry-run invocations
  remain log-free. Console level affects presentation only.
- Foundation code lives in the narrowest neutral target owner and never imports
  stages.

## Blocked by

- [LOG-02](../COMPLETED/LOG-02-define-logging-contract.md) — Required: exact public logging semantics must be approved.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent plan reviews must be incorporated.

## Completion unblocks

- [LOG-05](../TODO/LOG-05-activate-concise-default-logging.md) — Partially: every concrete `LOG-04-*` domain-adoption card must also complete before activation.

## Prerequisites

- `PLAN-02Z` must have created concrete, non-wildcard `LOG-04-*` adoption cards
  for all applicable domains.

## Required context

- Logging contract/inventory, target topology, public CLI and scheduler
  contracts, run/attempt identity, current ignored log paths, and failure tests.

## Questions owned by this card

- None.

## In scope

- Level parsing/validation, sink routing, durable context/identity, failure
  flush/tail behavior, neutral APIs, and independent foundation tests.

## Out of scope

- Migrating every stage, changing defaults, altering exits/artifacts, logging
  secrets, or implementing retention cleanup.

## Deliverables

- Neutral foundation, public API tests, and one representative adoption proving
  behavior invariance without broad rollout.

## Acceptance evidence

- Equivalent runs at every level preserve exact stable non-log artifacts,
  hashes, states, rollback, ordering, and exits. Contract-declared volatile
  receipt/output fields match under controlled or normalized comparison.
- Stream separation, severity/detail mapping, lossless diagnostic-byte
  encoding, sensitive `durable_only` child handling, sanitized failure tails,
  complete durable detail, interruption/failure flushing, and invalid-level
  behavior pass focused tests.

## Canonical documentation updates

- Current architecture, logging/local library README, `RUNBOOK.md` for exact
  interfaces, `TROUBLESHOOTING.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, and this
  card.

## Escalation conditions

- Stop if the foundation requires stage awareness, changes a machine stream,
  drops failure evidence, or introduces automatic log deletion.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
