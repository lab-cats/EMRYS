# LOG-02 — Define logging contract

## Objective

Define stable console, durable-log, level, stream, failure-tail, and retention
semantics for local and SLURM execution.

## Why this exists

Users need a concise, relevant default and maintainers need complete diagnostics.
Those goals require two explicit sinks and stable invariants rather than ad hoc
print suppression.

## Fixed decisions

- Default console output is concise and directly relevant; verbose and debug
  modes remain available.
- Complete durable logs are produced for every adopted application operation
  attempt; established help, parser/control-failure, and valid dry-run
  invocations remain log-free.
- Machine output uses stdout; human logs use stderr.
- Changing log level never changes computational or publication behavior.

## Blocked by

- [LOG-01](../COMPLETED/LOG-01-characterize-current-output.md) — Required: current output and consumers must be fully mapped.

## Completion unblocks

- [LOG-03](../TODO/LOG-03-build-two-sink-logging-foundation.md) — Partially: implementation also waits for the independent reviews.

## Prerequisites

- Resolve every output item that currently mixes machine and human audiences.

## Required context

- `LOG-01`, public CLI/SLURM contracts, transaction/recovery evidence, ignored
  runtime paths, security policy, and validation-lane behavior.

## Questions owned by this card

- `CHOICE-LOG-01` and `CHOICE-LOG-02`, resolved by the approved
  [logging decision](../../design/DECISIONS.md#separate-concise-console-output-from-durable-detailed-logs)
  and [version-1 target contract](../../architecture/FUTURE_ARCHITECTURE.md#logging-target).

## In scope

- Public levels/flags, default messages, stream rules, durable record content,
  run/attempt identity, timestamps/context, failure summaries, retention
  ownership, and compatibility/error semantics.

## Out of scope

- Implementing the foundation, migrating stages, altering artifacts, changing
  exit codes, or defining production data-retention policy.

## Deliverables

- A logging contract with scenario matrix and concrete foundation/adoption
  inputs. This card does not create or name rollout cards.

## Acceptance evidence

- The contract serves scientist, operator, automation, and maintainer audiences
  without mixed streams or evidence loss.
- Equivalent runs at different levels preserve exact stable non-log payloads,
  hashes, states, ordering, and exits. Contract-declared volatile fields are
  compared only under controlled identity/time fixtures or exact documented
  normalization.

## Canonical documentation updates

- `DECISIONS.md`, `FUTURE_ARCHITECTURE.md`, `QUESTIONS.md`,
  `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if the design requires hiding a command needed for recovery, logging
  secrets, or treating scheduler files and application logs as interchangeable.

## Completion record

Completed as a documentation-only target contract on a fresh descendant of the
published LOG-01 reconciliation. The
[version-1 logging target](../../architecture/FUTURE_ARCHITECTURE.md#logging-target)
defines public controls and resolution, stdout/stderr ownership, console detail
levels, dry-run command visibility, one-writer operation-attempt JSONL,
identity/permissions/no-clobber rules, child diagnostic handling, receipt-safe
publication ordering, bounded failure summaries, redaction, retention,
scheduler separation, evidence-role authorization, a scenario matrix, and
foundation/adoption inputs.

The preserved `dad6b79` candidate supplied useful design structure but was not
merged, rebased, cherry-picked, or treated as current state because it descends
from the rejected pre-correction LOG-01 candidate. This reconciliation narrows
its evidence claims, distinguishes execution attempts from other identities,
keeps dry-run commands visible, defines one-writer cross-language ownership,
and resolves log/receipt ordering without weakening transaction markers.

No logger, entry-point migration, default activation, rollout card, output
behavior, artifact, hash, receipt, evidence state, validation selection,
transaction, rollback, cleanup, or exit behavior changed. Computational
validation was therefore not applicable; the documentation gate and exact
publication evidence are recorded in
[`HANDOFF.md`](../../operations/HANDOFF.md#immediate-resume-point). `LOG-03`
remains a separate implementation package requiring its own selection,
task-specific plan, and approval.
