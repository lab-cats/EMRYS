# LIB-02J — Remove run-summary's private Step 09c dependency

## Objective

Replace run-summary science's private Step `09c` implementation load and
source-to-public reconstruction with a reporting-local reader/projection over
the committed public thirteen-file review package and validated artifact-index
records, without changing the normalized run-summary contract or Step `09c`.

## Why this exists

Completed `LIB-02I` placed the public review-package roster, headers,
vocabularies, bindings, and state reduction in their neutral final owner and
removed artifact indexing's private Step `09c` dependency. Run-summary science
still exact-loads the Step `09c` evidence implementation for `Artifact`,
`ReviewContext`, `build_context`, private evidence parsing, and stable-input
checks. That peer-owner direction is prohibited by `LIB-02F` and blocks direct
reporting relocation.

## Fixed decisions

- Keep the reader/projection inside the current reporting-owned
  `scripts/_run_summary_science.py`; `RPT-05A` moves that existing basename to
  `src/norad/reporting` immediately after this slice. Do not add a seventh
  reporting implementation basename or create a temporary compatibility owner.
- Read the explicit committed review-summary marker and its twelve fixed
  siblings using the neutral public review-package roster and headers. Validate
  their exact artifact-index scope, adapter, path, hash, byte size, row count,
  media type, completeness, and propagated science state.
- Project only the data required by the existing normalized scientific-review
  record. Reporting may own its local table reader, immutable package snapshot,
  lightweight input descriptor, and computational-evidence projection rules;
  it must not recreate Step `09c` review-plan/evidence-admission policy,
  source-to-public reconstruction, transaction, publication, or recovery.
- Preserve the public `--science-review-summary` interface, normalized JSON/TSV
  content, schema and semantic validation, deterministic ordering, messages for
  public-package failures, direct/Make/arbitrary-CWD behavior, and all current
  scientific/runtime evidence ceilings. The deliberate behavior contraction is
  that reporting no longer requires or revalidates Step `09c`'s private source
  inputs after the committed public package and artifact transaction validate.
- Remove the Step `09c` exact-file loader, cached identity, private types, and
  every private implementation reference from reporting. Continue exact-loading
  the neutral artifact and review-package contracts without package discovery,
  installation, `PYTHONPATH`, or `sys.path` mutation.
- Do not move reporting files/assets/tests, change the public review-package or
  artifact contracts, decompose reporting, add packaging metadata, or modify
  Step `09c` in this card.

## Blocked by

- None.

## Completion unblocks

- [RPT-05A](../TODO/RPT-05A-relocate-reporting-to-final-source-home.md) — Fully: reporting can move after its final private peer-owner dependency is removed.

## Prerequisites

- Use completed [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md)
  as the semantic direction and completed
  [LIB-02I](../COMPLETED/LIB-02I-extract-step09c-review-package-contract.md)
  as the final public review-package owner.
- Start from clean, published, live-remote-equal LIB-02I documentation close
  `1c04809475a42a9372e04c6278b682326a1b953d`.
- Freeze the current direct run-summary behavior, exact private symbol use,
  fixture shapes, failure messages, arbitrary-CWD behavior, modes, hashes, and
  coverage before implementation.

## Required context

- `LIB-02F`, `LIB-02I`, the target source topology, direct-migration mechanics,
  current run-summary science implementation, neutral artifact/review-package
  contracts, and only their direct run-summary tests and fixtures.

## Questions owned by this card

- None.

## In scope

- Reporting-local committed-package reading and projection inside
  `_run_summary_science.py`; removal of the private Step `09c` loader and every
  private implementation reference; direct fixture/test repairs and new
  dependency-absence/package-integrity coverage; focused parity, coverage,
  arbitrary-CWD, stale-dependency, and impact-directed documentation checks.

## Out of scope

- Step `09c` policy, validation, inputs, generated outputs, transaction,
  publication, locking, rollback, or recovery; neutral-contract changes;
  reporting relocation/assets/decomposition; report feature work; scheduler,
  ingestion, orchestration/profile, runtime, cluster, production, or biological
  work.

## Deliverables

- Run-summary science normalizes only from the committed public review package,
  its explicitly referenced evidence, and validated artifact-index records,
  with no Step `09c` implementation import and no compatibility owner.

## Acceptance evidence

- Pre/post valid-fixture normalized documents and output bytes are exact, and
  direct tests prove public-package tampering, wrong identity/state, changed
  referenced evidence, and package mutation during normalization fail closed.
- Exact searches and import-isolation tests prove reporting no longer loads or
  references the Step `09c` implementation while retaining one exact neutral
  review-package identity and arbitrary-CWD behavior.
- The direct run-summary, neutral contract, artifact, independent-golden, public
  CLI, measured Python coverage, applicable local, and documentation gates pass
  at the final executable state.

## Canonical documentation updates

- Current architecture and functional-owner inventory, runbook and
  troubleshooting routes for the removed loader, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, mutable dependency links, coverage path if applicable, and this
  card.

## Escalation conditions

- Stop for any need to change Step `09c`, the public review-package or artifact
  contracts, artifact-index reconciliation, normalized schemas or scientific
  meaning, non-path output bytes, public CLI behavior, packaging/import policy,
  or reporting relocation; any missing committed data that can only be obtained
  by recreating Step `09c` source policy; an external consumer; or loss of an
  independent parity oracle.

## Completion record

Selected from clean, published, live-remote-equal LIB-02I documentation close
`1c04809475a42a9372e04c6278b682326a1b953d` at selection checkpoint
`d18856fbaccd8acbd179630d14215d56634eade5`. The bounded dependency audit and
pre-change direct baseline passed `272` tests. Executable/test checkpoint
`253800654ebafcf88c605187c52c0cddfb17ce2b` removed the exact-file Step `09c`
loader, cached identity, private types, and every private implementation
reference from run-summary science. The replacement reporting-local reader
validates the committed thirteen-file public package, explicitly referenced
evidence and computational payloads, and the fixed artifact-index scope while
treating summary-declared private source inputs as committed descriptors only.
Step `09c`, the neutral contracts, normalized schemas, public CLI, and report
assets were not changed.

Independent old/new normalization across seven valid fixture shapes was byte-
exact, including incomplete and exploratory-complete state, missing and mixed
categories, mixed and multi-scope computational evidence, human reviewer names,
and empty candidate selection. Direct regressions prove dependency absence,
one neutral review-package identity, byte-exact normalization after removing
the original review plan, evidence manifest, and an indexed Step `08` source,
fixed package scope/state, public-package and referenced-evidence mutation,
nested computational-payload mutation, and in-flight package mutation. The
historical canonical-table tamper diagnostic remains exactly `Published Step
09c <key> rows differ from reconstruction.`

Final executable file evidence was:

- reporting helper: mode `0755`, `48,135` bytes, SHA-256
  `f1e0a7d56794e592f81291f07b0b41dd31d80a649d311e3bf7419586fd32a6fc`;
- direct run-summary suite: mode `0644`, `80,327` bytes, SHA-256
  `a0e82e5807cd126909deb591d171b5c4df21e3ec96883472381d3bc5f03ae34d`;
  and
- independent-golden suite: mode `0644`, `23,014` bytes, SHA-256
  `880235cb1b8b0f75c68381089c15f02e1868f0fe85b59bb52f1c36dd084e9717`.

The final affected roster passed `384` tests. Complete Python coverage passed
`1,540` tests with `17` skips, measured global line/branch rates
`0.845535`/`0.747115` across `35` files, and covered
`scripts/_run_summary_science.py` at `454/540` lines and `166/238` branches,
above its tracked `392/477`-line and `133/198`-branch baseline. Static
validation, all shell contracts, both project-local Step `08`/`09` real-R
semantic fixtures, and the pinned report-runtime route (`17` passed, `60`
deselected) passed. The unrestricted aggregate attempt remained
non-green only at guarded R, where the environment checker reported one out-
of-date package. No dependency was installed, restored, removed, or updated.
Two independent reviews found no remaining implementation, semantic, evidence,
or compatibility blocker.

`git diff --check` and `make -s documentation-check` passed at lifecycle close;
the documentation gate validated `222` Markdown documents, `139` task cards,
and `6` Mermaid sources.

This closes reporting's final private Step `09c` dependency and fully unblocks
`RPT-05A`. It creates no runtime, cluster, production, completed scientific-
review, editing-site, or biological-readiness evidence.
