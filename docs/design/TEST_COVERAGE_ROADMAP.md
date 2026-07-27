# Test coverage roadmap

This document is the canonical evidence-ranked test-coverage inventory,
residual-gap register, and future measurement strategy for NORAD. It records
which behavior is protected locally, which cases still deserve deterministic
tests, and which claims can be established only with real runtime, cluster,
production, or scientific evidence.

It is not the live package plan. Approved status, sequencing, and branch
lineage belong in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md). Refactor
opportunities and their implementation prerequisites belong in
[`FUTURE_IMPLEMENTATION_ROADMAP.md`](FUTURE_IMPLEMENTATION_ROADMAP.md).
Commands belong in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

## Evidence boundary

Coverage is evidence about exercised behavior. It does not by itself establish:

- production input identity or availability;
- real bcftools or batch-R compatibility;
- scheduler completion, resource sufficiency, or cluster proof;
- a production artifact, summary, report, or scientific-review transaction;
- biological validity or `biological_interpretation_ready`.

Local mocks protect command construction, contracts, failure behavior, and
publication law. Guarded real-R tests protect the declared R semantics on the
local runtime. The pinned-renderer gate protects the real local report
toolchain. Runtime and cluster claims still require their separately inspected
evidence.

## Audit method and snapshot

The coverage audit maps tracked production entry points and public contracts
to Python, shell, R, real-renderer, and external-evidence gates. Function and
line counts are structural signals, not quality scores or acceptance targets.
Parameterization means a pytest function count is not an executed-case count.

The post-coverage-foundation snapshot contains:

- 26 Python, 13 shell, and four R files under `scripts/`;
- 16 SLURM job files;
- five public/shared JSON Schema documents and 28 tracked configuration or
  schema-table contracts;
- 27 pytest files with 413 test-function declarations;
- 14 active shell suites and four R runner/test files;
- 26,265 lines of Python, shell, and R test/fixture source.

Every production script is named by a test except
`scripts/_run_summary_science.py`, which is intentionally exercised through
the public `build_run_summary.py` integration boundary. Step `00a` and Step
`00b` jobs have structural wrapper coverage but no dynamic fake-tool wrapper
fixtures.

No tracked CI workflow, Python test configuration, or pinned branch-coverage
tool exists. This package therefore establishes a behavioral ledger rather
than inventing an unrepeatable percentage baseline.

Refresh this snapshot after a major implementation sequence, a new public
entry point, the first production evidence transaction, or an approved
coverage-instrumentation package.

## Independent validation tiers

| Tier | Purpose | Representative gate | What it cannot replace |
| --- | --- | --- | --- |
| Fast deterministic | Contracts, command construction, mocks, negative cases, publication fault injection | pytest plus active shell suites | Real R, real renderer, or cluster behavior |
| Default real-R | Detect whether the default runtime can execute Step `08` and Step `09` semantic fixtures | `make real-r-test` | A skip, guarded project-library proof, or batch visibility |
| Strict guarded real-R | Execute both semantic suites in the locked repository environment without `SKIP` | `make local-real-r-test` plus `make r-check` | CSU batch compatibility or production-scale behavior |
| Real renderer | Exercise the pinned Quarto/Typst executable and PDF reader | `make report-test` | Production report identity or analysis validation |
| Runtime and cluster | Exercise approved tools, data, scheduler, logs, outputs, hashes, and resources | Step-specific runbook gates | Scientific or biological validation |
| Scientific evidence | Reconcile explicit production evidence, decisions, adjudication, and limitations | Step `09c` production gate | Orthogonal biological validation unless the policy explicitly requires and receives it |

Passing one tier never promotes another. A complete local gate reports all
applicable tiers separately.

## Coverage added by the foundation package

| Area | New protection | Defect or ambiguity resolved |
| --- | --- | --- |
| Manifest and schema CLI | Duplicate/blank headers, extra fields, blank rows, empty condition, directory FASTQs, help contract | Required `condition` is now nonempty; `--check-files` requires file paths rather than accepting directories; schema help describes one shared plus four public schemas |
| Step `01` STAR | Side-effect-free dry-run, all five required outputs, zero-output success, missing/empty output, tool failure, no-clobber, broken symlink, symlinked output directory | A zero-exit STAR invocation could previously leave no validated output; execute mode now stages, validates, and publishes each stable name with an atomic no-clobber hard link under tested path conditions |
| Shared validation reports | First publication, valid-predecessor restoration, input mutation, output aliases, rollback failure, cleanup failure | In tested incomplete rollback or cleanup cases, safely addressable recovery state and the owned lock are now retained |
| Report bundle | Symlink root, predecessor restoration, late foreign output, cleanup failure, output-directory replacement, SIGTERM process-group handling | Recovery and cleanup could address a foreign replacement directory; path cleanup and marker writes now require the original directory identity |
| Runtime and Quarto | Probe timeout, hash mismatch, first publication, rollback and backup cleanup, archive mutation, version timeout, restore/download cleanup | Runtime-preflight and Quarto download cleanup failures now surface normalized recovery state instead of silently discarding or obscuring it |
| Reference and storage evidence | Broken final symlinks, mid-backup failure, mid-publication failure, byte-identical predecessor restoration | Backup-phase interruption could leave a partial predecessor; moved members are restored before cleanup |
| Utility jobs and data checks | Static and mocked SLURM execution, manifest delegation, plain/gzip FASTQ pairing, Step `05` PASS/FAIL/PENDING and argument cases | Module/job-context drift, missing-option loops, ignored missing job files, and unreliable duplicated `tee` output were corrected |
| Structured Step `07`/`08` validators | Sample order, selector bounds, manifest hash, duplicate candidate, annotation hash, missing receipt row | One-invariant-at-a-time failures now protect additional independent report rows |
| SLURM family | Strict shell, stable logs, execute gate, delegated script, module capture, required job context | Current dry-run wrappers have a repository-wide static compatibility baseline |

These changes add characterization and safety coverage. They do not alter the
historical cluster status of any pipeline stage.

## Current source-to-suite ledger

| Area | Primary protection | Strength | Principal residual |
| --- | --- | --- | --- |
| Manifest and lightweight data checks | `test_validate_manifest.py`, `test_utility_jobs_and_data_checks.py` | Strong schema, path, pairing, argument, and tiny-fixture negatives | Full FASTQ content/scale and production manifest identity remain external |
| Steps `00a` and `00b` compute jobs | `test_slurm_wrapper_contracts.py`, `test_gtf_to_bed12.py` | Deterministic converter logic and wrapper structure | Mutating legacy jobs lack dynamic fake-tool characterization and dry-run/execute migration tests |
| Steps `00c`-`06` workflow scripts | Active `tests/shell/test_step_*.sh` suites | Strong dry-run, fake-tool, output, and common rollback behavior | Signal, late foreign replacement, rollback failure, and cleanup failure are not uniform across publishers |
| Step `07` | Shell suite plus `test_validate_step_07_mpileup_outputs.py` | Strong mocked bcftools pipelines, receipt law, selectors, order, hashes, and structured negatives | Real bcftools, production BAM/FAI behavior, resources, and cluster publication |
| Step `08` | Shell/fake-R, guarded real-R, and independent Python validator suites | Strong explicit-input, lexical count, annotation, transaction, and semantic coverage | No single shared golden/negative corpus across shell, R, and Python; no production-scale I/O baseline |
| Step `09` | Shell/fake-R, guarded real-R, and independent Python validator suites | Strong pairing, CMH/global-BH/status/subset/summary/PDF and transaction coverage | No shared cross-language conformance corpus and no real production transaction |
| Step `09c` | Python and shell scientific-validation suites | Strong state law, evidence identity, decisions, mutation, publication, and ordinary rollback | Some restoration/cleanup failure combinations and late unsafe replacement remain untested |
| Step validators `00a`-`09` | One focused pytest module per validator | Shared publication is strongly fault-injected; all public check sets have positive/negative fixtures | Hostile late lock replacement remains untested, and several `00b`-`06` suites aggregate multiple semantic mutations into one test |
| Artifact schemas and adapters | `test_artifact_schema_contracts.py`, `test_artifact_adapters.py` | Very strong closed-schema, all-adapter, identity, attempt, mutation, signal, rollback, and receipt coverage | Production inventory/source behavior remains external |
| Run summary | `test_artifact_run_summary.py` | Very strong exact-input, science, approvals, deterministic projections, mutation, transaction, and recovery coverage | Production adapter/review/approval inputs remain external |
| Static reports | HTML, export, Quarto restore, and shell wrapper suites | Very strong static/accessibility isolation, HTML/PDF parity, signals, output identity, rollback, cleanup, and determinism | The long timeout-to-SIGKILL escalation is not directly time-executed; real production report inputs remain external |
| Runtime preflight | `test_runtime_preflight.py` | Strong profile semantics, probe behavior, deterministic publication, timeout, rollback, and cleanup | Live batch paths/tools, filesystem `fsync` faults, and hostile lock replacement remain external or untested |
| Reference and storage foundations | Focused provenance and storage pytest modules | Strong parsing, measurement/reconciliation, broken paths, backup and publication restoration | Incomplete restoration/cleanup retention and late parent replacement need fault injection |
| Utility SLURM jobs | Static family tests plus mocked utility execution | Good job context, module capture, and manifest delegation | Live SLURM/module behavior remains a cluster gate |
| Documentation and tracked examples | Existing product tests validate many examples indirectly | Public schemas and central fixture contracts are strong | No offline link/path/diagram checker; several standalone example contracts lack one explicit aggregate suite |

## Ranked residual work

### External evidence: mandatory, not local-coverage debt

`EXT-01` — Promote Step `07` with real bcftools through the pilot,
one-primary-partition, and full declared-universe gates. Inspect scheduler
state, logs, sample order, selectors, hashes, counts, output residue, elapsed
time, memory, and storage before Steps `08` or `09`.

`EXT-02` — Execute the approved batch-visible R gate and then Steps `08` and
`09` upstream-first. Local real-R fixtures do not satisfy this work.

`EXT-03` — Populate and inspect production manifest, reference-provenance,
storage/retention, artifact-index, run-summary, Step `09c`, approval, and
report-bundle transactions. Keep transaction completion separate from
computational, scientific, and biological state.

### High-priority deterministic work

`CVG-01` — Complete the residual recovery-law matrices. For the shared
structured-validator publisher, inject hostile late lock replacement. For
`reference_provenance.py`, `storage_inventory.py`, and Step `09c`, inject
restoration failure, backup cleanup, lock cleanup, late unsafe replacement,
and source/contract mutation. Require either a byte-identical predecessor or
a clean first-publication state; when recovery is incomplete, require retained
lock/recovery evidence whenever the lock remains safely addressable.

`CVG-02` — Maintain a test-only transaction scenario ledger for Steps `01`,
`02`, `05`, `06`, `07`, and `08`. For each applicable publisher, record
coverage of first publication, valid predecessor, input mutation, late
foreign final, signal, cleanup failure, rollback failure, and recovery
retention. A ledger does not require a shared production abstraction.

`CVG-03` — Build one explicit positive and one-invariant-at-a-time negative
conformance corpus for the contracts independently implemented in Step `08`
shell/R/Python and Step `09` shell/R/Python. Require matching identity,
ordering, count, threshold, status, subset, summary, hash, and
acceptance/rejection outcomes.

`CVG-04` — Before changing or rerunning the legacy Step `00a`/`00b` jobs, add
temporary-root fake-tool characterization for exact arguments, context,
failure cleanup, output names, and overwrite behavior. Adding execute gates or
moving analysis into scripts is a separate implementation package and
requires renewed runtime validation.

`CVG-05` — Make validation target names truthful. Preserve plausible
compatibility aliases while distinguishing fast deterministic fixtures,
skippable default real-R, strict guarded real-R, pinned real renderer, and the
canonical complete local gate. Dependency restoration stays separate.

### Medium-priority deterministic work

`CVG-06` — Parameterize Step `00b`-`06` validator mutations so every public
check ID has at least one isolated failure and unrelated rows assert their
expected state. Do not duplicate shared publication tests.

`CVG-07` — Add mocked dynamic wrapper execution for Steps `01`-`04`, asserting
forwarded arguments, `EXECUTE=0/1`, context/module logging, script delegation,
and containment inside a temporary root.

`CVG-08` — Add one aggregate tracked-example suite for the run contract,
reference/storage contracts, report-table approval example, and Step `09`
pairing reference. Examples must remain explicitly non-production. Do not add
coverage around obsolete YAML or pending scaffolding until its disposition is
decided.

`CVG-09` — Add a deterministic no-network documentation gate for relative
links, referenced tracked paths, canonical Mermaid sources, and forbidden
inline copies of diagrams.

`CVG-10` — Consolidate only test support that has a demonstrated maintenance
cost: one Python script-loader/fixture helper and one sourceable shell
assertion helper, while preserving standalone suite execution and public
production import paths.

### Conditional or low-priority work

`CVG-11` — Add direct tests for `_run_summary_science.py` only if it becomes an
extracted public/internal boundary. Current integration coverage is
appropriate.

`CVG-12` — Exercise live Quarto download/official-archive restore and network
failure behavior only in an explicitly network-enabled setup test. Normal
render and test targets must remain offline and must never install.

`CVG-13` — Do not create tests merely to preserve stale YAML, pending test
plans, or unused job scaffolding. Decide whether each artifact is removed,
archived, or activated first.

## Branch-aware Python measurement

Instrumentation is a future package, not an implicit dependency change. When
approved:

1. Start from a clean, pushed, docpatched baseline.
2. Pin a branch-capable Python coverage tool in the tracked dependency model
   and configure subprocess collection explicitly.
3. Store machine-readable results only under ignored output storage.
4. Record the exact tool version, source set, test tiers, exclusions, and
   branch commit used for the baseline.
5. Compare each descendant against its merge base:
   - touched production modules may not lose previously exercised
     statements or branches;
   - every new or changed Python branch needs a named test or an explicit
     external-evidence waiver;
   - every new entry point must enter the source-to-suite ledger;
   - the repository-wide percentage remains diagnostic, not a target.
6. Advance the baseline only from another clean, pushed, docpatched branch
   using the same tool and suite definition.
7. When tooling or exclusions change, retain the old result and establish a
   side-by-side new baseline rather than rewriting history.

Do not invent a percentage threshold before the reproducible baseline exists.
Line coverage alone is especially weak evidence for scientific semantics,
negative contracts, and transactional recovery.

## Shell and R ratchets

Shell and R coverage is scenario-based:

- each public entry point has help/argument and dry-run behavior;
- execute paths use tiny tools or fixtures when safe;
- output validation and named failure modes are explicit;
- transaction publishers use the scenario ledger;
- independent shell/R/Python implementations share conformance cases where
  agreement is a contract;
- real-R suites remain separate from fake-R command-construction tests.

Do not impose shell or R line-percentage targets. Named scenarios,
cross-language outcomes, and real-runtime gates are the useful ratchet.

## Waiver and review law

A changed branch may omit a local deterministic test only when:

- the behavior can be observed only in a real runtime, cluster, production,
  or scientific context;
- the exact external gate and expected evidence are named;
- local mocks still protect command construction and fail-closed behavior
  where reasonable;
- the waiver is recorded in the package plan or review rather than hidden by
  a global percentage.

Performance, storage, scheduler, and biological claims never receive a local
fixture waiver that promotes their state. They remain pending until the
declared external evidence is inspected.

## Exit criteria for future coverage packages

Each package:

- maps changed production behavior to a named suite or external gate;
- adds the failing characterization test before a production defect fix;
- preserves public CLI, output, identity, schema, science, and recovery
  contracts unless a separately approved versioned change says otherwise;
- passes the complete applicable local gate;
- receives a separate repository-wide docpatch;
- leaves no generated coverage data, runtime output, or restored dependency
  tracked;
- reaches a clean, pushed, upstream-equal state before its baseline advances.
