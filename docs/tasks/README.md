# Task registry

Task cards are temporary specifications for actionable work. They are not a
historical archive: when a card is completed or retired, delete it. Git preserves
the former scope and evidence.

Existing cards keep their current paths under `TODO/`, `IN_PROGRESS/`, or
`INTEGRATION_REVIEW/`; selecting, pausing, resuming, or completing work does
not move or rewrite a card. New actionable cards start under `cards/`.
Nonselectable proposals remain under `UNREFINED/`.

## Read-only status

From the repository root:

```bash
./scripts/git_orchestration/task_status.py --repo "$(git rev-parse --show-toplevel)"
```

The output is derived from the surviving card files and is not registry
authority.

## Actionable-card contract

Actionable cards retain this heading order:

1. `Objective`
2. `Why this exists`
3. `Fixed decisions`
4. `Blocked by`
5. `Completion unblocks`
6. `Prerequisites`
7. `Required context`
8. `Questions owned by this card`
9. `In scope`
10. `Out of scope`
11. `Deliverables`
12. `Acceptance evidence`
13. `Canonical documentation updates`
14. `Escalation conditions`
15. `Completion record`

## Dependency semantics

Dependency lines use the following shape, with real IDs and relative paths:

```text
- CARD-ID, relative/path.md — Required: reason
- CARD-ID, relative/path.md — Fully: result
- CARD-ID, relative/path.md — Partially: result
```

Use `- None.` when a section has no edges. A referenced card that still
exists is an open dependency. A referenced card that has been deleted is
treated as satisfied; surviving cards are intentionally not repaired when
completed cards disappear. Self-dependencies and cycles among surviving cards
remain invalid.

A card owns only its bounded objective, dependencies, deliverables, acceptance,
documentation triggers, and escalation conditions. Current state, commands,
topology, rationale, and evidence belong in their canonical documents.

## `UNREFINED` proposals

`UNREFINED` preserves rough ideas without making them selectable work. Each
proposal has exactly one H1, the standard proposal-state line, and these
headings in order:

1. `Proposal`
2. `Why preserve it`
3. `Settled boundaries`
4. `Questions before refinement`
5. `Promotion conditions`

Proposals do not carry task dependencies, priority, implementation authority,
or completion records. Promotion requires explicit review and a new actionable
card; do not mutate the proposal into one.

## Validation

`make -s documentation-check` validates live-document links and anchors,
Mermaid sources, proposal shape, actionable-card structure, and dependency
cycles among surviving cards. Link targets inside card bodies and
`docs/history` are intentionally frozen and are not path-repair obligations.
