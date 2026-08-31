# Test baseline and contract-risk index

This document owns the current Python non-regression policy, evidence
vocabulary, contract-risk checklist, and direct regression routes. The tracked
machine baselines and current owner tests are authoritative; Git history retains
superseded counts, timings, matrices, and gate narratives.

## Evidence boundary

Python coverage measures executed Python statements and branches during the
Python behavior lane, including traced subprocesses. It does not measure shell
or R source coverage, prove expectation independence, or replace scenario,
mutation, transaction, recovery, real-runtime, scheduler, or cluster tests.

All evidence routed here is local engineering evidence. It does not promote a
workflow step, report, scientific review, editing-site claim, or biological
interpretation state. Low numerical coverage is a review signal, not by itself
proof of a user-visible defect or authority to change behavior.

## Current Python coverage gate

The authoritative tracked snapshot is
[`tests/baselines/python_coverage.json`](../../tests/baselines/python_coverage.json);
the comparison implementation and direct tests are
[`python_coverage_baseline.py`](../../tests/tools/python_coverage_baseline.py)
and
[`test_python_coverage_baseline.py`](../../tests/test_python_coverage_baseline.py).
Measure and compare through the supported target. A baseline rebase is an
explicit reviewed mutation:

```bash
make python-coverage-check
make python-coverage-baseline-update
git diff -- tests/baselines/python_coverage.json
make python-coverage-check
```

CI measures the same behavioral inventory across four deterministic Python
3.14 shards. [`python_test_shards.py`](../../tests/tools/python_test_shards.py)
collects the complete inventory independently in every shard, balances known
slow tests using the reviewed estimates in
[`python_test_durations.json`](../../tests/baselines/python_test_durations.json),
and records the exact selected node IDs before execution. The merge lane
requires all four receipts to be complete, disjoint, current, and identical to
the deterministic plan before combining coverage. The duration estimates
affect scheduling only; they never select, skip, or change a test expectation.
Each shard also reports its 50 slowest tests in the live job log.

The compact snapshot records schema `2.0.0`, coverage.py `7.15.2`, exact
repository totals, critical-owner aggregates, and route-specific subprocess
evidence from a separate subprocess-only probe.
It deliberately does not retain a private-module roster. It remains
authoritative after an accepted update; a rebase must reflect a reviewed
source/test surface rather than hide new uncovered code.

The accepted exact floors are:

| Coverage owner | Line floor | Branch floor |
| --- | ---: | ---: |
| Python behavior lane | `13817 / 15987` (`0.864265`) | `4530 / 6054` (`0.748266`) |
| Orchestration machine contracts | `436 / 492` (`0.886179`) | `193 / 236` (`0.817797`) |
| Local-pilot control plane | `3385 / 4138` (`0.818028`) | `1030 / 1498` (`0.687583`) |
| Source-checkout admission | `235 / 267` (`0.880150`) | `83 / 94` (`0.882979`) |
| Runtime-availability admission | `364 / 410` (`0.887805`) | `100 / 138` (`0.724638`) |
| `emrys.contracts.scientific_evidence` | `592 / 597` (`0.991625`) | `283 / 290` (`0.975862`) |
| `emrys.libraries.validation` | `371 / 379` (`0.978892`) | `116 / 122` (`0.950820`) |
| Shared scientific validation primitives | `341 / 341` (`1.000000`) | `123 / 124` (`0.991935`) |
| Report/publication and receipt validation | `5272 / 6247` (`0.843925`) | `1782 / 2480` (`0.718548`) |
| Paired-CMH analysis contracts | `85 / 85` (`1.000000`) | `16 / 18` (`0.888889`) |

The Campaign B coverage measurement ran the Python behavior lane with `1324`
passing tests and `6` explicit opt-in skips. Relative to the prior accepted
snapshot, the measured surface grew by `5556` statements and `1970` branches,
while covered counts grew by `4645` statements and `1396` branches. Coverage
therefore expanded substantially while the global ratios declined. This
explicit rebase accepts the measured Campaign B source/test surface and adds
independent non-regression floors for orchestration machine contracts, the
local-pilot control plane, source-checkout admission, and runtime-availability
admission.

Scientific-evidence line coverage increased with identical branch coverage;
shared scientific primitives and paired-CMH contracts retained their prior
ratios. Validation and reporting floors now
bind their expanded measured surfaces. These numerical floors do not prove
unchanged execution of every prior statement or replace transaction, recovery,
real-runtime, cluster, or scientific evidence.

Comparisons cross-multiply the exact counts. Six-decimal rates are display
values and never weaken the gate through rounding.

The active policy:

- measures branches over exactly `scripts` and `src/emrys`, with subprocess
  tracing enabled for the Python behavior lane;
- separately runs the subprocess-only GTF-to-BED12 and sample-manifest CLI
  suites and requires coverage in their exact public route modules;
- rejects any exact-ratio decrease in global line or branch coverage;
- rejects any exact-ratio decrease in the nine critical-owner groups above;
- allows private files to move, merge, or disappear when aggregate and owner
  coverage remain non-regressive;
- requires a genuinely new shared Python module named through
  `PYTHON_COVERAGE_NEW_SHARED_MODULES` to reach at least 90% line and 85%
  branch coverage during its reviewed introduction; and
- permits baseline change only through an explicit reviewed update, never as an
  ordinary test side effect.

## Current evidence vocabulary

- `preserved contract`: independent regression evidence protects the declared
  compatibility boundary.
- `characterized defect`: the behavior remains a defect; characterization
  neither approves nor normalizes it.
- `undefined — decision required`: implementation stops until an authorized
  owner decides the behavior.
- `environment-deferred`: local contract evidence exists, but the named
  runtime, scheduler, production, or scientific environment has not supplied
  the missing evidence.

An independent expectation must not import or derive the production rule it is
meant to detect. Producer-coupled integrated fixtures remain useful only as
additional end-to-end evidence. Readable failed validator evidence may publish
`status=fail` and exit zero; malformed or unsafe operation exits nonzero and
publishes nothing. Restore and baseline-update targets are explicit operator
mutations, never implicit test actions.

Direct-owner, adversarial, seeded-fault, and synthetic end-to-end defenses may
be removed only when an explicit invariant-to-test mapping establishes an
equal-or-stronger replacement at the same declared evidence level. Coverage or
the scientist-facing synthetic golden path alone is insufficient. This is the
binding [`AC-GUARD-005`](decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails)
replacement policy.

A **protection** is an executable or static defense such as a test, validator,
fixture, or oracle. **Evidence** is a retained record or artifact that supports
or bounds a claim, reproduction, or recovery. A test definition is not evidence
merely because it can produce a result; a retained result may be. Fixtures,
goldens, and oracles can be both, so both policies apply. An existing surviving
defense may satisfy the `AC-GUARD-005` mapping when it provides equal-or-stronger
coverage; replacement does not require one new test per removed mechanism.
Deleting retained evidence is a separate decision requiring exact explicit
user approval under [`AC-GUARD-008`](decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).

## Python entry points

Current executable behavior belongs to its implementation, colocated contract,
and direct regression owner. This index routes rechecks without duplicating the
archived entry-point matrices.

| Surface or risk | Current regression route |
| --- | --- |
| Python, shell, R, file mode, arbitrary CWD, and Make entry points | [`test_public_cli_contracts.py`](../../tests/test_public_cli_contracts.py) plus the applicable direct owner |
| Whole-Run execution profile, direct/Slurm placement, modules, private scratch, scheduler receipt, grouped control, and hosted successful-outcome parity | [`test_execution_profile.py`](../../tests/orchestration/local_pilot/test_execution_profile.py), [`test_slurm_submission.py`](../../tests/orchestration/local_pilot/test_slurm_submission.py), [`test_real_synthetic_e2e.py`](../../tests/test_real_synthetic_e2e.py), the retained [`real_synthetic_e2e.py`](../../tests/tools/real_synthetic_e2e.py) driver, and affected control/materialization/lifecycle tests |
| Exact validation check rosters | [`validation_roster_expectations.py`](../../tests/contract_integration/validation_rosters/validation_roster_expectations.py) and [`test_validation_check_rosters.py`](../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py) |
| Validation publication and neutral BAM/reference/executable-resolution helpers | [`test_validation_report.py`](../../tests/libraries/test_validation_report.py), [`test_bam_validation.py`](../../tests/libraries/test_bam_validation.py), [`test_reference_contigs.py`](../../tests/libraries/test_reference_contigs.py), [`test_executable_resolution.py`](../../tests/libraries/test_executable_resolution.py), and affected consumer transaction suites |
| Public schemas, headers, deterministic bytes, and computational statuses | Contract-owner tests under `tests/contracts/` plus [independent contract goldens](../../tests/contract_integration/independent_contract_goldens/README.md) and affected producer suites |
| Step `09` statistic, p-value, odds-ratio, and estimability behavior | [independent CMH oracle](../../tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py), fixed owner corpus, and guarded real-R comparison |
| Python non-regression measurement | Tracked snapshot, comparison implementation, and direct policy tests named above |

Local mocks, transport stubs, guarded R fixtures, and pinned report rendering do
not establish scheduler, production, scientific-review, or biological
evidence. Real R remains a separate mandatory gate because Python coverage does
not measure R source.

## Local validation lane ownership

`make all-checks` is the one assembled local gate. It first verifies that the
selected `.venv` matches `uv.lock` without installing or repairing anything,
then runs the static preflight serially. Only after preflight passes does the
runner schedule four independent owner lanes, with `--serial` remaining the
authoritative deterministic fallback:

| Lane | What it validates | Deliberate exclusions |
| --- | --- | --- |
| Static preflight | Ruff and dead-code configuration, documentation structure, `git diff --check`, shell syntax, Python compilation, and the example-manifest contract. | No behavior suite and no dependency restoration. |
| Python coverage | The Python behavior suite with branch and traced-subprocess coverage, including pure-Python Jinja report rendering and publication. Local `make all-checks` runs the complete inventory in one process group; CI runs the same inventory as four receipt-verified shards. The two route-specific subprocess probes remain focused measurements inside this lane. | The isolated-wheel suite, which runs in its owning lane. |
| Installed wheel | One offline wheel build, clean locked installation, packaged-schema/template/CSS checks, installed grouped CLI/resource probes, representative manifest validation, and installed Jinja rendering. | No replay of repository owner suites. |
| Shell owners | Direct shell-owner behavior contracts and the repository-local R-selection shell contract. | Whole-Run Slurm submission and transport, which are exercised by Python and selected real-synthetic lanes; no general Python validator or reporting suite. |
| Guarded real R | Locked-environment checks plus the Step `08` and Step `09` real-R contract suites. | No Python, reporting, shell, or wheel replay. |

`report-test`, `shell-test`, the package-distribution test, and direct owner
tests remain supported focused feedback routes; the assembled gate does not
invoke those same suites through a second lane. Quiet successful lane logs are
ephemeral. Failed, externally interrupted, and peer-cancelled lanes retain a
diagnostic log, and the first failing lane's exact nonzero status remains the
gate status. The former optional result-JSON aggregation had no active caller
or documented consumer and is not a supported contract.

Nox disposition: **REJECTED**. After native simplification,
`tests/tools/run_validation.py` and its direct test total 876 maintained lines,
down from 1,029. Nox parallel stop-on-error permits already-running sessions to
finish, while EMRYS's contract terminates their process groups and retains
interruption diagnostics. Matching that behavior would require a substantial
custom supervisor around Nox, failing the mandatory exact-cancellation/no-
custom-orchestration criterion. `uv` remains the sole Python dependency and
environment authority; Nox is not a dependency.

## Current output and log boundaries

Current production-operation output behavior belongs to each implementation,
contract, and direct test. No production operation currently adopts the neutral
logging foundation. The [`logging contract`](LOGGING_CONTRACT.md) owns both the
implemented foundation contract and guarantees for later operation adoption;
exact foundation behavior lives with the
[application-logging owner](../../src/emrys/libraries/application_logging/README.md)
and its [direct tests](../../tests/libraries/application_logging/). Git history
retains the superseded commit-bound crosswalk and exposure inventory.
The direct suite also ratchets the packaged-Python production-import roster,
which is currently empty; an approved adoption slice must change that roster
together with its owner contract, current source topology, and behavioral
evidence.

For production paths that have not adopted the foundation, retained current
boundaries are:

- console streams are human or mixed unless an interface explicitly declares a
  machine stream or output file;
- validator stdout may mix context with TSV-shaped rows, so the explicit
  validation-report file is the machine contract;
- scheduler `.out` and `.err` are conditional scheduler copies, not a general
  durable application-attempt log or evidence promotion;
- receipts, reports, QC, metrics, and manifests are durable artifacts, not
  complete console logs;
- the permanent Step `05` operator checker remains directly owned at
  `tests/data_checks/validate_step05_outputs.sh`; silent snapshot replacement
  remains a characterized defect; and
- paths, arguments, environment/tool diagnostics, URLs, and arbitrary child
  output may contain sensitive material and have no general redaction promise.

## Current cross-cutting risk checklist

| Risk area | Retained boundary and recheck route |
| --- | --- |
| Public help, dry-run, execute, malformed input, overwrite, and exit behavior | Preserve explicit distinctions through the public-CLI suite and direct owner. |
| Native output transactions | Preserve producer-specific locking, validation, publication, rollback, recovery, and unrelated-file boundaries; recorded rewrite-blindness, foreign-final deletion, and incomplete rollback or lock-loss remain defects. |
| Validation reports and exact check rosters | Preserve the literal seven-column report and ordered producer rosters through validator owners, roster agreement, and independent goldens. |
| Schemas, headers, deterministic bytes, and statuses | Preserve independent canonical JSON/TSV/receipt expectations plus broader contract and producer tests; do not infer evidence promotion from a shared status word. |
| Hashes, mutation, links, signals, and filesystem identity | Recheck stable-input detection, same-size/restored-mtime gaps, symlink/hardlink/directory substitution, cleanup, and recovery through the applicable fault-injection and transaction owner. |
| Computational and external interpretation boundaries | Keep local, runtime, cluster, and computational claims distinct; candidate review, adjudication, and biological interpretation remain external work-process records rather than test-owned pipeline states. |
| Direct execution, arbitrary CWD, and SLURM | Preserve file-mode, Bash 3.2, dry-run side-effect, CWD, module, delegation, and output-check exceptions through public-CLI, direct-owner, whole-Run transport, and real-synthetic suites. Hosted 130-pair direct/disposable-single-node-Slurm successful-outcome parity is proven; 100,000-pair, institutional site/module, failure/recovery, multi-node, and production behavior remain open. |
| Step `09` CMH semantics | Preserve the independent count-derived oracle and guarded real-R comparison; production-validator non-recomputation remains a characterized defect. |

## Fixture independence

Independent critical expectations supplement rather than replace integrated
producer-coupled fixtures. Recheck the applicable direct owner whenever a
schema, header, serialized byte, status, transaction, scientific rule, or
fixture builder changes.

Real bcftools, CSU scheduler/modules, production-scale R, and production reports
remain environment-deferred until separately inspected evidence exists.
External scientific review or adjudication records are evaluated outside this
test baseline.

## Evidence-derived characterization gaps

`TG-01` through `TG-06` are complete as characterization evidence, not as
automatic production corrections. Their dated completion records remain in the
historical testing snapshot; current recheck routes are the owners indexed
above. A changed surface must be reassessed against its current implementation,
contract, direct tests, and this evidence boundary. Completion never approves a
characterized defect, authorizes production mutation, supplies missing runtime
or cluster evidence, validates a scientific algorithm beyond its named oracle,
or authorizes biological interpretation.
