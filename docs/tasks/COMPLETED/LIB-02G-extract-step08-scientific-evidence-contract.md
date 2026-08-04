# LIB-02G — Extract the Step 08 scientific-evidence contract

## Objective

Extract the public Step `08` table/manifest contract into its permanent neutral
owner and cut over every repository-owned Python consumer without changing
accepted/rejected inputs, returned values, exceptions/messages, output bytes,
or scientific/runtime behavior.

## Why this exists

Step `08`/`09` validators and reporting-chain consumers currently obtain
public Step `08` structures through the private Step `09c` implementation.
Completed `LIB-02F` requires bottom-up neutral contracts so later reporting
relocation does not preserve that prohibited dependency direction.

## Fixed decisions

- Target `src/norad/contracts/scientific_evidence/step08.py` with mirrored
  direct tests at `tests/contracts/scientific_evidence/test_step08.py`.
- Extract only public Step `08` headers, closed vocabularies, manifest and
  artifact validation, and private subordinate parsing helpers required to
  implement that public contract.
- The bounded surface is the sample-manifest required/allowed columns,
  partition-manifest header, Step `08` metadata/inputs/summary headers, safe-ID
  checks, and sample-manifest, partition-manifest, Step `08` inputs/sites/
  summary validation.
- Preserve every accepted/rejected input, exception, message, ordering rule,
  deterministic byte, and consumer-visible identity through an exact-file,
  package-independent cutover.
- Preserve one shared module, error, and table identity across consumers; do
  not introduce a compatibility owner to manufacture identity.
- Keep Step `08` shell and R checks independent. Do not move or share its R
  algorithm, orientation/allele/filtering/annotation logic, runtime setup,
  publication, rollback, or recovery behavior.
- Do not extract Step `09` or public Step `09c` contracts in this card, and do
  not move reporting code or introduce packaging, installation metadata,
  `PYTHONPATH` mutation, or a permanent compatibility owner.

## Blocked by

- None.

## Completion unblocks

- [LIB-02H](../COMPLETED/LIB-02H-extract-step09-scientific-evidence-contract.md) — Fully: the final Step `08` neutral owner and shared error/table identity are available for the Step `09` contract extraction.
- [RPT-05A](../COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: Step `09`, public Step `09c`, and reporting-local dependency-removal slices must still close before reporting relocation.

## Prerequisites

- Use completed [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md)
  as the semantic boundary and completed
  [MIG-04A](../COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
  as the neutral-contract ownership predecessor.
- Reverify the exact current Step `08` public symbols, all direct imports and
  calls, exception identity, path-independent behavior, tests, goldens, and
  measured coverage before extraction.

## Required context

- The `LIB-02F` promotion matrix; `SOURCE_TOPOLOGY.md`; direct-migration
  mechanics; the Step `08`, Step `09`, and Step `09c` Python validators;
  `build_artifact_index.py`; and only their direct Step `08` tests/fixtures.
  `_run_summary_science.py` uses review-package rather than Step `08` public
  symbols and remains outside this slice unless refreshed direct evidence
  proves otherwise.

## Questions owned by this card

- None.

## In scope

- One neutral Python contract owner and independent direct tests; remove the
  extracted Step `08` ownership from the Step `09c` implementation and cut over
  the Step `08` validator, Step `09` validator, artifact-index builder, and
  their direct Python tests. Include only path/import repairs, focused parity,
  coverage, legacy-dependency absence searches, and impact-directed
  documentation close.

## Out of scope

- Scientific-method or threshold changes; R or shell consolidation; Step `09`
  or Step `09c` extraction; artifact/schema redesign; reporting relocation;
  scheduler, ingestion, orchestration/profile, runtime, cluster, production,
  or biological-readiness work.

## Deliverables

- One final Step `08` neutral contract module and mirrored suite, with every
  reviewed direct consumer cut over and no duplicate or private Step `09c`
  ownership of the extracted public surface.

## Acceptance evidence

- Frozen pre/post API and consumer parity proves exact accepted/rejected
  inputs, outputs, exceptions/messages, ordering, bytes, and arbitrary-CWD
  behavior.
- The neutral module imports no functional owner; Step `08` shell/R checks and
  Step `09c` evidence policy/publication remain independent and unchanged.
- Direct and affected integration/golden suites, measured Python coverage,
  complete applicable local gate, documentation gate, and exact old-
  dependency/duplicate-owner searches pass at the final executable state.

## Canonical documentation updates

- Current architecture and functional-owner inventory, `SOURCE_TOPOLOGY.md`
  only if owner wording needs clarification, `PIPELINE_PLAN.md`, `HANDOFF.md`,
  mutable dependency links, coverage path if applicable, and this card.

## Escalation conditions

- Stop for any Step `09` or public review-package contract; review-plan or
  evidence-payload policy; `Artifact`, `ReviewContext`, or `build_context`;
  algorithm, threshold, table/schema, error-contract, transaction, publication,
  locking, rollback, recovery, reporting, shell/R, or scientific-policy
  change; an external consumer; packaging/path mutation/wrapper need; loss of
  exact shared identity; or a missing independent parity oracle.

## Completion record

Selected from clean, published, live-remote-equal MIG-04A documentation close
`ec0b00f545b8272eaf19b3cebee7c608a20139e7`; status-only selection checkpoint
`e5f54e078eed82f523434aed6ab87c951f212315` was the frozen implementation
parent. Executable/test checkpoint
`f72cc0f7646a1db9daa625dbe4ff6bcc57ce3671` then extracted the exact Step `08`
contract into `src/norad/contracts/scientific_evidence/step08.py`, added the
mirrored independent suite, and cut over Step `09c`, the Step `08` and Step
`09` Python validators, artifact indexing, and their direct fixtures/tests. No
wrapper, copy, symlink, package import, `PYTHONPATH` mutation, installation
metadata, schema change, shell/R change, reporting change, or scientific-policy
change was added.

- The neutral owner and mirrored suite are mode `0644` with SHA-256 values
  `566239b28ab807adb67fe5a63ed735cce14a3ef7c1a2cf3db78f88efce2c47e6`
  and `17bd5bf77110c2f454d2833594e576c711fecf105ef92298f1fa70a9f33991d0`,
  respectively. The final Step `09c` owner is mode `0644` with SHA-256
  `cd3124233f6f077e62a454583221edf850b67a77f2c42cd4519bb3274a376939`.
- Frozen comparison proved all `29` moved definitions AST-identical to the
  selection parent. The neutral public API fingerprint is
  `8824d7b30f3c45dddcb475d21d4382ac52de2520031cdd89bab107fb2edc2bf1`;
  exact headers, signatures, error/table identity, accepted/rejected inputs,
  messages, ordering, path behavior, and consumer module identity remained
  unchanged. Exact searches found no stale repository-owned Python consumer or
  duplicate implementation of the extracted surface.
- The pre-extraction affected baseline passed `405` tests. At the final
  executable state the direct neutral suite passed `40` tests and the focused
  affected suite passed `379`. Focused Step `08`, Step `09`, and Step `09c`
  shell contracts all passed.
- The repository coverage run passed `1,425` tests with `17` skips and measured
  `0.839875` line and `0.737398` branch coverage across `33` files. The new
  neutral owner measured `238/241` lines and `129/130` branches. The committed
  affected-only floor is `0.825627` line and `0.715598` branch; no unrelated
  transient coverage gain was promoted.
- The correct project-local real-R route,
  `RSCRIPT_BIN=/usr/local/bin/Rscript make -s local-real-r-test`, passed both
  Step `08` and Step `09` semantic fixture suites. The pinned report-runtime
  route passed `17` tests with `60` deselected.
- The full serial aggregate reported static preflight, Python coverage, and
  shell contracts green. Its guarded-R lane remained environment-deferred,
  not green, solely because the installed library and `renv.lock` remain
  synchronized at `renv 1.2.3` while CRAN currently advertises
  `1.2.4`; a separate
  `RSCRIPT_BIN=/usr/local/bin/Rscript make -s r-check` confirmed the same drift.
  No package install, update, lockfile, cache, dependency, or runtime mutation
  was performed. This is not a LIB-02G regression or a passing aggregate claim.
- Documentation validation and `git diff --check` passed at lifecycle close.
  These results are local contract-preserving engineering evidence only; they
  add no runtime, cluster, production, scientific-review, or biological-
  readiness proof.
