# Test baseline and contract-risk index

This document owns the current Python non-regression policy, evidence
vocabulary, contract-risk checklist, and direct regression routes. Dated
counts, timings, matrices, gate narratives, and characterization completions
remain in the
[`2026-08-01 testing snapshot`](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md).

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

The compact snapshot records schema `2.0.0`, coverage.py `7.15.2`, exact
repository totals, critical-owner aggregates, and route-specific subprocess
evidence from a separate subprocess-only probe.
It deliberately does not retain a private-module roster. It remains
authoritative after an accepted update; a rebase must reflect a reviewed
source/test surface rather than hide new uncovered code.

The accepted exact floors are:

| Coverage owner | Line floor | Branch floor |
| --- | ---: | ---: |
| Python behavior lane | `9172 / 10431` (`0.879302`) | `3134 / 4084` (`0.767385`) |
| `norad.contracts.scientific_evidence` | `580 / 585` (`0.991453`) | `283 / 290` (`0.975862`) |
| `norad.libraries.validation` | `339 / 341` (`0.994135`) | `105 / 108` (`0.972222`) |
| Shared scientific validation primitives | `341 / 341` (`1.000000`) | `123 / 124` (`0.991935`) |
| Report/publication and receipt validation | `4920 / 5850` (`0.841026`) | `1733 / 2396` (`0.723289`) |
| Scientific-review publication | `860 / 1020` (`0.843137`) | `346 / 480` (`0.720833`) |
| Paired-CMH analysis contracts | `85 / 85` (`1.000000`) | `16 / 18` (`0.888889`) |

The Campaign A rebase removed 115 covered compatibility/helper statements from
`norad.contracts.scientific_evidence` while retaining its same five uncovered
statements and identical `283 / 290` branch result. Its lower line ratio is a
smaller-denominator effect, not lost behavior execution. Global and every
other critical-owner rate are equal or improved.

Comparisons cross-multiply the exact counts. Six-decimal rates are display
values and never weaken the gate through rounding.

The active policy:

- measures branches over exactly `scripts` and `src/norad`, with subprocess
  tracing enabled for the Python behavior lane;
- separately runs the subprocess-only GTF-to-BED12 and sample-manifest CLI
  suites and requires coverage in their exact public route modules;
- rejects any exact-ratio decrease in global line or branch coverage;
- rejects any exact-ratio decrease in the six critical-owner groups above;
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

## Python entry points

Current executable behavior belongs to its implementation, colocated contract,
and direct regression owner. This index routes rechecks without duplicating the
archived entry-point matrices.

| Surface or risk | Current regression route |
| --- | --- |
| Python, shell, R, file mode, arbitrary CWD, and Make entry points | [`test_public_cli_contracts.py`](../../tests/test_public_cli_contracts.py) plus the applicable direct owner |
| SLURM directives, modes, modules, CWD, delegation, arguments, outputs, and exits | [`test_slurm_wrapper_contracts.py`](../../tests/test_slurm_wrapper_contracts.py) plus the delegated functional owner |
| Exact validation check rosters | [`validation_roster_expectations.py`](../../tests/contract_integration/validation_rosters/validation_roster_expectations.py) and [`test_validation_check_rosters.py`](../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py) |
| Validation publication and neutral BAM/reference/executable-resolution helpers | [`test_validation_report.py`](../../tests/libraries/test_validation_report.py), [`test_bam_validation.py`](../../tests/libraries/test_bam_validation.py), [`test_reference_contigs.py`](../../tests/libraries/test_reference_contigs.py), [`test_executable_resolution.py`](../../tests/libraries/test_executable_resolution.py), and affected consumer transaction suites |
| Public schemas, headers, deterministic bytes, statuses, and shared scientific-state transitions | Contract-owner tests under `tests/contracts/` plus [independent contract goldens](../../tests/contract_integration/independent_contract_goldens/README.md) and affected producer suites |
| Step `09` statistic, p-value, odds-ratio, and estimability behavior | [independent CMH oracle](../../tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py), fixed owner corpus, and guarded real-R comparison |
| Step `09c` input, evidence policy, publication, signal, concurrency, and recovery behavior | [publisher suite](../../tests/evidence/scientific_review_package/test_step_09c_scientific_validation.py), adjacent shell contract, fixture builder, grouped assembly route, and neutral [review-package tests](../../tests/contracts/scientific_evidence/test_review_package.py) |
| Python non-regression measurement | Tracked snapshot, comparison implementation, and direct policy tests named above |

Local mocks, wrapper stubs, guarded R fixtures, and pinned report rendering do
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
| Static preflight | Ruff and dead-code configuration, documentation structure, `git diff --check`, shell and SLURM syntax, Python compilation, and the example-manifest contract. | No behavior suite and no dependency restoration. |
| Python coverage | The Python behavior suite with branch and traced-subprocess coverage, including pure-Python Jinja report rendering and publication. The two route-specific subprocess probes remain focused measurements inside this lane. | The isolated-wheel and SLURM-wrapper suites, which run in their owning lanes. |
| Installed wheel | One offline wheel build, clean locked installation, packaged-schema/template/CSS checks, installed grouped CLI/resource probes, representative manifest validation, and installed Jinja rendering. | No replay of repository owner suites. |
| Shell and SLURM | Shell behavior contracts, the repository-local R-selection shell contract, and SLURM wrapper directives, delegation, arguments, CWD, modules, outputs, and exits. | No general Python validator or reporting suite. |
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
finish, while NORAD's contract terminates their process groups and retains
interruption diagnostics. Matching that behavior would require a substantial
custom supervisor around Nox, failing the mandatory exact-cancellation/no-
custom-orchestration criterion. `uv` remains the sole Python dependency and
environment authority; Nox is not a dependency.

## LOG-01 current output and log inventory

The complete commit-bound profiles, crosswalk, exposure inventory, and future
logging candidates remain in the
[`LOG-01` snapshot](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#log-01-current-output-and-log-inventory).
Current output behavior belongs to each implementation, contract, and direct
test; future guarantees belong to the logging architecture.

Retained current boundaries:

- console streams are human or mixed unless an interface explicitly declares a
  machine stream or output file;
- validator stdout may mix context with TSV-shaped rows, so the explicit
  validation-report file is the machine contract;
- scheduler `.out` and `.err` are conditional scheduler copies, not a general
  durable application-attempt log or evidence promotion;
- receipts, reports, QC, metrics, and manifests are durable artifacts, not
  complete console logs;
- the permanent Step `05` operator checker remains directly owned at
  `tests/data_checks/validate_step05_outputs.sh`; duplicate truncating `tee`
  writers and silent snapshot replacement remain characterized defects; and
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
| Computational, scientific, and biological evidence states | Keep local, runtime, cluster, recorded, pending, absent, limitation, computational, review, and reserved-readiness meanings distinct. |
| Direct execution, arbitrary CWD, and SLURM | Preserve file-mode, Bash 3.2, dry-run side-effect, CWD, module, delegation, and output-check exceptions through public-CLI, wrapper, and owner suites; real scheduler/module behavior remains deferred. |
| Step `09` CMH semantics | Preserve the independent count-derived oracle and guarded real-R comparison; production-validator non-recomputation remains a characterized defect. |
| Step `09c` and shared science-policy projection | Preserve input/publication/recovery behavior and recorded/pending/absent/limitation/computational transitions through the direct evidence owner and neutral contract tests. |

## Fixture independence

Independent critical expectations supplement rather than replace integrated
producer-coupled fixtures. Recheck the applicable direct owner whenever a
schema, header, serialized byte, status, transaction, scientific rule, or
fixture builder changes.

Real bcftools, CSU scheduler/modules, production-scale R, production scientific
review, and production reports remain environment-deferred until separately
inspected evidence exists.

## Evidence-derived characterization gaps

`TG-01` through `TG-06` are complete as characterization evidence, not as
automatic production corrections. Their dated completion records remain in the
historical testing snapshot; current recheck routes are the owners indexed
above. A changed surface must be reassessed against its current implementation,
contract, direct tests, and this evidence boundary. Completion never approves a
characterized defect, authorizes production mutation, supplies missing runtime
or cluster evidence, validates a scientific algorithm beyond its named oracle,
or authorizes biological interpretation.
