# Refactor audit index and recheck triggers

This is the current route for refactor-audit findings and recheck triggers. It
does not restate dated evidence or own roadmap order, task status, executable
behavior, or scientific conclusions.

## Historical record

The complete Phase `00` audit is frozen as the
[`2026-07-30 comprehensive refactor audit`](../history/audits/2026-07-30-comprehensive-refactor-audit.md).
That record identifies the audited target, initial record commit, exact frozen
source snapshot, later amendment date, and source blob. Its ranks,
recommendations, measurements, and finding statuses describe that dated
record; current order remains in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), current
checkout and evidence in [`HANDOFF.md`](../operations/HANDOFF.md), and active
task status in the [task registry](../tasks/README.md).

## Finding index

The links below are navigation into the immutable record, not current status
claims.

| ID | Historical finding |
| --- | --- |
| [`RA-001`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-001--step-09-independent-cmh-oracle-gap) | Step 09 independent CMH oracle gap |
| [`RA-002`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-002--shared-validation-publication-and-recheck-safety) | Shared validation publication and recheck safety |
| [`RA-003`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-003--adapter-does-not-enforce-exact-validator-check-rosters) | Exact validator check-rosters gap |
| [`RA-004`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-004--legacy-early-stage-execution-and-publication-behavior) | Legacy early-stage execution and publication behavior |
| [`RA-005`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-005--artifact-adapter-monolith-and-shotgun-surgery) | Artifact-adapter cohesion and coupling |
| [`RA-006`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-006--report-module-import-cycle) | Report-module import cycle |
| [`RA-007`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-007--stage-specific-modules-used-as-generic-infrastructure) | Stage-specific modules used as generic infrastructure |
| [`RA-008`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-008--oversized-mixed-responsibility-modules) | Oversized mixed-responsibility modules |
| [`RA-009`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-009--repeated-transaction-mechanisms-are-not-one-proven-abstraction) | Heterogeneous transaction mechanisms |
| [`RA-010`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-010--primitive-internal-representations-hide-invariants) | Primitive internal representations |
| [`RA-011`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-011--diagnostic-and-exit-semantics-are-inconsistent) | Diagnostic and exit semantics |
| [`RA-012`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-012--canonical-lineage-and-status-were-stale) | Stale canonical lineage and status |
| [`RA-013`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-013--operations-document-navigation-load) | Operations-document navigation load |
| [`RA-014`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-014--architecture-and-reliability-description-drift) | Architecture and reliability-description drift |
| [`RA-015`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-015--runbook-command-and-validation-claim-drift) | Runbook command and validation-claim drift |
| [`RA-029`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-029--mutable-repository-freshness-conflicts-with-the-locked-r-gate) | Locked-R versus mutable-repository freshness |
| [`RA-016`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-016--no-measured-python-line-and-branch-baseline) | Missing measured Python baseline |
| [`RA-017`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-017--incomplete-public-contract-traceability) | Incomplete public-contract traceability |
| [`RA-018`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-018--uneven-slurm-behavior-coverage) | Uneven SLURM behavior coverage |
| [`RA-019`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-019--productiontest-shared-defect-exposure) | Production/test shared-defect exposure |
| [`RA-020`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-020--large-fixture-builders-and-coupled-integration-edits) | Large fixture builders and coupled integration edits |
| [`RA-021`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-021--stale-planning-and-configuration-artifacts) | Stale planning and configuration artifacts |
| [`RA-022`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-022--repeated-parsing-hashing-and-input-io-lacks-measurement) | Unmeasured repeated parsing, hashing, and input I/O |
| [`RA-023`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-023--direct-script-and-working-directory-inconsistency) | Direct-script and working-directory inconsistency |
| [`RA-024`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-024--independent-shell-r-and-python-checks-should-not-be-collapsed) | Independent shell, R, and Python checks |
| [`RA-025`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-025--steps-0709-algorithms-are-outside-local-refactor-scope) | Steps 07–09 algorithm boundary |
| [`RA-026`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-026--action-local-safety-and-producer-specific-recovery-should-remain-visible) | Action-local safety and producer-specific recovery |
| [`RA-027`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-027--computational-transaction-scientific-and-biological-states-must-stay-separate) | Evidence-state separation |
| [`RA-028`](../history/audits/2026-07-30-comprehensive-refactor-audit.md#ra-028--unique-documentation-evidence-must-survive-any-navigation-refactor) | Unique documentation evidence preservation |

## Current dispositions

| Finding | Current disposition |
| --- | --- |
| `RA-006` | Resolved for the live reporting owner. The public renderer files are compatibility facades over one private `_run_report` package; dispatch points from HTML selection to the bundle coordinator without the former HTML-to-bundle-to-HTML cycle. Direct-import, direct-script, format, deterministic-output, signal, lock, rollback, recovery, and arbitrary-CWD contracts remain protected by `make report-test`. |
| `RA-008` | The Step `09` scientific-evidence contract, artifact-contract Python, artifact-index, canonical run-summary, and reporting-renderer slices are resolved; the repository-wide finding remains open for its other named owners. Step `09` now has a 47-line public compatibility owner over definition, support, table, and semantic modules no larger than 373 lines, while preserving its public fingerprint and shared Step `08` identities. Artifact contracts retain 47- and 18-line compatibility owners with a largest extracted owner of 422 lines; the five-schema registry remains one file per public `$id`. Reporting slices retain their established facade, fault-injection, and transaction boundaries. No scientific algorithm, independent oracle, generic framework, or shared-library promotion was introduced. |

The reporting package passed 157 focused report tests plus its shell contract.
The repository coverage non-regression gate passed 1,250 tests with 18 skips at
line `0.856677` and branch `0.746936`, above the tracked `0.838935` and
`0.736276` baselines. These are local engineering results only; they do not
establish runtime, cluster, scientific-review, or biological evidence.

## Current recheck triggers

Re-run the applicable audit evidence before changing a disposition when:

- a public schema, check roster, status vocabulary, receipt, or output byte
  contract changes;
- runtime or cluster evidence for Steps `07`–`09` lands;
- a production Step `09c` review or report is inspected;
- an implementation package changes a transaction or recovery path;
- coverage or mutation evidence contradicts the current ranking; or
- a proposed abstraction would make an independent test import the production
  rule it is meant to verify.
