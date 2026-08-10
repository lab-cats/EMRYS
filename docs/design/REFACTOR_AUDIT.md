# Refactor audit index and recheck triggers

This file is the self-contained current owner for refactor findings, durable
constraints, and recheck triggers. It does not own roadmap order, task status,
executable behavior, or scientific conclusions. Exact current behavior and
defects remain with the applicable owner `README.md` and `CONTRACT.md`; current
test routes remain in [`TEST_BASELINE.md`](TEST_BASELINE.md).

## Status vocabulary

- `open` — a verified current gap still needs a separately reviewed correction;
- `characterized` — tests or owner documentation expose the defect or limit,
  but do not approve or correct it;
- `monitor` — no current defect justifies work; measure again on the named
  trigger;
- `resolved` — the current owner topology and regression routes remove the
  finding; and
- `retain` — the boundary is intentionally independent or owner-specific and
  must not be collapsed by a generic refactor.

## Current finding ledger

| ID | Finding | Status and current route |
| --- | --- | --- |
| `RA-001` | Step `09` independent CMH oracle gap | `open`: the count-derived test oracle is independent, but the production validator still does not recompute CMH statistic, p-value, odds ratio, or count-derived estimability. |
| `RA-002` | Shared validation publication and recheck safety | `open`: fault tests characterize metadata-only rewrite blindness, late-foreign-final deletion, and incomplete rollback or lock-loss; successful-path report bytes remain protected. |
| `RA-003` | Exact validator check-roster gap | `open`: artifact inspection validates common structure, safe unique IDs, step, scope, and status, but still does not enforce each producer's exact ordered check roster. |
| `RA-004` | Early-stage execution and publication behavior | `characterized`: direct-final, partial-publication, stale-output, dry-run, and recovery limits remain producer-specific and are routed through [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) and owner contracts. |
| `RA-005` | Artifact-adapter cohesion and coupling | `resolved`: artifact indexing now has one public facade over private registry, inspection, reconciliation, assembly, validation, and publication owners. |
| `RA-006` | Report-module import cycle | `resolved`: the public renderers delegate to an acyclic private `_run_report` package while retaining their public entry points. |
| `RA-007` | Stage-specific code used as generic infrastructure | `resolved`: the complete allowed neutral seams and dependency direction are declared in [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md); peer-private imports remain prohibited. |
| `RA-008` | Oversized mixed-responsibility modules | `monitor`: the reporting, artifact, runtime, storage, reference, Step `08`, Step `09`, and Step `09c` slices were decomposed without scientific or evidence-policy change; reassess other owners only with a measured coupling or change-cost trigger. |
| `RA-009` | Heterogeneous transaction mechanisms | `retain`: locking, publication, rollback, and recovery stay producer-specific until equivalent semantics and failure states are proved across named consumers. |
| `RA-010` | Primitive internal representations | `monitor`: introduce stronger internal models only when a current invariant is hidden or repeated; representation similarity alone is not refactor authority. |
| `RA-011` | Diagnostic and exit semantics | `characterized`: readable failed evidence may publish `status=fail` and exit zero, while malformed or unsafe operation exits nonzero and publishes nothing; other stream and exit behavior stays owner-local. |
| `RA-012` | Stale canonical lineage and status | `resolved`: [`HANDOFF.md`](../operations/HANDOFF.md), [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), the task registry, and live Git have distinct current ownership. |
| `RA-013` | Operations-document navigation load | `resolved`: canonical ownership, compact task routing, owner-local commands, and the reduced runbook/troubleshooting routes replace repeated narrative. |
| `RA-014` | Architecture and reliability-description drift | `resolved`: current topology, artifact edges, and evidence boundaries have explicit canonical owners. |
| `RA-015` | Runbook command and validation-claim drift | `resolved`: supported commands live in [`RUNBOOK.md`](../operations/RUNBOOK.md); [`TEST_BASELINE.md`](TEST_BASELINE.md) limits what each validation route proves. |
| `RA-016` | Missing measured Python baseline | `resolved`: the tracked line/branch snapshot, comparator, update boundary, and direct policy tests own the current baseline. |
| `RA-017` | Incomplete public-contract traceability | `resolved`: public CLI, SLURM, roster, contract-golden, transaction, and scientific-oracle routes are indexed in [`TEST_BASELINE.md`](TEST_BASELINE.md). |
| `RA-018` | Uneven SLURM behavior coverage | `characterized`: local directives, delegation, modes, arguments, CWD, and exits are covered; real scheduler, module, and production-runtime evidence remains environment-deferred. |
| `RA-019` | Production/test shared-defect exposure | `retain`: independent rosters, contract goldens, frozen bytes, and the CMH oracle supplement producer-coupled fixtures and must not import the production rule they verify. |
| `RA-020` | Large fixture builders and coupled integration edits | `monitor`: split a fixture only after measured repeated surgery or loss of expectation independence; size alone is insufficient. |
| `RA-021` | Stale planning and configuration artifacts | `resolved`: the [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md) and compact [`BACKLOG.md`](../tasks/BACKLOG.md) explicitly classify retained root surfaces, deferred inputs, and actionable work. |
| `RA-022` | Unmeasured repeated parsing, hashing, and input I/O | `monitor`: measure material runtime or change cost before caching or sharing; textual repetition is not evidence of a safe seam. |
| `RA-023` | Direct-script and working-directory inconsistency | `characterized`: public CLI and owner suites preserve declared file modes, arbitrary-CWD behavior, Bash `3.2` limits, side effects, and failures. |
| `RA-024` | Independent shell, R, and Python checks | `retain`: these lanes detect different failure classes and must not be collapsed into one production-derived oracle. |
| `RA-025` | Steps `07`–`09` algorithm boundary | `retain`: local refactors may preserve and characterize these algorithms but may not change or validate scientific meaning beyond the named independent evidence. |
| `RA-026` | Action-local safety and recovery | `retain`: recovery stays visible with the producer whose files, locks, transactions, and failure states it governs. |
| `RA-027` | Evidence-state separation | `retain`: computational, transaction, local-test, runtime, cluster, scientific-review, and biological-readiness states remain distinct. |
| `RA-028` | Unique documentation evidence preservation | `retain`: before deleting a live document, move each operative contract, safety rule, defect, and evidence ceiling to the owner declared by the [sitemap ownership rules](../sitemap/README.md#canonical-roles). |
| `RA-029` | Locked R reproducibility versus mutable repository freshness | `resolved/recheck`: [`RUNBOOK.md`](../operations/RUNBOOK.md) makes restoration explicit and lock changes reviewed; a future upstream-metadata-only failure stops for policy review rather than silently refreshing the lock. |

## Active correction boundaries

### `RA-001` — production CMH validation

The independent test oracle derives Step `09` statistic, p-value, odds ratio,
and estimability behavior from counts. The production validator checks related
depth, allele-frequency, background, call, and global-BH semantics but can
still accept a coordinated false CMH result. Any correction must preserve the
public check roster, statuses, deterministic report bytes, valid degeneracy
behavior, and the oracle's independence; local characterization is not
scientific or biological validation.

Recheck through the production
[`validate_step_09_cmh_outputs.py`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/validate_step_09_cmh_outputs.py)
and the independent
[`test_step_09_cmh_oracle.py`](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py).

### `RA-002` — validation-report publication

The shared publisher can miss a same-size rewrite with restored mtime, delete a
late foreign final, or lose protection after incomplete rollback or cleanup.
Any correction must preserve valid first/repeat publication bytes, names,
stage and predecessor validation, symlink and identity rejection, signal
behavior, descriptor cleanup, and recovery evidence across every consuming
validator. Do not generalize this transaction to unrelated publishers.

Recheck through the shared publisher's
[`test_validation_report.py`](../../tests/libraries/test_validation_report.py)
and every affected validator transaction suite.

### `RA-003` — artifact-side roster enforcement

Independent fixtures freeze every validator's ordered check IDs. Artifact
inspection must eventually reject missing, extra, substituted, duplicate, or
reordered checks without importing the producer roster or changing valid
records. Until then, a structurally plausible report can be mislabeled in the
artifact graph even when its native validator would reject it.

Recheck the current
[`inspection.py`](../../src/norad/reporting/_artifact_index/inspection.py),
independent [roster expectations](../../tests/contract_integration/validation_rosters/validation_roster_expectations.py),
and [artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py).

### `RA-008` — residual decomposition

Completed decompositions preserved public facades, direct imports, function
bodies, deterministic outputs, transactions, and evidence boundaries. Reopen
only for a named owner with measured repeated edit coupling, review load, or
regression isolation failure. Do not use facade size to hide total owner size,
create a generic framework, or move scientific and recovery policy into a
shared utility.

The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
owns the current decomposition and direct protection routes.

## Permanent refactor constraints

- Preserve independent expectations even when that duplicates a production
  rule intentionally.
- Preserve producer-specific transaction and recovery semantics; similarity
  is not proof of one safe abstraction.
- Preserve public schemas, headers, bytes, check rosters, paths, modes,
  streams, exits, CWD behavior, and unrelated-file boundaries.
- Preserve scientific-algorithm and evidence-state boundaries. Structural
  cleanup does not promote runtime, cluster, review, or biological evidence.
- Preserve unique operative documentation in its canonical subject owner;
  discard chronology, repeated totals, and superseded planning after that move.

## Current recheck triggers

Re-run the applicable audit evidence before changing a disposition when:

- a public schema, check roster, status vocabulary, receipt, or output byte
  contract changes;
- runtime or cluster evidence for Steps `07`–`09` lands;
- a production Step `09c` review or report is inspected;
- an implementation package changes a transaction or recovery path;
- coverage, mutation evidence, or repeated change coupling contradicts a
  current disposition;
- mutable dependency metadata invalidates an otherwise synchronized lock; or
- a proposed abstraction would make an independent test import the production
  rule it is meant to verify.
