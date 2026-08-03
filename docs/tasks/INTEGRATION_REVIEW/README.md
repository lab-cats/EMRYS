# Integration-review task cards

This directory contains full task cards whose exact candidate handoff is frozen
and awaiting asynchronous canonical integration beyond the current unpublished
integration package.

- Only the canonical integration owner may move a card here and repair every
  inbound lifecycle link in the same commit.
- Same-package handoff and integration remain `IN_PROGRESS`; they do not create
  a durable review transition.
- Scope and candidate bytes cannot change here. A correction returns the card
  to `IN_PROGRESS` before authoring resumes.
- `COMPLETED` remains unavailable until canonical integration, final
  validation, publication, and upstream equality are complete.
- Exact candidate SHA, worktree, checks, fragment, and lane identity remain in
  the live handoff rather than being copied into the card.

Cards retain the complete actionable schema and dependency rules in
[`../README.md`](../README.md).
