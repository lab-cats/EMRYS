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

| Public entry point | Direct regression owner | Covered cases | Independence | Status / remaining gap |
| --- | --- | --- | --- | --- |
| `build_artifact_index.py` | `tests/test_artifact_adapters.py` | `H D E M F N L B S I U P T V X` | mixed | adequate; independent contract mutation remains under `TG-06` |
| `build_run_summary.py` | `tests/test_artifact_run_summary.py` | `H D E M F N L B S I U P T V X` | mixed | adequate; independent serialized goldens remain under `TG-06` |
| `gtf_to_bed12.py` | `tests/test_gtf_to_bed12.py` | `H E M F T X` | independent | partial: exact existing-output and arbitrary-CWD behavior under `TG-04` |
| `reference_provenance.py` | `tests/test_reference_provenance.py` | `H D E M F N L P T V X` | independent | partial: injected publication/recheck failures under `TG-02` |
| `render_run_report.py` | `tests/test_report_html_v1.py`; `tests/test_report_exports_v1.py` | `H D E M F T V X` | mixed | partial: direct CLI/exit matrix under `TG-04` |
| `render_run_report_bundle.py` | `tests/test_report_exports_v1.py`; `tests/shell/test_render_run_report.sh` | `H D E M F N L B S I U P T V X W` | mixed | partial: low measured internal coverage and direct CLI matrix under `TG-04`; scenario evidence must precede any implementation change |
| `restore_quarto.py` | `tests/test_quarto_restore.py` | `H E M N L B I P T X` | independent | adequate for supported local restore; other platforms are not supported |
| `runtime_preflight.py` | `tests/test_runtime_preflight.py` | `H D E M F N L B I P T V X` | independent | partial: shared publication/recheck fault matrix under `TG-02`; CSU execution deferred |
| `step_09c_scientific_validation.py` | `tests/test_step_09c_scientific_validation.py`; `tests/shell/test_step_09c_scientific_validation.sh` | `H D E M F N L B S I U P T V X W` | mixed | adequate for local synthetic contracts; production science review deferred |
| `storage_inventory.py` | `tests/test_storage_inventory.py` | `H D E M F N L B I P T V X` | independent | partial: shared publication/recheck fault matrix under `TG-02`; CSU storage execution deferred |
| `validate_artifact_contracts.py` | `tests/test_artifact_schema_contracts.py` | `H M F U P T V X` | mixed | adequate; independent schema/golden mutation remains under `TG-06` |
| `validate_manifest.py` | `tests/test_validate_manifest.py` | `H M F P T X` | independent | adequate |
| `validate_step_00a_star_index.py` | `tests/test_validate_step_00a_star_index.py` | `D E M F N L T X R` | independent | partial: shared publication faults `TG-02`; roster mutation `TG-03`; help/exit matrix `TG-04` |
| `validate_step_00b_bed12.py` | `tests/test_validate_step_00b_bed12.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_00c_reference_sidecars.py` | `tests/test_validate_step_00c_reference_sidecars.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_01_star_alignment.py` | `tests/test_validate_step_01_star_alignment.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_02_canonical_bam.py` | `tests/test_validate_step_02_canonical_bam.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_02b_bam_qc.py` | `tests/test_validate_step_02b_bam_qc.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_03_rseqc_orientation.py` | `tests/test_validate_step_03_rseqc_orientation.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_04_mark_duplicates.py` | `tests/test_validate_step_04_mark_duplicates.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_05_split_ncigar.py` | `tests/test_validate_step_05_split_ncigar.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_06_orientation_outputs.py` | `tests/test_validate_step_06_orientation_outputs.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04` |
| `validate_step_07_mpileup_outputs.py` | `tests/test_validate_step_07_mpileup_outputs.py` | `D E M F N L T X R` | independent | partial: `TG-02`, `TG-03`, `TG-04`; real bcftools deferred |
| `validate_step_08_preprocessing_outputs.py` | `tests/test_validate_step_08_preprocessing_outputs.py` | `D E M F N L T X R` | producer-coupled | partial: `TG-02`, `TG-03`, `TG-04`, and independent headers/goldens `TG-06` |
| `validate_step_09_cmh_outputs.py` | `tests/test_validate_step_09_cmh_outputs.py` | `D E M F N L T V X R` | mixed | gap: count-derived independent CMH oracle `TG-01`; also `TG-02`, `TG-03`, and `TG-04` |

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
| `step_03_infer_strandedness_and_orientation.sh` | `tests/shell/test_step_03_infer_strandedness_and_orientation.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_04_mark_duplicates.sh` | `tests/shell/test_step_04_mark_duplicates.sh` | `H D E M F N L B I P T X` | adequate script coverage; SLURM matrix remains `TG-05` |
| `step_05_split_n_cigar_reads.sh` | `tests/shell/test_step_05_split_n_cigar_reads.sh` | `H D E M F N L B I P T X W` | adequate |
| `step_06_split_bam_by_read_orientation.sh` | `tests/shell/test_step_06_split_bam_by_read_orientation.sh` | `H D E M F N L B I P T X W` | adequate |
| `step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh` | `H D E M F N L B I U P T X W` | adequate with mocked bcftools; real bcftools deferred |
| `step_08_vcf_preprocessing.sh` | `tests/shell/test_step_08_vcf_preprocessing.sh`; guarded real-R suite | `H D E M F N L B S I U P T X W` | adequate local contract; production/cluster runtime deferred |
| `step_09_cmh_editing_site_calling.sh` | `tests/shell/test_step_09_cmh_editing_site_calling.sh`; guarded real-R suite | `H D E M F N L B S I U P T V X W` | adequate producer contract; independent validator oracle remains `TG-01` |
| `step_09c_scientific_validation.sh` | `tests/shell/test_step_09c_scientific_validation.sh` | `H D E M F N L B S I U P T V X W` | adequate local synthetic contract |

Signal coverage is strongest for the later transactional workflows and report
bundle. The matrix does not infer signal safety for an earlier workflow merely
because it has ordinary rollback coverage.

## R and dependency entry points

| Public entry point | Regression owner | Covered cases | Status / remaining gap |
| --- | --- | --- | --- |
| `check_r_environment.R` | `tests/shell/test_local_r_environment.sh`; guarded `make r-check` | `M F V X W` | adequate for the guarded local environment; CSU runtime deferred |
| `restore_r_environment.R` | `tests/shell/test_local_r_environment.sh`; explicit `make r-restore` | `M F N X W` | adequate explicit setup behavior; installation is never automatic |
| `step_08_vcf_preprocessing.R` | `tests/r/test_step_08_vcf_preprocessing.R`; wrapper suite | `E M F T X W` | adequate local real-R semantics; production scale and cluster runtime deferred |
| `step_09_cmh_editing_site_calling.R` | `tests/r/test_step_09_cmh_editing_site_calling.R`; wrapper suite | `E M F T V X W` | adequate producer semantics; independent validator oracle remains `TG-01` |

R source is not included in the Python coverage percentages. The guarded
real-R suite is therefore a separate mandatory gate.

## SLURM entry points

Static `bash -n` coverage applies to all wrappers but is not behavioral
coverage.

| Public wrapper | Dynamic regression owner | Covered cases | Status / remaining gap |
| --- | --- | --- | --- |
| `step_00a_build_novogene_star_index.slurm` | no focused dynamic wrapper suite | static only | gap: `TG-05`; wrapper embeds compute |
| `step_00b_gtf_to_bed12.slurm` | no focused dynamic wrapper suite | static only | gap: `TG-05`; wrapper embeds compute |
| `step_00c_prepare_gatk_reference.slurm` | Step `00c` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_01_star_align.slurm` | Step `01` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_02_sort_index_bam.slurm` | Step `02` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_02b_bam_qc.slurm` | Step `02b` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_03_infer_strandedness_and_orientation.slurm` | Step `03` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_04_mark_duplicates.slurm` | Step `04` shell suite | partial `D E M X W` | partial: `TG-05` |
| `step_05_split_n_cigar_reads.slurm` | Step `05` shell suite | `D E M F X W` | adequate local wrapper characterization |
| `step_06_split_bam_by_read_orientation.slurm` | Step `06` shell suite | `D E M F X W` | adequate local wrapper characterization |
| `step_07_bcftools_mpileup_by_chrom_and_strand.slurm` | Step `07` shell suite | `D E M F X W` | adequate with mocked runtime; cluster runtime deferred |
| `step_08_vcf_preprocessing.slurm` | Step `08` shell suite | `D E M F X W` | adequate local wrapper contract; cluster runtime deferred |
| `step_09_cmh_editing_site_calling.slurm` | Step `09` shell suite | `D E M F X W` | adequate local wrapper contract; cluster runtime deferred |
| `template.slurm` | no focused dynamic suite | static only | gap: characterize or explicitly retain as example under `TG-05` |
| `tool_check.slurm` | no focused dynamic suite | static only | gap: `TG-05` |
| `validate_manifest.slurm` | no focused dynamic suite | static only | gap: `TG-05` |

`TG-05` must test default/execute/invalid `EXECUTE`, module listing/loading,
submit working directory, exact delegation and arguments, output validation,
and child exit propagation. It must document the intentional Step `00a`/`00b`
legacy exceptions before any structural change.

## Make targets

| Public target(s) | Regression evidence | Status |
| --- | --- | --- |
| `test`, `shell-test`, `real-r-test`, `local-real-r-test`, `report-test` | run as explicit local gates | adequate; each retains its own evidence boundary |
| `r-restore`, `r-check`, `quarto-restore` | focused environment/restore tests plus explicit operator invocation | adequate; dependency mutation remains operator-only |
| `python-coverage-measure`, `python-coverage-check`, `python-coverage-baseline-update` | `tests/test_python_coverage_baseline.py` and successful repository measurement | adequate; baseline update remains deliberate |
| `validate`, `smoke`, `lint`, `all-checks` | target inspection plus component gates | partial: exact target/exit characterization under `TG-04` |
| `demo-step03-dry-run`, `demo-step03` | command inspection only | partial: submission behavior remains deferred with cluster work |

## Cross-cutting risk matrix

| Risk area | Current regression evidence | Independence | Disposition |
| --- | --- | --- | --- |
| Public help, dry-run, execute, malformed input, and exit behavior | focused Python/shell suites listed above | mostly independent | complete exact missing-case matrix in `TG-04` |
| Native output transactions | Step `02`, `05`–`09`, Step `09c`, adapters, summaries, and report bundle rollback suites | mixed | preserve; fill shared validator publication faults in `TG-02` |
| Seven-column validation report schema | every `tests/test_validate_step_*` module plus adapter propagation fixtures | mixed | preserve |
| Exact per-step check rosters | production `CHECK_IDS` plus uneven fixed-list assertions | producer-coupled/mixed | add mutation-resistant independent rosters in `TG-03` |
| Public JSON Schemas and table headers | schema-contract suite, artifact/run-summary suites, Step `09c`, per-step validators | mixed | freeze independent representative goldens in `TG-06` |
| Status vocabularies and state transitions | schema, adapter, Step `09c`, summary, and report negative cases | mixed | add production-constant mutation cases in `TG-06` |
| Deterministic JSON/TSV/QC/report bytes and ordering | retry/fixed-time tests, explicit ordered inventories, renderer comparisons | mixed | preserve; add small independent serialized goldens in `TG-06` |
| Locks, signals, rollback, cleanup, and recovery evidence | later shell workflows, artifact/summary/report transactions, Step `09c` | mixed | shared validation publication matrix `TG-02`; do not universalize action-local mechanisms |
| Stable hashes and input mutation | Step `07`–`09`, Step `09c`, artifact/summary/report, provenance/preflight/storage suites | mixed | preserve; fault-inject shared validator rechecks in `TG-02` |
| Unrelated-file immunity | Step `07`–`09`, Step `09c`, adapter/summary/report suites | independent/mixed | fill explicit CLI omissions in `TG-04` |
| Symlink, hardlink, and directory-identity substitution | adapter, summary, report, restore, preflight/storage/provenance suites | independent | preserve; fill shared validator publication paths in `TG-02` |
| Computational/scientific evidence-state boundaries | schemas, Step `09c`, adapters, summary, reports | mixed | preserve; mutation-resistant vocabulary cases in `TG-06` |
| Direct execution, arbitrary CWD, and SLURM delegation | strong for Steps `05`–`09`; uneven for early stages and utility jobs | independent | `TG-04` and `TG-05` |
| Step `09` CMH statistic, p-value, odds ratio, and estimability | wrapper producer fixtures; validator checks type/range and BH from reported p-values | producer-coupled | critical gap `TG-01`: independently recompute from DP/AD and corrupt coordinated fields |
| `_run_summary_science.py` policy projection | artifact, summary, Step `09c`, and report suites | producer-coupled/mixed | independent state-transition goldens in `TG-06` |

## Golden-output and fixture independence

| Fixture/output family | Classification | Evidence and required action |
| --- | --- | --- |
| `tests/fixtures/artifact_schema_v1/valid/*.json` | mixed | fixed documents provide useful independent bytes, but validation uses the production schemas; add mutation tests for critical enums, required fields, and state transitions in `TG-06` |
| `tests/fixtures/artifact_adapters_v1/build_fixture.py` | producer-coupled | imports production adapter code and builds broad integrated transactions; retain end-to-end coverage and add small independent records/index/receipt goldens in `TG-06` |
| `tests/fixtures/artifact_run_summary_v1/build_fixture.py` | mixed | fixed expected projections coexist with production-shaped builders; add independent canonical JSON/TSV/QC/receipt bytes in `TG-06` |
| `tests/fixtures/step09c/build_fixture.py` | mixed | explicit tables are useful, but the builder shares vocabulary and shapes with the producer; add independent status/evidence transition cases in `TG-06` |
| `tests/fixtures/report_html_v1/run_html_core.py` and report fixtures | producer-coupled | the helper loads production report modules; retain real-renderer end-to-end tests and add only a small independent content/banner golden where it detects a named risk |
| Step `00a`–`09` validation report fixtures | mostly independent | direct TSV/status assertions exist; exact roster independence is incomplete and belongs to `TG-03` |
| Step `07` mocked VCF/receipt outputs | mixed | good transaction and manifest coverage; real bcftools output remains a deferred runtime gate |
| Step `08` semantic outputs | mixed | guarded real-R fixtures are meaningful, but validator header expectations import Step `09c` production constants; independent headers and corruptions belong to `TG-06` |
| Step `09` semantic outputs | producer-coupled for CMH fields | coordinated false CMH fields can pass; `TG-01` must derive the oracle directly from DP/AD |
| HTML/PDF/report receipts | mixed | real pinned renderer and independent structural readers are exercised; production reports remain absent |

Independent duplication is intentional where it is the only way to detect a
shared producer/test defect. The hardening work must supplement, not replace,
the integrated fixtures.

## Evidence-derived characterization gaps

The matrix yields six cohesive gaps. The authoritative branch mapping and
order are in `PIPELINE_PLAN.md`.

| Gap | Scope | Exit evidence |
| --- | --- | --- |
| `TG-01` | Independent Step `09` CMH oracle | recompute estimability, continuity-corrected statistic, p-value, and common odds ratio from DP/AD; coordinated corruption fails while valid real-R fixture passes |
| `TG-02` | Validation publication and recheck faults | shared validator publication tests cover staged validation, prior-output validation, input/output identity changes, rename/fsync failures, rollback, cleanup, and retained recovery evidence without changing public behavior |
| `TG-03` | Exact validation check rosters | every step has a fixed independent ordered roster; missing, duplicate, extra, and reordered checks fail at the correct boundary |
| `TG-04` | Public CLI and exit contracts | every Python, shell, and Make entry point has an explicit applicable-case decision for help, direct/arbitrary-CWD use, malformed input, side effects, unrelated files, and exit propagation |
| `TG-05` | SLURM wrapper contracts | every job has a focused applicable-case decision for mode, modules, CWD, delegation, arguments, output validation, and exit propagation; legacy exceptions are characterized, not refactored |
| `TG-06` | Independent goldens and mutation resistance | critical schemas, headers, serialized bytes, status transitions, evidence boundaries, and shared policy rules fail when production constants change without the independent expectation |

The final Phase `01` sufficiency gate must rerun the measured baseline, update
this matrix with the completed characterization evidence, identify any
remaining accepted/deferred risks, and explicitly decide whether Phase `02`
planning may begin. It must not begin production refactoring.
