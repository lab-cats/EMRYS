PYTHON_COVERAGE_VERSION := 7.15.2
SHELLCHECK_BIN ?= shellcheck
SHFMT_BIN ?= shfmt
RUFF_BIN ?= ruff
VULTURE_BIN ?= vulture
DEAD_CODE_PATHS ?= scripts src/emrys
PYTHON_LINT_PATHS ?= scripts src/emrys tests
VULTURE_MIN_CONFIDENCE ?= 95
EMRYS_RENV_VERSION := 1.2.3
PYTHON_COVERAGE_NEW_SHARED_MODULES ?= \
	src/emrys/libraries/application_logging/controls.py \
	src/emrys/libraries/application_logging/handler.py \
	src/emrys/libraries/application_logging/helpers.py \
	src/emrys/libraries/application_logging/storage.py \
	src/emrys/libraries/installed_package_identity.py \
	src/emrys/libraries/process_environment.py
PYTHON_COVERAGE_NEW_SHARED_ARGS = $(foreach module,$(PYTHON_COVERAGE_NEW_SHARED_MODULES),--new-shared-module $(module))
PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS = $(if $(strip $(PYTHON_COVERAGE_NEW_SHARED_MODULES)),--coverage-json "$(PYTHON_COVERAGE_RAW)" $(PYTHON_COVERAGE_NEW_SHARED_ARGS))
PYTHON_SUBPROCESS_COVERAGE_DATA := $(PYTHON_COVERAGE_ROOT)/.coverage-subprocess
PYTHON_SUBPROCESS_COVERAGE_RAW := $(PYTHON_COVERAGE_ROOT)/subprocess-coverage.json
PYTHON_SUBPROCESS_COVERAGE_TESTS := \
	tests/stages/gtf_to_bed12/test_gtf_to_bed12.py \
	tests/ingestion/sample_manifest_admission/test_validate_manifest.py

SHELL_SYNTAX_PATHS := \
	src/emrys/libraries/gatk_invocation.sh \
	src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
	src/emrys/stages/star_index/step_00a_build_star_index.sh \
	src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
	src/emrys/stages/star_alignment/step_01_star_align.sh \
	src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh \
	src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh \
	src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh \
	src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh \
	src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh \
	src/emrys/analyses/scientific_context_projection/scientific_context_projection.sh \
	tests/analyses/scientific_context_projection/run_scientific_context_projection_tests.sh \
	tests/analyses/scientific_context_projection/test_scientific_context_projection.sh

documentation-check:
	./scripts/documentation/validate_structure.py --repo "$(CURDIR)"

validation-shell-contracts:
	bash tests/libraries/test_file_checks.sh
	bash tests/stages/fasta_sidecars/test_step_00c_prepare_gatk_reference.sh
	bash tests/stages/star_alignment/test_step_01_star_align.sh
	bash tests/stages/canonical_bam/test_step_02_sort_index_bam.sh
	bash tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh
	bash tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh
	bash tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh
	bash tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh
	bash tests/analyses/scientific_context_projection/test_scientific_context_projection.sh
	bash tests/shell/test_local_r_environment.sh

shell-test: validation-shell-contracts

validation-wheel-smoke:
	"$(REPORT_PYTHON_BIN)" -m pytest -q --tb=short \
		tests/test_package_distribution.py

real-r-test:
	bash tests/stages/cohort_candidate_preprocessing/run_step_08_vcf_preprocessing_tests.sh
	bash tests/analyses/paired_cmh_candidate_ranking/run_step_09_cmh_tests.sh
	bash tests/analyses/scientific_context_projection/run_scientific_context_projection_tests.sh

r-restore:
	EMRYS_USE_RENV=1 EMRYS_LOCAL_PILOT_R=0 \
		RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		"$(RSCRIPT_BIN)" scripts/restore_r_environment.R

r-check:
	test -n "$(RENV_LIBRARY)"
	test -d "$(RENV_LIBRARY)"
	EMRYS_USE_RENV=1 EMRYS_LOCAL_PILOT_R=1 \
		EMRYS_RENV_LIBRARY="$(RENV_LIBRARY)" \
		EMRYS_RENV_VERSION="$(EMRYS_RENV_VERSION)" \
		RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		"$(RSCRIPT_BIN)" scripts/check_r_environment.R

local-real-r-test:
	test -n "$(RENV_LIBRARY)"
	test -d "$(RENV_LIBRARY)"
	EMRYS_USE_RENV=1 EMRYS_LOCAL_PILOT_R=1 \
		EMRYS_RENV_LIBRARY="$(RENV_LIBRARY)" \
		EMRYS_RENV_VERSION="$(EMRYS_RENV_VERSION)" \
		RENV_CONFIG_SANDBOX_ENABLED=FALSE \
		RENV_CONFIG_AUTO_SNAPSHOT=FALSE RENV_PROJECT="$(CURDIR)" \
		R_PROFILE_USER="$(CURDIR)/.Rprofile" \
		STEP08_TEST_RSCRIPT_BIN= STEP09_TEST_RSCRIPT_BIN= \
		SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN= \
		RSCRIPT_BIN_OVERRIDE="$(RSCRIPT_BIN)" \
		$(MAKE) real-r-test

python-coverage-shard:
	test "$$("$(REPORT_PYTHON_BIN)" -c \
		'import importlib.metadata; print(importlib.metadata.version("coverage"))')" \
		= "$(PYTHON_COVERAGE_VERSION)"
	mkdir -p "$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage run \
		--rcfile="$(CURDIR)/.coveragerc" \
		tests/tools/python_test_shards.py run \
		--repo-root "$(CURDIR)" \
		--shard-index "$(PYTHON_TEST_SHARD_INDEX)" \
		--shard-count "$(PYTHON_TEST_SHARD_COUNT)" \
		--workers "$(PYTHON_COVERAGE_WORKERS)" \
		--duration-baseline "$(PYTHON_TEST_DURATION_BASELINE)" \
		--receipt "$(PYTHON_TEST_SHARD_RECEIPT)"

python-coverage-finalize:
	test "$$("$(REPORT_PYTHON_BIN)" -c \
		'import importlib.metadata; print(importlib.metadata.version("coverage"))')" \
		= "$(PYTHON_COVERAGE_VERSION)"
	mkdir -p "$(PYTHON_COVERAGE_ROOT)"
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
		--source=scripts,src/emrys,tests -m pytest -q \
		$(PYTHON_SUBPROCESS_COVERAGE_TESTS)
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage combine -q \
		"$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_SUBPROCESS_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage json \
		--rcfile="$(CURDIR)/.coveragerc" \
		--include="scripts/*,src/emrys/*" \
		-o "$(PYTHON_SUBPROCESS_COVERAGE_RAW)"
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py build \
		--coverage-json "$(PYTHON_COVERAGE_RAW)" \
		--subprocess-coverage-json "$(PYTHON_SUBPROCESS_COVERAGE_RAW)" \
		--output "$(PYTHON_COVERAGE_CURRENT)"

python-coverage-measure:
	mkdir -p "$(PYTHON_COVERAGE_ROOT)"
	COVERAGE_FILE="$(PYTHON_COVERAGE_DATA)" \
		"$(REPORT_PYTHON_BIN)" -m coverage erase
	$(MAKE) -s python-coverage-shard \
		PYTHON_TEST_SHARD_INDEX=0 \
		PYTHON_TEST_SHARD_COUNT=1 \
		PYTHON_TEST_SHARD_RECEIPT="$(PYTHON_COVERAGE_ROOT)/python-test-shard-0-of-1.json"
	$(MAKE) -s python-coverage-finalize

python-coverage-enforce:
	"$(REPORT_PYTHON_BIN)" tests/tools/python_coverage_baseline.py check \
		--baseline "$(PYTHON_COVERAGE_BASELINE)" \
		--current "$(PYTHON_COVERAGE_CURRENT)"$(if $(PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS), $(PYTHON_COVERAGE_NEW_SHARED_CHECK_ARGS))

python-coverage-check: python-coverage-measure
	$(MAKE) -s python-coverage-enforce

python-coverage-baseline-update: python-coverage-measure
	cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"

validation-guarded-r:
	$(MAKE) -s r-check
	$(MAKE) -s local-real-r-test

report-test:
	"$(REPORT_PYTHON_BIN)" -m pytest \
		tests/reporting/test_artifact_run_summary.py \
		tests/reporting/test_candidate_display.py \
		tests/reporting/test_figures.py \
		tests/reporting/test_report.py \
		tests/reporting/test_transaction_validation.py

define STATIC_SHELL_CHECKS
bash -n $(SHELL_SYNTAX_PATHS)
endef

validation-static: lint documentation-check
	"$(REPORT_PYTHON_BIN)" tests/tools/source_dependencies.py --repo "$(CURDIR)"
	git diff --check
	$(STATIC_SHELL_CHECKS)
	PYTHONDONTWRITEBYTECODE=1 \
		"$(REPORT_PYTHON_BIN)" -m compileall -q scripts src/emrys tests
	"$(REPORT_PYTHON_BIN)" -I -m emrys validate manifest \
		--manifest configs/samples.example.tsv

validate:
	"$(REPORT_PYTHON_BIN)" -I -m emrys validate manifest \
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
