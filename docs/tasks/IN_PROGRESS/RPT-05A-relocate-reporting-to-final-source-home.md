# RPT-05A — Relocate reporting to final source home

## Objective

Move reporting ownership directly into `src/norad/reporting` using the approved
temporary-wrapper and parity pattern.

## Why this exists

Reporting is a substantial domain, not a loose script collection. Its final
home should be inside the installable source tree because it is application
logic, while report assets remain explicitly owned and inspectable.

## Fixed decisions

- Target `src/norad/reporting`, not a root-level reporting implementation tree.
- Use a direct cutover when every known repository caller can move atomically;
  a root wrapper is allowed only for a named temporarily unmovable caller and
  must be removed inside this card.
- Preserve comprehensive/science behavior, explicit inputs, deterministic
  outputs, transaction/recovery semantics, and direct/Make invocation parity.
- Do not combine relocation with internal decomposition.
- Preserve QMD/CSS content hashes while recording their truthful new physical
  paths. Exact old-to-new physical-path substitutions in repository callers,
  help/usage and path diagnostics, delegated-command output, Make-expansion
  goldens, and path-bearing fixtures are approved relocation deltas. Product
  report bytes may change only through the exact path-valued QMD/CSS provenance
  fields derived from that substitution; every non-path byte or behavior
  change stops the card.

## Blocked by

- [LIB-02J](../COMPLETED/LIB-02J-remove-run-summary-private-step09c-dependency.md) — Required: the completed removal of reporting's private Step `09c` implementation dependency is the satisfied prerequisite for this move.

## Completion unblocks

- [RPT-03](../TODO/RPT-03-build-format-neutral-report-projection.md) — Partially: feature implementation also requires its approved science contract and independent review.
- [RPT-05B](../TODO/RPT-05B-decompose-report-rendering-modules.md) — Fully: decomposition can occur inside the final ownership boundary.
- [SIZE-07A](../TODO/SIZE-07A-decompose-artifact-index-builder.md) — Partially: decomposition also requires its live size refresh and independent review.
- [SIZE-07D](../TODO/SIZE-07D-decompose-run-summary-builder.md) — Partially: decomposition also requires its live size refresh and independent review.

## Prerequisites

- Completed [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md)
  fixes the neutral scientific-contract and reporting-local dependency
  directions; completed
  [MIG-04A](../COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
  places neutral artifact contracts in their permanent owner; and completed
  [LIB-02G](../COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md)
  places the public Step `08` contract and shared error/table identity in their
  final neutral owner; and completed
  [LIB-02H](../COMPLETED/LIB-02H-extract-step09-scientific-evidence-contract.md)
  places the public Step `09` output contract in its final neutral owner; and
  completed
  [LIB-02I](../COMPLETED/LIB-02I-extract-step09c-review-package-contract.md)
  places the public Step `09c` review-package contract in its final neutral
  owner; and completed
  [LIB-02J](../COMPLETED/LIB-02J-remove-run-summary-private-step09c-dependency.md)
  replaces reporting's private Step `09c` implementation edge with the
  reporting-local committed-package reader/projection required before this
  move.
- Reinspect all report imports, direct scripts, Make targets, assets, tests,
  Quarto inputs, arbitrary-CWD cases, packaged-asset constraints, and the
  artifact-schema receipt fixture that embeds the current QMD path.
- Verify that neutral artifact contracts occupy their final home and that no
  reporting module imports Step `09c` or another functional owner's private
  implementation. Reverify, but do not recreate or broaden, the completed
  reporting-local reader/projection boundary.

## Required context

- Target topology, direct-migration mechanics, report contracts/tests, CLI
  characterization, current report assets, and non-Python asset ownership.

## Questions owned by this card

- None.

## In scope

- Physical relocation, import/caller/test/doc migration, temporary shims,
  parity evidence, and shim removal where safe within the card's approved plan.

## Out of scope

- Internal renderer decomposition, default flip, public package versioning,
  wheel asset APIs, or report-contract changes.

## Deliverables

- Final source ownership, migrated consumers, bounded wrappers, parity tests,
  and explicit residual compatibility debt if any.

## Acceptance evidence

- Old/new behavior parity is demonstrated for every supported invocation,
  profile, format, transaction, fault, and arbitrary-CWD case.
- No report implementation has dual permanent ownership.
- Exact before/after evidence isolates the approved QMD/CSS physical-path
  provenance delta and every repository-facing old-to-new path substitution;
  template/style hashes and all non-path semantics remain unchanged.
- No final reporting source imports a stage, analysis, or evidence
  implementation.

## Canonical documentation updates

- Current `ARCHITECTURE.md`, repository/README maps, `RUNBOOK.md`,
  `TROUBLESHOOTING.md`, diagrams, `PIPELINE_PLAN.md`, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if non-Python assets require premature packaging/versioning, a wrapper
  becomes indefinite, or relocation changes bytes or behavior beyond the exact
  approved physical-path substitutions and their report-provenance-derived
  output delta.

## Completion record

Selected from clean, published, live-remote-equal LIB-02J documentation close
`387d818a9b55e09c956f3034fb2b898ace967924`. The bounded ownership/caller
audit confirms that all known callers are repository-owned, so the approved
implementation is one atomic direct cutover with no wrapper: six reporting
source basenames, two QMD templates, one CSS style, four direct Python suites,
one shell suite, and three reporting fixture groups move to their exact final
owners. Independent contract/public-CLI tests, their fixtures, coverage
policy, public configs, neutral schemas, dependency restoration, and runtime
report outputs remain in their current owners and change only as direct
consumers where required. Pre-change byte/mode/behavior freezing and executable
work have not begun.
