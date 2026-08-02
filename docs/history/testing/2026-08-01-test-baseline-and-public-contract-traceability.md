> **Historical record**
>
> Frozen snapshot date: 2026-08-01. Originating path:
> `docs/design/TEST_BASELINE.md`. Initial baseline record:
> `4fc32e08121e541f489ede32f25d59c2626a60e0` on 2026-07-31. Affirmative
> TEST-01Z snapshot: `dc6f444a40f23cf834ad2535e15ca98f0fa294bb` on
> 2026-07-31. Frozen source snapshot:
> `eb65c9553eec0689bc71098da4b30d114b47fda3`; source blob:
> `055d7bd50560a39327b8f735ff4b190b1f277717`.
>
> This record preserves the complete dated baseline, matrices, LOG-01
> inventory, characterization evidence, and TEST-01Z decision. It is not the
> current coverage policy, contract, roadmap, or evidence owner. Relocation
> changed only five relative link destinations so they continue to reach the
> same owners; all other source-body text remains unchanged.

# Test baseline and public-contract traceability

This document owns the Phase `01` measured Python coverage summary, the
public-contract risk-to-test matrix, fixture-independence classification, and
the characterization gaps derived from that evidence. The machine-readable
per-module snapshot is
[`../../../tests/baselines/python_coverage.json`](../../../tests/baselines/python_coverage.json).
The authoritative descendant branch names and order remain in
[`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md), and executable commands remain in
[`../operations/RUNBOOK.md`](../../operations/RUNBOOK.md).

## Evidence boundary

This baseline measures which Python statements and branches execute during the
complete Python test suite, including traced Python subprocesses. It does not
measure shell or R source coverage, prove that assertions are independent of
production rules, or replace scenario, mutation, transaction, recovery,
real-runtime, or cluster tests.

All results in this document are local engineering evidence. They do not
promote any workflow step, report, scientific review, or biological
interpretation state.

## Measured Python baseline

The tracked snapshot records:

| Measure | Baseline |
| --- | ---: |
| Python source modules | 26 |
| covered statements | 8,514 |
| total statements | 10,528 |
| line rate | 80.8701% |
| covered branches | 3,068 |
| total branches | 4,402 |
| branch rate | 69.6956% |

The baseline uses pinned `coverage.py` `7.15.2`, branch measurement, the
`scripts/` source root, relative paths, and subprocess tracing. It requires
measured subprocess execution of `scripts/gtf_to_bed12.py` and
`scripts/validate_manifest.py`.

The comparison policy:

- rejects any decrease in the global line or branch rate;
- rejects a tracked baseline module that disappears;
- requires a new shared Python module to meet at least 90% line and 85% branch
  coverage;
- compares exact covered/total ratios rather than rounded display values;
- requires an explicit, reviewed baseline update rather than updating during
  ordinary tests.

The lowest measured module is `scripts/render_run_report_bundle.py` at
37.9877% line and 20.3704% branch coverage. Its public behavior also has
substantial end-to-end shell and real-renderer coverage, so this numerical
result is a review signal, not proof of an uncovered user-visible defect.
Later characterization must name a missing scenario before changing that
module.

### TEST-01Z coverage refresh

The checked Python lane was refreshed on 2026-07-31 against executable/test
commit `1986898` and documentation-only descendant `d02717b`. It collected
860 tests: 843 passed and 17 expected conditional report-runtime tests were
skipped in this lane. The retained temporary snapshot records:

| Measure | TEST-01Z refresh | Tracked baseline | Result |
| --- | ---: | ---: | --- |
| Python source modules | 26 | 26 | unchanged |
| covered statements | 8,585 | 8,514 | no regression |
| total statements | 10,551 | 10,528 | measured current source |
| line rate | 81.3667% | 80.8701% | pass |
| covered branches | 3,111 | 3,068 | no regression |
| total branches | 4,404 | 4,402 | measured current source |
| branch rate | 70.6403% | 69.6956% | pass |

The current snapshot digest is
`ca7ad24dbdbeb848ef867739e78c51b43bab4131b0f1365ed2fdbb7800c95db1`.
The tracked baseline was checked, not rewritten. Coverage remains supporting
evidence only; the row dispositions below are the readiness gate.

## Matrix notation

The contract-case codes used below are:

| Code | Protected case |
| --- | --- |
| `H` | help or usage |
| `D` | default dry-run and side-effect freedom |
| `E` | explicit execute or successful publication |
| `M` | missing or malformed input |
| `F` | failed evidence remains explicit |
| `N` | existing-output and no-clobber behavior |
| `L` | owned or foreign lock behavior |
| `B` | publication failure and rollback |
| `S` | signal, child cleanup, or retained recovery state |
| `I` | hash, metadata, or input-mutation recheck |
| `U` | unrelated-file immunity |
| `P` | path, symlink, hardlink, or directory-identity substitution |
| `T` | deterministic bytes, ordering, or serialization |
| `V` | computational/scientific evidence-state boundary |
| `X` | nonzero exit or child-exit propagation |
| `W` | wrapper delegation, exact arguments, or arbitrary working directory |
| `R` | exact validation check roster |

Coverage status means:

- **adequate**: the declared compatibility boundary has direct regression
  coverage; this is not a claim that every source branch is exercised;
- **partial**: useful coverage exists, but a named high-risk gap remains;
- **gap**: the required independent or behavioral protection is absent;
- **deferred runtime**: local contract coverage exists, but the behavior needs
  the separately authorized real or cluster environment;
- **not applicable**: the case is not part of that entry point's contract.

Test independence is classified as:

- **independent**: expected values are fixed without importing the production
  rule they are meant to detect;
- **producer-coupled**: the fixture or expectation imports or derives from the
  producer contract;
- **mixed**: independent assertions and producer-derived fixture construction
  are both present;
- **not applicable**: the row concerns execution mechanics rather than a
  duplicated semantic rule.

## Python entry points

`scripts/_run_summary_science.py` is a private shared module, not a public CLI.
It is exercised through the artifact, run-summary, Step `09c`, and report
suites and is included in the cross-cutting matrix below.

`tests/test_public_cli_contracts.py` independently inventories all 25
top-level workflow Python entry points and the one top-level private module.
For every public entry point it protects interpreter-invoked help,
unknown-option failure, arbitrary-CWD use, and no working-directory artifacts.
It separately freezes the current eight executable and 17 interpreter-only
file modes. Direct help for the executable set is tested with a prepared
`python3` path because their env shebang deliberately delegates dependency
selection to the caller's environment.

Developer-facing integration-fragment commands are a separate operator
surface under [`scripts/git_orchestration/`](../../../scripts/git_orchestration/).
Their explicit inventory and arbitrary-CWD help behavior are protected here;
focused temporary-repository tests additionally cover exact Git identity,
dry-run side-effect freedom, fragment and target validation, conflict recovery,
finalization, no-op recording, exact-SHA canonical publication, and detection
of concurrent source-ref violations. These safeguards do
not make semantic integration decisions or establish pipeline evidence.

| Public entry point | Direct regression owner | Covered cases | Independence | Status / remaining gap |
| --- | --- | --- | --- | --- |
| `build_artifact_index.py` | `tests/test_artifact_adapters.py`; `tests/test_independent_contract_goldens.py` | `H D E M F N L B S I U P T V X` | mixed plus independent characterization | adequate; `TG-06` adds independent ordered headers, canonical JSON bytes, and named mutations |
| `build_run_summary.py` | `tests/test_artifact_run_summary.py`; `tests/test_independent_contract_goldens.py` | `H D E M F N L B S I U P T V X` | mixed plus independent characterization | adequate; `TG-06` adds independent ordered headers, serialized bytes, and shared-policy transitions |
| `gtf_to_bed12.py` | `tests/test_gtf_to_bed12.py` | `H E M F N U T X W` | independent | `TG-04` complete; arbitrary-CWD output is exact and the existing output is silently replaced as a characterized defect |
| `reference_provenance.py` | `tests/test_reference_provenance.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` and `TG-04` characterization complete; incomplete-rollback recovery remains a labeled production gap |
| `render_run_report.py` | `tests/test_report_html_v1.py`; `tests/test_report_exports_v1.py` | `H D E M F T V X` | mixed | `TG-04` complete; existing renderer cases remain the output contract |
| `render_run_report_bundle.py` | `tests/test_report_exports_v1.py`; `tests/shell/test_render_run_report.sh` | `H D E M F N L B S I U P T V X W` | mixed | `TG-04` complete; low measured internal coverage remains and scenario evidence must precede any implementation change |
| `restore_quarto.py` | `tests/test_quarto_restore.py` | `H E M N L B I P T X` | independent | adequate for supported local restore; other platforms are not supported |
| `runtime_preflight.py` | `tests/test_runtime_preflight.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` characterization complete; lock-fsync, lock-cleanup, and incomplete-rollback recovery remain labeled production gaps; CSU execution deferred |
| `step_09c_scientific_validation.py` | `tests/test_step_09c_scientific_validation.py`; `tests/shell/test_step_09c_scientific_validation.sh` | `H D E M F N L B S I U P T V X W` | mixed | adequate for local synthetic contracts; production science review deferred |
| `storage_inventory.py` | `tests/test_storage_inventory.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` characterization complete; incomplete-rollback recovery remains a labeled production gap; CSU storage execution deferred |
| `validate_artifact_contracts.py` | `tests/test_artifact_schema_contracts.py`; `tests/test_independent_contract_goldens.py` | `H M F U P T V X` | mixed plus independent characterization | adequate; `TG-06` adds representative literal schema-path and mutation oracles |
| `validate_manifest.py` | `tests/test_validate_manifest.py` | `H M F P T X` | independent | adequate |
| `validate_step_00a_star_index.py` | `tests/test_validate_step_00a_star_index.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_00b_bed12.py` | `tests/test_validate_step_00b_bed12.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_00c_reference_sidecars.py` | `tests/test_validate_step_00c_reference_sidecars.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_01_star_alignment.py` | `tests/test_validate_step_01_star_alignment.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_02_canonical_bam.py` | `tests/test_validate_step_02_canonical_bam.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_02b_bam_qc.py` | `tests/test_validate_step_02b_bam_qc.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_03_rseqc_orientation.py` | `tests/test_validate_step_03_rseqc_orientation.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_04_mark_duplicates.py` | `tests/test_validate_step_04_mark_duplicates.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_05_split_ncigar.py` | `tests/test_validate_step_05_split_ncigar.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_06_orientation_outputs.py` | `tests/test_validate_step_06_orientation_outputs.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps |
| `validate_step_07_mpileup_outputs.py` | `tests/test_validate_step_07_mpileup_outputs.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | independent | `TG-02` through `TG-04` complete with labeled production gaps; real bcftools remains deferred |
| `validate_step_08_preprocessing_outputs.py` | `tests/test_validate_step_08_preprocessing_outputs.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py`; `tests/test_independent_contract_goldens.py` | `D E M F N L B S I P T X R` | mixed plus independent characterization | `TG-02` through `TG-04` and representative `TG-06` contracts complete with labeled production gaps |
| `validate_step_09_cmh_outputs.py` | `tests/test_validate_step_09_cmh_outputs.py`; `tests/test_step_09_cmh_oracle.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T V X R` | mixed | `TG-01` through `TG-04` complete; compatible validator/recovery corrections remain separately reviewed |

The per-step validator rows intentionally distinguish malformed inputs, which
exit nonzero and publish nothing, from readable but failed evidence, which may
publish `status=fail` rows while the command exits zero. The Phase `01`
characterization must preserve that distinction.

## Shell workflow entry points

| Public entry point | Direct regression owner | Covered cases | Status / remaining gap |
| --- | --- | --- | --- |
| `render_run_report.sh` | `tests/shell/test_render_run_report.sh` | `H D E M F N L B S I U P T V X W` | adequate for the public bundle wrapper |
| `step_00c_prepare_gatk_reference.sh` | `tests/shell/test_step_00c_prepare_gatk_reference.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_01_star_align.sh` | `tests/shell/test_step_01_star_align.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_02_sort_index_bam.sh` | `tests/shell/test_step_02_sort_index_bam.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_02b_bam_qc.sh` | `tests/shell/test_step_02b_bam_qc.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_03_infer_strandedness_and_orientation.sh` | `tests/shell/test_step_03_infer_strandedness_and_orientation.sh` | `H D E M F N L B I P T X W` | adequate script coverage; non-executable mode requires explicit `bash`; SLURM matrix remains `TG-05` |
| `step_04_mark_duplicates.sh` | `tests/shell/test_step_04_mark_duplicates.sh` | `H D E M F N L B I P T X W` | adequate script coverage; non-executable mode requires explicit `bash`; SLURM matrix remains `TG-05` |
| `step_05_split_n_cigar_reads.sh` | `tests/shell/test_step_05_split_n_cigar_reads.sh` | `H D E M F N L B I P T X W` | adequate script coverage; non-executable mode requires explicit `bash` |
| `step_06_split_bam_by_read_orientation.sh` | `tests/shell/test_step_06_split_bam_by_read_orientation.sh` | `H D E M F N L B I P T X W` | adequate |
| `step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `H D E M F N L B I U P T X W` | adequate with mocked bcftools; real bcftools deferred |
| `step_08_vcf_preprocessing.sh` | `tests/shell/test_step_08_vcf_preprocessing.sh`; guarded real-R suite | `H D E M F N L B S I U P T X W` | adequate local contract; production/cluster runtime deferred |
| `step_09_cmh_editing_site_calling.sh` | `tests/shell/test_step_09_cmh_editing_site_calling.sh`; guarded real-R suite; independent CMH corpus | `H D E M F N L B S I U P T V X W` | adequate producer contract; independent `TG-01` characterization complete |
| `step_09c_scientific_validation.sh` | `tests/shell/test_step_09c_scientific_validation.sh` | `H D E M F N L B S I U P T V X W` | adequate local synthetic contract |

`tests/test_public_cli_contracts.py` additionally inventories all 13 shell
entry points and protects Bash-invoked help, missing-argument failure,
arbitrary-CWD use, and side-effect freedom. It protects direct help for the ten
executable scripts and freezes the three non-executable Step `03`, `04`, and
`05` file modes as characterized defects requiring explicit `bash` invocation.

Signal coverage is strongest for the later transactional workflows and report
bundle. The matrix does not infer signal safety for an earlier workflow merely
because it has ordinary rollback coverage.

## R and dependency entry points

| Public entry point | Regression owner | Covered cases | Status / remaining gap |
| --- | --- | --- | --- |
| `check_r_environment.R` | `tests/shell/test_local_r_environment.sh`; guarded `make r-check` | `M F V X W` | characterized legacy exception: directly executable but any positional argument, including `--help`, is rejected; CSU runtime deferred |
| `restore_r_environment.R` | `tests/shell/test_local_r_environment.sh`; explicit `make r-restore` | `M F N X W` | characterized legacy exception: directly executable but has no help mode; installation remains explicit and never automatic |
| `step_08_vcf_preprocessing.R` | `tests/r/run_step_08_vcf_preprocessing_tests.sh`; `tests/r/test_step_08_vcf_preprocessing.R`; wrapper suite | `H E M F T X W` | adequate local real-R semantics; file mode is Rscript-only; production scale and cluster runtime deferred |
| `step_09_cmh_editing_site_calling.R` | `tests/r/run_step_09_cmh_tests.sh`; `tests/r/test_step_09_cmh_editing_site_calling.R`; wrapper suite; `tests/fixtures/step_09_cmh_oracle.tsv` | `H E M F T V X W` | adequate producer semantics; file mode is Rscript-only; independent `TG-01` count-derived equivalence corpus complete |

`tests/test_public_cli_contracts.py` freezes the two direct and two
Rscript-only file-mode sets. R source is not included in the Python coverage
percentages. The guarded real-R suite is therefore a separate mandatory gate.

## SLURM entry points

Static `bash -n` coverage applies to all wrappers but is not behavioral
coverage.

`tests/test_slurm_wrapper_contracts.py` independently inventories all 16
tracked jobs and freezes exact SBATCH directives, shebangs, strict mode, file
modes, execution-mode applicability, module calls and failure policy,
submit-directory behavior, delegation and arguments, output-validation
ownership, and child-exit propagation. Every dynamic case uses generated child
stubs, fake modules, fake tools, and tiny temporary inputs; it never invokes a
scheduler or real workflow executable.

| Public wrapper | Dynamic regression owner | Covered cases | Status / remaining gap |
| --- | --- | --- | --- |
| `step_00a_build_novogene_star_index.slurm` | central mocked wrapper suite | `E X W` | characterized legacy exception: caller-CWD embedded STAR compute, implicit execution, and no wrapper output check; cluster runtime deferred |
| `step_00b_gtf_to_bed12.slurm` | central mocked wrapper suite | `E M F T X W` | characterized legacy exception: required submit CWD and implicit embedded conversion/sort; exact BED12 shape check protected; cluster runtime deferred |
| `step_00c_prepare_gatk_reference.slurm` | central mocked wrapper suite; Step `00c` shell suite | `D E M F X W` | adequate mocked delegation/output contract; Bash 3.2 empty-array dry-run defect characterized; cluster runtime deferred |
| `step_01_star_align.slurm` | central mocked wrapper suite; Step `01` shell suite | `D E M X W` | caller-CWD and default dry-run placeholder side effects protected; output validation remains delegated; cluster runtime deferred |
| `step_02_sort_index_bam.slurm` | central mocked wrapper suite; Step `02` shell suite | `D E M F X W` | caller-CWD and dry-run output-directory side effect protected; Bash 3.2 empty-array defect characterized; cluster runtime deferred |
| `step_02b_bam_qc.slurm` | central mocked wrapper suite; Step `02b` shell suite | `D E M F X W` | required submit CWD and dry-run output-directory side effect protected; Bash 3.2 defect characterized; cluster runtime deferred |
| `step_03_infer_strandedness_and_orientation.slurm` | central mocked wrapper suite; Step `03` shell suite | `D E M F X W` | fallback submit CWD, exact delegation, and output check protected; Bash 3.2 defect characterized; cluster runtime deferred |
| `step_04_mark_duplicates.slurm` | central mocked wrapper suite; Step `04` shell suite | `D E M F X W` | exact modules/tools/delegation and three-output check protected; Bash 3.2 defect characterized; cluster runtime deferred |
| `step_05_split_n_cigar_reads.slurm` | central mocked wrapper suite; Step `05` shell suite | `D E M F X W` | exact delegation and two-output check protected; Bash 3.2 defect characterized; cluster runtime deferred |
| `step_06_split_bam_by_read_orientation.slurm` | central mocked wrapper suite; Step `06` shell suite | `D E M F X W` | exact delegation and five-output check protected; Bash 3.2 defect characterized; cluster runtime deferred |
| `step_07_bcftools_mpileup_by_chrom_and_strand.slurm` | central mocked wrapper suite; Step `07` shell suite | `D E M F X W` | adequate local wrapper contract with mocked runtime; cluster runtime deferred |
| `step_08_vcf_preprocessing.slurm` | central mocked wrapper suite; Step `08` shell suite | `D E M F X W` | adequate local wrapper contract without guessed R modules; cluster runtime deferred |
| `step_09_cmh_editing_site_calling.slurm` | central mocked wrapper suite; Step `09` shell suite | `D E M F X W` | adequate local wrapper contract without dependency installation; cluster runtime deferred |
| `template.slurm` | central mocked wrapper suite | `M X W` | characterized caller-CWD, mode-less lightweight template probe; strict module loads and tolerant unredirected module lists preserved |
| `tool_check.slurm` | central mocked wrapper suite | `M X W` | characterized caller-CWD, mode-less tool probe; required probes propagate failure while optional Picard version failure is tolerated |
| `validate_manifest.slurm` | central mocked wrapper suite | `M X W` | characterized caller-CWD, mode-less lightweight validation with strict Python module/child exit; no module-list call |

`TG-05` is complete as local characterization. Cluster execution, actual CSU
module behavior, and production-scale runtime remain environment-deferred.
The Step `00a`/`00b` embedded-compute exceptions and every other differing
wrapper behavior remain unchanged pending later structural review.

## Make targets

| Public target(s) | Regression evidence | Status |
| --- | --- | --- |
| `test`, `shell-test`, `validation-shell-contracts`, `real-r-test`, `r-check`, `local-real-r-test`, `report-test`, `python-coverage-check`, `validate`, `smoke`, `lint`, `all-checks` | exact inventory and command expansion in `tests/test_public_cli_contracts.py`; focused component and orchestrator suites; complete gate | adequate local-gate category with existing failure/exit ownership preserved |
| `r-restore`, `quarto-restore`, `python-coverage-baseline-update` | exact inventory/expansion plus focused restore and baseline tests | adequate explicit operator-mutation category; never an implicit test action |
| `validation-report-runtime`, `demo-report`, `python-coverage-measure` | exact inventory/expansion plus focused output/runtime suites | adequate explicit-output category; commands retain their declared output and evidence boundaries |
| `validation-python-coverage`, `validation-guarded-r`, `validation-static` | exact inventory/expansion plus `all-checks` orchestration tests | adequate internal-lane category; not standalone user workflow claims |
| `demo-step03-dry-run`, `demo-step03` | exact inventory and local command expansion only | environment-deferred: scheduler submission remains future cluster evidence |

## LOG-01 current output and log inventory

This inventory characterizes current behavior; it does not prescribe the
future logging interface or authorize output changes. It covers all 25 public
Python, 13 public shell, 4 R, and 16 SLURM entry points enumerated above, all
23 Make targets, the opted-in R startup hook, the validation orchestrator and
its lanes, the inline documentation gate, two executable operational checks
under `tests/data_checks`, and the durable console-copy surfaces found by
targeted repository searches. The private `_run_summary_science.py` module has
no independent command surface or console output and is explicitly excluded.

The inventory uses these terms:

- **human** means prose intended for an operator, even when it uses regular
  label/value lines;
- **machine** means a declared structured stream or file safe for a program to
  consume;
- **protected** means the named regression owner fixes the stated content,
  channel, ordering, command, or exit relationship, not that the entire
  console byte stream is a golden;
- **artifact only** means durable receipts, reports, QC, or scientific outputs
  exist but are not a complete console copy;
- **conditional scheduler copy** means SLURM owns job-level stdout/stderr files
  only when submission-CWD and pre-created `logs/` requirements succeed. The
  repository cannot establish actual scheduler capture locally.

Severity is semantic rather than a current logger enum: resolved context,
plans, progress, pass, and success are informational; explicit warnings remain
warnings; `ERROR`, `FAIL`, `INTERRUPTED`, R `stop`, and delegated nonzero
diagnostics are errors. Arbitrary tool/renderer/test output has owner-defined
severity. Stability follows each crosswalk `Trace`: the named assertions are
protected, while unasserted prose and delegated output are observational. No
row claims that a complete console stream is golden.

All public Python entry points have protected help on stdout and unknown-option
failure on stderr. All public shell entry points have protected help on stdout
plus missing-argument nonzero and side-effect-free behavior; their common CLI
test does not assert a universal missing-argument stderr contract. The four R
entry points retain the distinct help and file-mode cases recorded above.

Targeted searches at `b2af738` found no tracked non-test runtime or production
component parsing a workflow or validator console stream. Tests do capture and
inspect those streams as regression consumers, and SLURM is configured to
capture them as job evidence, while durable TSV, JSON, receipt, and report
files remain separate contracts. External operator, cluster, and downstream
consumers were not inspected, so this is not a claim about compatibility
outside the repository.

Static inspection found no credential-specific CLI option or committed
credential literal in these surfaces. Runtime argument values, paths,
environment or tool diagnostics, URLs, renderer output, and arbitrary child
output may nevertheless contain sensitive material. LOG-02 must define
avoidance or redaction before detailed commands become an application-log
contract.

### Output profiles

The crosswalk below maps every surface to one of these normalized profiles.
Per-surface exceptions remain in the crosswalk rather than weakening a
profile's meaning.

| Profile | Current streams, audience, and stability | Durable and recovery value | Principal exposure |
| --- | --- | --- | --- |
| `PY-TXN` | Human mode, identity, path, count, evidence-boundary, and publication prose on stdout; actionable `ERROR` on stderr; not a machine stream | Declared reports/receipts are durable, but direct console is not; attempt IDs, hashes, locks, publication order, rollback, and cleanup are recovery-critical | Resolved paths, run/review/attempt IDs, hashes, artifact/sample IDs, statuses, and counts |
| `PY-REPORT` | Human NORAD plan plus exact renderer command and delegated renderer output on stdout; renderer/error diagnostics on stderr; mixed prose | Report bundle is durable but console is not; commands, hashes, receipt-last publication, rollback, and cleanup are recovery-critical | Paths, table/run IDs, hashes, tool versions, and renderer diagnostics |
| `PY-CONVERT` | Human success on stdout; warnings and errors on stderr; not machine-readable | BED output is durable; console contains little recovery state and has no complete copy | Input/output paths and transcript diagnostics |
| `PY-RESTORE` | Human download, validation, and installation progress on stdout; errors on stderr | Installed tool tree is durable operator mutation; console is not retained | URL, install path, pinned version/hash, and archive diagnostics |
| `PY-CHECK` | Human pass/summary prose on stdout and validation errors on stderr; not a machine stream | Inputs remain unchanged and no validation receipt or console log is produced | Schema/document/manifest paths, counts, and manifest labels |
| `PY-STEPVAL` | Seven-column validation-report TSV bytes and human context/status share stdout. Semantic validation failures are `status=fail` rows and may still exit zero; malformed or unsafe operational exceptions use stderr and exit 2. Stdout is therefore not safe as standalone TSV; the explicit report file is the machine contract | Execute mode persists the report; dry-run and surrounding console are ephemeral. Check, failed-evidence, lock, publication, rollback, and cleanup detail is recovery-critical | Paths, scope IDs, check details, hashes, statuses, and tool observations |
| `SH-LAUNCH` | Script-owned launcher context and shell-escaped child command use stdout; launcher errors use stderr. Delegated children retain their own channels except explicit captures or merges | Child artifacts are durable but direct console is not; exact delegation and child transaction failures are recovery-critical | Interpreter and input/output/tool paths, IDs, arguments, and child diagnostics |
| `SH-STAGE` | Script-owned resolved context, exact commands, validation/publication plans, and success use stdout; script-owned errors, warnings, mismatches, and rollback detail use stderr. Delegated tools retain owner-defined channels except explicit captures or merges | Native outputs/QC are durable; direct console is not. Run-token, lock, staging, backup, command, and rollback detail can be recovery-critical | Sample IDs, paths, command arguments, tool versions, headers, and metadata |
| `SH-COHORT` | Script-owned cohort/analysis context, manifests/hashes, exact pipeline or R command, validation/publication plans, and results use stdout; script-owned failures and recovery detail use stderr. Delegated R/tool output retains owner-defined channels except explicit captures or merges | Artifacts and receipts are durable, not the console; input-set identity, hashes, locks, mutation checks, publication, and rollback are recovery-critical | Cohort/analysis/sample IDs, paths, hashes, filters, thresholds, commands, and policy/status values |
| `R-ENV` | R `message` progress and `stop` failures use stderr; dependency-owned diagnostics may use either stream; no declared stdout result | Restore mutates the guarded library; neither command retains a console log | Project/library/lockfile paths, package and R/Bioconductor versions, and repository URLs |
| `R-ANALYSIS` | Help on stdout; completion messages and computation/validation errors on stderr; structured results only in explicit files | Scientific outputs are durable; direct R console is not | Paths, IDs, columns, thresholds, and candidate state in diagnostics |
| `SLURM-EMBED` | Human job/module/command context and embedded tool output split between configured `.out` and `.err`; not machine-readable | Conditional scheduler copy of bytes reaching job streams; no separate application receipt for console | Job/node/CWD/TMPDIR, references, outputs, commands, module/tool details, and previews |
| `SLURM-DELEGATE` | Human job/module/command context and delegated child stdout in `.out`; wrapper/child stderr in `.err`, with some diagnostic stderr intentionally merged to `.out` | Conditional scheduler copy contains delegated command and child recovery detail; no second application console log | Job context, environment paths, IDs, hashes, thresholds, module/tool versions, and arguments |
| `SLURM-PROBE` | Human environment, module, tool, or manifest-validation output split according to each wrapper; not machine-readable | Conditional scheduler copy is the principal diagnostic evidence | Host/CWD/TMPDIR, module set, tool paths/versions, manifest labels, and errors |
| `MAKE-LOCAL` | Make may echo non-`@` recipe commands unless `-s`; children emit human test/check progress, summaries, and failure captures | Direct use has no complete log; child frameworks may retain declared results or failure captures | Test names, temporary paths, assertions, and child diagnostics |
| `MAKE-MUTATE` | Make may echo recipes, followed by human restore/baseline-update progress and failures | Restored tools/libraries or coverage baseline are durable explicit operator mutations; no console log | Repository/library/install paths, versions, URLs, hashes, and diagnostics |
| `MAKE-OUTPUT` | Make may echo recipes; children emit human producer/renderer progress, while declared JSON, XML, coverage, fixture, or report files are separate machine outputs | Explicit output is durable but not a complete console log | Interpreter, repository, output, test, tool, report, and fixture paths plus diagnostics |
| `MAKE-INTERNAL` | Make may echo recipes plus human internal-lane output; no standalone user machine stream | Durability follows the orchestrator profile when selected by `all-checks` | Commands, test/tool paths, and dependency diagnostics |
| `MAKE-SUBMIT` | Make may echo recipes; `sbatch` result uses stdout and local submission failures use stderr | NORAD writes no submission receipt, so the job ID is ephemeral unless the operator captures it. Later scheduler files and accounting are conditional and environment-deferred | Export values, sample ID, job ID, and submission errors |
| `VALIDATION` | Default/serial quiet stdout has elapsed `PASS` lines and `SUMMARY`; stderr has `FAIL`/`INTERRUPTED`, retained-log paths, and failed-lane replay. Verbose mode merges child stderr into live child stdout | In quiet mode, successful lane logs are deleted, every interrupted running lane is retained but not replayed, and every nonzero lane observed in one completion poll is retained and replayed before remaining lanes are terminated. Verbose mode creates no per-lane temporary log to retain. Optional result JSON is a separate machine contract | Exact lane commands, tool/test/temp paths, dependency diagnostics, and arbitrary captured child output |
| `DOC-GATE` | Human/machine-like pass count and Git inspection on stdout; aggregated actionable failures on stderr; no declared machine stream | No durable log or receipt; exact link, anchor, dependency, and diagram failures are repair evidence | Repository-relative paths, card IDs, links, and cycles |
| `OP-FASTQ` | Human sample/read context and `PASS` on stdout; mismatch failures on stderr | No durable copy; normalized read-ID mismatch detail is operationally useful but ephemeral | FASTQ paths, sample ID, read counts, and normalized read IDs |
| `OP-STEP05` | TSV-shaped stdout and human summary/errors on stderr; intended output copy is unsafe because two identical truncating `tee` process substitutions concurrently target the same path | Best-effort output only, not a transactional durable contract. Existing writable output is silently replaced; no direct automated regression owns this behavior | Sample/job IDs and states, BAM/BAI paths and sizes, `SAMTOOLS` path, scheduler state, and output path |

### Per-surface crosswalk

`Trace` names the direct regression or consumer evidence. The detailed public
entry-point tables above remain the canonical case/independence roster; this
crosswalk adds output/log semantics without copying those matrices.

#### Python surfaces

| Surface | Profile | Trace | Exception or durable output |
| --- | --- | --- | --- |
| `build_artifact_index.py` | `PY-TXN` | CLI inventory; artifact-adapter and independent-golden suites | Artifact index, receipt, and declared evidence files |
| `build_run_summary.py` | `PY-TXN` | CLI inventory; run-summary and independent-golden suites | Run summary, projections, and receipt |
| `gtf_to_bed12.py` | `PY-CONVERT` | CLI inventory; `test_gtf_to_bed12.py` | Existing output replacement is a characterized defect |
| `reference_provenance.py` | `PY-TXN` | CLI inventory; provenance and publication-fault suites | Provenance report; incomplete-recovery defects remain characterized |
| `render_run_report.py` | `PY-REPORT` | CLI inventory; HTML and export suites | Renderer output and report assets |
| `render_run_report_bundle.py` | `PY-REPORT` | CLI inventory; export and shell-wrapper suites | Atomic report bundle and receipt |
| `restore_quarto.py` | `PY-RESTORE` | CLI inventory; Quarto-restore suite | Explicit tool restoration only |
| `runtime_preflight.py` | `PY-TXN` | CLI inventory; preflight and publication-fault suites | Preflight report; recovery defects remain characterized |
| `step_09c_scientific_validation.py` | `PY-TXN` | CLI inventory; Python and shell Step 09c suites | Scientific-review artifacts without evidence promotion |
| `storage_inventory.py` | `PY-TXN` | CLI inventory; storage and publication-fault suites | Inventory report; never performs retention action |
| `validate_artifact_contracts.py` | `PY-CHECK` | CLI inventory; schema and independent-golden suites | No validation receipt |
| `validate_manifest.py` | `PY-CHECK` | CLI inventory; manifest suite | No validation receipt |
| `validate_step_00a_star_index.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `00a` report file |
| `validate_step_00b_bed12.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `00b` report file; additional human context precedes TSV |
| `validate_step_00c_reference_sidecars.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `00c` report file |
| `validate_step_01_star_alignment.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `01` report file |
| `validate_step_02_canonical_bam.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `02` report file |
| `validate_step_02b_bam_qc.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `02b` report file |
| `validate_step_03_rseqc_orientation.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `03` report file |
| `validate_step_04_mark_duplicates.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `04` report file |
| `validate_step_05_split_ncigar.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `05` report file |
| `validate_step_06_orientation_outputs.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `06` report file |
| `validate_step_07_mpileup_outputs.py` | `PY-STEPVAL` | direct validator, roster, and publication-fault suites | Step `07` report file; real bcftools remains deferred |
| `validate_step_08_preprocessing_outputs.py` | `PY-STEPVAL` | direct validator, roster, publication-fault, and golden suites | Step `08` report file |
| `validate_step_09_cmh_outputs.py` | `PY-STEPVAL` | direct validator, CMH-oracle, roster, and publication-fault suites | Step `09` report file; statistic recomputation gap remains characterized |

#### Shell and R surfaces

| Surface | Profile | Trace | Exception or durable output |
| --- | --- | --- | --- |
| `render_run_report.sh` | `SH-LAUNCH` | CLI inventory; report shell and export suites | Report bundle; conditional scheduler copy only when job-wrapped |
| `step_09c_scientific_validation.sh` | `SH-LAUNCH` | CLI inventory; Step 09c shell/Python suites | Scientific-review artifacts; conditional scheduler copy when job-wrapped |
| `step_00c_prepare_gatk_reference.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | Reference sidecars |
| `step_01_star_align.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | BAM plus STAR-native diagnostic logs |
| `step_02_sort_index_bam.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | BAM/BAI |
| `step_02b_bam_qc.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | QC output |
| `step_03_infer_strandedness_and_orientation.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | RSeQC output; non-executable file-mode defect |
| `step_04_mark_duplicates.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | BAM/BAI/metrics; non-executable file-mode defect |
| `step_05_split_n_cigar_reads.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | BAM/BAI; non-executable file-mode defect |
| `step_06_split_bam_by_read_orientation.sh` | `SH-STAGE` | CLI inventory; same-named shell suite | BAM/BAI pairs and count table |
| `step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `SH-COHORT` | CLI inventory; same-named shell suite | VCFs and receipt; real bcftools deferred |
| `step_08_vcf_preprocessing.sh` | `SH-COHORT` | CLI inventory; shell and guarded real-R suites | Three-output transaction |
| `step_09_cmh_editing_site_calling.sh` | `SH-COHORT` | CLI inventory; shell, guarded real-R, and CMH-oracle suites | Six-output transaction |
| `check_r_environment.R` | `R-ENV` | local-R shell suite and guarded `r-check` | Any positional argument, including `--help`, is rejected |
| `restore_r_environment.R` | `R-ENV` | local-R shell suite and explicit `r-restore` | No help mode; no-argument execution is operator mutation |
| `step_08_vcf_preprocessing.R` | `R-ANALYSIS` | real-R runner/fixtures and shell owner | Rscript-only file mode |
| `step_09_cmh_editing_site_calling.R` | `R-ANALYSIS` | real-R runner/fixtures, shell owner, and CMH oracle | Rscript-only file mode |
| `.Rprofile` opted-in activation | `R-ENV` | local-R shell suite and guarded Make lanes | Indirect startup hook, not a public command; invalid controls stop, and delegated `renv` activation may emit dependency-owned output |

#### Scheduler surfaces

All 16 wrappers configure `logs/%x-%j.out` and `logs/%x-%j.err`, and the
central SLURM suite protects those directives. These paths are relative to the
submission context, and `logs/` must exist before SLURM opens them; an in-job
`mkdir -p logs` is too late to satisfy that precondition. The files are
therefore conditional scheduler copies, not an unconditional application
run/attempt logging contract.

| Surface | Profile | Trace | Exception or durable output |
| --- | --- | --- | --- |
| `step_00a_build_novogene_star_index.slurm` | `SLURM-EMBED` | central SLURM suite | Embedded compute; caller-CWD and cluster runtime deferred |
| `step_00b_gtf_to_bed12.slurm` | `SLURM-EMBED` | central SLURM suite | Embedded conversion/sort and BED preview; submit-CWD required |
| `step_00c_prepare_gatk_reference.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Bash 3.2 dry-run defect characterized |
| `step_01_star_align.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Default dry-run placeholder side effects characterized |
| `step_02_sort_index_bam.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Dry-run directory and Bash 3.2 defects characterized |
| `step_02b_bam_qc.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Submit-CWD, dry-run directory, and Bash 3.2 defects characterized |
| `step_03_infer_strandedness_and_orientation.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Fallback submit-CWD and Bash 3.2 defect characterized |
| `step_04_mark_duplicates.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Bash 3.2 defect characterized |
| `step_05_split_n_cigar_reads.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Bash 3.2 defect; comments preserve pre-submit `logs/` requirement |
| `step_06_split_bam_by_read_orientation.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Bash 3.2 defect characterized |
| `step_07_bcftools_mpileup_by_chrom_and_strand.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Real cluster/runtime deferred |
| `step_08_vcf_preprocessing.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Real cluster/runtime deferred |
| `step_09_cmh_editing_site_calling.slurm` | `SLURM-DELEGATE` | central SLURM and delegated shell suites | Real cluster/runtime deferred |
| `template.slurm` | `SLURM-PROBE` | central SLURM suite | Mode-less probe; module-list stderr differs from delegated wrappers |
| `tool_check.slurm` | `SLURM-PROBE` | central SLURM suite | Required and optional probes have distinct failure policies |
| `validate_manifest.slurm` | `SLURM-PROBE` | central SLURM and manifest suites | Validation has no separate receipt |

#### Make, validation, and operational surfaces

| Surface | Profile | Trace | Exception or durable output |
| --- | --- | --- | --- |
| `test` | `MAKE-LOCAL` | literal Make golden; complete Python suite | Pytest capture is failure-visible, not a durable log |
| `validation-shell-contracts` | `MAKE-INTERNAL` | literal Make golden; selected shell/Python owners | Under `all-checks`, follows `VALIDATION` retention |
| `shell-test` | `MAKE-LOCAL` | literal Make golden; selected shell/Python owners | No direct durable log |
| `real-r-test` | `MAKE-LOCAL` | literal Make golden; real-R runners | Ambient-runtime diagnostic, not guarded evidence |
| `r-restore` | `MAKE-MUTATE` | literal Make golden; local-R shell suite | Explicit guarded library mutation |
| `r-check` | `MAKE-LOCAL` | literal Make golden; local-R shell suite | No direct durable log |
| `local-real-r-test` | `MAKE-LOCAL` | literal Make golden; guarded real-R runners | No direct durable log |
| `quarto-restore` | `MAKE-MUTATE` | literal Make golden; Quarto-restore suite | Explicit tool restoration |
| `report-test` | `MAKE-LOCAL` | literal Make golden; report suites | No direct durable log |
| `validation-report-runtime` | `MAKE-OUTPUT` | literal Make golden; pinned runtime suites | Explicit JUnit XML, not complete console |
| `demo-report` | `MAKE-OUTPUT` | literal Make golden; fixture/report/wrapper suites | Ignored synthetic bundle, not production evidence |
| `python-coverage-measure` | `MAKE-OUTPUT` | literal Make golden; coverage tests | Coverage JSON/current snapshot |
| `python-coverage-check` | `MAKE-LOCAL` | literal Make golden; coverage tests | Coverage work files persist until operator cleanup |
| `python-coverage-baseline-update` | `MAKE-MUTATE` | literal Make golden; coverage tests | Explicit tracked baseline mutation |
| `validation-python-coverage` | `MAKE-INTERNAL` | literal Make golden; coverage and orchestrator tests | Under `all-checks`, follows `VALIDATION` retention |
| `validation-guarded-r` | `MAKE-INTERNAL` | literal Make golden; local-R and orchestrator tests | Under `all-checks`, follows `VALIDATION` retention |
| `validation-static` | `MAKE-INTERNAL` | literal Make golden; manifest and orchestrator tests | Under `all-checks`, follows `VALIDATION` retention |
| `validate` | `MAKE-LOCAL` | literal Make golden; manifest suite | No durable validation receipt |
| `smoke` | `MAKE-LOCAL` | literal Make golden | Syntax output only on failure |
| `lint` | `MAKE-LOCAL` | literal Make golden | Compile artifacts suppressed/ignored by policy |
| `all-checks` | `VALIDATION` | literal Make golden; validation-orchestrator suite | Optional result JSON; per-lane failure/interruption retention described above |
| `demo-step03-dry-run` | `MAKE-SUBMIT` | literal Make golden | Scheduler submission remains environment-deferred |
| `demo-step03` | `MAKE-SUBMIT` | literal Make golden | Scheduler submission remains environment-deferred |
| `tests/tools/run_validation.py` | `VALIDATION` | validation-orchestrator suite; `all-checks` consumer | Internal executable selected by Make, not a separate public workflow claim |
| Inline documentation gate in `RUNBOOK.md` | `DOC-GATE` | repository documentation gate; no focused extracted owner | Embedded implementation remains pending `DOC-GATE-01` |
| Direct shell/R test runners selected by Make | `MAKE-LOCAL` | their own assertions and Make target selection | Temporary child captures normally removed |
| `tests/data_checks/check_fastq_pairs.sh` | `OP-FASTQ` | no direct automated regression or current runbook consumer found | Supported status requires later review if retained |
| `tests/data_checks/validate_step05_outputs.sh` | `OP-STEP05` | recorded runbook inspection; no direct automated regression | Duplicate-`tee` and silent-replacement defects characterized |

### Durable-copy and evidence-role boundary

| Current durable surface | Completeness and role | Retention behavior |
| --- | --- | --- |
| `logs/%x-%j.out` and `logs/%x-%j.err` | Conditional scheduler-level copy of bytes reaching each wrapper's job streams; job-scoped, not application-attempt-scoped; actual capture is environment-deferred | Ignored by Git; repository defines no automatic deletion or retention policy |
| STAR `Log.out`, `Log.progress.out`, and `Log.final.out` | Tool-native alignment diagnostics, not a wrapper/script console copy | Workflow output ownership; no automatic NORAD deletion |
| Validation reports, QC, receipts, manifests, summaries, metrics, scientific-evidence records, and report bundles | Durable machine/evidence artifacts preserving declared facts and transaction markers, not complete diagnostic logs | Producer-specific no-clobber/publication/rollback rules; not governed as application logs |
| Artifact roles `runtime_log` and `cluster_log` | Exact role, path, hash, and relationship fields are required evidence components for specific runtime/cluster claims; they are not synonymous with a future application log | Source preservation remains the operator or evidence owner's responsibility, with no automatic retention; merely creating an application log cannot satisfy or promote these roles |
| System temporary-directory `norad-validation-<lane>-*.log` (the exact printed retained-log path is authoritative) | In default/serial quiet mode, complete merged output is retained per failed lane observed before cancellation and per running lane on interruption; failure replays content, interruption does not. Verbose mode creates no per-lane temporary log | Successful quiet-mode logs are deleted; retained logs require explicit operator preservation before platform cleanup or expiry |
| Optional result JSON, JUnit XML, coverage JSON/snapshots, and Step 05 inspection TSV | Machine-readable result summaries, not complete console logs; Step 05 TSV is best-effort because of the duplicate-`tee` defect | Produced only at explicit paths; operator-owned retention, with no transactional guarantee for the Step 05 TSV |

The following are candidates for LOG-02 and later implementation, not approved
changes:

- reduce repeated resolved paths, modes, commands, module lists, tool versions,
  and publication plans across nested Make, SLURM, shell, Python, and R layers;
- keep exact commands, run/attempt IDs, locks, hashes, input sets, publication
  order, rollback/cleanup failures, failed evidence, and evidence-boundary text
  in complete durable logs even if normal console output becomes concise;
- provide run/attempt-scoped durable application logs for direct local
  executable runs instead of relying on scheduler capture, output artifacts,
  or failure-only validation logs;
- separate the 13 validators' report TSV from human status text and keep child
  stderr distinct during verbose validation without changing artifacts,
  validation, exits, or transaction behavior;
- define redaction and avoidance rules before exact commands or arbitrary child
  output become durable application logs;
- replace complete quiet-mode failed-lane replay with a concise actionable tail
  only after the complete retained-log and recovery-path contract is defined;
- add direct characterization for the two operational checks and extract a
  focused documentation-gate owner if those surfaces remain supported.

### Validation-efficiency characterization

Phase `01aa` left the reviewed baseline file and its non-regression policy
unchanged. The final executable state ran 463 Python tests with 17 expected
conditional skips and measured 26 production modules, 8,542/10,551 lines, and
3,074/4,404 branches. Serial and every characterized parallel candidate had
identical per-file counts, totals, and coverage digest.

The package separately characterized one through four Python workers and one
through four top-level lane slots. It enabled two Python workers and three
top-level slots only after exceeding the required improvement thresholds and
selecting the smallest candidates within 5% of the fastest medians. Three
consecutive default gates reproduced exact serial result/coverage equality.
Controlled nonzero failure and `SIGINT` tests also proved exit propagation,
retained failed output, process-group cleanup, handler restoration, and no
stale owned logs. Exact timings and the current evidence boundary are recorded
in [`../operations/HANDOFF.md`](../../operations/HANDOFF.md).

## Cross-cutting risk matrix

| Risk area | Current regression evidence | Independence | Disposition |
| --- | --- | --- | --- |
| Public help, dry-run, execute, malformed input, and exit behavior | focused entry-point suites plus the exact Python/shell/R/Make inventory in `tests/test_public_cli_contracts.py` | mostly independent | `TG-04` complete; preserve explicit legacy mode/help/overwrite exceptions rather than normalizing them |
| Native output transactions | Step `02`, `05`–`09`, Step `09c`, adapters, summaries, report bundle rollback suites, and Phase `01b` publisher fault injection | mixed | `TG-02` characterization complete; preserve labeled production gaps for reviewed correction |
| Seven-column validation report schema | every `tests/test_validate_step_*` module plus adapter propagation fixtures | mixed | preserve |
| Exact per-step check rosters | test-only literal ordered rosters, all 13 live producer-output suites, shared report-consumer mutations, and artifact-adapter mutations | independent characterization | `TG-03` complete; preserve the characterized order-insensitive shared validator and wrong-unique/reordering adapter defects for separate correction review |
| Public JSON Schemas and table headers | schema-contract suite, artifact/run-summary suites, Step `09c`, per-step validators, and literal path/header oracles in `tests/fixtures/independent_contract_goldens/` | independent characterization plus integrated coverage | `TG-06` complete for representative critical schemas and exact ordered headers; preserve the broader integrated suites |
| Status vocabularies and state transitions | schema, adapter, Step `09c`, summary, report negative cases, and independent named-constant/transition mutations | independent characterization plus integrated coverage | `TG-06` complete for critical public states, Step `09c` aggregation, and shared science-policy projection |
| Deterministic JSON/TSV/QC/report bytes and ordering | retry/fixed-time tests, explicit ordered inventories, renderer comparisons, and exact independent canonical JSON, UTF-8 TSV, and report-receipt bytes | independent characterization plus integrated coverage | `TG-06` complete for bounded critical bytes; retain broad producer-integrated transaction fixtures |
| Locks, signals, rollback, cleanup, and recovery evidence | later shell workflows, artifact/summary/report transactions, Step `09c`, and shared/ancillary publisher fault injection | mixed | `TG-02` characterization complete; do not universalize action-local mechanisms or mistake a characterized gap for a safe contract |
| Stable hashes and input mutation | Step `07`–`09`, Step `09c`, artifact/summary/report, provenance/preflight/storage, and shared-validator snapshot suites | mixed | `TG-02` characterization complete; digest-backed shared snapshots remain a reviewed production correction |
| Unrelated-file immunity | central public-CLI help/failure matrix, `gtf_to_bed12.py`, Step `07`–`09`, Step `09c`, adapter/summary/report suites | independent/mixed | `TG-04` applicable CLI omissions complete; preserve deeper transaction suites |
| Symlink, hardlink, and directory-identity substitution | adapter, summary, report, restore, preflight/storage/provenance, and shared-validator publication suites | independent | `TG-02` characterization complete; preserve |
| Computational/scientific evidence-state boundaries | schemas, Step `09c`, adapters, summary, reports, literal banner/status oracles, and shared computational-scope mappings | independent characterization plus integrated coverage | `TG-06` complete; reserved readiness remains excluded and no evidence state is promoted |
| Direct execution, arbitrary CWD, and SLURM delegation | exact public script/job modes, arbitrary-CWD CLI matrix, exact mocked submit-CWD/delegation matrix, and existing workflow suites | independent | `TG-04` and local `TG-05` characterization complete; real scheduler/module/runtime evidence remains environment-deferred |
| Step `09` CMH statistic, p-value, odds ratio, and estimability | independent Python oracle, fixed corpus, direct committed-R comparison, and coordinated-corruption rejection; production validator still checks type/range and BH from reported p-values | independent characterization plus producer-coupled validator | `TG-01` characterization complete; compatible production-validator correction remains separately reviewed |
| `_run_summary_science.py` policy projection | artifact, summary, Step `09c`, report suites, and independent recorded/pending/absent decision, limitation, and computational-status transitions | independent characterization plus integrated coverage | `TG-06` complete; preserve exact provisional evidence language |

## Golden-output and fixture independence

| Fixture/output family | Classification | Evidence and required action |
| --- | --- | --- |
| `tests/fixtures/artifact_schema_v1/valid/*.json` | mixed | fixed documents remain useful integrated examples; `TG-06` now adds independently spelled critical schema paths, enums, versions, and evidence-boundary constants plus a direct mutation case |
| `tests/fixtures/artifact_adapters_v1/build_fixture.py` | producer-coupled | retain its broad end-to-end transactions; `TG-06` supplements it with literal artifact-index/validation headers and exact canonical JSON bytes rather than duplicating the large builder |
| `tests/fixtures/artifact_run_summary_v1/build_fixture.py` | mixed | retain its broad projections; `TG-06` supplements it with an exact run-summary header and independent canonical JSON/TSV/receipt byte oracles |
| `tests/fixtures/step09c/build_fixture.py` | mixed | retain the integrated package; `TG-06` adds literal review/evidence headers, status constants, seven aggregation cases, and shared policy-transition oracles |
| `tests/fixtures/report_html_v1/run_html_core.py` and report fixtures | producer-coupled | retain real-renderer end-to-end tests; `TG-06` adds exact independent report-receipt projection bytes and schema banner boundaries without duplicating rendered reports |
| Step `00a`–`09` validation report fixtures | mostly independent | direct TSV/status assertions plus test-only literal ordered rosters complete `TG-03`; bounded canonical JSON/TSV and validation-header independence now complete `TG-06` without duplicating every fixture |
| Step `07` mocked VCF/receipt outputs | mixed | good transaction and manifest coverage; real bcftools output remains a deferred runtime gate |
| Step `08` semantic outputs | mixed plus independent header characterization | guarded real-R fixtures remain the semantic evidence; `TG-06` independently spells the critical shared Step `09c` review/evidence headers and rejects header mutations |
| Step `09` semantic outputs | mixed | `TG-01` now derives an independent oracle directly from DP/AD and proves coordinated corruption detectable; the production validator remains unchanged |
| HTML/PDF/report receipts | mixed | real pinned renderer and independent structural readers are exercised; production reports remain absent |

Independent duplication is intentional where it is the only way to detect a
shared producer/test defect. The hardening work must supplement, not replace,
the integrated fixtures.

## Evidence-derived characterization gaps

The baseline matrix yielded six cohesive gaps. `TG-01` through `TG-06` are now
characterized; the final row-by-row sufficiency decision remains owned by
`TEST-01Z` and must not infer readiness from these completions alone.

| Gap | Scope | Exit evidence |
| --- | --- | --- |
| `TG-01` | Independent Step `09` CMH oracle | recompute estimability, continuity-corrected statistic, p-value, and common odds ratio from DP/AD; coordinated corruption fails while valid real-R fixture passes |
| `TG-02` | Validation publication and recheck faults | shared validator publication tests cover staged validation, prior-output validation, input/output identity changes, rename/fsync failures, rollback, cleanup, and retained recovery evidence without changing public behavior |
| `TG-03` | Exact validation check rosters | every step has a fixed independent ordered roster; missing, duplicate, extra, and reordered checks fail at the correct boundary |
| `TG-04` | Public CLI and exit contracts | every Python, shell, and Make entry point has an explicit applicable-case decision for help, direct/arbitrary-CWD use, malformed input, side effects, unrelated files, and exit propagation |
| `TG-05` | SLURM wrapper contracts | every job has a focused applicable-case decision for mode, modules, CWD, delegation, arguments, output validation, and exit propagation; legacy exceptions are characterized, not refactored |
| `TG-06` | Independent goldens and mutation resistance | complete: critical schema paths, ordered headers, serialized bytes, status transitions, evidence boundaries, and shared policy rules fail when named production values change without the independent expectation |

### Completed `TG-01` characterization

Implementation commit `bef0f97` completes the test-only `TG-01`
characterization. `tests/tools/step_09_cmh_oracle.py` does not import
production NORAD modules and derives missing/low-coverage/degenerate/tested
status, the two-sided continuity-corrected stratified CMH statistic and
p-value, common odds ratio, and global BH adjustment from paired DP/AD counts.
The fixed corpus covers the required valid, zero-cell, all-zero, missing,
low-coverage, infinite-odds, rounding, multi-stratum, global-BH, and
coordinated-corruption boundaries.

Twenty focused Python oracle tests passed. The guarded Step `09` real-R suite
loads only the committed CMH function and constants needed for a direct corpus
comparison. The complete local implementation gate passed with 452 Python
tests, 17 expected conditional skips, unchanged 80.8701% line and 69.6956%
branch coverage across 26 production Python modules, every shell suite,
guarded R environment and Step `08`/`09` real-R checks, and 143 pinned
report-runtime tests.

This closes the characterization package, not the executable validator gap.
`validate_step_09_cmh_outputs.py` still does not replace reported CMH fields
with count-derived expectations. That compatible correction remains subject
to the reviewed Phase `02`/`03` plan and must preserve check IDs, statuses,
thresholds, output bytes, scientific language, and the Step `09` method.

### Completed `TG-02` characterization

Implementation commit `f7e00e4` adds 28 test-only fault cases: 18 exercise
the single publisher imported by all 13 step validators, and 10 exercise the
distinct reference-provenance, runtime-preflight, and storage-inventory
publishers. The shared suite freezes the exact validator inventory and covers
same-size/restored-mtime mutation, inode and symlink substitution, first and
replacement publication, staged and prior validation, fsync and move faults,
post-publication validation, rollback, cleanup, a late foreign final, and
`KeyboardInterrupt`. The ancillary cases cover input rechecks, multi-file
rollback, lock/stage fsync, lock cleanup, and incomplete restoration.

The tests deliberately label rather than normalize current unsafe behavior.
The shared metadata snapshot cannot detect changed bytes when size and mtime
are restored; a late foreign final can be deleted; and incomplete rollback can
lose its lock without a recovery marker. Reference and storage multi-file
restoration can likewise leave backups without lock/marker protection.
Runtime preflight can retain a lock and descriptor after lock fsync failure,
leave an unprotected backup after failed restoration, or report success while
an owned lock remains after cleanup failure. These are characterized Phase
`03` correction candidates, not accepted recovery contracts.

The 56 directly affected tests passed five serial repetitions and one
two-worker xdist run. Separate covered serial and xdist executions had
identical per-file coverage (1,367/10,551 lines and 325/4,404 branches). The
broader 132-test validator/provenance/preflight/storage regression passed. The
canonical complete gate passed in 153.161 seconds with 491 Python passes, 17
expected skips, all shell contracts,
guarded R checks and real-R fixtures, and 17 pinned report-runtime passes. A
retained Python-lane measurement recorded 8,566/10,551 lines and 3,103/4,404
branches across the same 26 modules, with snapshot digest
`a59ee1897b4b8a0d02881c3c5070f12f47f0a6b1067cd883624db88ad8056137`.
The reviewed non-regression baseline was not rewritten merely because this
test-only package increased coverage.

This closes `TG-02` characterization only. It changes no publisher,
validator, report, workflow, scientific, runtime, or cluster behavior.

### Completed `TG-03` characterization

Implementation commit `8d58fc6` adds a test-only literal ordered roster for
all 13 live `validate_step_*` entry points. Every successful producer test now
compares emitted `check_id` values and order with that independent expectation.
The separate roster suite proves that missing, extra, duplicate, and reordered
mutations fail the test oracle and that the literal script inventory neither
omits nor invents a live validator.

The tests preserve two production defects rather than correcting them. The
shared validation-report consumer rejects missing, extra, and duplicate IDs
but accepts an exact-ID reorder because it compares sets. The artifact adapter
also rejects row-count and duplicate-ID mutations, but accepts reordered rows
and a wrong-but-unique safe check ID. Those behaviors are characterized defects,
not approved contracts or evidence of a valid validation roster.

The 250-test focused validator/adapter regression passed. The de-duplicated
complete local gate then passed static preflight, all shell contracts, the
checked Python line/branch non-regression baseline, the guarded R environment
and Step `08`/`09` real-R fixtures, and the pinned report runtime in 164.635
seconds. No production, schema, workflow, scientific, runtime, or cluster
behavior changed.

### Completed `TG-04` characterization

Implementation commit `a003065` adds a test-only exact inventory of 25 public
Python entry points, 13 shell workflows, four R entry points, and 23 callable
Make targets. It protects Python help and unknown-option failure, shell help
and missing-argument failure, arbitrary working directories, working-directory
side-effect freedom, executable versus interpreter-only file modes, and exact
Make-target applicability categories plus side-effect-free command expansion.
Existing focused suites remain the owners of entry-point-specific dry-run,
execute, malformed-input, publication, and child-exit behavior.

The tests preserve rather than normalize current exceptions. Seventeen Python
entry points are interpreter-only, while direct execution of the eight
executable Python files depends on the caller's shebang-selected environment.
Steps `03`, `04`, and `05` shell workflows are non-executable and require
explicit `bash`. The two environment-management R entry points reject every
positional argument and have no help mode; the two analysis R files are
Rscript-only. `gtf_to_bed12.py` silently replaces its declared existing output
while leaving an unrelated file unchanged.

The 116-test focused Python CLI/converter set, guarded local-R shell contract,
and Step `08` and `09` real-R fixtures passed. The de-duplicated complete local
gate then passed static preflight, shell contracts, checked Python line/branch
non-regression, guarded R, and pinned report runtime in 164.719 seconds. No
production, schema, workflow, Makefile, dependency, scientific, runtime, or
cluster behavior changed.

A later Phase `0` adversarial review found two gaps behind that completion
claim: Make targets were dry-expanded but not compared with a literal oracle,
and the environment-management R entry points were source-inspected but not
executed on their rejection paths. Test-only correction `0c64d1a` adds one
committed 23-target dry-expansion fixture, rejects a deliberate recipe
mutation, and directly executes `check_r_environment.R` and
`restore_r_environment.R` with both `--help` and an arbitrary positional
argument from an empty working directory. It never invokes no-argument restore
behavior. The first final review reproduced a bare-`make` portability gap;
follow-up `44d3255` removes caller recursion state and adds literal bare and
absolute `make` and `gmake` normalization cases. The second review reproduced
ambient `MAKEFILES` contamination; `fd98244` bounds the expansion environment
and directly tests hostile Make state. The corrected 111-case public-contract
file and guarded local-R contract passed, followed by the reopened complete
local gate in 207.451 seconds. No production or public behavior changed.

### Completed `TG-05` characterization

Implementation commit `9a4fb09` adds one exact test-only matrix for all 16
tracked SLURM and utility jobs. Eleven wrappers have explicit dry-run, execute,
and invalid-mode decisions; Steps `00a` and `00b` retain implicit embedded
compute; `template.slurm`, `tool_check.slurm`, and `validate_manifest.slurm`
retain their mode-less probe or validation roles. Four jobs are executable
files and 12 remain interpreter/submission-only. The tests freeze exact SBATCH
directives without changing resource policy.

Every dynamic case replaces modules, delegated scripts, Rscript, Java, STAR,
samtools, GATK, bcftools, Python, and bedtools with local stubs. The matrix
proves exact module calls and failure policy, caller/required/fallback submit
CWD behavior, exact delegated arguments, output-validation ownership, and
child-exit propagation. No `sbatch`, scheduler, CSU module system, real
workflow binary, dependency restore, or production input is used.

The package preserves several differences rather than normalizing them. Steps
`00c`, `02`, `02b`, `03`, `04`, `05`, and `06` abort before their default
dry-run child under Bash 3.2 because an empty `execute_args` array is expanded
under `set -u`; execute mode is still reachable and newer Bash behavior is
version-conditioned. Step `01` default dry-run creates placeholder input files
and an index directory. Steps `02` and `02b` create their output directory in
dry-run. Six jobs use caller CWD, two require `SLURM_SUBMIT_DIR`, and eight use
its fallback form. Module failure tolerance and wrapper-level output checks
also remain deliberately non-uniform.

All 113 focused mocked-wrapper tests passed. The de-duplicated complete local
gate passed static preflight, shell contracts, checked Python line/branch
non-regression, guarded R, and pinned report runtime in 168.770 seconds. No
production job, script, Makefile, schema, dependency, resource, scientific,
runtime, cluster, or biological behavior changed. All cluster/runtime rows
remain environment-deferred rather than cluster-proven.

### Completed `TG-06` characterization

Implementation commit `dcb5dd4` and targeted shared-policy correction
`1986898` add one compact literal fixture family and 22 focused tests. The
fixtures do not import production constants or use a producer-backed builder.
They independently spell representative paths and values across all five
public artifact schemas; exact artifact-index, validation-report, run-summary,
report-receipt, review-plan, and evidence-manifest headers; canonical UTF-8
JSON and TSV bytes; one exact report-receipt projection; critical scientific
status vocabularies; and seven evidence-aggregation transitions.

The shared-science oracle independently locks recorded, pending, and absent
decision projections, active-to-open limitation projection, and local,
runtime, and cluster computational-evidence status mappings. Deliberate
mutations of one public schema boundary, four named headers, five named status
constants, canonical JSON and receipt serialization, the decision-dimension
set, and the computational-scope policy are rejected while unmodified outputs
pass. Opaque fixture provenance and evidence limits are recorded beside the
fixtures; the TSV files contain no embedded commentary.

The final de-duplicated complete local gate passed static preflight in 0.110
seconds, shell contracts in 44.963 seconds, checked Python line/branch
non-regression in 177.681 seconds, guarded R in 170.644 seconds, and pinned
report runtime in 135.134 seconds; total elapsed time was 180.219 seconds. No
production module, schema, workflow, dependency, scientific policy, runtime,
cluster, or biological behavior changed.

## TEST-01Z closed behavior-contract matrix

TEST-01Z closes all 88 rows in the public-entry-point, cross-cutting-risk, and
fixture-independence tables above. A row can contain more than one atomic
behavior, so mixed rows preserve each applicable label rather than allowing a
local contract to hide a defect or environmental deferral. The only labels
used are `preserved contract`, `characterized defect`, `undefined — decision
required`, and `environment-deferred`.

Independent evidence keys used below are:

- **CLI** — literal entry-point, file-mode, help/failure, arbitrary-CWD, and
  Make-target expectations in `tests/test_public_cli_contracts.py`, the
  committed `tests/fixtures/public_cli_contracts/` oracle, plus the row's
  named direct regression owner;
- **FAULT** — independent mutation/fault injection in
  `tests/test_validation_publication_faults.py` and the named provenance,
  preflight, storage, transaction, and rollback suites;
- **ROSTER** — literal live-validator inventory and ordered expectations in
  `tests/validation_roster_expectations.py` and
  `tests/test_validation_check_rosters.py`;
- **GOLD** — literal schema, ordered-header, canonical-byte, status, evidence,
  and shared-policy oracles in `tests/test_independent_contract_goldens.py`;
- **CMH** — count-derived independent Step `09` oracle and fixed R comparison
  in `tests/test_step_09_cmh_oracle.py` and its committed corpus;
- **SLURM** — literal 16-job matrix and generated local fakes in
  `tests/test_slurm_wrapper_contracts.py`;
- **REAL-R** — guarded fixed Step `08`/`09` R fixtures and their direct shell
  owners;
- **REPORT** — independent HTML/PDF structural readers, fixed evidence banners,
  exact receipt golden, and pinned real-renderer regression owners;
- **GATE** — checked Python coverage, shell contracts, guarded R, and pinned
  report runtime from the final TEST-01F gate and the TEST-01Z coverage refresh;
- **ENV** — the reviewed evidence boundary in this document, RA-025, and
  `HANDOFF.md`; it is a disposition, not local or cluster proof.

### Python rows (25)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| `build_artifact_index.py` | `preserved contract`; `characterized defect` | CLI + GOLD + FAULT + ROSTER protect public transactions and bytes; the reordered/wrong-unique roster acceptance remains a labeled adapter defect. |
| `build_run_summary.py` | `preserved contract` | CLI + GOLD + FAULT + REPORT protect publication, canonical projections, shared science policy, and evidence boundaries. |
| `gtf_to_bed12.py` | `preserved contract`; `characterized defect` | CLI and the direct converter suite protect exact bytes/CWD behavior; silent replacement of the declared existing output remains a defect. |
| `reference_provenance.py` | `preserved contract`; `characterized defect` | CLI + FAULT protect its normal transaction and independently freeze incomplete-rollback recovery gaps. |
| `render_run_report.py` | `preserved contract` | CLI + REPORT protect local render inputs, outputs, banners, and failure behavior. |
| `render_run_report_bundle.py` | `preserved contract` | CLI + REPORT + GOLD + FAULT protect bundle publication and exact receipt behavior; low internal line coverage alone is not an undefined behavior row. |
| `restore_quarto.py` | `preserved contract` | CLI and the direct restore suite protect the supported pinned local restore; unsupported platforms are outside the declared contract. |
| `runtime_preflight.py` | `preserved contract`; `characterized defect`; `environment-deferred` | CLI + FAULT protect normal publication and named lock/rollback defects; CSU runtime remains ENV. |
| `step_09c_scientific_validation.py` | `preserved contract`; `environment-deferred` | CLI + GOLD + FAULT protect local synthetic review transactions and reserved evidence states; production science review remains ENV. |
| `storage_inventory.py` | `preserved contract`; `characterized defect`; `environment-deferred` | CLI + FAULT protect normal inventory publication and incomplete-restoration defects; CSU storage/quota execution remains ENV. |
| `validate_artifact_contracts.py` | `preserved contract` | CLI + GOLD and the direct schema suite protect critical public schemas, headers, status, and evidence boundaries. |
| `validate_manifest.py` | `preserved contract` | CLI and the direct manifest suite protect exact parsing, diagnostics, and exit behavior. |
| `validate_step_00a_star_index.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_00b_bed12.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_00c_reference_sidecars.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_01_star_alignment.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_02_canonical_bam.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_02b_bam_qc.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_03_rseqc_orientation.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_04_mark_duplicates.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_05_split_ncigar.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_06_orientation_outputs.py` | `preserved contract`; `characterized defect` | ROSTER + FAULT and its direct suite protect exact checks and independently freeze shared publisher defects. |
| `validate_step_07_mpileup_outputs.py` | `preserved contract`; `characterized defect`; `environment-deferred` | ROSTER + FAULT protect the local validator and publisher defects; real bcftools/cluster evidence remains ENV. |
| `validate_step_08_preprocessing_outputs.py` | `preserved contract`; `characterized defect`; `environment-deferred` | ROSTER + FAULT + GOLD + REAL-R protect local validation and shared publisher defects; production/cluster execution remains ENV. |
| `validate_step_09_cmh_outputs.py` | `preserved contract`; `characterized defect`; `environment-deferred` | ROSTER + FAULT + CMH + REAL-R protect local semantics; non-recomputation of reported CMH fields remains a validator defect and production/cluster scientific changes remain ENV. |

### Shell rows (13)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| `render_run_report.sh` | `preserved contract` | CLI + REPORT + FAULT protect delegation, CWD, transaction, bytes, and exits. |
| `step_00c_prepare_gatk_reference.sh` | `preserved contract` | CLI and its direct shell suite protect dry-run, execute, validation, rollback, and exits. |
| `step_01_star_align.sh` | `preserved contract` | CLI and its direct shell suite protect dry-run, execute, inputs, and exits. |
| `step_02_sort_index_bam.sh` | `preserved contract` | CLI + FAULT and its direct shell suite protect paired publication and rollback. |
| `step_02b_bam_qc.sh` | `preserved contract` | CLI and its direct shell suite protect exact input/index/output behavior. |
| `step_03_infer_strandedness_and_orientation.sh` | `preserved contract`; `characterized defect` | CLI and its direct suite protect invocation/delegation; its non-executable file mode requiring explicit `bash` remains a defect. |
| `step_04_mark_duplicates.sh` | `preserved contract`; `characterized defect` | CLI and its direct suite protect invocation/delegation; its non-executable file mode requiring explicit `bash` remains a defect. |
| `step_05_split_n_cigar_reads.sh` | `preserved contract`; `characterized defect` | CLI + FAULT and its direct suite protect transactions; its non-executable file mode requiring explicit `bash` remains a defect. |
| `step_06_split_bam_by_read_orientation.sh` | `preserved contract` | CLI + FAULT and its direct suite protect exact multi-output publication and rollback. |
| `step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `preserved contract`; `environment-deferred` | CLI and its mocked-bcftools transaction suite protect local behavior; real bcftools/cluster evidence remains ENV. |
| `step_08_vcf_preprocessing.sh` | `preserved contract`; `environment-deferred` | CLI + REAL-R + FAULT protect local transactions and semantics; production/cluster execution remains ENV. |
| `step_09_cmh_editing_site_calling.sh` | `preserved contract`; `environment-deferred` | CLI + REAL-R + CMH + FAULT protect local transactions and semantics; production/cluster scientific execution remains ENV. |
| `step_09c_scientific_validation.sh` | `preserved contract`; `environment-deferred` | CLI + GOLD + FAULT protect local review publication; production science review remains ENV. |

### R rows (4)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| `check_r_environment.R` | `preserved contract`; `characterized defect`; `environment-deferred` | CLI executes real `--help` and arbitrary-argument rejection from an empty CWD, while guarded environment checks protect dependency validation; absence of help remains a defect and CSU availability remains ENV. |
| `restore_r_environment.R` | `preserved contract`; `characterized defect` | CLI executes real rejection paths without invoking no-argument restore, and the explicit restore contract protects operator-only mutation; absence of help remains a defect. |
| `step_08_vcf_preprocessing.R` | `preserved contract`; `characterized defect`; `environment-deferred` | CLI + REAL-R protect local semantics; Rscript-only file mode remains a defect and production-scale/cluster execution remains ENV. |
| `step_09_cmh_editing_site_calling.R` | `preserved contract`; `characterized defect`; `environment-deferred` | CLI + REAL-R + CMH protect local semantics; Rscript-only file mode remains a defect and production-scale/cluster execution remains ENV. |

### SLURM rows (16)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| `step_00a_build_novogene_star_index.slurm` | `characterized defect`; `environment-deferred` | SLURM freezes implicit embedded compute, caller CWD, no wrapper output check, and exit behavior; actual modules/scheduler/runtime remain ENV. |
| `step_00b_gtf_to_bed12.slurm` | `characterized defect`; `environment-deferred` | SLURM freezes implicit embedded conversion, required submit CWD, shape check, and exit behavior; actual modules/scheduler/runtime remain ENV. |
| `step_00c_prepare_gatk_reference.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects delegation/output/exit mechanics; the Bash 3.2 default dry-run abort remains a defect and cluster behavior remains ENV. |
| `step_01_star_align.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects caller-CWD delegation and exits; default placeholder side effects remain a defect and cluster behavior remains ENV. |
| `step_02_sort_index_bam.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects execute/delegation/output behavior; Bash 3.2 abort and dry-run directory creation remain defects and cluster behavior remains ENV. |
| `step_02b_bam_qc.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects execute/delegation/output behavior; Bash 3.2 abort and dry-run directory creation remain defects and cluster behavior remains ENV. |
| `step_03_infer_strandedness_and_orientation.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects CWD/delegation/output behavior; the Bash 3.2 default dry-run abort remains a defect and cluster behavior remains ENV. |
| `step_04_mark_duplicates.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects modules/delegation/three-output checks; the Bash 3.2 default dry-run abort remains a defect and cluster behavior remains ENV. |
| `step_05_split_n_cigar_reads.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects delegation/two-output checks; the Bash 3.2 default dry-run abort remains a defect and cluster behavior remains ENV. |
| `step_06_split_bam_by_read_orientation.slurm` | `preserved contract`; `characterized defect`; `environment-deferred` | SLURM protects delegation/five-output checks; the Bash 3.2 default dry-run abort remains a defect and cluster behavior remains ENV. |
| `step_07_bcftools_mpileup_by_chrom_and_strand.slurm` | `preserved contract`; `environment-deferred` | SLURM protects mocked local mode/modules/delegation/output/exits; actual CSU modules, scheduler, and runtime remain ENV. |
| `step_08_vcf_preprocessing.slurm` | `preserved contract`; `environment-deferred` | SLURM protects mocked local mode/delegation/output/exits without inventing modules; actual CSU scheduler/runtime remain ENV. |
| `step_09_cmh_editing_site_calling.slurm` | `preserved contract`; `environment-deferred` | SLURM protects mocked local mode/delegation/output/exits without installing dependencies; actual CSU scheduler/runtime remain ENV. |
| `template.slurm` | `preserved contract`; `environment-deferred` | SLURM protects its mode-less lightweight probe and module-list policy; actual CSU module resolution remains ENV. |
| `tool_check.slurm` | `preserved contract`; `environment-deferred` | SLURM protects required/optional probe exit policy; actual CSU tools/modules remain ENV. |
| `validate_manifest.slurm` | `preserved contract`; `environment-deferred` | SLURM protects mode-less validation and strict Python child exit; actual CSU module resolution remains ENV. |

### Make rows (5)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| complete local-gate targets | `preserved contract` | CLI's committed golden + GATE and orchestrator tests protect exact default-context expansion, lane ownership, and exit behavior. |
| explicit restore/baseline-update targets | `preserved contract` | CLI's committed golden and direct restore/baseline tests protect explicit operator mutation and prohibit implicit installation. |
| explicit output/runtime targets | `preserved contract` | CLI's committed golden + REPORT and direct owners protect declared output/evidence boundaries. |
| internal validation-lane targets | `preserved contract` | CLI's committed golden + GATE and orchestrator tests protect exact internal-lane semantics. |
| `demo-step03-dry-run`, `demo-step03` | `preserved contract`; `environment-deferred` | CLI's committed golden protects exact local command expansion; actual scheduler submission remains ENV. |

### Cross-cutting rows (15)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| public help/dry-run/execute/malformed-input/exit behavior | `preserved contract`; `characterized defect` | CLI plus direct owners protect applicable cases; legacy mode/help/overwrite exceptions remain defects. |
| native output transactions | `preserved contract`; `characterized defect` | FAULT plus direct transaction owners protect normal publication and independently freeze named recovery gaps. |
| seven-column validation-report schema | `preserved contract` | ROSTER + GOLD and every direct validator owner protect the literal schema. |
| exact per-step check rosters | `preserved contract`; `characterized defect` | ROSTER protects every producer roster; shared consumer and adapter reorder/wrong-unique acceptance remain defects. |
| public JSON schemas and table headers | `preserved contract` | GOLD plus schema/direct owners protect representative critical paths and exact ordered headers. |
| status vocabularies and state transitions | `preserved contract` | GOLD plus direct owners protect named constants, aggregation, and shared-policy transitions. |
| deterministic JSON/TSV/QC/report bytes and ordering | `preserved contract` | GOLD + REPORT plus fixed-time/direct owners protect canonical critical bytes and broad transaction outputs. |
| locks, signals, rollback, cleanup, and recovery evidence | `preserved contract`; `characterized defect` | FAULT plus direct owners protect normal cases and independently preserve every named unsafe recovery state. |
| stable hashes and input mutation | `preserved contract`; `characterized defect` | FAULT plus direct owners protect rechecks; same-size/restored-mtime and related snapshot gaps remain defects. |
| unrelated-file immunity | `preserved contract` | CLI plus direct owners protect declared-output boundaries. |
| symlink, hardlink, and directory-identity substitution | `preserved contract` | FAULT plus direct owners independently exercise identity substitutions. |
| computational/scientific evidence-state boundaries | `preserved contract`; `environment-deferred` | GOLD + REPORT + REAL-R protect local state boundaries; production scientific review and biological readiness remain ENV and unreleased. |
| direct execution, arbitrary CWD, and SLURM delegation | `preserved contract`; `characterized defect`; `environment-deferred` | CLI + SLURM protect exact local mechanics; legacy file/mode/CWD defects remain labeled and actual cluster behavior remains ENV. |
| Step `09` CMH statistic, p-value, odds ratio, and estimability | `preserved contract`; `characterized defect`; `environment-deferred` | CMH + REAL-R protect count-derived local semantics; validator non-recomputation remains a defect and production/cluster algorithm changes remain ENV. |
| `_run_summary_science.py` policy projection | `preserved contract` | GOLD plus artifact/summary/report direct owners protect recorded, pending, absent, limitation, and computational-status transitions. |

### Fixture/evidence rows (10)

| Source row | TEST-01Z outcome | Independent regression or explicit disposition |
| --- | --- | --- |
| artifact-schema valid JSON fixtures | `preserved contract` | GOLD supplements integrated schema validation with literal critical paths, states, and a direct mutation. |
| artifact-adapter fixture builder | `preserved contract` | GOLD + ROSTER + FAULT supplement the coupled builder for critical index/header/byte/roster behavior. |
| artifact-run-summary fixture builder | `preserved contract` | GOLD + REPORT + FAULT supplement broad integrated projections with independent headers, bytes, receipt, and policy transitions. |
| Step `09c` fixture builder | `preserved contract` | GOLD supplements integrated tables with literal headers, status constants, aggregation, and policy transitions. |
| report HTML/PDF fixture helpers | `preserved contract`; `environment-deferred` | REPORT + GOLD protect local structure, banners, and receipt bytes; production report evidence remains ENV. |
| Step `00a`–`09` validation-report fixtures | `preserved contract` | ROSTER + GOLD + FAULT protect exact reports without duplicating every integrated fixture. |
| Step `07` mocked VCF/receipt outputs | `preserved contract`; `environment-deferred` | Direct transaction owners protect mocked local publication; real bcftools/cluster output remains ENV. |
| Step `08` semantic outputs | `preserved contract`; `environment-deferred` | REAL-R + GOLD protect local semantics and shared headers; production/cluster output remains ENV. |
| Step `09` semantic outputs | `preserved contract`; `environment-deferred` | REAL-R + CMH protect local semantics independently; production/cluster output remains ENV. |
| HTML/PDF/report receipts | `preserved contract`; `environment-deferred` | REPORT + GOLD protect pinned local renders and exact critical receipt behavior; production reports remain ENV. |

### TEST-01Z result

- All 88 source rows have an explicit disposition; no row is classified
  `undefined — decision required`.
- Every `preserved contract` component names independent regression evidence.
  Producer-coupled integrated fixtures remain only as additional end-to-end
  evidence and are not the sole oracle for a preserved critical rule.
- `characterized defect` components remain defects. This decision does not
  normalize, approve, or silently migrate them.
- Every `environment-deferred` component is already reviewed in the evidence
  boundary, RA-025, and the current handoff. These deferrals continue to block
  runtime, cluster, scientific, and biological claims, but they do not require
  inventing local evidence before architecture-planning inventory begins.
- The initial post-TEST-01F reviewer found no repair. A later Phase `0`
  adversarial review identified two false protection claims and stopped
  publication. Correction `0c64d1a` closes both with a literal Make oracle and
  direct real-R rejection-path execution; after the first final review exposed
  a bare-`make` portability defect, `44d3255` added explicit portable recursive
  identities. A second review exposed ambient `MAKEFILES` contamination;
  `fd98244` isolates the default-context expansion and adds a hostile-state
  regression. The focused tests and reopened complete local gate pass. Final
  independent review at `fb21c9d` reproduced both prior blockers, passed the
  30-case Make-focused slice and guarded real-R contract, and returned
  `PUBLISHABLE`. The checked coverage refresh has no line or branch regression.

The TEST-01Z decision is **affirmative for the named Phase `02` planning roots
only**. It releases `ARCH-02A`, `RPT-01`, `LOG-01`, and `DOC-IA-01` for their
own separately approved task starts. The TEST-01Z side of `CODEDOC-05` and
`SIZE-07` is satisfied, but those cards retain their other direct blockers.
This decision does not begin Phase `02`, release production mutation, approve
any characterized defect, establish runtime or cluster evidence, validate a
scientific algorithm, or authorize biological interpretation.
