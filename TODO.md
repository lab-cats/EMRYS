# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

If [`HANDOFF.md`](docs/operations/HANDOFF.md#immediate-resume-point) records an
external or non-reconstructable resume boundary, honor it. Otherwise no
successor is implied: inspect the derived task view and roadmap, then select and
approve one dependency-valid package. Selection does not change card state or
create a status commit.

## Canonical routes

- Task scope, dependencies, acceptance, and lifecycle:
  [`task registry`](docs/tasks/README.md).
- Roadmap order and package acceptance:
  [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).
- Current checkout, evidence, and exact resume point:
  [`HANDOFF.md`](docs/operations/HANDOFF.md). Live blockers remain in its
  [current-blockers section](docs/operations/HANDOFF.md#current-blockers).
- Open operational and scientific evidence gaps:
  [`QUESTIONS.md`](docs/design/QUESTIONS.md#operational-and-scientific-evidence).
