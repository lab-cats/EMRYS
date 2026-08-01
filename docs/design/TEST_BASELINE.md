# Test baseline and public-contract traceability

This document owns the Phase `01` measured Python coverage summary, the
public-contract risk-to-test matrix, fixture-independence classification, and
the characterization gaps derived from that evidence. The machine-readable
per-module snapshot is
[`../../tests/baselines/python_coverage.json`](../../tests/baselines/python_coverage.json).
The authoritative descendant branch names and order remain in
[`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), and executable commands remain in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

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

`tests/test_public_cli_contracts.py` independently inventories all 25 public
Python entry points and the one private module. For every public entry point it
protects interpreter-invoked help, unknown-option failure, arbitrary-CWD use,
and no working-directory artifacts. It separately freezes the current eight
executable and 17 interpreter-only file modes. Direct help for the executable
set is tested with a prepared `python3` path because their env shebang
deliberately delegates dependency selection to the caller's environment.

| Public entry point | Direct regression owner | Covered cases | Independence | Status / remaining gap |
| --- | --- | --- | --- | --- |
| `build_artifact_index.py` | `tests/test_artifact_adapters.py` | `H D E M F N L B S I U P T V X` | mixed | adequate; independent contract mutation remains under `TG-06` |
| `build_run_summary.py` | `tests/test_artifact_run_summary.py` | `H D E M F N L B S I U P T V X` | mixed | adequate; independent serialized goldens remain under `TG-06` |
| `gtf_to_bed12.py` | `tests/test_gtf_to_bed12.py` | `H E M F N U T X W` | independent | `TG-04` complete; arbitrary-CWD output is exact and the existing output is silently replaced as a characterized defect |
| `reference_provenance.py` | `tests/test_reference_provenance.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` and `TG-04` characterization complete; incomplete-rollback recovery remains a labeled production gap |
| `render_run_report.py` | `tests/test_report_html_v1.py`; `tests/test_report_exports_v1.py` | `H D E M F T V X` | mixed | `TG-04` complete; existing renderer cases remain the output contract |
| `render_run_report_bundle.py` | `tests/test_report_exports_v1.py`; `tests/shell/test_render_run_report.sh` | `H D E M F N L B S I U P T V X W` | mixed | `TG-04` complete; low measured internal coverage remains and scenario evidence must precede any implementation change |
| `restore_quarto.py` | `tests/test_quarto_restore.py` | `H E M N L B I P T X` | independent | adequate for supported local restore; other platforms are not supported |
| `runtime_preflight.py` | `tests/test_runtime_preflight.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` characterization complete; lock-fsync, lock-cleanup, and incomplete-rollback recovery remain labeled production gaps; CSU execution deferred |
| `step_09c_scientific_validation.py` | `tests/test_step_09c_scientific_validation.py`; `tests/shell/test_step_09c_scientific_validation.sh` | `H D E M F N L B S I U P T V X W` | mixed | adequate for local synthetic contracts; production science review deferred |
| `storage_inventory.py` | `tests/test_storage_inventory.py` | `H D E M F N L B S I P T V X` | independent | `TG-02` characterization complete; incomplete-rollback recovery remains a labeled production gap; CSU storage execution deferred |
| `validate_artifact_contracts.py` | `tests/test_artifact_schema_contracts.py` | `H M F U P T V X` | mixed | adequate; independent schema/golden mutation remains under `TG-06` |
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
| `validate_step_08_preprocessing_outputs.py` | `tests/test_validate_step_08_preprocessing_outputs.py`; `tests/test_validation_check_rosters.py`; `tests/test_validation_publication_faults.py` | `D E M F N L B S I P T X R` | mixed | `TG-02` through `TG-04` complete with labeled production gaps; `TG-06` remains |
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
in [`../operations/HANDOFF.md`](../operations/HANDOFF.md).

## Cross-cutting risk matrix

| Risk area | Current regression evidence | Independence | Disposition |
| --- | --- | --- | --- |
| Public help, dry-run, execute, malformed input, and exit behavior | focused entry-point suites plus the exact Python/shell/R/Make inventory in `tests/test_public_cli_contracts.py` | mostly independent | `TG-04` complete; preserve explicit legacy mode/help/overwrite exceptions rather than normalizing them |
| Native output transactions | Step `02`, `05`–`09`, Step `09c`, adapters, summaries, report bundle rollback suites, and Phase `01b` publisher fault injection | mixed | `TG-02` characterization complete; preserve labeled production gaps for reviewed correction |
| Seven-column validation report schema | every `tests/test_validate_step_*` module plus adapter propagation fixtures | mixed | preserve |
| Exact per-step check rosters | test-only literal ordered rosters, all 13 live producer-output suites, shared report-consumer mutations, and artifact-adapter mutations | independent characterization | `TG-03` complete; preserve the characterized order-insensitive shared validator and wrong-unique/reordering adapter defects for separate correction review |
| Public JSON Schemas and table headers | schema-contract suite, artifact/run-summary suites, Step `09c`, per-step validators | mixed | freeze independent representative goldens in `TG-06` |
| Status vocabularies and state transitions | schema, adapter, Step `09c`, summary, and report negative cases | mixed | add production-constant mutation cases in `TG-06` |
| Deterministic JSON/TSV/QC/report bytes and ordering | retry/fixed-time tests, explicit ordered inventories, renderer comparisons | mixed | preserve; add small independent serialized goldens in `TG-06` |
| Locks, signals, rollback, cleanup, and recovery evidence | later shell workflows, artifact/summary/report transactions, Step `09c`, and shared/ancillary publisher fault injection | mixed | `TG-02` characterization complete; do not universalize action-local mechanisms or mistake a characterized gap for a safe contract |
| Stable hashes and input mutation | Step `07`–`09`, Step `09c`, artifact/summary/report, provenance/preflight/storage, and shared-validator snapshot suites | mixed | `TG-02` characterization complete; digest-backed shared snapshots remain a reviewed production correction |
| Unrelated-file immunity | central public-CLI help/failure matrix, `gtf_to_bed12.py`, Step `07`–`09`, Step `09c`, adapter/summary/report suites | independent/mixed | `TG-04` applicable CLI omissions complete; preserve deeper transaction suites |
| Symlink, hardlink, and directory-identity substitution | adapter, summary, report, restore, preflight/storage/provenance, and shared-validator publication suites | independent | `TG-02` characterization complete; preserve |
| Computational/scientific evidence-state boundaries | schemas, Step `09c`, adapters, summary, reports | mixed | preserve; mutation-resistant vocabulary cases in `TG-06` |
| Direct execution, arbitrary CWD, and SLURM delegation | exact public script/job modes, arbitrary-CWD CLI matrix, exact mocked submit-CWD/delegation matrix, and existing workflow suites | independent | `TG-04` and local `TG-05` characterization complete; real scheduler/module/runtime evidence remains environment-deferred |
| Step `09` CMH statistic, p-value, odds ratio, and estimability | independent Python oracle, fixed corpus, direct committed-R comparison, and coordinated-corruption rejection; production validator still checks type/range and BH from reported p-values | independent characterization plus producer-coupled validator | `TG-01` characterization complete; compatible production-validator correction remains separately reviewed |
| `_run_summary_science.py` policy projection | artifact, summary, Step `09c`, and report suites | producer-coupled/mixed | independent state-transition goldens in `TG-06` |

## Golden-output and fixture independence

| Fixture/output family | Classification | Evidence and required action |
| --- | --- | --- |
| `tests/fixtures/artifact_schema_v1/valid/*.json` | mixed | fixed documents provide useful independent bytes, but validation uses the production schemas; add mutation tests for critical enums, required fields, and state transitions in `TG-06` |
| `tests/fixtures/artifact_adapters_v1/build_fixture.py` | producer-coupled | imports production adapter code and builds broad integrated transactions; retain end-to-end coverage and add small independent records/index/receipt goldens in `TG-06` |
| `tests/fixtures/artifact_run_summary_v1/build_fixture.py` | mixed | fixed expected projections coexist with production-shaped builders; add independent canonical JSON/TSV/QC/receipt bytes in `TG-06` |
| `tests/fixtures/step09c/build_fixture.py` | mixed | explicit tables are useful, but the builder shares vocabulary and shapes with the producer; add independent status/evidence transition cases in `TG-06` |
| `tests/fixtures/report_html_v1/run_html_core.py` and report fixtures | producer-coupled | the helper loads production report modules; retain real-renderer end-to-end tests and add only a small independent content/banner golden where it detects a named risk |
| Step `00a`–`09` validation report fixtures | mostly independent | direct TSV/status assertions plus test-only literal ordered rosters now complete `TG-03`; broader serialized fixture independence remains under `TG-06` |
| Step `07` mocked VCF/receipt outputs | mixed | good transaction and manifest coverage; real bcftools output remains a deferred runtime gate |
| Step `08` semantic outputs | mixed | guarded real-R fixtures are meaningful, but validator header expectations import Step `09c` production constants; independent headers and corruptions belong to `TG-06` |
| Step `09` semantic outputs | mixed | `TG-01` now derives an independent oracle directly from DP/AD and proves coordinated corruption detectable; the production validator remains unchanged |
| HTML/PDF/report receipts | mixed | real pinned renderer and independent structural readers are exercised; production reports remain absent |

Independent duplication is intentional where it is the only way to detect a
shared producer/test defect. The hardening work must supplement, not replace,
the integrated fixtures.

## Evidence-derived characterization gaps

The baseline matrix yielded six cohesive gaps. `TG-01` through `TG-05` are now
characterized; the authoritative branch mapping and remaining order are in
`PIPELINE_PLAN.md`.

| Gap | Scope | Exit evidence |
| --- | --- | --- |
| `TG-01` | Independent Step `09` CMH oracle | recompute estimability, continuity-corrected statistic, p-value, and common odds ratio from DP/AD; coordinated corruption fails while valid real-R fixture passes |
| `TG-02` | Validation publication and recheck faults | shared validator publication tests cover staged validation, prior-output validation, input/output identity changes, rename/fsync failures, rollback, cleanup, and retained recovery evidence without changing public behavior |
| `TG-03` | Exact validation check rosters | every step has a fixed independent ordered roster; missing, duplicate, extra, and reordered checks fail at the correct boundary |
| `TG-04` | Public CLI and exit contracts | every Python, shell, and Make entry point has an explicit applicable-case decision for help, direct/arbitrary-CWD use, malformed input, side effects, unrelated files, and exit propagation |
| `TG-05` | SLURM wrapper contracts | every job has a focused applicable-case decision for mode, modules, CWD, delegation, arguments, output validation, and exit propagation; legacy exceptions are characterized, not refactored |
| `TG-06` | Independent goldens and mutation resistance | critical schemas, headers, serialized bytes, status transitions, evidence boundaries, and shared policy rules fail when production constants change without the independent expectation |

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

The final Phase `01` sufficiency gate must rerun the measured baseline, update
this matrix with the completed characterization evidence, identify any
remaining accepted/deferred risks, and explicitly decide whether Phase `02`
planning may begin. It must not begin production refactoring.
