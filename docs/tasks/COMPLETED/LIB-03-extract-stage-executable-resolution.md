# LIB-03 — Extract stage executable resolution

## Objective

Extract the one proven three-argument Bash executable-resolution primitive into
a neutral source-only library and cut over its five stage-producer consumers
without changing tool selection, diagnostics, commands, or stage behavior.

## Why this exists

Steps `00c`, `05`, `06`, `07`, and `08` each carried the same roughly 20-line
resolver for explicit paths, `PATH` names, and default tool names. The first
four bodies were byte-identical and the fifth differed only by line wrapping.
Keeping five implementations added maintenance drift without preserving an
independent scientific, evidence, or transaction check.

## Fixed decisions

- Create one mode-`0644`, source-only owner at
  `src/norad/libraries/executable_resolution.sh` exposing only
  `resolve_executable_value(label, value, default_name)`.
- Source that exact repository-adjacent owner from the final Step `00c`, `05`,
  `06`, `07`, and `08` Bash producers independently of invocation CWD.
- Preserve empty-value fallback, slash-path existence and executable checks,
  unchanged path output, basename resolution through `command -v`, exact
  diagnostics, and exit behavior, including characterized acceptance of an
  executable directory.
- Keep tool-specific argument, environment-override, `JAVA_HOME`, and default
  precedence; version checks; commands; and caller-local `die` policy with each
  consumer.
- Do not absorb the Step `09` two-argument resolver, the Step `09c`
  Python-specific resolver, the RSeQC validation-only helper, or any other
  shell utility.
- Do not create a generic shell framework, installed package, public CLI,
  compatibility copy, scheduler abstraction, or new runtime dependency.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Use the completed shared-library promotion decision in
  [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md): promote
  only demonstrated equivalent behavior into the narrowest neutral owner with
  independent and consumer tests.
- Confirm the five final stage owners contain the same three-argument behavior
  and preserve their tool-specific wrappers as the consumer boundary.

## Required context

- The five producer scripts, their direct shell suites, the public CLI
  characterization, `src/norad/libraries/README.md`, and the neutral-seam
  rules in `SOURCE_TOPOLOGY.md` only.

## Questions owned by this card

- None.

## In scope

- One source-only executable resolver, five exact source edges, removal of the
  five local definitions, an independent direct suite, one-owner/consumer
  guards, Bash syntax and arbitrary-CWD checks, and directly affected
  ownership documentation.

## Out of scope

- Tool-specific wrappers or precedence; tool/version execution; other shell
  helpers; scheduler or environment policy; scientific inputs, algorithms, or
  outputs; validation reports; evidence vocabulary; publication, locking,
  rollback, or recovery; package/import conventions; runtime, cluster,
  production, scientific-review, or biological work.

## Deliverables

- One neutral resolver definition with independent tests, exactly five
  consumers and nine unchanged tool-wrapper calls, and no remaining local
  three-argument definition.

## Acceptance evidence

- Exact source inspection proves one definition, five repository-adjacent
  source edges after the caller's failure function, nine unchanged calls, and
  preservation of all five consumer modes.
- Direct tests preserve default and explicit selection, verbatim path and
  `PATH` output, exact failure bytes/statuses, source-only behavior, the
  executable-directory edge, arbitrary CWD, and Bash syntax.
- Targeted public CLI and representative Step `07`/`08` consumer suites pass;
  exact review confirms the tool-specific wrappers and excluded resolver
  families remain local.

## Canonical documentation updates

- Neutral-library ownership, the five consumer contracts, functional-owner
  inventory, architecture/source topology, documentation ownership,
  `PIPELINE_PLAN.md`, lifecycle links, and this card.

## Escalation conditions

- Stop for any change to tool-selection precedence, returned bytes,
  diagnostics, exit behavior, commands, version checks, consumer modes,
  invocation-CWD behavior, scientific or evidence semantics, transaction or
  recovery behavior, or any need for a generic loader/framework, package,
  compatibility owner, additional consumer, or runtime dependency.

## Completion record

Completed in the explicitly approved PI-readiness tranche. Read-only JIT
inspection found exactly five three-argument definitions and nine calls. The
20-line Step `00c`, `05`, `06`, and `07` bodies had the identical SHA-256
`7e97371931fb22899328568cc4001a385a6e051bbe831b440d9a657515df397f`;
Step `08` was behavior-identical with only one continued `|| die` line. The
related Step `09`, Step `09c`, and RSeQC helpers have different APIs or failure
contracts and remain owner-local.

The single final owner is mode `0644`, 22 lines, and 663 bytes with SHA-256
`43689bb2c6289b5301bd95b88b27a7014cf7fc90ed31b9a27b791197b8231764`.
Each consumer sources it after defining `die`, relative to its own
`BASH_SOURCE`, and retains its tool-specific wrapper unchanged. Resulting
consumer line counts are 497, 578, 766, 875, and 1,005 for Steps `00c`, `05`,
`06`, `07`, and `08`; their modes remain `0755`, `0644`, `0755`, `0755`, and
`0755` respectively. The independent mode-`0644` suite is 269 lines and 7,241
bytes with SHA-256
`1f1abfa3a329bc3d89f52fba9c9c9ccf3687b079c54f08ab92489742ed836fd9`.

Focused local evidence passed: all 15 independent resolver cases, 10 targeted
public-CLI arbitrary-CWD/help/missing-argument/mode cases, the complete Step
`07` and Step `08` shell suites, Bash syntax for the owner and five consumers,
`git diff --check`, and independent body/wrapper, Bash 3.2, arbitrary-CWD, and
`PATH` review. The helper changes no shell options, traps, CWD, or `PATH` when
sourced. Tool-specific argument/environment/`JAVA_HOME` precedence, version
checks, commands, stage outputs, and failure policy remain local and unchanged.

This is local behavior-preserving engineering evidence only. It adds no
runtime, cluster, production, scientific-review, or biological-readiness
evidence.
