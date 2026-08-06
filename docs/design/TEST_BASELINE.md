# Test baseline and contract-risk index

This document owns the current Python non-regression policy, evidence
vocabulary, contract-risk checklist, and direct regression routes. Dated
counts, timings, matrices, gate narratives, and characterization completions
remain in the
[`2026-08-01 testing snapshot`](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md).

## Evidence boundary

Python coverage measures executed Python statements and branches during the
complete Python suite, including traced subprocesses. It does not measure shell
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
Exact measurement, check, and reviewed-update commands live in the
[`RUNBOOK.md` local gate](../operations/RUNBOOK.md#local-validation-gate).

The current snapshot identity is schema `1.0.0` with coverage.py `7.15.2`.
Across `69` tracked Python files, its totals are `10873/12804` lines
(`0.849188`) and `3787/5058` branches (`0.748715`). The machine-readable
snapshot remains authoritative after any later accepted update. The reviewed
concurrency-tool retirement removed three measured modules. Against the
predecessor with those modules removed, coverage increased from `0.848585` line
/ `0.748613` branch; the lower unadjusted aggregate is a denominator effect of
deleting unusually highly covered dead code, not reduced coverage of the
surviving topology.

The active policy:

- measures branches and Python subprocesses over exactly `scripts` and
  `src/norad`;
- requires subprocess coverage for
  `src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py` and
  `src/norad/ingestion/sample_manifest_admission/validate_manifest.py`;
- rejects any exact-ratio decrease in global line or branch coverage;
- rejects disappearance of a tracked baseline module;
- requires each explicitly named new shared Python module to reach at least
  90% line and 85% branch coverage, including after reviewed promotion into
  the baseline;
- compares exact covered/total ratios, not rounded display values; and
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
| Step `09` statistic, p-value, odds-ratio, and estimability behavior | [independent CMH oracle](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py), fixed owner corpus, and guarded real-R comparison |
| Step `09c` input, evidence policy, publication, signal, concurrency, and recovery behavior | [direct Python suite](../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py), adjacent shell contract, fixture builder, and neutral [review-package tests](../../tests/contracts/scientific_evidence/test_review_package.py) |
| Python non-regression measurement | Tracked snapshot, comparison implementation, and direct policy tests named above |

Local mocks, wrapper stubs, guarded R fixtures, and pinned report rendering do
not establish scheduler, production, scientific-review, or biological
evidence. Real R remains a separate mandatory gate because Python coverage does
not measure R source.

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
