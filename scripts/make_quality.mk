PYTHON_COVERAGE_VERSION := 7.15.2
SHELLCHECK_BIN ?= shellcheck
SHFMT_BIN ?= shfmt
RUFF_BIN ?= ruff
VULTURE_BIN ?= vulture
DEAD_CODE_PATHS ?= scripts src/norad
PYTHON_LINT_PATHS ?= scripts src/norad tests
VULTURE_MIN_CONFIDENCE ?= 95
PYTHON_COVERAGE_NEW_SHARED_MODULES ?=
PYTHON_COVERAGE_NEW_SHARED_ARGS = $(foreach module,$(PYTHON_COVERAGE_NEW_SHARED_MODULES),--new-shared-module $(module))
PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS = $(if $(strip $(PYTHON_COVERAGE_NEW_SHARED_MODULES)),--coverage-json "$(PYTHON_COVERAGE_RAW)" $(PYTHON_COVERAGE_NEW_SHARED_ARGS))
PYTHON_COVERAGE_EXCLUDES := \
	--ignore=tests/test_package_distribution.py \
	--ignore=tests/test_slurm_wrapper_contracts.py
PYTHON_SUBPROCESS_COVERAGE_DATA := $(PYTHON_COVERAGE_ROOT)/.coverage-subprocess
PYTHON_SUBPROCESS_COVERAGE_RAW := $(PYTHON_COVERAGE_ROOT)/subprocess-coverage.json
PYTHON_SUBPROCESS_COVERAGE_TESTS := \
	tests/stages/gtf_to_bed12/test_gtf_to_bed12.py \
	tests/ingestion/sample_manifest_admission/test_validate_manifest.py

SHELL_SYNTAX_PATHS := \
	src/norad/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
	src/norad/stages/star_index/step_00a_build_star_index.sh \
	src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
	src/norad/stages/star_alignment/step_01_star_align.sh \
	src/norad/stages/canonical_bam/step_02_sort_index_bam.sh \
	src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
	src/norad/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
	src/norad/stages/duplicate_marking/step_04_mark_duplicates.sh \
	src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.sh \
	src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh \
	src/norad/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
	src/norad/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh \
	src/norad/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.sh \
	src/norad/evidence/scientific_review_package/step_09c_scientific_validation.sh

SLURM_SYNTAX_PATHS := \
	src/norad/evidence/runtime_availability/tool_check.slurm \
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
	src/norad/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.slurm \
	src/norad/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.slurm \
	src/norad/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.slurm

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
	bash tests/stages/partitioned_cohort_mpileup/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
	bash tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.sh
	bash tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_editing_site_calling.sh
	bash tests/evidence/scientific_review_package/test_step_09c_scientific_validation.sh
	bash tests/shell/test_local_r_environment.sh

validation-shell-slurm: validation-shell-contracts
	"$(REPORT_PYTHON_BIN)" -m pytest -q --tb=short \
		tests/test_slurm_wrapper_contracts.py

shell-test: validation-shell-slurm

validation-wheel-smoke:
	"$(REPORT_PYTHON_BIN)" -m pytest -q --tb=short \
		tests/test_package_distribution.py

real-r-test:
	bash tests/stages/cohort_candidate_preprocessing/run_step_08_vcf_preprocessing_tests.sh
	bash tests/analyses/paired_cmh_candidate_ranking/run_step_09_cmh_tests.sh

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
		$(PYTHON_COVERAGE_EXCLUDES) $(PYTHON_COVERAGE_PYTEST_ARGS)
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage combine -q \
		"$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage json \
		--rcfile="$(CURDIR)/.coveragerc" \
		-o "$(PYTHON_COVERAGE_RAW)"
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage erase
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage run \
		--rcfile="$(CURDIR)/.coveragerc" \
		--source=scripts,src/norad,tests -m pytest -q \
		$(PYTHON_SUBPROCESS_COVERAGE_TESTS)
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage combine -q \
		"$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage json \
		--rcfile="$(CURDIR)/.coveragerc" \
		--include="scripts/*,src/norad/*" \
		-o "$(PYTHON_SUBPROCESS_COVERAGE_RAW)"
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py build \
		--coverage-json "$(PYTHON_COVERAGE_RAW)" \
		--subprocess-coverage-json "$(PYTHON_SUBPROCESS_COVERAGE_RAW)" \
		--output "$(PYTHON_COVERAGE_CURRENT)"

python-coverage-check: python-coverage-measure
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py check \
		--baseline "$(PYTHON_COVERAGE_BASELINE)" \
		--current "$(PYTHON_COVERAGE_CURRENT)"$(if $(PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS), $(PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS))

python-coverage-baseline-update: python-coverage-measure
	cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"

validation-guarded-r:
	$(MAKE) -s r-check
	$(MAKE) -s local-real-r-test

define STATIC_SHELL_CHECKS
bash -n $(SHELL_SYNTAX_PATHS)
bash -n $(SLURM_SYNTAX_PATHS)
endef

validation-static: lint documentation-check
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
