# Compression campaign — closed

Started **2026-09-02**; closed by the user on **2026-09-14** after
[PR #169](https://github.com/lab-cats/EMRYS/pull/169) merged at `2ecf7d44`.
The campaign reduced duplicated code and competing documentation, clarified
ownership, and made retained explanations and implementations easier to follow.
Formatting alone was not treated as simplification.

## Recorded authority

[`COMPRESS-01`](backlog_matrix.md#repository-maintenance) records closure.
The [closed compression backlog](compression_backlog_matrix.md) retains the
CS cards, decisions, counterexamples and evidence; it is no longer a work queue.
Accepted unfinished work stays with its existing owners in the main matrix,
polish campaign and optimization campaign, as linked in the
[disposition record](compression_backlog_matrix.md#original-discovery-disposition).
The temporary format followed the architecture campaign and backlog at
`b9cf4767e6ebdf686070410f06b9cc9298582979`, before their retirement in `fe9f99a5`.

## Scope and results

- **Documentation:** give each subject one owner, move useful information
  before retiring duplication, and explain purpose and unfamiliar terms before
  detail. Preserve complete procedures, examples, decisions and evidence limits.
- **Code:** simplify complete responsibilities through existing owners and
  established language patterns; migrate equivalent callers together. Wrappers
  and file splits do not themselves count as compression.
- **Tests and supporting files:** remove demonstrated redundancy while
  preserving independent scientific checks and recovery protections.

Product fell from **69,223 to 55,862 lines** against the agreed `cab77a26`
baseline: **13,361 fewer lines (19.30%)**. The 20% target was not reached;
484 more lines would have been required. The user closed this campaign at
that result. Separate integration accounting and exact validation evidence are
in the [closed backlog](compression_backlog_matrix.md#working-queue).

## Completion and retirement

All 43 cards have a completed or transferred disposition. CS-05 remains with
`REPORT-ROSTER-01`; dashboard retirement still requires a validated replacement.
Scientific meaning, provenance, immutable Runs and current recovery remain
required. Hosted software and disposable-Slurm checks do not establish
institutional-site, scientific-review or biological validation.

The campaign and backlog remain as closed records. No retained evidence or
unresolved decision was deleted. Further work requires its own selection and
authority under the [workflow](../operations/WORKFLOW.md) and permanent
[architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
