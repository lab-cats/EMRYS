# Test baseline and contract-risk index

This is the current route for coverage policy, test evidence boundaries,
contract-risk categories, and independent regression owners. Exact historical
counts, timings, matrices, and completion narratives live in the
[`2026-08-01 test-baseline snapshot`](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md).

## Evidence boundary

Python coverage measures which Python statements and branches execute during
the complete Python test suite, including traced Python subprocesses. It does
not measure shell or R source coverage, prove that assertions are independent
of production rules, or replace scenario, mutation, transaction, recovery,
real-runtime, or cluster tests.

All results routed here are local engineering evidence. They do not promote
any workflow step, report, scientific review, or biological interpretation
state.

## Current Python coverage gate

The machine-readable tracked snapshot is
[`tests/baselines/python_coverage.json`](../../tests/baselines/python_coverage.json).
Exact measurement and update commands live in the
[`RUNBOOK.md` local gate](../operations/RUNBOOK.md#local-validation-gate).

The active comparison policy:

- rejects any decrease in the global line or branch rate;
- rejects a tracked baseline module that disappears;
- requires each explicitly named new shared Python module to meet at least 90%
  line and 85% branch coverage, including after its reviewed promotion into
  the tracked baseline;
- compares exact covered/total ratios rather than rounded display values; and
- requires an explicit, reviewed baseline update rather than updating during
  ordinary tests.

Coverage uses branch and subprocess measurement over exactly `scripts` and
`src/norad`, and must include
`src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py` and
`scripts/validate_manifest.py`. Low numerical coverage is a review signal; it
is not by itself proof of a user-visible defect or authority to change
behavior.

The tracked Step `00c` validator row resolves to
`src/norad/stages/construct_FASTA_sidecars/validate_step_00c_reference_sidecars.py`.
Its current measured `136/142` line and `39/44` branch counts include the
reviewed neutral reference-contig loader. The tracked Step `01` validator
remains at its final path with `125/140` measured lines and `34/44` measured
branches.

The final MIG-03F serial measurement moved Step `02` to
`src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py`
at `137/149` covered lines and `32/42` branches. The reviewed private-loader
changes measure Step `04` at `144/155` and `33/42`, Step `05` at `138/149` and
`31/38`, and neutral `src/norad/libraries/bam_validation.py` at `12/12` lines
with no branches.

The final MIG-03G serial measurement moved Step `02b` to
`src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py`
at `103/110` covered lines and `24/30` branches. It passed `1,113` tests with
`17` skips and one explicit deselection of the documentation assertion reserved
for the separate close. Every non-target row remained exact; global measurement
is `9505/11677` lines and `3328/4756` branches, above the frozen covered-count
floors, and the standalone policy comparison passed.

The final MIG-03H serial measurement moved Step `03` to
`src/norad/evidence/collect_RSeQC_paired_orientation_evidence/validate_step_03_rseqc_orientation.py`
at `103/115` covered lines and `28/34` branches. It passed `1,120` tests with
`17` skips and one explicit deselection of the documentation assertion reserved
for the separate close. Every non-target row remained exact; global measurement
is `9508/11677` lines and `3331/4756` branches, above the frozen covered-count
floors, and the standalone policy comparison passed.

The final MIG-03I measurement moved Step `04` to
`src/norad/stages/mark_BAM_duplicates_with_Picard/validate_step_04_mark_duplicates.py`
at `146/155` covered lines and `35/42` branches. It passed `1,134` tests with
`17` skips and one explicit deselection of the documentation assertion reserved
for the separate close. Every non-target row remained exact; global measurement
is `9510/11677` lines and `3333/4756` branches, above the frozen covered-count
floors, and the standalone policy comparison passed.

The final MIG-03J measurement moved Step `05` to
`src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py`
at `178/192` covered lines and `45/54` branches. It passed `1,159` tests with
`17` skips and one explicit deselection of the documentation assertion reserved
for the separate close. Every non-target row remained exact; global measurement
is `9550/11720` lines and `3347/4772` branches, above the frozen covered-count
floors, and the standalone policy comparison passed.

The final MIG-03K measurement moved Step `06` to
`src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py`
at `108/119` covered lines and `24/30` branches. It passed `1,177` tests with
`17` skips and one explicit deselection of the documentation assertion reserved
for the separate close. Every non-target row remained exact; global measurement
is `9551/11720` lines and `3348/4772` branches, above the frozen covered-count
floors, and the standalone policy comparison passed.

The final MIG-03L measurement moved Step `07` to
`src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/validate_step_07_mpileup_outputs.py`
at `177/198` covered lines and `51/72` branches. Python ran `1,199`
passes with `17` skips before the sole documentation assertion reported ten
intentionally deferred migration links plus nine inherited `UNREFINED`
locations. The tracked target-only baseline keeps every non-target row exact;
global covered-count floors are `9561/11720` lines and `3351/4772` branches,
and the standalone policy comparison passed. This result is not a green
aggregate gate.

The final MIG-03M measurement moved Step `08` to
`src/norad/stages/preprocess_and_annotate_cohort_candidates/validate_step_08_preprocessing_outputs.py`
at `162/167` covered lines and `42/48` branches. The policy measurement passed
`1,219` tests with `17` skips and one explicit deselection of the documentation
assertion reserved for this close. The tracked target-only baseline keeps every
non-target row exact; global covered-count floors are `9601/11758` lines and
`3367/4784` branches, and the standalone comparison passed. An untouched full
Python run had the same `1,219` passes and `17` skips before its sole failure
listed twelve deferred MIG-03M links plus nine inherited `UNREFINED` locations.
Neither result makes the aggregate gate green.

The final MIG-03O measurement moved Step `09c` to
`src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.py`
at `1279/1534` covered lines and `568/788` branches. Artifact indexing retained
`1658/2069` lines and `701/986` branches, and run-summary science retained
`321/403` lines and `111/172` branches, above their frozen rate floors. The
policy measurement passed `1,323` tests with `17` skips and one explicit
deselection of the documentation assertion reserved for this close; global
measurement is `9937/11916` lines and `3527/4842` branches, and the standalone
comparison passed. The untouched aggregate Python lane reached the same
`1,323` passes and `17` skips before its sole failure listed eight intentionally
deferred MIG-03O documentation links; coverage therefore did not run in that
aggregate attempt. Neither result makes that earlier aggregate gate green.

The current MIG-04B measurement protects final
`src/norad/evidence/reference_provenance/reference_provenance.py` at `332/379`
covered lines and `107/142` branches. The committed tracked baseline remains
`10323/12387` lines and `3633/4986` branches; only that file identity moved,
with its counts and rates unchanged and no unrelated baseline promotion. The
complete Python lane passed `1,590` tests with `17` skips and measured
`0.847971` global line coverage and `0.750594` global branch coverage across
`36` files. The final affected roster passed `183` tests; static, all shell,
public CLI/Make, coverage-policy, and documentation gates passed. This is
direct relocation, arbitrary-CWD, and loader-integrity evidence only; no
dependency was installed, restored, removed, or updated, and no runtime,
cluster, scientific-review, or biological evidence was created.

DOC-GATE-01 independently freezes the extracted documentation validator with a
hard-coded legacy heading oracle, isolated valid/invalid repositories, exact
ordered diagnostics, explicit-root and fail-closed Git inventory scenarios,
all current card/link/anchor/dependency/orphan/Mermaid rules, and distinct
`IN_PROGRESS`/`COMPLETED` blocker boundaries. Its card-boundary focused suite
passed `183` tests. The logic-free `documentation-check` Make target has a
literal public-command expansion and same-engine success fixture. Its failure
fixture locks the direct engine's exit `1`, the preserved engine diagnostic,
and Make's appended target error and native exit `2`; production validator
semantics did not change.

The corresponding full command was not green. Static preflight passed before
guarded R stopped with status `2` on the inherited ignored malformed `macos`
library entry and unavailable Bioconductor metadata DNS. The separate complete
documentation check reported only the eight authorized `UNREFINED` proposals
plus their README. At that checkpoint those nine findings were a nonpassing
repository-state boundary assigned to `TASK-LIFECYCLE-01`, not a DOC-GATE pass
claim. No dependency was installed, restored, removed, or updated.

TASK-LIFECYCLE-01 adds independent accepted/rejected fixtures for the exact
lightweight `UNREFINED` proposal schema and full-card `INTEGRATION_REVIEW`
behavior while retaining the frozen actionable-card heading oracle. Its
card-boundary documentation/public-command set passed `197` tests. The exact
`make -s documentation-check` then passed with `204` Markdown documents, `125`
actionable task cards, and `6` Mermaid sources. This closes the nine lifecycle
findings; it is documentation-structure evidence only and supplies no guarded-
R, cluster, production, scientific-review, or biological-readiness evidence.

The repository-health continuation moved the exact ignored malformed
`renv/library/macos/R-4.6/aarch64-apple-darwin23/macos/` directory tree to a
recoverable `/private/tmp` quarantine; it contained only nested empty
directories (`0B`). Sandboxed `make -s r-check` then failed only on Bioconductor
metadata DNS, while the authorized network-enabled rerun reported no project-
library issue and passed with R `4.6.1` and Bioconductor `3.23`. No dependency
was installed, restored, removed, or updated.

The first exact full gate at published lifecycle close `776dad3` passed static,
shell, guarded-R, and report-runtime lanes, then failed only because the
documentation-wrapper fixture expected direct-run `make` while recursive GNU
Make correctly emitted `make[2]`. The retained log is
`/var/folders/y0/bg0yx6g54bs0403dn0x_k28w0000gn/T/norad-validation-python-coverage-3vtydtkj.log`.
Test-only checkpoint `10be692` derives the exact native label from inherited
`MAKELEVEL`; direct and explicit level-`2` focused cases passed. The exact full-
gate rerun passed with static `0.120s`, shell `53.922s`, guarded R `163.293s`,
report runtime `128.434s`, Python coverage `198.164s`, and overall parallel
status `0` in `198.291s`. This is complete local repository-gate evidence, not
cluster, production, scientific-review, or biological-readiness evidence.

## Current evidence vocabulary

- `preserved contract` means independent regression evidence protects the
  declared compatibility boundary.
- `characterized defect` remains a defect; characterization does not approve
  or normalize it.
- `undefined — decision required` means implementation must stop until an
  owner decides the behavior.
- `environment-deferred` means local contract evidence exists but the named
  runtime, scheduler, production, or scientific environment has not supplied
  the missing evidence.

An independent expectation does not import or derive the production rule it
is meant to detect. Producer-coupled integrated fixtures remain useful only as
additional end-to-end evidence. Readable failed validator evidence may publish
`status=fail` and exit zero; malformed or unsafe operation exits nonzero and
publishes nothing. Restore and baseline-update targets remain explicit
operator mutations, never implicit test actions.

## Python entry points

Current executable behavior belongs to the implementation, its colocated
contract, and its direct regression owners. These indexes keep the full public
surface reachable without copying the dated row-by-row matrices:

| Surface or risk | Current regression route |
| --- | --- |
| Python, shell, R, file-mode, arbitrary-CWD, and Make entry points | `tests/test_public_cli_contracts.py` and the direct owner named by each entry point; exact path maps cover final migrated-owner paths plus intentionally retained cross-cutting flat owners |
| SLURM modes, modules, CWD, delegation, arguments, outputs, and exits | `tests/test_slurm_wrapper_contracts.py` plus each delegated workflow owner; direct migrated-stage tests through Step `08` live under `tests/stages/`, Step `09` under `tests/analyses/`, and migrated Step `02b`, Step `03`, and Step `09c` evidence tests under their owner directories in `tests/evidence/` |
| Exact Step `00a`–`09` validation rosters | `tests/validation_roster_expectations.py` and `tests/test_validation_check_rosters.py` |
| Validation publication, neutral BAM/reference helper loading, and recovery faults | `tests/libraries/test_validation_report.py`, `tests/libraries/test_bam_validation.py`, `tests/libraries/test_reference_contigs.py`, plus affected consumer and producer-specific transaction suites |
| Public schemas, headers, bytes, statuses, and shared-policy transitions | `tests/contracts/scientific_evidence/test_review_package.py` directly protects the neutral review-package roster, headers, vocabularies, bindings, and status reducer; `tests/test_independent_contract_goldens.py` plus schema and producer suites protect cross-owner parity. |
| Step `09` statistic, p-value, odds-ratio, and estimability characterization | `tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py`, its owner-local fixed corpus, and guarded real-R comparison |
| Step `09c` evidence policy, input, publication, signal, concurrency, and recovery behavior | `tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py` plus its adjacent shell contract and fixture builder; public review-package contract protection is neutral, and characterized signal defects remain defects |
| Python non-regression measurement | the tracked coverage snapshot and coverage tests |
| Full dated entry-point matrices and regression dispositions | [historical Python matrix](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#python-entry-points) and adjacent shell, R, SLURM, and Make sections |

Local mocks, wrapper stubs, guarded R fixtures, and pinned report rendering do
not establish scheduler, production, scientific-review, or biological
evidence. Real R remains a separate mandatory gate because Python coverage
does not measure R source.

## LOG-01 current output and log inventory

The complete commit-bound LOG-01 profiles, per-surface crosswalk, search
evidence, exposure inventory, and LOG-02 candidates are frozen in the
[dated snapshot](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#log-01-current-output-and-log-inventory).
Current output behavior remains owned by each implementation, contract, and
direct regression test; future logging guarantees remain in the logging
architecture owner.

The retained current boundaries are:

- console streams are human or mixed unless an interface explicitly declares
  a machine stream or output file;
- validator stdout mixes human context with TSV-shaped rows, so the explicit
  validation-report file is the machine contract;
- scheduler `.out`/`.err` files are conditional scheduler copies, not a
  general durable application-attempt log or evidence promotion;
- durable receipts, reports, QC, metrics, manifests, and scientific records
  are not complete console logs;
- Step `05` inspection output remains best-effort because duplicate truncating
  `tee` writers and silent replacement are characterized defects; and
- paths, arguments, environment/tool diagnostics, URLs, and arbitrary child
  output may contain sensitive material and have no general redaction promise.

## Current cross-cutting risk checklist

| Risk area | Retained boundary and recheck route |
| --- | --- |
| Public help, dry-run, execute, malformed input, and exit behavior | Preserve explicit legacy mode, help, overwrite, and exit distinctions through the public-CLI and direct-owner tests. |
| Native output transactions | Preserve producer-specific publication and recovery; metadata-only rewrite blindness, late-foreign-final deletion, and incomplete rollback or lock-loss remain characterized defects. |
| Seven-column validation-report schema | Preserve the literal schema through every validator owner plus roster and independent-golden tests. |
| Exact per-step check rosters | Preserve literal ordered producer rosters; shared-consumer reorder and adapter reordered or wrong-unique acceptance remain characterized defects. |
| Public JSON Schemas and table headers | Preserve representative independent paths/headers plus broader integrated schema tests. |
| Status vocabularies and transitions | Preserve closed states, aggregation, and shared scientific-policy projections without evidence promotion. |
| Deterministic bytes and ordering | Preserve independent canonical JSON/TSV/receipt bytes plus producer transaction fixtures. |
| Locks, signals, rollback, cleanup, and recovery evidence | Preserve heterogeneous action-local mechanisms; never infer one universal safe transaction from shared vocabulary. |
| Stable hashes and input mutation | Preserve independent rechecks; same-size/restored-mtime gaps remain characterized where recorded. |
| Unrelated-file immunity | Preserve declared-output boundaries through CLI and transaction owners. |
| Symlink, hardlink, and directory identity | Preserve substitution cases in fault and direct transaction suites. |
| Computational, scientific, and biological evidence states | Keep local, runtime, cluster, review, and reserved readiness meanings distinct. |
| Direct execution, arbitrary CWD, and SLURM delegation | Preserve file-mode, Bash 3.2, dry-run side-effect, CWD, module, and output-check exceptions; real scheduler/module/runtime behavior remains deferred. |
| Step `09` CMH semantics | Preserve the independent count-derived oracle; production-validator non-recomputation remains a characterized defect, not a corrected contract. |
| Shared science-policy projection | Preserve recorded, pending, absent, limitation, and computational-status transitions through independent plus integrated owners. |

## Fixture independence

Independent critical expectations supplement rather than replace integrated
producer-coupled fixtures. Recheck the applicable direct owner whenever a
schema, header, serialized byte, status, transaction, scientific rule, or
fixture builder changes. Real bcftools, CSU scheduler/modules, production-scale
R, production scientific review, and production reports remain
environment-deferred until separately inspected evidence exists.

## Evidence-derived characterization gaps

The six historical characterization gaps are complete as test evidence, not
as automatic production corrections:

| Gap | Current route |
| --- | --- |
| `TG-01` independent Step `09` CMH oracle | Independent oracle and real-R comparison; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-01-characterization) |
| `TG-02` validation publication and recheck faults | Fault-injection owners; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-02-characterization) |
| `TG-03` exact validation rosters | Literal roster owners; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-03-characterization) |
| `TG-04` public CLI and exit contracts | Public-CLI and direct owners; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-04-characterization) |
| `TG-05` SLURM wrapper contracts | Mocked wrapper and direct workflow owners; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-05-characterization) |
| `TG-06` independent goldens and mutation resistance | Independent-golden and integrated owners; [dated completion](../history/testing/2026-08-01-test-baseline-and-public-contract-traceability.md#completed-tg-06-characterization) |

The dated TEST-01Z matrix classified 88 source rows with no undefined row, but
that affirmative result released only its named planning roots. It did not
approve a characterized defect, authorize production mutation, establish
runtime or cluster evidence, validate a scientific algorithm, or authorize
biological interpretation. Any changed surface must be reassessed against its
current implementation, contract, direct tests, and this evidence boundary.
