# NORAD comprehensive refactor audit

This document records the final Phase `00` audit performed against
`post09-validation-report-09` commit
`5bdf53664d72f047d88f4a59d38ff2d8c80dc503`. It is an engineering audit, not
a runtime, cluster, scientific, or biological validation result.

The audit is recorded on the descendant
`refactor-00-comprehensive-audit`. During its final gate, the user explicitly
authorized a one-time update of the project-locked `bitops` dependency on this
branch. That lock change was isolated in commit `288dd93`; no NORAD source,
schema, config, fixture, test, scientific method, or public contract changed.
Future changes return to the normal descendant-branch gate.

## Evidence boundary and method

The audit included:

- all required project documents and the current/future architecture documents;
- all scripts, SLURM wrappers, tests, fixtures, configs, schemas, reports, and
  standalone Mermaid sources;
- public CLI, environment, output, schema, receipt, status, ordering, hashing,
  transaction, and evidence-state contracts;
- dependency directions, imports, file size, commit-level change coupling,
  working-directory assumptions, file modes, and Make targets;
- the final Step `08` and Step `09` validators, adapters, fixtures, reports,
  and documentation;
- the complete parent validation gate and the live clean/upstream-equal Git
  gate.

Inventory measurements at the audited commit:

| Measure | Observed |
| --- | ---: |
| top-level files under `scripts/` | 43 |
| top-level files under `jobs/` | 16 |
| test files excluding ignored bytecode caches | 56 |
| config files | 28 |
| schema files | 5 |
| report source/style files | 3 |
| documentation files | 17 |
| required-document lines | 7,494 |
| `RUNBOOK.md` plus `TROUBLESHOOTING.md` lines | 6,261 |
| largest Python module | 5,404 lines |
| per-step validation implementation commits inspected | 13 |

The Phase `P2` parent-reconciliation gate on 2026-07-28 produced:

- Python: `425 passed, 17 skipped`; the skipped tier was separately exercised
  by the pinned report-runtime gate;
- all shell tests passed;
- Step `08` and Step `09` real-R tests passed with explicit repository-local
  R activation;
- the R environment check and local guarded real-R target passed;
- report tests: `143 passed` with the pinned Quarto/Typst runtime;
- a clean worktree and `0` ahead / `0` behind the refreshed remote.

Those results are local engineering evidence. They do not promote Steps
`07`–`09`, the scientific review, or any report to production or cluster
evidence.

The Phase `00` revalidation on 2026-07-30 reproduced the static, Python,
shell, guarded Step `08`/`09` real-R, and pinned report results. The separate
R environment check initially found release-repository drift:
`renv::status()` reported the locked project synchronized, but CRAN advertised
`bitops 1.1-0` while `renv.lock` and the installed project library contained
`1.0-9`. `BiocManager::valid()` therefore failed.

Under the explicit one-time authorization, the upstream source delta and
project dependency paths were inspected. The official `1.1-0` source archive
had SHA-256
`73f063f15c6334d769202a178f7dd5499bdd10044a4ffbef571be57cbcc68b22`;
its compiled-code change removes undefined negative double-to-unsigned
conversion behavior. NORAD does not call `bitops` directly; the package enters
through the Step `08` dependency closure. Only `bitops` was updated and
locked, and every captured bitwise/checksum boundary output remained
identical.
Upstream's consistency suite, `renv` synchronization, current-release
validation, the guarded Step `08`/`09` real-R fixtures, all static checks,
`425` passing Python tests with `17` expected skips, the complete shell gate,
and `143` pinned report tests then passed. This resolves `RA-029` for the
current lock without changing the validation policy or any production,
cluster, scientific, or biological evidence state.

The audit used static inspection, targeted adversarial fixture copies, the
real Step `09` R oracle, commit-history comparison, and the complete gate.
Temporary audit fixtures were outside the repository and were not retained.

## Ranking method

Priority reflects correctness and recovery risk first, then contract exposure,
user/operator benefit, change coupling, effort, and dependencies. Proposed
phases are recommendations for the later measured and reviewed plan; they do
not authorize implementation outside that plan.

| Rank | Finding | Priority | Contract sensitivity | Effort | Proposed phase |
| ---: | --- | --- | --- | --- | --- |
| 1 | `RA-001` Step 09 independent CMH oracle gap | critical | very high | large | `01` characterization, then reviewed `03` |
| 2 | `RA-002` shared validation publication/recheck safety | high | very high | large | `01` characterization, then reviewed `03` |
| 3 | `RA-003` adapter does not enforce exact check rosters | high | high | medium | `01` characterization, then reviewed `03` |
| 4 | `RA-029` mutable repository freshness conflicts with the locked R gate | high | high | medium | resolved by one-time Phase `00` dependency refresh |
| 5 | `RA-016` no measured line/branch baseline | high | low | medium | resolved in `01` baseline |
| 6 | `RA-017` incomplete public-contract traceability | high | high | large | matrix resolved in `01`; named gaps remain |
| 7 | `RA-018` uneven SLURM behavior coverage | high | high | large | `01` |
| 8 | `RA-019` production/test shared-defect exposure | high | high | medium | `01` |
| 9 | `RA-004` legacy early-stage execution/publication behavior | high | very high | large | characterize in `01`; mostly defer |
| 10 | `RA-005` artifact adapter monolith and shotgun surgery | medium | very high | large | reviewed `03` |
| 11 | `RA-006` report-module import cycle | medium | high | medium | reviewed `03` |
| 12 | `RA-007` stage-specific modules used as infrastructure | medium | high | medium | reviewed `03` |
| 13 | `RA-008` oversized mixed-responsibility modules | medium | very high | very large | reviewed incremental `03` |
| 14 | `RA-010` primitive internal representations | medium | high | large | reviewed `03` |
| 15 | `RA-011` inconsistent diagnostic and exit semantics | medium | very high | medium | `01`, then reviewed `03` |
| 16 | `RA-020` large fixture builders and coupled integration edits | medium | high | large | `01`, then reviewed `03` |
| 17 | `RA-012` stale canonical lineage and status | medium | medium | small | resolved in `00` |
| 18 | `RA-013` operations-document navigation load | medium | medium | medium | reviewed documentation phase |
| 19 | `RA-014` architecture and reliability-description drift | medium | high | small | corrected/recorded in `00` |
| 20 | `RA-015` runbook command and validation-claim drift | medium | high | small | corrected in `00` |
| 21 | `RA-021` stale planning/configuration artifacts | low | medium | small | `01` evidence, then documentation |
| 22 | `RA-022` repeated parsing, hashing, and input I/O | low | high | medium | measure before reviewed `03` |
| 23 | `RA-023` direct-script and working-directory inconsistency | low | high | medium | `01` characterization |
| 24 | `RA-009` repeated transaction mechanisms | retain/evaluate | very high | very large | no generic extraction yet |
| 25 | `RA-024` independent shell/R/Python checks | retain | very high | none | do not abstract |
| 26 | `RA-025` Steps 07–09 scientific algorithms | defer | very high | very large | after remote baseline only |
| 27 | `RA-026` action-local safety and recovery logic | retain/evaluate | very high | large | do not universalize |
| 28 | `RA-027` evidence and scientific-state separation | retain | very high | none | do not collapse |
| 29 | `RA-028` unique documentation evidence | retain | high | none | preserve during navigation work |

## Findings

### RA-001 — Step 09 independent CMH oracle gap

- **Category:** correctness, scientific-computation validation, misleading
  documentation
- **Affected files and symbols:** `scripts/validate_step_09_cmh_outputs.py`
  `build`; `scripts/step_09c_scientific_validation.py`
  `validate_step09_result_semantics`; Step `09` validator tests and operational
  descriptions
- **Objective evidence:** the validator recomputes depth, AF, background,
  call, and global BH values, but only type/range-checks `cmh_statistic`,
  `cmh_p_value`, and `common_odds_ratio`; a coordinated false CMH/p/odds/BH/call
  fixture and an all-zero edited-count fixture relabeled `tested` both retained
  seven passing checks. The real-R oracle produced a statistic near `33.6926`,
  p-value near `6.45e-09`, and odds ratio near `3.4590` for the normal row and
  non-finite CMH results for the zero-edited row.
- **Description:** `status_semantics` claims independent CMH recomputation that
  the implementation does not perform. The allowed
  `{"degenerate_table", "tested"}` choice is not derived from count-table
  estimability.
- **User impact:** a coordinated, statistically false output set can be
  presented as a passing structured validation report.
- **Maintainer and cognitive-load impact:** maintainers must infer the actual
  validation boundary from several functions while the report text says more.
- **Correctness or safety risk:** critical; the gap concerns the principal
  ranking statistic.
- **Change-coupling impact:** any fix touches semantic validation, fixtures,
  adapter/report projections, tests, and documentation.
- **Contract sensitivity:** very high; check IDs, statuses, thresholds,
  deterministic output, and Step `09` statistical behavior must remain stable.
- **Whether duplication may be intentional:** yes; an independent
  count-derived oracle is desirable duplication and must not import the
  producer's result values as truth.
- **Recommended disposition:** correct the documentation immediately; build
  an independent DP/AD-derived characterization oracle and corruption corpus
  before deciding whether a compatible validator correction is safe.
- **Characterization tests required first:** valid, zero-cell, all-zero,
  missing, low-coverage, continuity-correction, infinite-odds, rounding,
  multi-stratum, global-BH, and coordinated-corruption cases, checked against
  the committed R implementation.
- **Priority:** critical
- **Estimated effort:** large
- **Dependencies:** measured test baseline; architecture and reliability
  review; statistical-equivalence evidence
- **Proposed phase:** Phase `01` characterization, then a separately reviewed
  Phase `03` package
- **Status:** Phase `01a` independent characterization complete at
  `bef0f97`; prose overclaim corrected in Phase `00`; production validator
  correction remains a separately reviewed executable gap

### RA-002 — Shared validation publication and recheck safety

- **Category:** filesystem safety, TOCTOU, rollback, recovery
- **Affected files and symbols:** `scripts/validate_step_00a_star_index.py`
  `Snapshot`, `regular_snapshot`, `publish`; all twelve validators importing
  that module as `report`
- **Objective evidence:** input identity records device, inode, size, and
  mtime, but not a digest or ctime; `publish` unconditionally attempts stage
  cleanup and lock removal in `finally` and has no retained recovery marker
  when rollback or cleanup cannot be proved.
- **Description:** a same-size rewrite with restored mtime can evade the final
  metadata recheck, and an exceptional rollback/cleanup path can lose the lock
  that should protect recovery evidence.
- **User impact:** a report can be published against changed bytes, or an
  operator can encounter ambiguous recovery state without an owned lock.
- **Maintainer and cognitive-load impact:** one compact helper carries hidden
  safety semantics for every stage-specific validator.
- **Correctness or safety risk:** high
- **Change-coupling impact:** one change affects thirteen report formats and
  all publication tests.
- **Contract sensitivity:** very high; lock names, stable bytes, no-clobber,
  rollback, cleanup, and recovery behavior are public contracts.
- **Whether duplication may be intentional:** the shared implementation is
  intentional, but independent fault-injection expectations are still needed.
- **Recommended disposition:** add adversarial tests before changing the
  helper; evaluate digest-backed snapshots and retained-lock/recovery behavior
  that preserves current successful-path bytes and names.
- **Characterization tests required first:** same-size rewrite with restored
  mtime, inode replacement, symlink substitution, late foreign final, move
  failure, restoration failure, stage cleanup failure, lock cleanup failure,
  signal, and valid-predecessor retry.
- **Characterization evidence:** implementation commit `f7e00e4` covers the
  full thirteen-validator shared-publisher inventory and the listed fault
  boundaries. It confirms the metadata-only rewrite blind spot, late-foreign-
  final deletion, and unprotected incomplete-rollback states without changing
  production behavior. Ancillary reference, runtime-preflight, and storage
  publishers are characterized separately because their transactions are not
  the same implementation.
- **Priority:** high
- **Estimated effort:** large
- **Dependencies:** Phase `01` fault-injection harness and exact public
  transaction inventory
- **Proposed phase:** Phase `01` tests, then reviewed Phase `03`
- **Status:** Phase `01b` characterization complete; executable correction
  remains a reviewed Phase `03` candidate

### RA-003 — Adapter does not enforce exact validator check rosters

- **Category:** contract validation, ordering, typed adaptation
- **Affected files and symbols:** `scripts/build_artifact_index.py`
  `ADAPTER_REGISTRY`, `inspect_tsv`, `inspect_artifact`;
  `scripts/validate_step_00a_star_index.py` `validate_report`
- **Objective evidence:** adapters enforce the common header, row count,
  step/scope, safe unique check IDs, and status vocabulary, but do not compare
  check IDs or their order with the stage-specific public roster.
- **Description:** a correctly sized report with plausible but wrong unique
  check IDs can enter the artifact graph even though the native validator
  would reject it.
- **User impact:** summaries and reports can project the wrong evidence labels
  as an accepted stage report.
- **Maintainer and cognitive-load impact:** expected rosters live implicitly
  across validator code, fixtures, and prose instead of one explicit adapter
  contract.
- **Correctness or safety risk:** high
- **Change-coupling impact:** all validator adapters and fixture builders are
  involved.
- **Contract sensitivity:** high; existing IDs and order must not change.
- **Whether duplication may be intentional:** yes; adapter-side roster
  duplication is useful independent validation if tests do not import the
  producer roster.
- **Recommended disposition:** first freeze each exact roster and order in an
  independent traceability fixture, then add stage-specific adapter checks
  without changing valid records.
- **Characterization tests required first:** wrong ID, missing ID, extra ID,
  duplicate ID, correct IDs in wrong order, wrong step/scope, pass/fail mix,
  and deterministic serialized-record cases for every stage.
- **Priority:** high
- **Estimated effort:** medium
- **Dependencies:** Phase `01` risk-to-test matrix
- **Proposed phase:** Phase `01` characterization, then reviewed Phase `03`
- **Status:** confirmed; unresolved

### RA-004 — Legacy early-stage execution and publication behavior

- **Category:** dry-run safety, transaction consistency, SLURM boundaries
- **Affected files and symbols:** Steps `00a`, `00b`, `00c`, `01`, `02b`,
  `03`, and `04` scripts/wrappers
- **Objective evidence:** Step `00a` and `00b` wrappers embed compute and have
  no `EXECUTE` gate; Step `01` and `02b` create output directories before the
  dry-run exit; the Step `01` wrapper creates default fixtures in dry-run;
  Step `00c` publishes FAI and DICT sequentially without restoration of the
  first final if the second publication fails; Steps `02b`, `03`, and `04`
  publish individual stable outputs rather than receipt-last transactions.
- **Description:** early stages predate the repository's later dry-run and
  recoverable-publication conventions.
- **User impact:** dry-runs can change local filesystem state, and interrupted
  early-stage publication can require manual inspection.
- **Maintainer and cognitive-load impact:** operators must remember which
  stages implement which generation of safety behavior.
- **Correctness or safety risk:** high for shared reference outputs; medium
  elsewhere.
- **Change-coupling impact:** changing existing behavior touches public jobs,
  scripts, runbook commands, local fixtures, and cluster assumptions.
- **Contract sensitivity:** very high; current paths, modes, and behavior are
  explicitly protected.
- **Whether duplication may be intentional:** stage-specific publication is
  partly intentional because output shapes and recovery obligations differ.
- **Recommended disposition:** characterize every current behavior; improve
  diagnostics where compatible; defer behavior-changing migrations unless a
  versioned, operator-approved compatibility plan is proven.
- **Characterization tests required first:** job `EXECUTE=0/1/invalid`,
  dry-run filesystem snapshots, first publication, valid predecessor,
  partial predecessor, second-move failure, signal, foreign file, and direct
  invocation from a non-repository CWD.
- **Priority:** high
- **Estimated effort:** large
- **Dependencies:** public-contract matrix and remote evidence for any
  runtime-sensitive change
- **Proposed phase:** characterize in Phase `01`; defer most implementation
- **Status:** confirmed; behavior retained in Phase `00`

### RA-005 — Artifact adapter monolith and shotgun surgery

- **Category:** cohesion, change coupling, complex control flow
- **Affected files and symbols:** `scripts/build_artifact_index.py`,
  especially adapter registration, roster validation, native inspection,
  evidence construction, and publication
- **Objective evidence:** the module is `5,404` lines; all thirteen validator
  implementation commits changed this file and the same eight integration
  surfaces: `Makefile`, inventory, adapter, two fixture builders, and three
  cross-layer test modules.
- **Description:** registry data, parser mechanics, stage-specific semantics,
  evidence modeling, transaction control, and CLI orchestration share one
  module.
- **User impact:** small adapter additions carry broad regression exposure.
- **Maintainer and cognitive-load impact:** reviewers must understand distant
  code paths and large fixtures for a local stage addition.
- **Correctness or safety risk:** medium to high because the module owns
  identity and transaction evidence.
- **Change-coupling impact:** high and already observed in history.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** stage-specific rules should
  remain explicit; registry decomposition must not become a generic semantic
  dispatcher.
- **Recommended disposition:** after coverage, separate neutral data/registry,
  native readers, evidence assembly, and publication seams incrementally,
  preserving the public script as a shim.
- **Characterization tests required first:** exact adapter roster, public CLI,
  deterministic JSON/TSV/receipt bytes, all absence/failure states, input
  mutation, lock, rollback, and every stage-specific anchor.
- **Priority:** medium
- **Estimated effort:** large
- **Dependencies:** `RA-003`, `RA-016`–`RA-020`, reviewed architecture plan
- **Proposed phase:** incremental reviewed Phase `03`
- **Status:** confirmed; candidate, not yet authorized for extraction

### RA-006 — Report-module import cycle

- **Category:** dependency direction, cycle, module boundary
- **Affected files and symbols:** `scripts/render_run_report.py` `main`;
  `scripts/render_run_report_bundle.py` module import
- **Objective evidence:** the bundle imports the HTML renderer at module load;
  the HTML renderer imports the bundle inside its public `main`, forming a
  runtime cycle.
- **Description:** public dispatch and the HTML implementation share one
  module, while the bundle depends on many private HTML helpers.
- **User impact:** behavior works now, but importing or extracting either
  renderer is fragile.
- **Maintainer and cognitive-load impact:** ownership of parsing, models,
  helpers, and public dispatch is unclear.
- **Correctness or safety risk:** medium.
- **Change-coupling impact:** HTML, PDF, transaction, and report tests move
  together.
- **Contract sensitivity:** high; the public entrypoint, default `all` mode,
  deterministic outputs, and report transaction cannot move.
- **Whether duplication may be intentional:** no clear verification benefit
  from the cycle.
- **Recommended disposition:** after baseline coverage, introduce a neutral
  internal report model/dispatcher while retaining the public script shim.
- **Characterization tests required first:** direct import, direct script,
  `html`/`pdf`/`all`, help, malformed inputs, deterministic bytes, valid
  HTML-only predecessor, lock/signal/rollback, and arbitrary CWD.
- **Priority:** medium
- **Estimated effort:** medium
- **Dependencies:** report coverage baseline and reviewed package layout
- **Proposed phase:** reviewed Phase `03`
- **Status:** confirmed; unresolved

### RA-007 — Stage-specific modules used as generic infrastructure

- **Category:** dependency direction, naming, hidden coupling
- **Affected files and symbols:** twelve validators importing
  `validate_step_00a_star_index` as `report`; Step `08`, Step `09`, adapter,
  and summary code importing `step_09c_scientific_validation`
- **Objective evidence:** neutral report rendering/publication primitives are
  owned by a Step `00a` module; general manifest, TSV, hashing, and Step
  `08`/`09` contract functions are owned by a Step `09c` module.
- **Description:** dependency direction points from many stages toward
  scientifically named leaf modules.
- **User impact:** no current CLI failure, but internal reuse is surprising and
  raises regression risk.
- **Maintainer and cognitive-load impact:** a maintainer cannot infer module
  responsibility from names.
- **Correctness or safety risk:** medium.
- **Change-coupling impact:** high because leaf edits have repository-wide
  consumers.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** scientific semantic checks
  should remain independent; only proven-neutral primitives are extraction
  candidates.
- **Recommended disposition:** map each imported symbol, characterize it, and
  extract only neutral report/contract primitives behind compatibility
  imports.
- **Characterization tests required first:** direct-script import paths,
  exception types/messages, stable TSV bytes, report publication faults,
  Step `08`/`09` semantic fixtures, and adapters.
- **Priority:** medium
- **Estimated effort:** medium
- **Dependencies:** `RA-001`–`RA-003`, measured import graph, reviewed plan
- **Proposed phase:** reviewed Phase `03`
- **Status:** confirmed; candidate

### RA-008 — Oversized mixed-responsibility modules

- **Category:** cohesion, complexity, reviewability
- **Affected files and symbols:** `build_artifact_index.py` (`5,404` lines),
  `step_09c_scientific_validation.py` (`4,533`),
  `render_run_report.py` (`3,021`), `build_run_summary.py` (`2,789`), and
  `validate_artifact_contracts.py` (`1,893`)
- **Objective evidence:** each module combines contract constants/parsing,
  validation, transformation, I/O, and/or publication; the largest test
  modules are also `1,565`–`1,961` lines.
- **Description:** large responsibility sets obscure invariants and make
  bounded changes difficult.
- **User impact:** slower fixes and greater chance of unrelated regression.
- **Maintainer and cognitive-load impact:** high onboarding and review cost.
- **Correctness or safety risk:** medium to high around identity, science
  state, and publication.
- **Change-coupling impact:** high.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** some closed-contract constants
  and independent validation logic are intentionally local.
- **Recommended disposition:** decompose only along observed seams, one module
  and one concern per branch; avoid a framework rewrite.
- **Characterization tests required first:** line/branch baseline, public CLI
  matrix, deterministic fixtures, fault injection, import compatibility, and
  stage-specific semantic cases.
- **Priority:** medium
- **Estimated effort:** very large
- **Dependencies:** Phase `01`, all three Phase `02` reviews
- **Proposed phase:** multiple small reviewed Phase `03` packages
- **Status:** confirmed; candidate

### RA-009 — Repeated transaction mechanisms are not one proven abstraction

- **Category:** duplication, locks, staging, rollback, signal, cleanup
- **Affected files and symbols:** compute scripts, scientific-review,
  artifact, summary, validation-report, Quarto restore, and report publishers
- **Objective evidence:** many publishers share vocabulary but differ in lock
  file versus directory, number of members, commit marker, predecessor
  validation, signal handling, directory identity, backup layout, and retained
  recovery rules.
- **Description:** lexical repetition exists, but the safety state machines are
  not interchangeable.
- **User impact:** a premature common helper could weaken stage-specific
  recovery.
- **Maintainer and cognitive-load impact:** repeated implementations cost
  review effort, yet make local ownership visible.
- **Correctness or safety risk:** very high if generalized incorrectly.
- **Change-coupling impact:** a universal helper would create repository-wide
  coupling.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes; much of it is intentional
  evidence-local safety.
- **Recommended disposition:** first build a transaction-state comparison
  table and fault-injection matrix; extract only identical, side-effect-free
  primitives if a later review proves benefit.
- **Characterization tests required first:** per-producer lock ownership,
  predecessor forms, first publish, rollback, cleanup, signal, late foreign
  replacement, recovery-marker, and receipt-last cases.
- **Priority:** retain/evaluate
- **Estimated effort:** very large
- **Dependencies:** comprehensive transaction matrix
- **Proposed phase:** no generic extraction in the current plan unless Phase
  `02` proves a narrow safe seam
- **Status:** confirmed intentional/heterogeneous duplication

### RA-010 — Primitive internal representations hide invariants

- **Category:** typed models, status vocabularies, identity, serialization
- **Affected files and symbols:** artifact adapter, run summary, scientific
  review, and report modules using nested dictionaries, tuples, and string
  statuses
- **Objective evidence:** immutable identities, evidence states, source
  snapshots, approvals, adapter specifications, and output records are often
  passed as open dictionaries; some modules already use dataclasses, but the
  boundary is inconsistent.
- **Description:** required fields and state transitions are enforced late
  through distributed string lookups.
- **User impact:** no proven current output defect, but malformed internal
  states are harder to prevent.
- **Maintainer and cognitive-load impact:** reviewers repeatedly reconstruct
  shapes and allowed transitions.
- **Correctness or safety risk:** medium.
- **Change-coupling impact:** broad if public serialization and internal models
  are changed together.
- **Contract sensitivity:** high; external JSON/TSV shapes must remain exact.
- **Whether duplication may be intentional:** independent schema validation
  must remain even if internal types are added.
- **Recommended disposition:** consider frozen internal models at narrow seams
  with explicit serializers; never substitute internal types for public schema
  validation.
- **Characterization tests required first:** round-trip and exact-byte
  fixtures, unknown/missing fields, every status transition, ordering, hash,
  and schema-version cases.
- **Priority:** medium
- **Estimated effort:** large
- **Dependencies:** schema/serializer traceability and coverage
- **Proposed phase:** reviewed Phase `03`
- **Status:** candidate; not yet justified at repository-wide scale

### RA-011 — Diagnostic and exit semantics are inconsistent

- **Category:** CLI usability, failure evidence, compatibility
- **Affected files and symbols:** Python validators, renderer, shell scripts,
  SLURM wrappers, and Make targets
- **Objective evidence:** Python tools use different error exit codes; a
  structurally valid validation report can exit zero while containing failed
  checks by design; shell tools vary in `die` conventions and tool-resolution
  messages.
- **Description:** infrastructure failure and recorded evidence failure are
  not uniformly discoverable without stage-specific knowledge.
- **User impact:** automation can misinterpret a successful inspection as a
  passing computation if it ignores report rows.
- **Maintainer and cognitive-load impact:** callers need bespoke handling.
- **Correctness or safety risk:** medium.
- **Change-coupling impact:** high because exit codes and messages are protected
  public behavior.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes; “report published with
  failed checks” is an intentional evidence model, not a generic process
  failure.
- **Recommended disposition:** document and test an exit/evidence matrix before
  considering compatible diagnostic helpers; do not normalize exit codes
  casually.
- **Characterization tests required first:** help, parse error, unavailable
  input, malformed input, valid failed evidence, lock, rollback, cleanup, and
  success for every public CLI.
- **Priority:** medium
- **Estimated effort:** medium
- **Dependencies:** Phase `01` public CLI matrix
- **Proposed phase:** Phase `01`, then reviewed Phase `03` only if compatible
- **Status:** confirmed; unresolved documentation/test burden

### RA-012 — Canonical lineage and status were stale

- **Category:** documentation ownership, stale claims
- **Affected files and symbols:** `TODO.md`, `HANDOFF.md`,
  `PIPELINE_PLAN.md`, and remote-lineage references in `RUNBOOK.md`
- **Objective evidence:** the canonical files still prescribed
  `post09-comprehensive-docpatch -> post09-refactor-roadmap ->
  post09-test-coverage`, while the authorized program begins at
  `refactor-00-comprehensive-audit`.
- **Description:** superseded branch instructions remained in every canonical
  current-state owner.
- **User impact:** a resumed operator could create the wrong descendant.
- **Maintainer and cognitive-load impact:** conflicting plans undermine the
  documentation ownership model.
- **Correctness or safety risk:** medium operational risk.
- **Change-coupling impact:** limited to canonical status and command owners.
- **Contract sensitivity:** medium; branch history is operational state, not an
  executable interface.
- **Whether duplication may be intentional:** status should not be duplicated;
  links are preferred.
- **Recommended disposition:** make the audit lineage authoritative in
  `PIPELINE_PLAN.md`, keep the live checkout in `HANDOFF.md`, and reduce
  `TODO.md` to prioritized gates.
- **Characterization tests required first:** documentation search for
  superseded branch names and consistency review after every docpatch.
- **Priority:** medium
- **Estimated effort:** small
- **Dependencies:** verified clean parent and exact authorized program
- **Proposed phase:** Phase `00`
- **Status:** resolved in Phase `00`

### RA-013 — Operations-document navigation load

- **Category:** documentation size, navigation, repetition, operator usability
- **Affected files and symbols:** `RUNBOOK.md` (`3,733` lines) and
  `TROUBLESHOOTING.md` (`2,528` lines)
- **Objective evidence:** the two operational documents contain `6,261` lines,
  more than eighty percent of the required-document corpus; troubleshooting
  contains more than seventy top-level symptom sections without a compact
  index.
- **Description:** canonical ownership is clear, but discovery within the
  owners is slow and repeated safety language obscures stage-specific facts.
- **User impact:** new researchers and operators must scan large documents to
  locate one gate or recovery path.
- **Maintainer and cognitive-load impact:** docpatches are broad and omission
  risk is high.
- **Correctness or safety risk:** medium because unique recovery instructions
  must remain findable.
- **Change-coupling impact:** documentation-wide.
- **Contract sensitivity:** medium; exact commands and unique cautions cannot
  be lost.
- **Whether duplication may be intentional:** repeated local safety warnings
  are often intentional at the action point.
- **Recommended disposition:** add generated-free manual navigation indexes
  and clearer section grouping before considering any split; map every unique
  fact before relocation.
- **Characterization tests required first:** link/anchor check, command
  inventory, unique-fact destination map, and role-based walkthroughs.
- **Priority:** medium
- **Estimated effort:** medium
- **Dependencies:** usability review
- **Proposed phase:** Phase `02d` recommendation and later documentation-only
  package
- **Status:** confirmed; deferred pending navigation plan

### RA-014 — Architecture and reliability-description drift

- **Category:** current/future topology, diagrams, stale claims
- **Affected files and symbols:** `docs/architecture/ARCHITECTURE.md`,
  `FUTURE_ARCHITECTURE.md`, `diagrams/pipeline.mmd`, and
  `diagrams/reliability.mmd`
- **Objective evidence:** current prose called the workflow linear despite
  parallel reference preparation, QC, and evidence branches; Step `09` claimed
  CMH recomputation; the generic reliability diagram labeled every dry-run
  side-effect-free and every publication atomic although early stages differ.
- **Description:** the diagrams are useful abstractions but were written more
  strongly than the implemented cross-stage guarantees.
- **User impact:** readers can assume protections that a legacy stage does not
  provide.
- **Maintainer and cognitive-load impact:** audits must reconcile prose with
  each implementation.
- **Correctness or safety risk:** medium operational risk.
- **Change-coupling impact:** architecture, runbook, troubleshooting, and audit
  claims move together.
- **Contract sensitivity:** high because safety claims influence operator
  behavior.
- **Whether duplication may be intentional:** current and future views are
  intentionally separate and should remain so.
- **Recommended disposition:** qualify the current DAG and reliability diagram
  as a target/modern-stage pattern with explicit legacy exceptions; correct
  the Step `09` boundary.
- **Characterization tests required first:** repository-wide prose-to-code
  review and Mermaid source/render review.
- **Priority:** medium
- **Estimated effort:** small
- **Dependencies:** `RA-001` and `RA-004`
- **Proposed phase:** Phase `00`
- **Status:** corrected in Phase `00`

### RA-015 — Runbook command and validation-claim drift

- **Category:** executable documentation, dependency environment, evidence
  language
- **Affected files and symbols:** local validation gate, Step `09` structured
  validation, and deferred-lineage commands in `RUNBOOK.md`
- **Objective evidence:** bare `make real-r-test` used ambient R and failed on
  the audited Mac, while the guarded `local-real-r-test` path passed; Step `09`
  prose claimed count-derived CMH recomputation; remote commands named the
  superseded local predecessor.
- **Description:** exact commands and their evidence boundaries had diverged
  from the actual successful gate and authorized lineage.
- **User impact:** a developer can get a false environment failure or overstate
  what a passing report proves.
- **Maintainer and cognitive-load impact:** multiple near-equivalent R commands
  invite accidental use of the wrong environment.
- **Correctness or safety risk:** medium.
- **Change-coupling impact:** Make targets, runbook, troubleshooting, handoff,
  and plan.
- **Contract sensitivity:** high; dependency activation remains explicit and
  opt-in.
- **Whether duplication may be intentional:** bare and guarded targets serve
  distinct environment checks, but their intended use must be explicit.
- **Recommended disposition:** use the guarded canonical target in the
  complete local gate, retain bare real-R as an explicit ambient-environment
  diagnostic, and state the exact Step `09` validation limit.
- **Characterization tests required first:** guarded activation on/off/invalid,
  ambient failure, no automatic restore, and Step `09` corruption fixtures.
- **Priority:** medium
- **Estimated effort:** small
- **Dependencies:** actual local gate evidence
- **Proposed phase:** Phase `00`
- **Status:** corrected in Phase `00`

### RA-029 — Mutable repository freshness conflicts with the locked R gate

- **Category:** dependency reproducibility, validation availability, mutable
  external state
- **Affected files and symbols:** `renv.lock`, the ignored project library,
  `scripts/check_r_environment.R` `BiocManager::valid`, `Makefile` `r-check`,
  and the local validation gate
- **Objective evidence:** on 2026-07-30, guarded `renv::status()` reported the
  project synchronized and the installed/locked `bitops` version was `1.0-9`;
  current CRAN metadata advertised `1.1-0`, causing
  `BiocManager::valid()` and `make r-check` to fail. The same check passed on
  2026-07-28 before that repository change.
- **Description:** one gate simultaneously requires exact lockfile
  synchronization and current mutable-repository freshness, so an upstream
  release can invalidate an unchanged, synchronized checkout.
- **User impact:** a documentation-only branch cannot close its full local
  gate without either updating a dependency/lock or revising validation
  policy.
- **Maintainer and cognitive-load impact:** reproducibility and freshness are
  conflated in one pass/fail result.
- **Correctness or safety risk:** high because silently bypassing either check
  would weaken dependency evidence.
- **Change-coupling impact:** R lockfile, restored library, validation script,
  tests, runbook, troubleshooting, and branch gate.
- **Contract sensitivity:** high; dependency restoration must remain explicit,
  compute must not install packages, and lock changes require review.
- **Whether duplication may be intentional:** yes; lock synchronization and
  release validity answer different questions and both are useful when
  reported separately.
- **Recommended disposition:** resolved under an explicit one-time exception
  by reviewing and locking `bitops 1.1-0` in a separate dependency commit on
  this branch. Preserve explicit restoration, guarded activation, disabled
  automatic snapshots, and reviewed lock diffs. If mutable-repository drift
  recurs, evaluate reproducible-lock and online-freshness policy separation on
  a normal separately reviewed descendant.
- **Characterization tests required first:** the initial synchronized-old-lock
  failure, exact pre/post boundary-output comparison, upstream consistency
  suite, exact current lock, no implicit dependency expansion/snapshot,
  guarded activation, and the complete repository gate were exercised.
  Offline metadata and too-new-package policy remain future reliability
  scenarios if the validation policy itself changes.
- **Priority:** high
- **Estimated effort:** medium
- **Dependencies:** explicit one-time user authorization and complete
  post-update validation
- **Proposed phase:** resolved in Phase `00`; future policy changes require a
  normal separately reviewed package
- **Status:** resolved on 2026-07-30 by commit `288dd93`; the guarded local
  gate passes with `bitops 1.1-0`

### RA-016 — No measured Python line and branch baseline

- **Category:** test measurement, refactor gate
- **Affected files and symbols:** Python test configuration, requirements, and
  Make targets
- **Objective evidence:** no tracked line/branch coverage tool, baseline
  artifact, or non-regression target exists at the audited commit.
- **Description:** pass counts show scenario execution but not unexercised
  branches in large safety-critical modules.
- **User impact:** refactors cannot be compared against a quantified Python
  baseline.
- **Maintainer and cognitive-load impact:** test sufficiency depends on manual
  inspection alone.
- **Correctness or safety risk:** high during later refactors.
- **Change-coupling impact:** developer-only dependencies and CI/local gates.
- **Contract sensitivity:** low if tooling remains explicit and development
  only.
- **Whether duplication may be intentional:** numerical coverage never replaces
  scenario coverage.
- **Recommended disposition:** add pinned developer-only line/branch coverage,
  record global and per-module baselines, and enforce no reduction plus the
  new-module thresholds.
- **Characterization tests required first:** self-test the coverage target,
  exclusion policy, subprocess/shell boundaries, and deterministic baseline
  generation.
- **Priority:** high
- **Estimated effort:** medium
- **Dependencies:** explicit dependency installation approval within Phase
  `01`
- **Proposed phase:** `refactor-01-test-baseline`
- **Resolution evidence:** the Phase `01` package pins developer-only
  line/branch measurement, traces Python subprocesses, records deterministic
  global and per-module data, rejects exact global regression and missing
  modules, and self-tests the measurement/check interfaces. See
  [`TEST_BASELINE.md`](TEST_BASELINE.md).
- **Status:** resolved; the measured baseline is now a continuing gate

### RA-017 — Incomplete public-contract traceability

- **Category:** regression boundary, CLI, transaction, schema
- **Affected files and symbols:** every public script and SLURM entrypoint,
  schemas, Make targets, and tests
- **Objective evidence:** no single matrix maps each CLI to help, dry-run,
  execute, malformed/missing input, failed evidence, lock, rollback, signal,
  recovery, deterministic bytes, and exit behavior.
- **Description:** many strong tests exist, but coverage is distributed and
  completeness cannot be demonstrated.
- **User impact:** a protected public behavior can change without a clearly
  named regression test.
- **Maintainer and cognitive-load impact:** reviewers repeatedly search the
  corpus to determine whether a contract is covered.
- **Correctness or safety risk:** high during refactoring.
- **Change-coupling impact:** repository-wide tests and docs.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** independent contract tests
  across layers are intentional.
- **Recommended disposition:** create the required risk-to-test matrix and
  derive one cohesive test-hardening branch per uncovered high-risk gap.
- **Characterization tests required first:** the matrix itself must include
  every protected compatibility item from the authorized program.
- **Priority:** high
- **Estimated effort:** large
- **Dependencies:** `RA-016`
- **Proposed phase:** Phase `01`
- **Resolution evidence:** [`TEST_BASELINE.md`](TEST_BASELINE.md) now names
  every Python, shell, R, SLURM, and Make entry point; maps protected
  transaction/schema/status/determinism/recovery/evidence boundaries; and
  classifies fixture independence.
- **Status:** matrix resolved; the first evidence-derived characterization gap
  is complete and five remain queued in the authoritative lineage

### RA-018 — Uneven SLURM behavior coverage

- **Category:** wrapper compatibility, runtime boundary, test gaps
- **Affected files and symbols:** `jobs/*.slurm`, especially Steps `00a`–`04`,
  `template.slurm`, `tool_check.slurm`, and `validate_manifest.slurm`
- **Objective evidence:** strong dynamic wrapper cases exist for Steps
  `00c`, `05`–`09`; early wrappers have partial or no execute/invalid flag,
  delegation, module, output-validation, and arbitrary-CWD coverage. Steps
  `00a` and `00b` embed compute rather than delegate.
- **Description:** wrapper confidence varies by generation.
- **User impact:** cluster-only argument, path, or mode regressions can escape
  local tests.
- **Maintainer and cognitive-load impact:** wrapper conventions cannot be
  assumed uniformly.
- **Correctness or safety risk:** high for cluster execution.
- **Change-coupling impact:** jobs, scripts, shell fixtures, and runbook.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** wrappers should remain thin and
  stage-specific; a generic dispatcher is not warranted.
- **Recommended disposition:** characterize each wrapper with mocked module
  and command environments; document legacy exceptions instead of changing
  them prematurely.
- **Characterization tests required first:** default/execute/invalid modes,
  module list/load, submit CWD, delegation, exact arguments, no heavy login-node
  work, output validation, and exit propagation.
- **Priority:** high
- **Estimated effort:** large
- **Dependencies:** public CLI matrix
- **Proposed phase:** Phase `01`
- **Status:** confirmed; queued

### RA-019 — Production/test shared-defect exposure

- **Category:** test independence, fixture correctness
- **Affected files and symbols:** validator tests importing production
  headers/constants; fixture builders importing or mirroring production
  contracts
- **Objective evidence:** tests for Step `08` directly import production
  constants, and large builders share contract vocabulary with the producers;
  the Step `09` false-CMH case passed because all dependent fields were changed
  consistently.
- **Description:** some tests prove internal consistency rather than an
  independent external contract.
- **User impact:** producer and test can agree on the same wrong rule.
- **Maintainer and cognitive-load impact:** apparent coverage overstates defect
  detection.
- **Correctness or safety risk:** high for scientific and serialized contracts.
- **Change-coupling impact:** production constants and fixtures change
  together.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** yes; independently spelled
  expected headers, rosters, formulas, and bytes are valuable duplication.
- **Recommended disposition:** classify every fixture as producer-coupled or
  independent and add independent goldens/oracles for critical contracts.
- **Characterization tests required first:** mutation of production constants,
  check rosters, formulas, status transitions, headers, ordering, and hashes
  while the independent expectation remains fixed.
- **Priority:** high
- **Estimated effort:** medium
- **Dependencies:** `RA-001`, `RA-003`, and risk-to-test matrix
- **Proposed phase:** Phase `01`
- **Status:** confirmed; queued

### RA-020 — Large fixture builders and coupled integration edits

- **Category:** test maintainability, fixture duplication, shotgun surgery
- **Affected files and symbols:** artifact adapter/run-summary builders and
  test modules, including tests of `1,565`–`1,961` lines
- **Objective evidence:** every per-step validator package changed both shared
  fixture builders and three integration test modules; builders generate
  cross-layer artifacts for many stages.
- **Description:** adding one stage requires editing broad fixture construction
  code and long integration suites.
- **User impact:** no direct runtime failure, but regression work is slow and
  error-prone.
- **Maintainer and cognitive-load impact:** high.
- **Correctness or safety risk:** medium because fixtures define expected
  evidence projections.
- **Change-coupling impact:** high and historically observed.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** end-to-end fixtures are
  intentionally integrated; independent small goldens should supplement, not
  replace them.
- **Recommended disposition:** split stage fixture declarations from neutral
  builders only after freezing independent outputs; keep end-to-end coverage.
- **Characterization tests required first:** deterministic fixture rebuild,
  independent known-good bytes, one-stage addition, and corrupted stage
  projection cases.
- **Priority:** medium
- **Estimated effort:** large
- **Dependencies:** coverage and fixture-independence classification
- **Proposed phase:** Phase `01` hardening, then reviewed Phase `03`
- **Status:** confirmed; candidate

### RA-021 — Stale planning and configuration artifacts

- **Category:** hygiene, dead/stale assets, discoverability
- **Affected files and symbols:** `tests/pending/test_step_04_mark_duplicates.sh`,
  `tests/pending/test_step_06_split_bam_by_read_orientation.sh`,
  `configs/local_test.yaml`, and utility jobs
- **Objective evidence:** pending Step `04` and `06` plans describe tests that
  now exist; `local_test.yaml` has no discovered active consumer; utility jobs
  lack one clear operator-ownership narrative.
- **Description:** historical scaffolds remain alongside implemented behavior.
- **User impact:** new contributors can mistake stale plans/configs for active
  entrypoints.
- **Maintainer and cognitive-load impact:** low to medium.
- **Correctness or safety risk:** low unless an operator executes a stale
  artifact.
- **Change-coupling impact:** low.
- **Contract sensitivity:** medium; absence of a discovered consumer is not
  proof that an external user has none.
- **Whether duplication may be intentional:** pending plans may preserve
  history, but that role is not declared.
- **Recommended disposition:** confirm Git history and references, then mark,
  archive with destination, or remove only through a separately reviewed
  documentation/test package; do not infer dead production code.
- **Characterization tests required first:** repository reference search,
  direct user-facing documentation search, and active-job inventory.
- **Priority:** low
- **Estimated effort:** small
- **Dependencies:** usability review
- **Proposed phase:** Phase `01` evidence, then documentation-only cleanup
- **Status:** confirmed stale candidates; no deletion authorized

### RA-022 — Repeated parsing, hashing, and input I/O lacks measurement

- **Category:** performance, avoidable I/O, stable-input checks
- **Affected files and symbols:** artifact adapter, run summary, report
  renderer, validators, and early reference/FASTQ preparation
- **Objective evidence:** large explicit transactions are parsed and/or hashed
  at multiple validation layers; Step `00a` conditionally decompresses shared
  references; Step `01` delegates gzip decompression per alignment. No profile
  quantifies the local overhead.
- **Description:** some repetition is required for independent validation and
  mutation detection, while some may be avoidable within one process.
- **User impact:** potential local and future cluster latency; no current
  measured bottleneck.
- **Maintainer and cognitive-load impact:** optimization proposals are hard to
  judge without profiles.
- **Correctness or safety risk:** medium if caching weakens stable-input checks.
- **Change-coupling impact:** high around hashes and immutable identity.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** yes; re-reading and rehashing at
  trust boundaries is often intentional.
- **Recommended disposition:** instrument representative fixtures and retain
  independent boundary checks; optimize only proven repeated work within one
  ownership boundary.
- **Characterization tests required first:** call/count profiling, mutation
  between reads, deterministic hash/serialization, and large-file estimates
  without production execution.
- **Priority:** low
- **Estimated effort:** medium
- **Dependencies:** measured baseline and remote evidence for runtime changes
- **Proposed phase:** measurement in Phase `01`; implementation only if later
  reviews justify it
- **Status:** candidate; no performance defect claimed

### RA-023 — Direct-script and working-directory inconsistency

- **Category:** portability, import compatibility, file modes
- **Affected files and symbols:** Python sibling imports, shell scripts with
  mixed executable modes, SLURM wrappers using relative paths, and runbook
  examples
- **Objective evidence:** Python scripts depend on repository-local sibling
  imports; shell scripts and jobs are a mix of executable and non-executable
  modes; wrappers vary between explicit `SLURM_SUBMIT_DIR` changes and caller
  CWD assumptions.
- **Description:** direct invocation works through documented paths but the
  supported CWD and executable-mode boundary is not uniform.
- **User impact:** a user can see import/path or permission failures when using
  an otherwise plausible invocation.
- **Maintainer and cognitive-load impact:** packaging or module extraction can
  silently break direct scripts and SLURM.
- **Correctness or safety risk:** low now, high during refactoring.
- **Change-coupling impact:** scripts, imports, tests, runbook, and jobs.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** explicit `bash script.sh`
  invocation is a valid compatibility choice.
- **Recommended disposition:** inventory and test the currently documented
  direct-script, repository-root, alternate-CWD, and SLURM forms before
  selecting any package layout.
- **Characterization tests required first:** `--help` and dry-run from the
  repository root and another CWD, environment-only invocation, import without
  installation, and job submit-directory behavior.
- **Priority:** low
- **Estimated effort:** medium
- **Dependencies:** Phase `01` CLI/SLURM matrix
- **Proposed phase:** Phase `01`
- **Status:** confirmed inconsistency; preserve until measured

### RA-024 — Independent shell, R, and Python checks should not be collapsed

- **Category:** do not abstract, independent verification
- **Affected files and symbols:** Step `08` and `09` shell tests, real-R tests,
  and structured Python validators
- **Objective evidence:** the three layers exercise different failure modes:
  transaction/orchestration, actual R semantics, and read-only output
  reconciliation.
- **Description:** similar checks are not equivalent duplicates.
- **User impact:** collapsing them would reduce the chance of detecting a
  shared implementation defect.
- **Maintainer and cognitive-load impact:** higher test volume is justified by
  independent evidence.
- **Correctness or safety risk:** high if collapsed.
- **Change-coupling impact:** keeping layers independent limits common-mode
  failures.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes, explicitly.
- **Recommended disposition:** retain independent implementations; share only
  inert fixture transport when independence is proven.
- **Characterization tests required first:** none for retention; future helper
  proposals must demonstrate they do not share the rule under test.
- **Priority:** retain
- **Estimated effort:** none
- **Dependencies:** none
- **Proposed phase:** permanent constraint
- **Status:** intentionally retained

### RA-025 — Steps 07–09 algorithms are outside local refactor scope

- **Category:** do not abstract, scientific/statistical boundary
- **Affected files and symbols:** Step `07` bcftools behavior, Step `08`
  orientation/allele semantics, Step `09` CMH/BH/threshold/call algorithms
- **Objective evidence:** Step `07` has mocked-bcftools evidence only; Steps
  `08` and `09` have guarded local real-R fixtures but no production/cluster
  baseline.
- **Description:** algorithmic restructuring cannot be evaluated safely from
  the current local evidence.
- **User impact:** premature refactoring could change scientific results.
- **Maintainer and cognitive-load impact:** deferral preserves a clear boundary
  for the local engineering program.
- **Correctness or safety risk:** very high.
- **Change-coupling impact:** scientific outputs, schemas, reports, and review
  evidence.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes; stage-local scientific code
  should remain explicit until another cohort supports abstraction.
- **Recommended disposition:** characterize and preserve only; defer algorithm
  refactors until inspected upstream-sequential runtime evidence exists.
- **Characterization tests required first:** current local semantic goldens
  plus future real-bcftools, cluster outputs, logs, hashes, and another cohort.
- **Priority:** defer
- **Estimated effort:** very large
- **Dependencies:** remote validation and separate scientific authorization
- **Proposed phase:** outside the current local refactor program
- **Status:** explicitly deferred

### RA-026 — Action-local safety and producer-specific recovery should remain visible

- **Category:** do not abstract, operator recovery, documentation
- **Affected files and symbols:** transaction implementations and their
  corresponding `RUNBOOK.md`/`TROUBLESHOOTING.md` sections
- **Objective evidence:** each producer names different stable members, lock
  forms, backup paths, commit markers, validation rules, and recovery evidence.
- **Description:** local repetition gives operators the exact facts needed at
  the failure point.
- **User impact:** replacing it with a generic reference can make recovery less
  safe.
- **Maintainer and cognitive-load impact:** repetition costs maintenance but
  reduces context switching during incidents.
- **Correctness or safety risk:** very high if unique instructions are lost.
- **Change-coupling impact:** broad if centralized.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes.
- **Recommended disposition:** retain action-local warnings and exact recovery
  paths; navigation aids may link to them, but a later consolidation must map
  every unique fact.
- **Characterization tests required first:** unique-fact inventory and
  role-based recovery walkthroughs.
- **Priority:** retain/evaluate
- **Estimated effort:** large for any safe consolidation
- **Dependencies:** usability and reliability reviews
- **Proposed phase:** permanent constraint on later documentation/refactor work
- **Status:** intentionally retained pending proof

### RA-027 — Computational, transaction, scientific, and biological states must stay separate

- **Category:** do not abstract, evidence-state safety
- **Affected files and symbols:** schemas, artifact records, run summaries,
  report banners, Step `09c`, docs, and status vocabularies
- **Objective evidence:** the current contracts separately represent
  implementation, local testing, runtime validation, cluster dry-run, cluster
  proof, science review, transaction completion, and reserved biological
  readiness.
- **Description:** apparent status duplication encodes distinct evidence
  questions.
- **User impact:** collapsing states would create false scientific or
  operational claims.
- **Maintainer and cognitive-load impact:** the vocabulary is large but
  necessary.
- **Correctness or safety risk:** very high.
- **Change-coupling impact:** repository-wide public contracts.
- **Contract sensitivity:** very high.
- **Whether duplication may be intentional:** yes.
- **Recommended disposition:** retain closed vocabularies and explicit
  transitions; improve navigation and typed internal representation without
  merging meanings.
- **Characterization tests required first:** every lawful/unlawful transition,
  report banner, reserved-ready rejection, and transaction-complete with
  failed/missing evidence.
- **Priority:** retain
- **Estimated effort:** none for retention
- **Dependencies:** none
- **Proposed phase:** permanent compatibility boundary
- **Status:** intentionally retained

### RA-028 — Unique documentation evidence must survive any navigation refactor

- **Category:** do not delete, documentation provenance
- **Affected files and symbols:** mandatory docs, architecture docs, diagrams,
  and demo material
- **Objective evidence:** current owners contain unique cohort names,
  historical cluster evidence, exact recovery commands, durable decisions,
  open questions, and scientific cautions that are not interchangeable.
- **Description:** document size and repetition do not justify wholesale
  merging, archiving, or deletion.
- **User impact:** lost provenance would impair takeover, recovery, and
  scientific review.
- **Maintainer and cognitive-load impact:** any navigation change needs a
  destination map rather than broad trimming.
- **Correctness or safety risk:** high if unique evidence is removed.
- **Change-coupling impact:** documentation-wide.
- **Contract sensitivity:** high.
- **Whether duplication may be intentional:** local cautions may be repeated
  intentionally; mutable status should still have one owner.
- **Recommended disposition:** preserve all unique facts, use links for mutable
  facts, and require an explicit source-to-destination inventory before any
  merge, split, archive, or deletion.
- **Characterization tests required first:** link check, unique-fact map,
  canonical-owner search, diagram-source comparison, and role-based review.
- **Priority:** retain
- **Estimated effort:** none for retention
- **Dependencies:** documentation usability review
- **Proposed phase:** permanent constraint
- **Status:** intentionally retained

## Phase recommendations

The findings and measured Phase `01` baseline support the authorized sequence:

1. The developer-only Python coverage baseline and public-contract matrix are
   established in [`TEST_BASELINE.md`](TEST_BASELINE.md) before any production
   refactor.
2. The independent Step `09` oracle and shared validation-publication fault
   characterizations are complete. The four remaining measured hardening gaps
   cover exact check rosters, public CLI/exit behavior, every SLURM wrapper,
   and independent critical goldens. The intervening validation-efficiency
   package reduces local gate cost without changing production behavior.
   Exact descendant names and order are owned by
   [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
3. Phase `02` should prefer small neutral seams over a repository-wide
   framework. The architecture review must reject reversed dependency
   direction; the reliability review must preserve every transaction state;
   the usability review must preserve unique operational evidence.
4. Phase `03` may consider neutral validation-report infrastructure, adapter
   decomposition, report-cycle removal, and narrow typed models only after the
   measured gate and three reviews.
5. Steps `07`–`09` scientific algorithms, automatic cleanup, generic
   dispatchers/job arrays, and biological-readiness policy remain outside the
   local refactor scope.

## Recheck triggers

Re-run this audit evidence before changing a disposition when:

- a public schema, check roster, status vocabulary, receipt, or output byte
  contract changes;
- runtime or cluster evidence for Steps `07`–`09` lands;
- a production Step `09c` review or report is inspected;
- an implementation package changes a transaction or recovery path;
- coverage or mutation evidence contradicts the current ranking;
- a proposed abstraction would make an independent test import the production
  rule it is meant to verify.
