# Future implementation roadmap

This document is the evidence-ranked engineering opportunity register for
NORAD. It records where maintenance cost, coupling, repeated support code, or
unclear ownership justifies future work, and it defines the evidence required
before that work begins.

This is not the live package plan. Approved branch lineage, package status,
and current acceptance criteria belong in
[`PIPELINE_PLAN.md`](PIPELINE_PLAN.md). Target-state constraints belong in
[`../architecture/FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md).
The detailed coverage inventory, residual gaps, and ratchet strategy belong in
[`TEST_COVERAGE_ROADMAP.md`](TEST_COVERAGE_ROADMAP.md).

## Decision rule

Refactoring is justified when it reduces a demonstrated maintenance or safety
risk while preserving observable behavior. Line count or visual similarity
alone is not sufficient.

Use four readiness classes:

| Readiness | Meaning |
| --- | --- |
| Foundation | May proceed after focused characterization tests; no new runtime evidence is required |
| Production-gated | Wait for one inspected production transaction or cluster/runtime baseline |
| Second-cohort-gated | Wait for unchanged interfaces to run against a genuinely different real cohort |
| Evidence-triggered | Implement only after repeated operational evidence demonstrates a concrete need |

Moving a production-gated or second-cohort-gated item earlier requires an
explicit change to the authoritative plan. A prior cluster-proven result is a
comparison baseline, not proof for changed code.

## Invariants for every package

Future maintenance work must preserve, unless a separately approved versioned
change says otherwise:

- public script and job entry points, arguments, environment variables, exit
  semantics, and output paths;
- side-effect-free dry-run behavior and explicit execute mode;
- manifest-defined identity, ordering, pairing, and explicit-input-only
  operation;
- exact public headers, row order, JSON Schema IDs and versions, canonical
  hashes, and immutable run-identity rules;
- CMH, global Benjamini-Hochberg, background, threshold, and candidate-order
  semantics;
- `legacy_provisional_v1`, neutral mechanical-orientation language, and the
  separation of computational, scientific, and biological states;
- exact table authorization and deterministic report projections;
- owned locks, run-token staging, stable-input rechecks, no-clobber behavior,
  rollback, cleanup, retained recovery evidence, and marker-last publication;
- independent shell, R, and Python checks where their agreement is deliberate
  defense in depth.

A refactor package must start with characterization or fault-injection tests,
retain compatibility facades, and compare exact outputs and negative cases.
Behavior improvements belong in a later package after equivalence is proven.

## Repository audit snapshot

The following structural measurements identify risk concentrations. They are
not quality scores and do not authorize a rewrite.

| Area | Observed signal | Interpretation |
| --- | --- | --- |
| Validation reports | `validate_step_00a_star_index.py` is 411 lines after recovery hardening; the other 12 step validators import it and make 165 `report.*` references | Generic report and publication ownership is inverted through a Step `00a` module |
| Scientific review | `step_09c_scientific_validation.py` is 4,533 lines and combines shared contracts, semantic law, evidence assembly, CLI behavior, and transaction publication | Pure contracts and executable coordination need separate ownership |
| Artifact contracts | `validate_artifact_contracts.py` is 1,896 lines and validates four public record types plus the shared schema and inventory | Record-specific semantics can be isolated behind the existing CLI |
| Artifact index | `build_artifact_index.py` is 5,404 lines with 92 top-level definitions, 62 adapter specifications, and 14 step rosters serving the explicit 81-row fixture inventory | Registry, inspection, reconciliation, projection, and publication concerns are concentrated in one module |
| Run summary | `build_run_summary.py` is 2,789 lines with 53 top-level definitions and uses 21 artifact-index symbols through 45 references | A producer imports another producer as a transaction utility library |
| Reports | `render_run_report.py` and `render_run_report_bundle.py` total 4,035 lines and 100 definitions; each imports the other, and the bundle uses 29 HTML-module symbols through 76 references | Format-neutral content, format validation, tool execution, and publication lack leaf-module boundaries |
| Steps `08` and `09` | Their shell and R implementations total 5,499 lines | Size is real, but duplicated cross-language checks protect scientific contracts and are not automatically redundant |
| Tests | The coverage roadmap owns current inventory totals; this refactor scan found repeated test support in shell assertions, dynamic Python script loaders, and hardcoded inventory-size expectations | Test-only support can reduce maintenance before production code moves without duplicating mutable coverage status here |
| Local gate | `Makefile` mixes ambient `python`, `PYTHON_BIN`, and `REPORT_PYTHON_BIN`; `all-checks` omits the strict R-environment checks and can accept a skipped default R path | Target names do not accurately communicate the canonical gate |
| Python environment | `requirements.txt` is a flat 24-pin environment; repository imports do not use the scientific plotting/data roots `matplotlib`, `pandas`, or `scipy` | Direct requirements and transitive constraints are not distinguished; removal still requires a clean restore |
| Operational docs | The nine required documents exceed 7,500 lines; `RUNBOOK.md` and `TROUBLESHOOTING.md` remain the majority | Navigation and shared recovery explanations can improve without changing canonical ownership |
| Scaffolding | Two pending Step `04`/`06` plans have active replacements; two YAML examples are unconsumed, and two legacy SLURM utility files are fixture-covered but have no confirmed operator consumer | Stale scaffolding can imply capabilities that do not exist |
| Data checks | `tests/data_checks/validate_step05_outputs.sh` retains a cluster-specific samtools default and six hardcoded samples after its arguments and deterministic TSV publication were fixture-hardened | Its historical-evidence and maintained operator-tool roles remain conflated |
| Repository policy | `.gitignore` excludes primary sequence/alignment data but not common VCF indexes and compressed/indexed variant forms | Preventive data guards should match the documented policy |

## Opportunity register

| ID | Opportunity | Value | Risk | Readiness |
| --- | --- | --- | --- | --- |
| `FND-01` | Freeze public behavior and add fault-injection/golden baselines | Critical | Low | Foundation |
| `HYG-01` | Remove or explicitly archive misleading scaffolding | High | Low | Foundation |
| `GATE-01` | Make local validation targets accurately represent fast, real-R, renderer, and full gates | High | Low-medium | Foundation |
| `DEP-01` | Separate declared Python roots from generated/transitive constraints | Medium-high | Medium | Foundation, removal production-gated |
| `TEST-01` | Consolidate test-only Python loading/fixtures and shell assertions | High | Low-medium | Foundation |
| `VAL-01` | Extract a neutral validation-report and publication core | Very high | Medium | Production-gated after fault injection |
| `CON-01` | Extract pure Step `08`/`09`/`09c` contracts and split record semantics | Very high | Medium-high | Production-gated after contract parity |
| `TXN-01` | Extract only proven low-level transaction primitives | Very high | High | Production-gated |
| `ART-01` | Decompose artifact-index registry, inspectors, reconcilers, projections, and coordinator | Very high | High | Production-gated |
| `SUM-01` | Decompose adapter loading, science normalization, approvals, projections, and summary publication | Very high | High | Production-gated |
| `REP-01` | Break the report import cycle and separate view model, format validation, tool execution, and publication | High | High | Production-gated |
| `SCI-01` | Decompose Step `09c` evidence law, decisions, normalization, and publication | Very high | High | Production-review-gated |
| `OPS-01` | Decide whether legacy data checks are historical evidence or maintained operator tools | High | Medium | Production-gated |
| `DOC-01` | Add offline document/link/path/diagram checks and improve operations-doc navigation | High | Low | Foundation |
| `ANL-01` | Decompose Step `08`/`09` internals within each language | Very high | Very high | Second-cohort-gated |
| `CFG-01` | Introduce a versioned analysis-configuration boundary only after real variation is known | Medium-high | High | Second-cohort-gated |
| `SHL-01` | Extract narrow policy-free shell/SLURM helpers | Medium | Medium-high | Evidence-triggered |
| `ORC-01` | Add targeted reruns, dispatchers, or job arrays | Unknown | High | Evidence-triggered |

## Phase 0: coverage and compatibility foundation

Readiness: Foundation. This is the only structural prerequisite that should
start before remote promotion.

### Work

1. Record public `--help`, required arguments, exit codes, output basenames,
   headers, dry-run side effects, and publication order for every component
   selected for refactoring.
2. Add byte-level golden outputs where deterministic bytes are part of the
   contract.
3. Add transaction fault injection for first publication, replacement of a
   valid predecessor, input mutation, foreign or aliased replacement,
   cleanup failure, rollback failure, signal handling, and retained lock/
   recovery evidence.
4. Add cross-language conformance fixtures for the contracts intentionally
   implemented independently in shell, R, and Python.
5. Establish branch-aware coverage measurement as a diagnostic and ratchet
   only after a reproducible baseline. Do not invent a percentage target.

The current source-to-suite ledger and remaining scenario matrix are in
[`TEST_COVERAGE_ROADMAP.md`](TEST_COVERAGE_ROADMAP.md); use that document
rather than copying test status here.

### Exit gate

- The complete local validation gate passes.
- Every later extraction names the characterization tests that protect it.
- Golden outputs and negative cases are unchanged.
- No production code has been abstracted merely to enable coverage.

## Phase 1: repository and test-support hygiene

Readiness: Foundation.

### Work

- Remove the obsolete pending Step `04` and Step `06` plans after mapping each
  bullet to the active suites.
- Remove, archive, or explicitly document the unconsumed YAML examples so they
  do not imply a functioning YAML configuration layer.
- Retire or modernize `jobs/template.slurm` and `jobs/tool_check.slurm` only
  after confirming that no operator depends on them. Preserve
  `jobs/validate_manifest.slurm`.
- Extend ignored data forms to include the compressed/indexed variant and
  alignment-index files prohibited by repository policy.
- Introduce small test-only support:
  - one Python script-loader/fixture helper without changing production import
    paths;
  - one sourceable shell assertion helper while preserving standalone suite
    execution;
  - one explicit inventory-size contract assertion, with downstream counts
    derived from the loaded fixture where they are not independently testing
    the number.
- Add an offline documentation check for relative links, referenced tracked
  paths, canonical Mermaid sources, and forbidden inline copies of diagrams.

### Make and dependency follow-up

Define target names that distinguish:

- fast deterministic Python and shell fixtures;
- default real-R tests, which may skip only when the default runtime is
  unavailable;
- strict repository-local real-R tests, which may not skip;
- the pinned real-renderer report gate;
- the complete canonical local gate.

Use one explicit project Python default with deliberate overrides. Keep
dependency restoration outside every test target.

Separate direct runtime/test requirements from their exact constraints, or
document the flat file as a generated lock with declared roots. Candidate
removals must be proven in a fresh environment with `pip check`, the complete
Python/shell/report gate, and supported-platform checks. “No direct import”
alone is not removal evidence.

### Exit gate

- No tracked file advertises an unimplemented configuration or obsolete test.
- Existing target names remain as compatibility aliases if external use is
  plausible.
- A clean environment can be restored from tracked declarations.
- The complete local gate and repository reference scan pass.

## Candidate control-plane extractions

Readiness: Production-gated after the baseline in Phase 2. These boundaries
are specified here so Phase 0 can add the correct characterization tests; the
default sequence does not implement them before remote validation and
production evidence. Moving a pure extraction earlier requires explicit
reprioritization in `PIPELINE_PLAN.md`.

### `VAL-01`: validation-report core

Move the generic seven-column report model, snapshots, validation, and safe
publication out of the Step `00a` validator into a neutral leaf module.
Retain compatibility re-exports temporarily so all 13 public validators stay
stable.

Do not change failed checks into process failures: a structurally valid report
containing failed checks remains publishable evidence. Preserve lock naming,
predecessor validation, exact check order, dry-run behavior, and bytes.

Exit:

- no validator imports another step-specific validator;
- all 13 focused validator suites pass;
- adapter, summary, and HTML/PDF propagation fixtures remain identical;
- publication fault-injection parity is complete.

### `CON-01`: pure contract modules

First extract immutable headers, enums, schema versions, status laws, and pure
parsers now embedded in the Step `09c` executable. Then split artifact-record,
scientific-review, run-summary, report-receipt, and inventory semantic
validation by record type behind the unchanged
`validate_artifact_contracts.py` CLI.

Do not change the five schema files, schema IDs/versions, closed shapes,
canonical hashing, strict JSON behavior, diagnostic categories, or rejection
of the reserved biological-ready state.

Exit:

- current executable modules remain stable facades;
- all positive and negative fixture matrices retain acceptance/rejection
  parity;
- every contract constant and normalized document is unchanged;
- no new cross-import from a producer executable is introduced.

## Phase 2: production and recovery baselines

Readiness: prerequisite for transaction and producer decomposition.

### Runtime baseline

Promote Step `07` with real bcftools through the approved pilot, partition, and
full declared-universe gates. Then promote Steps `08` and `09`
upstream-first. Inspect scheduler state, logs, outputs, validators, elapsed
time, peak memory, I/O behavior, hashes, and recovery residue.

### Evidence-product baseline

Build and inspect one production:

- artifact-index transaction;
- canonical run-summary transaction;
- exact report-table approval manifest when applicable;
- HTML/PDF/summary-TSV/report-receipt bundle;
- Step `09c` scientific-evidence transaction.

Perform a deterministic rerun and an explicit, safe recovery drill for each
transaction type. Transaction completion must not be described as scientific
or biological validation.

### Exit gate

- Exact production inputs and identities are recorded.
- One valid predecessor/replacement path and one failure/recovery path have
  inspected evidence.
- The baseline outputs are retained for byte/semantic comparison.
- Cluster proof is scoped to the exact unchanged implementation that ran.

## Phase 3: control-plane and evidence-product decomposition

Readiness: Production-gated. Implement `VAL-01` and `CON-01` first, followed
by one narrowly scoped descendant package per transaction or producer
boundary.

### `TXN-01`: low-level primitives only

Extract already-shared, policy-free primitives for canonical bytes and hashes,
regular-file snapshots, exclusive writes, fsync, owned locks, signal
installation/restoration, process-group termination where applicable, and
owned-path cleanup.

Keep producer-specific choreography explicit. Validator files, artifact-index
directories, run-summary sets, Step `09c` summaries, and report bundles have
different predecessor, marker-last, rollback, and recovery rules. Do not force
them through one generic transaction framework.

### `ART-01`: artifact index

Suggested boundaries:

- ordered adapter specifications and step rosters;
- source/container inspectors;
- reference, sample, cohort, and scientific-review reconcilers;
- artifact-record, index, and receipt projections;
- attempt-lineage and transaction coordinator;
- unchanged CLI facade.

Exit:

- all 62 adapters reconcile against the explicit 81-row fixture;
- records, ordered index, and receipt bytes remain deterministic;
- same-contract retries, supersession, and immutable run identity are
  unchanged;
- fault injection demonstrates predecessor restoration and retained evidence.

### `SUM-01`: run summary

Separate:

- exact adapter-transaction loading;
- Step `09c` normalization;
- report-table approval reconciliation;
- canonical document and TSV/QC projections;
- receipt-last publication;
- unchanged CLI facade.

Eliminate the dependency on `build_artifact_index.py` as a general utility
module through neutral leaves, not copied implementations.

Exit:

- canonical JSON, artifact TSV, QC TSV, and receipt bytes remain equivalent;
- optional science and approval behavior is unchanged;
- input mutation, output-directory replacement, rollback, and cleanup tests
  retain parity.

### `REP-01`: report layer

Break the cycle between the public HTML entry point and bundle coordinator.
Suggested leaves:

- immutable format-neutral view model;
- HTML projection and static/accessibility validation;
- Quarto/Typst execution and PDF validation;
- deterministic summary and receipt projections;
- bundle transaction coordinator;
- unchanged Python and shell facades.

Exit:

- the pinned real-renderer gate passes;
- HTML/PDF/TSV/receipt outputs remain deterministic;
- every-page banners, table authorization, accessibility, script/resource
  isolation, HTML-only predecessor upgrades, timeouts, process-group
  termination, rollback, and recovery all retain parity.

### `SCI-01`: scientific review

After one production review transaction, separate:

- evidence-category and record parsing;
- orientation/annotation/QC/sensitivity and candidate reconciliation;
- decision and adjudication law;
- computational-evidence normalization;
- state derivation and reserved-state rejection;
- transaction publication;
- unchanged CLI facade.

Exit:

- all 13 output roles and ten required evidence categories retain exact
  ownership;
- incomplete and exploratory state laws are unchanged;
- non-provisional orientation and computational-proof gates retain exact
  behavior;
- no refactor can emit `biological_interpretation_ready`.

## Phase 4: second-cohort analysis refactoring

Readiness: Second-cohort-gated.

Run the unchanged Step `07`–`09` public interfaces on another real cohort
first. The cohort must expose meaningful variation in sample count, replicate
layout, partitions, candidate density, or annotation rather than repeating the
same fixture shape.

Then decompose within each language:

- Step `08`: contract parsing, VCF parsing, annotation model, site projection,
  summary projection, and transaction coordination;
- Step `09`: cohort/policy parsing, candidate statistics, multiple-testing
  adjustment, spectrum/plot projection, summary projection, and transaction
  coordination.

Do not collapse independent shell/R/Python checks. Extract their shared
declarations only after a conformance suite proves that order, hashes,
thresholds, background policy, global BH family, candidate subset, summaries,
and PDFs agree.

Exit:

- shell/fake-R, guarded real-R, and independent Python validators pass;
- both real cohorts remain semantically equivalent through the public
  contracts;
- representative cluster pilots show no material I/O or memory regression;
- scientific conclusions are unchanged and remain provisional where required.

## Phase 5: configuration and orchestration only when earned

Readiness: Second-cohort-gated for configuration; evidence-triggered for
orchestration.

A versioned analysis configuration may be introduced only after two real
cohorts show which fields genuinely vary. It must preserve manifest,
reference, partition, and policy identity separation and must not turn
filenames into provenance.

Broad shell/SLURM helpers, module wrapping, dispatchers, job arrays, and
targeted-rerun orchestration require repeated operational evidence. Start with
narrow policy-free utilities only after wrapper behavior has dry-run snapshot
coverage and cluster dry-run evidence. Keep step-specific resources, modules,
environment variables, and logs visible.

Do not implement:

- a generic dispatcher merely because step wrappers look similar;
- automatic dependency installation or restoration;
- automatic stale-lock deletion, cleanup, or recovery;
- discovered or glob-generated artifact inventories;
- public-data ingestion or publishing infrastructure without a separate need;
- a policy that unlocks biological readiness.

## Operational documentation maintenance

Do not split canonical ownership merely to reduce file length. Instead:

1. add a compact index to each long operations document;
2. consolidate truly identical transaction/recovery explanations into one
   shared section, then retain component-specific differences beside the
   component;
3. validate relative links, anchors, tracked paths, and Mermaid sources
   offline;
4. keep exact commands only in `RUNBOOK.md` and symptom/cause/diagnosis/fix
   guidance only in `TROUBLESHOOTING.md`;
5. keep live package status and lineage only in `PIPELINE_PLAN.md`;
6. docpatch after every implementation package.

Any later physical split of an operations document requires a recorded
ownership decision, lossless content mapping, redirecting links, and a
repository-wide duplicate-owner scan.

## Package sizing and review discipline

Each future refactor should move one boundary at a time:

```text
characterization tests
-> compatibility extraction
-> complete local gate
-> implementation commit
-> repository-wide docpatch
-> clean pushed gate
-> runtime revalidation when the changed boundary previously had runtime proof
```

Do not combine an extraction with schema evolution, scientific-policy change,
output renaming, dependency pruning, or behavior cleanup. Small linear
packages make exact regressions and evidence boundaries inspectable.

## Completion criteria for this roadmap

The roadmap is successful when it prevents premature abstraction as well as
identifying worthwhile work. An opportunity may be closed by implementation,
by evidence that the current explicit design is safer, or by a recorded
decision that its maintenance benefit does not justify migration risk.

Refresh this audit when a major implementation sequence, first production
evidence transaction, or second real cohort materially changes the evidence.
Never copy live status into this file; link to the canonical owner.
