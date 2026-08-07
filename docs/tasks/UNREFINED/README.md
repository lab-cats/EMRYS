# UNREFINED — Proposal intake

`UNREFINED` preserves useful ideas without placing them on NORAD's committed
roadmap or making them actionable task cards.

- Proposals here cannot be selected, started, placed in dependency
  relationships, or used to block or unblock work.
- They claim no implementation, planning, priority, lifecycle, or publication
  authority.
- Rough questions, incomplete scope, and unresolved design choices may remain
  until a proposal is deliberately refined.
- Promotion to `docs/tasks/cards/` requires explicit review, the complete
  stable-card contract, and an integration-owner decision.
- File presence preserves the proposal; it does not approve its implementation.

Each proposal must have exactly one `# CARD-ID — Title` H1, a matching
`CARD-ID-*.md` filename, and the exact local declaration
``State: [`UNREFINED` proposal](README.md). ...``. These core headings occur once
and in this order:

1. `Proposal`
2. `Why preserve it`
3. `Settled boundaries`
4. `Questions before refinement`
5. `Promotion conditions`

Additional proposal headings may preserve useful context. Headings from the
full actionable-card schema and dependency-edge syntax are prohibited.
Proposals are excluded from actionable-card counts; the documentation gate
validates these rules directly.

`cards/` is the only location for a new actionable card. Translating an
unrefined proposal into that registry is an integration action, not an
automatic consequence of age, detail, related work, or file presence.
