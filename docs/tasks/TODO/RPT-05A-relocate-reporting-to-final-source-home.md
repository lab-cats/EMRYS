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
- Root wrappers are temporary migration scaffolding only.
- Preserve comprehensive/science behavior, explicit inputs, deterministic
  outputs, transaction/recovery semantics, and direct/Make invocation parity.
- Do not combine relocation with internal decomposition.

## Blocked by

- [RPT-04](../TODO/RPT-04-implement-science-report-usability.md) — Required: both report profiles and their usability behavior must be complete before relocation.

## Completion unblocks

- [RPT-05B](../TODO/RPT-05B-decompose-report-rendering-modules.md) — Fully: decomposition can occur inside the final ownership boundary.

## Prerequisites

- Reinspect all report imports, direct scripts, Make targets, assets, tests,
  Quarto inputs, arbitrary-CWD cases, and packaged-asset constraints.

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

## Canonical documentation updates

- Current `ARCHITECTURE.md`, repository/README maps, `RUNBOOK.md`,
  `TROUBLESHOOTING.md`, diagrams, `PIPELINE_PLAN.md`, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if non-Python assets require premature packaging/versioning, a wrapper
  becomes indefinite, or relocation changes report bytes/behavior unexpectedly.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
