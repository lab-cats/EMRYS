# Current functional-owner inventory

This is the implementation-backed `ARCH-02A` ownership roster. It assigns
every current public script, SLURM job, validator, and Make interface exactly
once without changing historical execution order. Functional-owner slugs are
the stable public identities owned by
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md); this inventory owns
their current executable surfaces and direct protection, not identity or DAG
definitions.

The executable roster is protected by
[`test_public_cli_contracts.py`](../../tests/test_public_cli_contracts.py), the
job roster by
[`test_slurm_wrapper_contracts.py`](../../tests/test_slurm_wrapper_contracts.py),
and public Make expansions by
[`make_target_expansions.json`](../../tests/fixtures/public_cli_contracts/make_target_expansions.json).
Files beginning with `_` and the explicitly listed orchestration helpers are
private library surfaces, not additional public entry points.

## Numbered workflow and evidence owners

| Historical owner | Public implementation and scheduler surfaces | Independent validator | Direct protection |
| --- | --- | --- | --- |
| [`00a` — `construct_STAR_index`](../../src/norad/stages/construct_STAR_index/CONTRACT.md) | [`step_00a_build_novogene_star_index.slurm`](../../src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm) embeds the current producer | [`validate_step_00a_star_index.py`](../../src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py) | [validator test](../../tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py), [mocked-job test](../../tests/stages/construct_STAR_index/test_step_00a_build_novogene_star_index.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`00b` — `convert_GTF_to_BED12`](../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md) | [`gtf_to_bed12.py`](../../src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py), [`step_00b_gtf_to_bed12.slurm`](../../src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm) | [`validate_step_00b_bed12.py`](../../src/norad/stages/convert_GTF_to_BED12/validate_step_00b_bed12.py) | [producer test](../../tests/stages/convert_GTF_to_BED12/test_gtf_to_bed12.py), [validator test](../../tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py), [mocked-job test](../../tests/stages/convert_GTF_to_BED12/test_step_00b_gtf_to_bed12.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`00c` — `construct_FASTA_sidecars`](../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md) | [`step_00c_prepare_gatk_reference.sh`](../../src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh), [`step_00c_prepare_gatk_reference.slurm`](../../src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm) | [`validate_step_00c_reference_sidecars.py`](../../src/norad/stages/construct_FASTA_sidecars/validate_step_00c_reference_sidecars.py) | [shell contract](../../tests/stages/construct_FASTA_sidecars/test_step_00c_prepare_gatk_reference.sh), [`test_validate_step_00c_reference_sidecars.py`](../../tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py) |
| [`01` — `align_RNA_reads_with_STAR`](../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md) | [`step_01_star_align.sh`](../../src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh), [`step_01_star_align.slurm`](../../src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm) | [`validate_step_01_star_alignment.py`](../../src/norad/stages/align_RNA_reads_with_STAR/validate_step_01_star_alignment.py) | [shell contract](../../tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh), [`test_validate_step_01_star_alignment.py`](../../tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`02` — `construct_canonical_BAM`](../../src/norad/stages/construct_canonical_BAM/CONTRACT.md) | [`step_02_sort_index_bam.sh`](../../src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh), [`step_02_sort_index_bam.slurm`](../../src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm) | [`validate_step_02_canonical_bam.py`](../../src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py) | [shell contract](../../tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh), [`test_validate_step_02_canonical_bam.py`](../../tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`02b` — `collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md) | [`step_02b_bam_qc.sh`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh), [`step_02b_bam_qc.slurm`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm) | [`validate_step_02b_bam_qc.py`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py) | [shell contract](../../tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh), [`test_validate_step_02b_bam_qc.py`](../../tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`03` — `collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md) | [`step_03_infer_strandedness_and_orientation.sh`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh), [`step_03_infer_strandedness_and_orientation.slurm`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm) | [`validate_step_03_rseqc_orientation.py`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/validate_step_03_rseqc_orientation.py) | [shell contract](../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_step_03_infer_strandedness_and_orientation.sh), [`test_validate_step_03_rseqc_orientation.py`](../../tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`04` — `mark_BAM_duplicates_with_Picard`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md) | [`step_04_mark_duplicates.sh`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh), [`step_04_mark_duplicates.slurm`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.slurm) | [`validate_step_04_mark_duplicates.py`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/validate_step_04_mark_duplicates.py) | [shell contract](../../tests/stages/mark_BAM_duplicates_with_Picard/test_step_04_mark_duplicates.sh), [`test_validate_step_04_mark_duplicates.py`](../../tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`05` — `split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md) | [`step_05_split_n_cigar_reads.sh`](../../src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh), [`step_05_split_n_cigar_reads.slurm`](../../src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.slurm) | [`validate_step_05_split_ncigar.py`](../../src/norad/stages/split_N_cigar_reads_with_GATK/validate_step_05_split_ncigar.py) | [shell contract](../../tests/stages/split_N_cigar_reads_with_GATK/test_step_05_split_n_cigar_reads.sh), [`test_validate_step_05_split_ncigar.py`](../../tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`06` — `partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md) | [`step_06_split_bam_by_read_orientation.sh`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh), [`step_06_split_bam_by_read_orientation.slurm`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.slurm) | [`validate_step_06_orientation_outputs.py`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/validate_step_06_orientation_outputs.py) | [shell contract](../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh), [`test_validate_step_06_orientation_outputs.py`](../../tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`07` — `generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md) | [`step_07_bcftools_mpileup_by_chrom_and_strand.sh`](../../scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh), [`step_07_bcftools_mpileup_by_chrom_and_strand.slurm`](../../jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm) | [`validate_step_07_mpileup_outputs.py`](../../scripts/validate_step_07_mpileup_outputs.py) | [shell contract](../../tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh), [`test_validate_step_07_mpileup_outputs.py`](../../tests/test_validate_step_07_mpileup_outputs.py) |
| [`08` — `preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md) | [`step_08_vcf_preprocessing.sh`](../../scripts/step_08_vcf_preprocessing.sh), [`step_08_vcf_preprocessing.R`](../../scripts/step_08_vcf_preprocessing.R), [`step_08_vcf_preprocessing.slurm`](../../jobs/step_08_vcf_preprocessing.slurm) | [`validate_step_08_preprocessing_outputs.py`](../../scripts/validate_step_08_preprocessing_outputs.py) | [shell contract](../../tests/shell/test_step_08_vcf_preprocessing.sh), [R contract](../../tests/r/test_step_08_vcf_preprocessing.R), [`test_validate_step_08_preprocessing_outputs.py`](../../tests/test_validate_step_08_preprocessing_outputs.py) |
| [`09` — `rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md) | [`step_09_cmh_editing_site_calling.sh`](../../scripts/step_09_cmh_editing_site_calling.sh), [`step_09_cmh_editing_site_calling.R`](../../scripts/step_09_cmh_editing_site_calling.R), [`step_09_cmh_editing_site_calling.slurm`](../../jobs/step_09_cmh_editing_site_calling.slurm) | [`validate_step_09_cmh_outputs.py`](../../scripts/validate_step_09_cmh_outputs.py) | [shell contract](../../tests/shell/test_step_09_cmh_editing_site_calling.sh), [R contract](../../tests/r/test_step_09_cmh_editing_site_calling.R), [`test_validate_step_09_cmh_outputs.py`](../../tests/test_validate_step_09_cmh_outputs.py), [independent oracle](../../tests/test_step_09_cmh_oracle.py) |
| [`09c` — `assemble_scientific_review_evidence_package`](../../src/norad/evidence/assemble_scientific_review_evidence_package/CONTRACT.md) | [`step_09c_scientific_validation.sh`](../../scripts/step_09c_scientific_validation.sh), [`step_09c_scientific_validation.py`](../../scripts/step_09c_scientific_validation.py); no SLURM wrapper | No separate validator: the Python entry point validates and publishes the package | [shell contract](../../tests/shell/test_step_09c_scientific_validation.sh), [`test_step_09c_scientific_validation.py`](../../tests/test_step_09c_scientific_validation.py) |

All numbered scheduler wrappers belong to the same owner as their delegated
operation. Scheduler concerns are a boundary around a stage, not additional
scientific stages.

## Cross-cutting product and operational owners

| Current functional owner | Public surfaces assigned here | Direct protection and boundary |
| --- | --- | --- |
| Intake contract validation | [`validate_manifest.py`](../../scripts/validate_manifest.py), [`validate_manifest.slurm`](../../jobs/validate_manifest.slurm), [`samples.example.tsv`](../../samples.example.tsv), Make `validate` in the [`Makefile`](../../Makefile) | [`test_validate_manifest.py`](../../tests/test_validate_manifest.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). This validates current manifest input; it is not an ingestion runner. |
| Reference provenance evidence | [`reference_provenance.py`](../../scripts/reference_provenance.py) | [`test_reference_provenance.py`](../../tests/test_reference_provenance.py). This inventories declared reference identity and consistency without repairing reference artifacts. The final FASTA-sidecar and Step `05` validators use private exact-file bridges to this unchanged public owner. |
| Structured runtime inspection | [`runtime_preflight.py`](../../scripts/runtime_preflight.py), [`runtime_preflight.example.tsv`](../../configs/runtime_preflight.example.tsv) | [`test_runtime_preflight.py`](../../tests/test_runtime_preflight.py). Profile-driven availability evidence does not establish workflow runtime or cluster proof. |
| Legacy manual cluster probe | [`tool_check.slurm`](../../jobs/tool_check.slurm) | [Wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). It emits scheduler logs rather than a structured runtime-preflight transaction and is not a compute stage. |
| Dependency lifecycle | [`check_r_environment.R`](../../scripts/check_r_environment.R), [`restore_r_environment.R`](../../scripts/restore_r_environment.R), [`restore_quarto.py`](../../scripts/restore_quarto.py); Make `r-check`, `r-restore`, and `quarto-restore` | [local R contract](../../tests/shell/test_local_r_environment.sh), [`test_quarto_restore.py`](../../tests/test_quarto_restore.py), [public Make contracts](../../tests/test_public_cli_contracts.py). Restoration is explicit operator mutation, never compute-time bootstrap. |
| Storage evidence | [`storage_inventory.py`](../../scripts/storage_inventory.py) | [`test_storage_inventory.py`](../../tests/test_storage_inventory.py). Inventory and approval state never execute retention actions. |
| Validation-evidence publication protocol | Neutral owner [`validation_report.py`](../../src/norad/libraries/validation_report.py) with exact-file private loaders in ten final owner validators through `partition_BAM_by_mechanical_read_orientation` and three remaining flat validators; no package/import identity or public CLI is assigned to the library | [`test_validation_report.py`](../../tests/libraries/test_validation_report.py), [`test_validation_check_rosters.py`](../../tests/test_validation_check_rosters.py). Stage parsing/check rosters remain stage-owned, and current validation still does not enforce report-row order. |
| BAM validation primitives | Neutral private owner [`bam_validation.py`](../../src/norad/libraries/bam_validation.py) exact-loaded by the final Step `02`, Step `04`, and Step `05` validators; no package/import identity or public CLI is assigned | [`test_bam_validation.py`](../../tests/libraries/test_bam_validation.py) protects exact helper behavior and loader integrity. Stage-specific checks, arguments, reports, and evidence remain with their three functional owners. |
| Artifact contracts and indexing | [`validate_artifact_contracts.py`](../../scripts/validate_artifact_contracts.py), [`build_artifact_index.py`](../../scripts/build_artifact_index.py), [`schemas/artifacts/v1/`](../../schemas/artifacts/v1/) | [`test_artifact_schema_contracts.py`](../../tests/test_artifact_schema_contracts.py), [`test_artifact_adapters.py`](../../tests/test_artifact_adapters.py). Generic inventory mechanics belong here; native adapter semantics remain with their functional owners. |
| Canonical run-summary assembly | [`build_run_summary.py`](../../scripts/build_run_summary.py), private helper [`_run_summary_science.py`](../../scripts/_run_summary_science.py) | [`test_artifact_run_summary.py`](../../tests/test_artifact_run_summary.py). This normalizes one declared artifact transaction and optional exact review inputs without owning Step `09c` policy. |
| Static reporting | [`render_run_report.sh`](../../scripts/render_run_report.sh), [`render_run_report.py`](../../scripts/render_run_report.py), [`render_run_report_bundle.py`](../../scripts/render_run_report_bundle.py), [`reports/`](../../reports/); Make `demo-report` and `report-test` | [shell renderer contract](../../tests/shell/test_render_run_report.sh), [`test_report_html_v1.py`](../../tests/test_report_html_v1.py), [`test_report_exports_v1.py`](../../tests/test_report_exports_v1.py). Rendering consumes one canonical summary and never reruns analysis. |

## Repository-development interfaces

These public repository interfaces are deliberately outside the product
pipeline owner graph but still receive one owner:

| Current owner | Public surfaces assigned here | Direct protection and boundary |
| --- | --- | --- |
| Scheduler scaffolding | [`template.slurm`](../../jobs/template.slurm) | [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). This is a future-job template/probe, not a pipeline stage. |
| Documentation/Git orchestration | Public commands in [`scripts/git_orchestration/`](../../scripts/git_orchestration/): `apply_fragment_candidate.sh`, `finalize_fragment_integration.sh`, `publish_exact_ref.sh`, `record_fragment_noop.sh`, `validate_documentation.py`, `validate_fragment_candidate.py`, and `validate_fragment_target.py` | [`tests/git_orchestration/`](../../tests/git_orchestration/), [public CLI contracts](../../tests/test_public_cli_contracts.py). These operate on repository state, never scientific artifacts or evidence state. |
| Developer quality gates | Make `all-checks`, `lint`, `local-real-r-test`, `python-coverage-baseline-update`, `python-coverage-check`, `python-coverage-measure`, `real-r-test`, `shell-test`, `smoke`, `test`, `validation-guarded-r`, `validation-python-coverage`, `validation-report-runtime`, `validation-shell-contracts`, and `validation-static` in the [`Makefile`](../../Makefile) | [literal Make expansions](../../tests/fixtures/public_cli_contracts/make_target_expansions.json), [public CLI contracts](../../tests/test_public_cli_contracts.py), [`test_python_coverage_baseline.py`](../../tests/test_python_coverage_baseline.py). These are development gates, not workflow stages. |
| Demonstration facade | Make `demo-step03` and `demo-step03-dry-run` in the [`Makefile`](../../Makefile) | [literal Make expansions](../../tests/fixtures/public_cli_contracts/make_target_expansions.json). They submit the existing Step `03` wrapper and do not own Step `03` behavior. |

## Private-library and mixed-ownership findings

Private helpers do not add public owners:

- [`_run_summary_science.py`](../../scripts/_run_summary_science.py) belongs to
  canonical-summary normalization.
- [`git_orchestration/_common.py`](../../scripts/git_orchestration/_common.py)
  and [`_common.sh`](../../scripts/git_orchestration/_common.sh) belong to
  documentation/Git orchestration.
- Shared validation-report publication belongs to the neutral
  [`validation_report.py`](../../src/norad/libraries/validation_report.py)
  owner. Ten final owner validators and three legacy-path validators use
  exact-file private loaders until any later packaging decision or
  functional-owner migration.
- Shared samtools execution and BAM-header parsing belong to neutral private
  [`bam_validation.py`](../../src/norad/libraries/bam_validation.py). The final
  Step `02`, Step `04`, and Step `05` validators exact-load it; no
  peer-stage implementation import remains.
- Reusable Step `08`/`09` schemas and validators currently belong to the Step
  `09c` implementation and are imported upstream.
- Base intake validation does not require `replicate`, while the Step `09` and
  `09c` analysis profile does; that is a base contract plus a stricter consumer
  refinement, not two interchangeable manifest definitions.
- Step `07` owns partition selection semantics. Steps `08` and `09` consume
  the duplicated schema but do not become additional selection owners.
- [`reference_provenance.py`](../../scripts/reference_provenance.py) spans the
  `00a`/`00b`/`00c` bundle and remains cross-cutting even when a stage contract
  links to it.
- The artifact-index implementation embeds stage-specific reconciliation, but
  those adapter semantics remain accountable to the corresponding stage,
  evidence, or analysis owner.

The last two are observed reverse-dependency and responsibility leaks, not a
decision to preserve those owners in the target architecture. Extraction and
shared-library ownership remain deferred to the approved follow-on cards.

## Coverage result

The protected current roster contains 25 public Python entry points (19 under
`scripts/` and six final owner-local entry points), 13 shell entry points (ten
under `scripts/` and three final owner-local producers), 4 R entry points, 7
Git-orchestration entry points, 16 SLURM jobs (11 under `jobs/` and five final
owner-local jobs), and 23 public Make targets. Every member is assigned once
above. The one private top-level Python module, two neutral library sources,
and three private orchestration files are classified separately. No current
autonomous pipeline orchestrator,
ingestion executor, or installable-package entry point exists.
