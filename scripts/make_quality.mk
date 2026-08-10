PYTHON_COVERAGE_VERSION := 7.15.2
RUFF_VERSION := 0.16.2
VULTURE_VERSION := 2.16
SHELLCHECK_BIN ?= shellcheck
SHFMT_BIN ?= shfmt
RUFF_BIN ?= ruff
VULTURE_BIN ?= vulture
DEAD_CODE_PATHS ?= scripts src/norad
PYTHON_LINT_PATHS ?= scripts src/norad tests
VULTURE_MIN_CONFIDENCE ?= 95

SHELL_SYNTAX_PATHS := \
	src/norad/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
	src/norad/reporting/render_run_report.sh \
	src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
	src/norad/stages/star_alignment/step_01_star_align.sh \
	src/norad/stages/canonical_bam/step_02_sort_index_bam.sh \
	src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
	src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
	src/norad/stages/duplicate_marking/step_04_mark_duplicates.sh \
	src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.sh \
	src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh \
	src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
	src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh \
	src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.sh \
	src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.sh

SLURM_SYNTAX_PATHS := \
	src/norad/evidence/runtime_preflight/tool_check.slurm \
	src/norad/ingestion/sample_manifest_admission/validate_manifest.slurm \
	src/norad/stages/star_index/step_00a_build_novogene_star_index.slurm \
	src/norad/stages/gtf_to_bed12/step_00b_gtf_to_bed12.slurm \
	src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.slurm \
	src/norad/stages/star_alignment/step_01_star_align.slurm \
	src/norad/stages/canonical_bam/step_02_sort_index_bam.slurm \
	src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.slurm \
	src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.slurm \
	src/norad/stages/duplicate_marking/step_04_mark_duplicates.slurm \
	src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.slurm \
	src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.slurm \
	src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm \
	src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.slurm \
	src/norad/analyses/rank_cohort_candidates_with_paired_CMH/step_09_cmh_editing_site_calling.slurm

documentation-check:
	./scripts/git_orchestration/validate_documentation.py --repo "$(CURDIR)"

validation-shell-contracts:
	bash tests/libraries/test_file_checks.sh
	bash tests/stages/fasta_sidecars/test_step_00c_prepare_gatk_reference.sh
	bash tests/stages/star_alignment/test_step_01_star_align.sh
	bash tests/stages/canonical_bam/test_step_02_sort_index_bam.sh
	bash tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh
	bash tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh
	bash tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh
	bash tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh
	bash tests/stages/mechanical_orientation/test_step_06_split_bam_by_read_orientation.sh
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
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/star_index/test_validate_step_00a_star_index.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/gtf_to_bed12/test_validate_step_00b_bed12.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/fasta_sidecars/test_validate_step_00c_reference_sidecars.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/star_alignment/test_validate_step_01_star_alignment.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/canonical_bam/test_validate_step_02_canonical_bam.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/canonical_bam_qc/test_validate_step_02b_bam_qc.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/evidence/rseqc_orientation/test_validate_step_03_rseqc_orientation.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/duplicate_marking/test_validate_step_04_mark_duplicates.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/split_n_cigar/test_validate_step_05_split_ncigar.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/mechanical_orientation/test_validate_step_06_orientation_outputs.py
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
		--new-shared-module src/norad/contracts/scientific_evidence/step08.py \
		--new-shared-module src/norad/contracts/scientific_evidence/step09.py \
		--new-shared-module src/norad/contracts/scientific_evidence/review_package.py \
		--new-shared-module src/norad/libraries/validation/errors.py \
		--new-shared-module src/norad/libraries/validation/inputs.py \
		--new-shared-module src/norad/libraries/validation/publication.py \
		--new-shared-module src/norad/libraries/validation/report.py \
		--new-shared-module src/norad/libraries/validation/runtime.py \
		--new-shared-module src/norad/libraries/alignments/bam.py \
		--new-shared-module src/norad/libraries/alignments/bed.py \
		--new-shared-module src/norad/libraries/alignments/orientation.py \
		--new-shared-module src/norad/libraries/alignments/star.py \
		--new-shared-module src/norad/libraries/evidence/qc.py \
		--new-shared-module src/norad/libraries/quality/picard.py \
		--new-shared-module src/norad/libraries/validation/mpileup.py \
		--new-shared-module src/norad/libraries/references/contigs.py

python-coverage-baseline-update: python-coverage-measure
	cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"

validation-guarded-r:
	$(MAKE) -s r-check
	$(MAKE) -s local-real-r-test

define STATIC_SHELL_CHECKS
bash -n $(SHELL_SYNTAX_PATHS)
bash -n $(SLURM_SYNTAX_PATHS)
endef

validation-static: lint
	git diff --check
	$(STATIC_SHELL_CHECKS)
	PYTHONDONTWRITEBYTECODE=1 \
		"$(REPORT_PYTHON_BIN)" -m compileall -q scripts src/norad tests
	"$(REPORT_PYTHON_BIN)" -I -m norad validate manifest \
		--manifest configs/samples.example.tsv

validate:
	"$(REPORT_PYTHON_BIN)" -I -m norad validate manifest \
		--manifest configs/samples.example.tsv

smoke:
	$(STATIC_SHELL_CHECKS)

lint:
	test "$$("$(REPORT_PYTHON_BIN)" -c 'import importlib.metadata; print(importlib.metadata.version("ruff"))')" = "$(RUFF_VERSION)"
	test "$$("$(REPORT_PYTHON_BIN)" -c 'import importlib.metadata; print(importlib.metadata.version("vulture"))')" = "$(VULTURE_VERSION)"
	"$(REPORT_PYTHON_BIN)" -m "$(RUFF_BIN)" check --no-cache $(PYTHON_LINT_PATHS)
	"$(REPORT_PYTHON_BIN)" -m "$(VULTURE_BIN)" \
		--min-confidence $(VULTURE_MIN_CONFIDENCE) \
		$(DEAD_CODE_PATHS)

all-checks:
	"$(REPORT_PYTHON_BIN)" tests/tools/run_validation.py \
		--repo-root "$(CURDIR)" \
		--python-bin "$(REPORT_PYTHON_BIN)" \
		--rscript-bin "$(RSCRIPT_BIN)" \
		--jobs "$(VALIDATION_JOBS)" \
		--python-workers "$(VALIDATION_PYTHON_WORKERS)" $(VALIDATION_ARGS)
