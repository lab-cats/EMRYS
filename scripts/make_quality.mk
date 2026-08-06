PYTHON_COVERAGE_VERSION := 7.15.2

SHELL_SYNTAX_PATHS := \
	src/norad/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
	src/norad/reporting/render_run_report.sh \
	src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
	src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
	src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
	src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
	src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh \
	src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh \
	src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh \
	src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh \
	src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
	src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh \
	src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh \
	src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.sh

SLURM_SYNTAX_PATHS := \
	src/norad/evidence/runtime_preflight/tool_check.slurm \
	src/norad/ingestion/sample_manifest_admission/validate_manifest.slurm \
	src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm \
	src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm \
	src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm \
	src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm \
	src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm \
	src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm \
	src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm \
	src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.slurm \
	src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.slurm \
	src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.slurm \
	src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm \
	src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.slurm \
	src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.slurm

documentation-check:
	./scripts/git_orchestration/validate_documentation.py --repo "$(CURDIR)"

validation-shell-contracts:
	bash tests/stages/construct_FASTA_sidecars/test_step_00c_prepare_gatk_reference.sh
	bash tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh
	bash tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh
	bash tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh
	bash tests/evidence/collect_RSeQC_paired_orientation_evidence/test_step_03_infer_strandedness_and_orientation.sh
	bash tests/stages/mark_BAM_duplicates_with_Picard/test_step_04_mark_duplicates.sh
	bash tests/stages/split_N_cigar_reads_with_GATK/test_step_05_split_n_cigar_reads.sh
	bash tests/stages/partition_BAM_by_mechanical_read_orientation/test_step_06_split_bam_by_read_orientation.sh
	bash tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
	bash tests/stages/preprocess_and_annotate_cohort_candidates/test_step_08_vcf_preprocessing.sh
	bash tests/analyses/rank_cohort_candidates_with_paired_CMH/test_step_09_cmh_editing_site_calling.sh
	bash tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.sh
	bash tests/shell/test_local_r_environment.sh
	bash tests/reporting/test_render_run_report.sh

shell-test: validation-shell-contracts
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/runtime_preflight/test_runtime_preflight.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/reference_provenance/test_reference_provenance.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/libraries/test_reference_contigs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/storage_inventory/test_storage_inventory.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/ingestion/sample_manifest_admission/test_check_fastq_pairs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/collect_RSeQC_paired_orientation_evidence/test_validate_step_03_rseqc_orientation.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/mark_BAM_duplicates_with_Picard/test_validate_step_04_mark_duplicates.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/split_N_cigar_reads_with_GATK/test_validate_step_05_split_ncigar.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/partition_BAM_by_mechanical_read_orientation/test_validate_step_06_orientation_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py

real-r-test:
	bash tests/stages/preprocess_and_annotate_cohort_candidates/run_step_08_vcf_preprocessing_tests.sh
	bash tests/analyses/rank_cohort_candidates_with_paired_CMH/run_step_09_cmh_tests.sh

r-restore:
	NORAD_USE_RENV=1 RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		"$(RSCRIPT_BIN)" scripts/restore_r_environment.R

r-check:
	NORAD_USE_RENV=1 RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		"$(RSCRIPT_BIN)" scripts/check_r_environment.R

local-real-r-test:
	NORAD_USE_RENV=1 RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		STEP08_TEST_RSCRIPT_BIN= STEP09_TEST_RSCRIPT_BIN= \
		RSCRIPT_BIN_OVERRIDE="$(RSCRIPT_BIN)" \
		$(MAKE) real-r-test

python-coverage-measure:
	test "$$("$(REPORT_PYTHON_BIN)" -c \
		'import importlib.metadata; print(importlib.metadata.version("coverage"))')" \
		= "$(PYTHON_COVERAGE_VERSION)"
	mkdir -p "$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage erase
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage run \
		--rcfile="$(CURDIR)/.coveragerc" -m pytest \
		$(PYTHON_COVERAGE_PYTEST_ARGS)
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage combine -q \
		"$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage json \
		--rcfile="$(CURDIR)/.coveragerc" \
		-o "$(PYTHON_COVERAGE_RAW)"
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py build \
		--coverage-json "$(PYTHON_COVERAGE_RAW)" \
		--output "$(PYTHON_COVERAGE_CURRENT)"

python-coverage-check: python-coverage-measure
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py check \
		--baseline "$(PYTHON_COVERAGE_BASELINE)" \
		--current "$(PYTHON_COVERAGE_CURRENT)" \
		--new-shared-module scripts/git_orchestration/_common.py \
		--new-shared-module src/norad/contracts/scientific_evidence/step08.py \
		--new-shared-module src/norad/contracts/scientific_evidence/step09.py \
		--new-shared-module src/norad/contracts/scientific_evidence/review_package.py \
		--new-shared-module src/norad/libraries/validation_report.py \
		--new-shared-module src/norad/libraries/bam_validation.py \
		--new-shared-module src/norad/libraries/reference_contigs.py

python-coverage-baseline-update: python-coverage-measure
	cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"

validation-python-coverage: python-coverage-check

validation-guarded-r:
	$(MAKE) -s r-check
	$(MAKE) -s local-real-r-test

validation-static:
	git diff --check
	bash -n $(SHELL_SYNTAX_PATHS)
	bash -n scripts/git_orchestration/*.sh
	bash -n $(SLURM_SYNTAX_PATHS)
	PYTHONDONTWRITEBYTECODE=1 \
		"$(REPORT_PYTHON_BIN)" -m compileall -q scripts src/norad tests
	"$(REPORT_PYTHON_BIN)" src/norad/ingestion/sample_manifest_admission/validate_manifest.py \
		--manifest configs/samples.example.tsv

validate:
	python src/norad/ingestion/sample_manifest_admission/validate_manifest.py --manifest configs/samples.example.tsv

smoke:
	bash -n $(SHELL_SYNTAX_PATHS)
	bash -n scripts/git_orchestration/*.sh
	bash -n $(SLURM_SYNTAX_PATHS)

lint:
	python -m compileall scripts src/norad tests

all-checks:
	"$(REPORT_PYTHON_BIN)" tests/tools/run_validation.py \
		--repo-root "$(CURDIR)" \
		--python-bin "$(REPORT_PYTHON_BIN)" \
		--rscript-bin "$(RSCRIPT_BIN)" \
		--jobs "$(VALIDATION_JOBS)" \
		--python-workers "$(VALIDATION_PYTHON_WORKERS)" $(VALIDATION_ARGS)
