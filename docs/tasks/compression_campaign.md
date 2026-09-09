# Compression campaign

Started **2026-09-02**. This campaign makes EMRYS smaller and easier to
understand: less duplicated code, fewer competing explanations, and ordinary
language and programming patterns that a new contributor can follow.
Documentation reduction and readability are primary outcomes. Formatting
alone does not make complicated code idiomatic.

## Working authority

The [temporary backlog](compression_backlog_matrix.md) owns the CS cards,
their scope, status, decisions, and evidence. The main matrix's
[`COMPRESS-01`](backlog_matrix.md#repository-maintenance) owns campaign completion.
The temporary format follows the architecture campaign and backlog at
`b9cf4767e6ebdf686070410f06b9cc9298582979`, before their retirement in `fe9f99a5`.

## Scope and next tranche

- **Documentation:** give each owner a clear responsibility and each subject
  one authoritative explanation. Move misplaced information to its proper owner
  and verify the transfer before removing it. Make all documentation readable
  for its intended audience: explain purpose and unfamiliar terms before
  details, and keep complete procedures, useful examples, and necessary limits.
- **Code:** simplify complete responsibilities using the existing owner,
  standard library, and established language patterns. Retire equivalent
  implementations across every applicable caller. A new wrapper or a split
  into more files is not an outcome by itself.
- **Tests and supporting files:** remove redundancy with the implementation
  it protects, while retaining independent scientific checks and recovery proof.

The [working queue](compression_backlog_matrix.md#working-queue) records the
approved documentation work and larger code targets. Small cleanups accompany
relevant work; they do not lead another substantial tranche. The dashboard
stays until its replacement is implemented and validated.

Follow the [workflow](../operations/WORKFLOW.md) and
[architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
Report product, test, documentation, configuration, tooling, and evidence
changes separately. Documentation-only work must reduce and improve the
documentation; it cannot offset product growth. Preserve scientific meaning,
immutable Runs, public behavior, historical readers, and recovery guarantees.
Changing those guarantees or deleting retained evidence needs its own approval.

## Completion and retirement

Each card needs a verified result or a reasoned retain/reject/transfer decision.
One repaired example does not close a whole family. Preserve useful decisions,
counterexamples, and evidence limits in the existing subject owner, and place
unfinished accepted work in the main matrix before retiring either temporary
document. Verify those transfers and live links, then obtain the user's final
disposition. The campaign remains open until both code and documentation
obligations are accounted for.
