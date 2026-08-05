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
| [`07` — `generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md) | [`step_07_bcftools_mpileup_by_chrom_and_strand.sh`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh), [`step_07_bcftools_mpileup_by_chrom_and_strand.slurm`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm) | [`validate_step_07_mpileup_outputs.py`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/validate_step_07_mpileup_outputs.py) | [shell contract](../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh), [`test_validate_step_07_mpileup_outputs.py`](../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`08` — `preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md) | [`step_08_vcf_preprocessing.sh`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh), [`step_08_vcf_preprocessing.R`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.R), [`step_08_vcf_preprocessing.slurm`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.slurm) | [`validate_step_08_preprocessing_outputs.py`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/validate_step_08_preprocessing_outputs.py) | [shell contract](../../tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.sh), [R contract](../../tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.R), [`test_validate_step_08_preprocessing_outputs.py`](../../tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py) |
| [`09` — `rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md) | [`step_09_cmh_editing_site_calling.sh`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh), [`step_09_cmh_editing_site_calling.R`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.R), [`step_09_cmh_editing_site_calling.slurm`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.slurm) | [`validate_step_09_cmh_outputs.py`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/validate_step_09_cmh_outputs.py) | [shell contract](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.sh), [R contract](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.R), [neutral contract](../../tests/contracts/scientific_evidence/test_step09.py), [`test_validate_step_09_cmh_outputs.py`](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py), [independent oracle](../../tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_oracle.py) |
| [`09c` — `assemble_scientific_review_evidence_package`](../../src/norad/evidence/assemble_scientific_review_evidence_package/CONTRACT.md) | [`step_09c_scientific_validation.sh`](../../src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.sh), [`step_09c_scientific_validation.py`](../../src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.py); no SLURM wrapper | No separate validator: the Python entry point validates and publishes the package | [shell contract](../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.sh), [`test_step_09c_scientific_validation.py`](../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py) |

All numbered scheduler wrappers belong to the same owner as their delegated
operation. Scheduler concerns are a boundary around a stage, not additional
scientific stages.

## Cross-cutting product and operational owners

| Current functional owner | Public surfaces assigned here | Direct protection and boundary |
| --- | --- | --- |
| Intake contract validation | [`validate_manifest.py`](../../scripts/validate_manifest.py), [`validate_manifest.slurm`](../../jobs/validate_manifest.slurm), [`samples.example.tsv`](../../samples.example.tsv), Make `validate` in the [`Makefile`](../../Makefile) | [`test_validate_manifest.py`](../../tests/test_validate_manifest.py), [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). This validates current manifest input; it is not an ingestion runner. |
| Reference provenance evidence | Final owner [`reference_provenance.py`](../../src/norad/evidence/reference_provenance/reference_provenance.py), public starter [`reference_provenance.example.tsv`](../../configs/reference_provenance.example.tsv) | Mirrored [`test_reference_provenance.py`](../../tests/evidence/reference_provenance/test_reference_provenance.py). This inventories declared reference identity and consistency without repairing reference artifacts. Through completed [`LIB-02K`](../tasks/COMPLETED/LIB-02K-extract-reference-contig-parser-library.md) and [`MIG-04B`](../tasks/COMPLETED/MIG-04B-migrate-reference-provenance-to-final-evidence-owner.md), it occupies its final evidence home and consumes the one neutral `reference_contigs` identity shared with the final Step `00c`/`05` validators while consumer-specific aggregation and evidence remain local. |
| Structured runtime inspection | Final owner [`runtime_preflight.py`](../../src/norad/evidence/runtime_preflight/runtime_preflight.py), public starter [`runtime_preflight.example.tsv`](../../configs/runtime_preflight.example.tsv) | Mirrored [`test_runtime_preflight.py`](../../tests/evidence/runtime_preflight/test_runtime_preflight.py). Through completed [`MIG-04C`](../tasks/COMPLETED/MIG-04C-migrate-runtime-preflight-to-final-evidence-owner.md), the command and direct suite occupy their final evidence-owner homes. Profile-driven availability evidence does not establish workflow runtime or cluster proof. |
| Legacy manual cluster probe | [`tool_check.slurm`](../../jobs/tool_check.slurm) | [Wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). It emits scheduler logs rather than a structured runtime-preflight transaction and is not a compute stage. |
| Dependency lifecycle | [`check_r_environment.R`](../../scripts/check_r_environment.R), [`restore_r_environment.R`](../../scripts/restore_r_environment.R), [`restore_quarto.py`](../../scripts/restore_quarto.py); Make `r-check`, `r-restore`, and `quarto-restore` | [local R contract](../../tests/shell/test_local_r_environment.sh), [`test_quarto_restore.py`](../../tests/test_quarto_restore.py), [public Make contracts](../../tests/test_public_cli_contracts.py). Restoration is explicit operator mutation, never compute-time bootstrap. |
| Storage evidence | Final owner [`storage_inventory.py`](../../src/norad/evidence/storage_inventory/storage_inventory.py), public starters [`storage_roots.example.tsv`](../../configs/storage_roots.example.tsv) and [`retention_policy.example.tsv`](../../configs/retention_policy.example.tsv) | Mirrored [`test_storage_inventory.py`](../../tests/evidence/storage_inventory/test_storage_inventory.py). Through completed [`MIG-04D`](../tasks/COMPLETED/MIG-04D-migrate-storage-inventory-to-final-evidence-owner.md), the command and direct suite occupy their final evidence-owner homes while both public starter contracts remain at root. Inventory and approval state never execute retention actions. |
| Validation-evidence publication protocol | Neutral owner [`validation_report.py`](../../src/norad/libraries/validation_report.py) with exact-file private loaders in all thirteen final owner validators through `rank_cohort_candidates_with_paired_CMH`; no package/import identity or public CLI is assigned to the library | [`test_validation_report.py`](../../tests/libraries/test_validation_report.py), [`test_validation_check_rosters.py`](../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py). Through completed [`MIG-04F`](../tasks/COMPLETED/MIG-04F-converge-validation-roster-agreement.md), validation-roster agreement occupies its final contract-integration owner. Stage parsing/check rosters remain stage-owned, and current validation still does not enforce report-row order. |
| BAM validation primitives | Neutral private owner [`bam_validation.py`](../../src/norad/libraries/bam_validation.py) exact-loaded by the final Step `02`, Step `04`, and Step `05` validators; no package/import identity or public CLI is assigned | [`test_bam_validation.py`](../../tests/libraries/test_bam_validation.py) protects exact helper behavior and loader integrity. Stage-specific checks, arguments, reports, and evidence remain with their three functional owners. |
| Reference contig parsing | Neutral private owner [`reference_contigs.py`](../../src/norad/libraries/reference_contigs.py) exact-loaded by reference provenance and the final Step `00c` and Step `05` validators; no package/import identity or public CLI is assigned | [`test_reference_contigs.py`](../../tests/libraries/test_reference_contigs.py) plus the three affected consumer suites protect exact parser behavior and one ready owner identity. Agreement, per-role versus short-circuit aggregation, evidence, commands, and publication remain consumer-local. |
| Artifact contract validation | Neutral [`validate_artifact_contracts.py`](../../src/norad/contracts/artifacts/validate_artifact_contracts.py) and five public schemas under [`contracts/schemas/artifacts/v1/`](../../src/norad/contracts/schemas/artifacts/v1/) | Mirrored [`test_artifact_schema_contracts.py`](../../tests/contracts/artifacts/test_artifact_schema_contracts.py) and [`artifact_schema_v1`](../../tests/contracts/artifacts/fixtures/artifact_schema_v1/) fixtures. The five Python reporting-chain consumers share this one exact final module identity, and the shell preflight exact-loads the final file without package or path setup; schema identity and validation semantics remain neutral. |
| Step `08` scientific-evidence contract | Neutral [`step08.py`](../../src/norad/contracts/scientific_evidence/step08.py); no public CLI, package identity, or installation surface | Mirrored [`test_step08.py`](../../tests/contracts/scientific_evidence/test_step08.py) plus affected consumer suites. Neutral Step `09`, the Step `08` and Step `09` validators, Step `09c`, and the artifact index share one exact-file module, `ContractError`, and `Table` identity. Shell/R algorithms, review policy, publication, and artifact reconciliation remain owner-local. |
| Step `09` scientific-evidence contract | Neutral [`step09.py`](../../src/norad/contracts/scientific_evidence/step09.py); no public CLI, package identity, or installation surface | Mirrored [`test_step09.py`](../../tests/contracts/scientific_evidence/test_step09.py) plus affected consumer suites. The owner exact-loads neutral Step `08`; the Step `09` validator, Step `09c`, and artifact index share one exact ready module identity. Step `09` shell/R method, Step `09c` review policy/publication, and artifact reconciliation remain owner-local. |
| Step `09c` review-package contract | Neutral [`review_package.py`](../../src/norad/contracts/scientific_evidence/review_package.py); no public CLI, package identity, or installation surface | Mirrored [`test_review_package.py`](../../tests/contracts/scientific_evidence/test_review_package.py) plus affected consumer suites. Step `09c`, artifact indexing, and run-summary science share one exact ready module identity for the public thirteen-file roster, headers, vocabularies, bindings, and state reducer. Step `09c` retains review/input policy, context, validation, publication, locking, rollback, and recovery. |
| Artifact indexing | [`build_artifact_index.py`](../../src/norad/reporting/build_artifact_index.py), public starter [`artifact_inventory.example.tsv`](../../configs/artifact_inventory.example.tsv) | [`test_artifact_adapters.py`](../../tests/reporting/test_artifact_adapters.py) and its adjacent fixture builder. Generic inventory mechanics belong here; native adapter semantics remain with their functional owners. Artifact indexing consumes the neutral Step `08`, Step `09`, and review-package contracts, has no private Step `09c` dependency, and keeps index reconciliation independently implemented. |
| Canonical run-summary assembly | [`build_run_summary.py`](../../src/norad/reporting/build_run_summary.py), private helper [`_run_summary_science.py`](../../src/norad/reporting/_run_summary_science.py), public starter [`artifact_run_contract.example.json`](../../configs/artifact_run_contract.example.json) | [`test_artifact_run_summary.py`](../../tests/reporting/test_artifact_run_summary.py) and its adjacent fixture builder. The helper exact-loads the neutral review-package contract and uses a reporting-local reader/projection over the committed public thirteen-file package, explicitly referenced evidence, and validated index records. It does not load Step `09c`, revalidate private Step `09c` source inputs, or own review/evidence policy. |
| Static reporting | [`render_run_report.sh`](../../src/norad/reporting/render_run_report.sh), [`render_run_report.py`](../../src/norad/reporting/render_run_report.py), [`render_run_report_bundle.py`](../../src/norad/reporting/render_run_report_bundle.py), owned [`templates/`](../../src/norad/reporting/templates/) and [`styles/`](../../src/norad/reporting/styles/), public starter [`report_table_approvals.example.tsv`](../../configs/report_table_approvals.example.tsv); Make `demo-report` and `report-test` | [shell renderer contract](../../tests/reporting/test_render_run_report.sh), [`test_report_html_v1.py`](../../tests/reporting/test_report_html_v1.py), [`test_report_exports_v1.py`](../../tests/reporting/test_report_exports_v1.py), and report fixtures under [`report_html_v1/`](../../tests/reporting/fixtures/report_html_v1/). Rendering consumes one canonical summary and never reruns analysis. |

## Repository-development interfaces

These public repository interfaces are deliberately outside the product
pipeline owner graph but still receive one owner:

| Current owner | Public surfaces assigned here | Direct protection and boundary |
| --- | --- | --- |
| Scheduler scaffolding | [`template.slurm`](../../jobs/template.slurm) | [wrapper contracts](../../tests/test_slurm_wrapper_contracts.py). This is a future-job template/probe, not a pipeline stage. |
| Documentation/Git orchestration | Public commands in [`scripts/git_orchestration/`](../../scripts/git_orchestration/): `apply_fragment_candidate.sh`, `finalize_fragment_integration.sh`, `publish_exact_ref.sh`, `record_fragment_noop.sh`, `validate_documentation.py`, `validate_fragment_candidate.py`, and `validate_fragment_target.py` | [`tests/git_orchestration/`](../../tests/git_orchestration/), [public CLI contracts](../../tests/test_public_cli_contracts.py). These operate on repository state, never scientific artifacts or evidence state. |
| Developer quality gates | Make `all-checks`, `lint`, `local-real-r-test`, `python-coverage-baseline-update`, `python-coverage-check`, `python-coverage-measure`, `real-r-test`, `shell-test`, `smoke`, `test`, `validation-guarded-r`, `validation-python-coverage`, `validation-report-runtime`, `validation-shell-contracts`, and `validation-static` in the [`Makefile`](../../Makefile) | [literal Make expansions](../../tests/fixtures/public_cli_contracts/make_target_expansions.json), [public CLI contracts](../../tests/test_public_cli_contracts.py), [`test_python_coverage_baseline.py`](../../tests/test_python_coverage_baseline.py). These are development gates, not workflow stages. |
| Demonstration facade | Make `demo-step03` and `demo-step03-dry-run` in the [`Makefile`](../../Makefile) | [literal Make expansions](../../tests/fixtures/public_cli_contracts/make_target_expansions.json). They submit the existing Step `03` wrapper and do not own Step `03` behavior. |

## Residual tracked-path coverage

`PLAN-03A` inspected the tracked residual implementation-bearing roots,
remaining shared/root test surfaces, top-level developer inputs, project
environment anchors, and intentional operational placeholders. The 87 paths
are partitioned once below. Counts are inspection checks, not a permanent
repository-size baseline; each later owner migration updates this current
inventory when paths move.

| Exact current path group | Paths | Current owner or boundary |
| --- | ---: | --- |
| `scripts/{check_r_environment.R,restore_r_environment.R,restore_quarto.py}`; `tests/shell/test_local_r_environment.sh`; `tests/test_quarto_restore.py` | 5 | Explicit repository dependency lifecycle; intentionally repository-level pending any separately approved setup redesign. |
| All ten tracked `scripts/git_orchestration/` paths and all seven tracked `tests/git_orchestration/` paths | 17 | Repository documentation/Git orchestration; intentionally outside scientific-workflow orchestration. |
| The 26 non-profile files under root `configs/`: three reporting starters, one reference starter, one runtime starter, two storage/retention starters, three Step `07` operator inputs, one Step `09` reference manifest, and fifteen Step `09c` examples/schema references | 26 | Public operator/reference inputs retained at root; they are not owner-native implementation assets. |
| `tests/baselines/python_coverage.json`; `tests/test_python_coverage_baseline.py`; `tests/test_validation_orchestrator.py`; both `tests/tools/` files; `tests/test_public_cli_contracts.py` and its two fixture paths | 8 | Repository quality-gate, coverage, and cross-entry-point command infrastructure retained at repository level. The public-command suite spans Make, Git tooling, modes, and multiple runtime domains, so it is not a neutral artifact-contract integration test. |
| `.Rprofile`, `.coveragerc`, `.gitignore`, `AGENTS.md`, `Makefile`, `README.md`, `TODO.md`, `pytest.ini`, `renv.lock`, `requirements.txt`; all three tracked `renv/` project files; five tracked `data/test`, `logs`, `refs`, and `results` `.gitkeep` anchors | 18 | Project configuration, documentation routing, dependency environment, and intentional operational/fixture roots retained at repository level. |
| `scripts/validate_manifest.py`; `jobs/validate_manifest.slurm`; `samples.example.tsv`; `tests/test_validate_manifest.py`; `tests/data_checks/check_fastq_pairs.sh` | 5 | Deferred ingestion/admission family; current validator behavior remains supported but no ingestion runner exists. |
| `jobs/{template.slurm,tool_check.slurm}`; `tests/test_slurm_wrapper_contracts.py` | 3 | Deferred scheduler family and mixed wrapper characterization. Owner-specific scheduler assets already remain with their functional owners. |
| `configs/{cluster_full.yaml.example,local_test.yaml}` | 2 | Deferred runtime orchestration/profile inputs; no executable orchestrator exists. |
| `tests/data_checks/validate_step05_outputs.sh` | 1 | Permanent repository-level operational inspection utility through completed [`REVIEW-LEGACY-05A`](../tasks/COMPLETED/REVIEW-LEGACY-05A-confirm-step05-operational-checker-owner.md). It uniquely retains optional scheduler-state lookup, six-sample/cohort status aggregation, output-size and scratch inspection, additional `LB`/`PL` read-group requirements, a best-effort persisted twelve-column TSV snapshot, and aggregate exit `0`/`1`/`2` behavior not supplied by the final Step `05` validator. The duplicate truncating `tee` writers and silent replacement remain characterized defects. |
| `tests/pending/test_step_04_mark_duplicates.sh` | 1 | Intentional non-runnable pending-plan scaffold preserved unchanged during selected [`REVIEW-LEGACY-04A`](../tasks/IN_PROGRESS/REVIEW-LEGACY-04A-retire-step04-pending-test-scaffold.md) until its no-loss comparison records one final owner/retirement disposition. |
| `work/active/JIT-01.md` | 1 | `RETIRE` through existing [`DOC-CONS-08H`](../tasks/TODO/DOC-CONS-08H-retire-jit-temporary-work-record.md), which must first preserve both unique cleanup entries in authorized owners. It is not source-migration scope. |

The table does not reclassify already final owner-local paths under
`src/norad/` or mirrored `tests/stages/`, `tests/analyses/`,
`tests/evidence/`, `tests/libraries/`, and `tests/contract_integration/`. Root
callers such as `Makefile`,
coverage rows, command rosters, and current documentation remain integration
surfaces to update atomically when a `MOVE` unit is approved; their own
repository-level ownership does not change.

The current executable layout is deliberately mode-nonuniform: final reporting
`build_artifact_index.py` and `render_run_report_bundle.py` plus final owner-
local `storage_inventory.py` are `0644`, while reporting-private
`_run_summary_science.py` is `0755`. Each JIT card refreshes every touched mode
and preserves it; relocation does not normalize executability by filename or
language.

## Private-library and mixed-ownership findings

Private helpers do not add public owners:

- [`_run_summary_science.py`](../../src/norad/reporting/_run_summary_science.py) belongs to
  canonical-summary normalization.
- [`git_orchestration/_common.py`](../../scripts/git_orchestration/_common.py)
  and [`_common.sh`](../../scripts/git_orchestration/_common.sh) belong to
  documentation/Git orchestration.
- Shared validation-report publication belongs to the neutral
  [`validation_report.py`](../../src/norad/libraries/validation_report.py)
  owner. All thirteen final owner validators use exact-file private loaders
  until any later packaging decision.
- Shared samtools execution and BAM-header parsing belong to neutral private
  [`bam_validation.py`](../../src/norad/libraries/bam_validation.py). The final
  Step `02`, Step `04`, and Step `05` validators exact-load it; no
  peer-stage implementation import remains.
- Reusable Step `08` schemas and validators belong to neutral
  [`step08.py`](../../src/norad/contracts/scientific_evidence/step08.py) and are
  exact-loaded under one shared identity. Reusable Step `09` schemas and
  validators belong to neutral
  [`step09.py`](../../src/norad/contracts/scientific_evidence/step09.py), which
  reuses the Step `08` error/table identity and is exact-loaded under one shared
  ready-owner identity. The public review-package roster, headers,
  vocabularies, bindings, and state reducer belong to neutral
  [`review_package.py`](../../src/norad/contracts/scientific_evidence/review_package.py)
  and are exact-loaded under one shared ready-owner identity. Step `09c`
  review policy, evidence sources, context, publication, rollback, and recovery
  remain local.
- Base intake validation does not require `replicate`, while the Step `09` and
  `09c` analysis profile does; that is a base contract plus a stricter consumer
  refinement, not two interchangeable manifest definitions.
- Step `07` owns partition selection semantics. Steps `08` and `09` consume
  the duplicated schema but do not become additional selection owners.
- [`reference_provenance.py`](../../src/norad/evidence/reference_provenance/reference_provenance.py) spans the
  `00a`/`00b`/`00c` bundle and remains cross-cutting even when a stage contract
  links to it. Its shared FASTA/FAI/DICT parsing is final under neutral
  `reference_contigs` through `LIB-02K`; the provenance CLI, hashing,
  reconciliation, evidence, publication, and recovery remain evidence-owner
  behavior. Its direct source and mirrored suite are final through completed
  `MIG-04B`.
- The artifact-index implementation embeds stage-specific reconciliation, but
  those adapter semantics remain accountable to the corresponding stage,
  evidence, or analysis owner.

The remaining reverse dependencies are temporary current-state facts, not
final ownership. Completed
[`LIB-02F`](../tasks/COMPLETED/LIB-02F-define-shared-library-ownership.md) fixes
their exact permanent dispositions, and
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#approved-neutral-shared-seams)
owns the target paths. The Step `08`, Step `09`, and public review-package
contract extractions and reporting-local dependency removal are implemented;
reference-contig parsing is also implemented through completed `LIB-02K`.

## Coverage result

The protected current roster contains 25 public Python entry points (two under
`scripts/` and 23 final owner-local entry points), 13 final owner-local shell
entry points, 4 R entry points, 7 Git-orchestration entry points, 16 SLURM jobs
(three under `jobs/` and 13 final owner-local jobs), and 24 public Make targets.
Every member is assigned once
above. The reporting-private Python module, three neutral library sources, four
neutral contract implementation sources, and three private orchestration files
are classified separately. No current
autonomous pipeline orchestrator,
ingestion executor, or installable-package entry point exists.
