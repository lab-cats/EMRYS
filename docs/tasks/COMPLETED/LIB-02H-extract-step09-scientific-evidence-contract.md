# LIB-02H — Extract the Step 09 scientific-evidence contract

## Objective

Extract the existing public Step `09` output contract into its permanent
neutral owner and cut over every repository-owned Python consumer without
changing accepted/rejected inputs, returned values, exceptions/messages,
output bytes, or scientific/runtime behavior.

## Why this exists

Completed `LIB-02G` removed the upstream Step `08` dependency on private Step
`09c` implementation, but the Step `09` Python validator and artifact index
still obtain public Step `09` headers and validation through that evidence
owner. The bottom-up boundary fixed by `LIB-02F` requires the public analysis
contract to move before the public Step `09c` review-package contract or
reporting-local dependency removal can proceed.

## Fixed decisions

- Target `src/norad/contracts/scientific_evidence/step09.py` with mirrored
  direct tests at `tests/contracts/scientific_evidence/test_step09.py`.
- The Step `09` neutral owner exact-loads the final Step `08` neutral owner and
  preserves one shared module, `ContractError`, and `Table` identity across all
  consumers without a package import or compatibility owner.
- The bounded public surface is the Step `09` result, summary, and mutation-
  spectrum headers; canonical mutation order; test, call, and background
  vocabularies and status-count bindings; result, summary, statistical-state,
  exact-significant-subset, mutation-spectrum, and PDF validation; and only the
  private subordinate parsing/pairing/path/count helpers required to implement
  those public checks.
- Preserve every current threshold edge, accepted/rejected input, exception,
  message, row/order rule, path-resolution rule, deterministic byte, and
  consumer-visible identity through an exact-file, package-independent cutover.
- Cut over Step `09c`, the Step `09` Python validator, artifact indexing, and
  their direct Python tests/fixtures. `_run_summary_science.py` and reporting
  remain outside this slice unless refreshed direct evidence finds a Step `09`
  public-symbol dependency.
- Keep the Step `09` shell and R implementation/checks independent. Do not move
  or share CMH/BH computation, candidate calling, plotting, runtime setup,
  transaction, publication, rollback, or recovery behavior.
- Do not extract the public Step `09c` review-package contract, review policy,
  or reporting code in this card, and do not introduce packaging, installation
  metadata, `PYTHONPATH` mutation, a wrapper, or a permanent compatibility
  owner.

## Blocked by

- [LIB-02G](../COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md) — Required: the Step `08` contract and shared error/table identity must occupy their final neutral owner before Step `09` builds on them.

## Completion unblocks

- [RPT-05A](../IN_PROGRESS/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: the public Step `09c` review-package contract and reporting-local dependency-removal slices must still close before reporting relocation.

## Prerequisites

- Use completed [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md)
  as the semantic boundary and completed
  [LIB-02G](../COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md)
  as the required lower-level neutral-contract owner.
- Reverify the exact current Step `09` public symbols, subordinate closure,
  direct imports/calls, shared identities, arbitrary-CWD behavior, tests,
  goldens, modes, hashes, and measured coverage before extraction.

## Required context

- The `LIB-02F` promotion matrix, target source topology, direct-migration
  mechanics, final Step `08` contract, Step `09` and Step `09c` Python
  validators, `build_artifact_index.py`, and only their direct Step `09`
  tests/fixtures.

## Questions owned by this card

- None.

## In scope

- One neutral Step `09` Python contract owner and independent direct suite;
  removal of the extracted public ownership from Step `09c`; exact-file loader
  and caller cutover for the Step `09` validator and artifact-index builder;
  direct fixture/test repairs; focused parity, coverage, old-dependency and
  duplicate-owner searches; and impact-directed documentation close.

## Out of scope

- Step `09` scientific-method, threshold, transformation, shell, R, plotting,
  runtime, or publication changes; public Step `09c` review-package extraction;
  review-plan/evidence-payload policy; artifact/schema redesign; reporting
  relocation; scheduler, ingestion, orchestration/profile, cluster, production,
  or biological-readiness work.

## Deliverables

- One final Step `09` neutral contract module and mirrored suite, with every
  reviewed direct Python consumer cut over and no duplicate or private Step
  `09c` ownership of the extracted public surface.

## Acceptance evidence

- Frozen pre/post API and consumer parity proves exact accepted/rejected
  inputs, outputs, exceptions/messages, threshold edges, ordering, bytes, and
  arbitrary-CWD behavior.
- The neutral Step `09` module depends only on the exact final Step `08`
  contract and standard library; Step `09` shell/R logic and Step `09c` evidence
  policy/publication remain independent and unchanged.
- Direct and affected integration/golden suites, measured Python coverage,
  complete applicable local gate, documentation gate, and exact old-
  dependency/duplicate-owner searches pass at the final executable state.

## Canonical documentation updates

- Current architecture and functional-owner inventory, source topology only if
  owner wording needs clarification, `PIPELINE_PLAN.md`, `HANDOFF.md`, mutable
  dependency links, coverage path if applicable, and this card.

## Escalation conditions

- Stop for any public Step `09c` review-package roster/state-reduction contract;
  review plan, evidence source/payload, `Artifact`, `ReviewContext`,
  `build_context`, analysis-directory path construction, transaction,
  publication, locking, rollback, recovery, reporting, shell/R, algorithm,
  threshold, table/schema, error, or byte change; an external consumer;
  packaging/path mutation or wrapper need; loss of exact Step `08` module/error/
  table identity; or a missing independent parity oracle.

## Completion record

Selected from clean, published, live-remote-equal LIB-02G documentation close
`d38f782a65de96fff6e7f138fba16eb3d0066267`; status-only selection checkpoint
`7bde6f4f4e871ef3d61da7bd4554f31289881124` was the frozen implementation
parent. Executable/test checkpoint
`97f91690aa1d5e7a67c96d407ab6e3b0e9c1e68f` then extracted the bounded public
Step `09` contract into its permanent neutral owner, added its mirrored direct
suite, and cut over Step `09c`, the Step `09` Python validator, artifact
indexing, and their direct fixtures/tests. `_run_summary_science.py` had no
direct Step `09` public-symbol dependency and remained unchanged. No wrapper,
copy, symlink, package import, `PYTHONPATH` mutation, installation metadata,
schema, shell/R, reporting, review-policy, publication, or scientific/runtime
behavior change was added.

- The neutral owner and mirrored suite are mode `0644` with SHA-256 values
  `bf43bb6fffe765534570e06c0ef9d3b5eb722f13c6a100238824c77a5d834b5f`
  and `f6bfa41604ee05ab092e250624a72186b1a736980fde382085242e2d435a1ff7`,
  respectively. The retained Step `09c` owner is mode `0644` with SHA-256
  `f2917f08c64c1df61e6888b8c6d0484f2cc0b4ee6f302d3359409709cf5bddcb`.
- Frozen comparison proved all eight constants, six validators, and four
  subordinate helpers AST-identical to the selection parent. The `6118`-byte
  public API fingerprint is
  `e4cc56f8cf226e3eb8759fa3438dd1d3ffdfca6796f5851f9fc2bb5f113cdc36`;
  exact signatures, headers, status vocabularies, count bindings, exceptions,
  messages, thresholds, ordering, paths, object identities, and deterministic
  bytes remained unchanged. Exact searches found no stale repository-owned
  Step `09` public-symbol consumer or duplicate implementation.
- The pre-extraction focused scope passed `509` tests. At the final executable
  state, the direct neutral Step `09` suite passed `45` tests and the same
  focused scope plus that direct suite passed `584`. Focused Step `08`, Step
  `09`, and Step `09c` shell contracts all passed.
- The repository coverage run passed `1,500` tests with `17` skips and measured
  `0.844007` line and `0.745770` branch coverage across `34` files. The new
  neutral owner measured `319/332` lines and `169/178` branches. The committed
  affected-only floor is `0.829931` line and `0.724201` branch; no unrelated
  transient coverage gain was promoted.
- The project-local real-R route passed both Step `08` and Step `09` semantic
  fixture suites. The pinned report-runtime route passed `17` tests with `60`
  deselected.
- The full serial aggregate reported static preflight, Python coverage, and
  shell contracts green. Its guarded-R lane remained expected environment
  drift, not green, solely because `renv.lock` and the installed library remain
  at `renv 1.2.3` while CRAN advertises `1.2.4`. No package install, update,
  lockfile, cache, dependency, or runtime mutation was performed. This is not a
  LIB-02H regression or a passing aggregate claim.
- Documentation validation and `git diff --check` passed at lifecycle close.
  These results are local contract-preserving engineering evidence only; they
  add no runtime, cluster, production, scientific-review, or biological-
  readiness proof. Public Step `09c` review-package extraction and reporting-
  local dependency removal remain separate, uncreated JIT slices.
