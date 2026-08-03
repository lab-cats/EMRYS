DEMO_SAMPLE ?= ABE_EV_2
RSCRIPT_BIN ?= Rscript
PYTHON_BIN ?= python3
REPORT_PYTHON_BIN ?= $(CURDIR)/.venv/bin/python
PYTHON_COVERAGE_VERSION := 7.15.2
PYTHON_COVERAGE_ROOT ?= $(CURDIR)/.coverage-work
PYTHON_COVERAGE_DATA ?= $(PYTHON_COVERAGE_ROOT)/.coverage
PYTHON_COVERAGE_RAW ?= $(PYTHON_COVERAGE_ROOT)/coverage.json
PYTHON_COVERAGE_CURRENT ?= $(PYTHON_COVERAGE_ROOT)/python_coverage.current.json
PYTHON_COVERAGE_BASELINE ?= $(CURDIR)/tests/baselines/python_coverage.json
PYTHON_COVERAGE_PYTEST_ARGS ?=
QUARTO_VERSION := 1.9.38
QUARTO_SHA256 := 47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a
QUARTO_TOOLS_ROOT ?= $(CURDIR)/.tools/quarto
QUARTO_BIN ?= $(QUARTO_TOOLS_ROOT)/$(QUARTO_VERSION)/bin/quarto
VALIDATION_JOBS ?= 3
VALIDATION_PYTHON_WORKERS ?= 2
VALIDATION_ARGS ?=
REPORT_TEST_RESULT ?=
DEMO_REPORT_ROOT ?= $(CURDIR)/results/demo-report
DEMO_REPORT_FORMATS ?= all
DEMO_REPORT_RUN_ID := synthetic_full_run_demo
DEMO_REPORT_FIXTURE_ROOT := $(DEMO_REPORT_ROOT)/full-run-fixture
DEMO_REPORT_ARTIFACT_ROOT := $(DEMO_REPORT_FIXTURE_ROOT)/artifacts
DEMO_REPORT_OUTPUT_ROOT := $(DEMO_REPORT_ROOT)/reports
DEMO_REPORT_SCIENCE_SUMMARY := $(DEMO_REPORT_FIXTURE_ROOT)/science_fixture/step09c_fixture/output/review_fixture/review_fixture.step09c_review_summary.tsv
DEMO_REPORT_TABLE_APPROVALS := $(DEMO_REPORT_FIXTURE_ROOT)/report_table_approvals.tsv

.PHONY: test shell-test validation-shell-contracts real-r-test r-restore r-check local-real-r-test quarto-restore report-test validation-report-runtime demo-report python-coverage-measure python-coverage-check python-coverage-baseline-update validation-python-coverage validation-guarded-r validation-static validate smoke lint all-checks demo-step03-dry-run demo-step03

test:
	python -m pytest

validation-shell-contracts:
	bash tests/shell/test_step_00c_prepare_gatk_reference.sh
	bash tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh
	bash tests/shell/test_step_02_sort_index_bam.sh
	bash tests/shell/test_step_02b_bam_qc.sh
	bash tests/shell/test_step_03_infer_strandedness_and_orientation.sh
	bash tests/shell/test_step_04_mark_duplicates.sh
	bash tests/shell/test_step_05_split_n_cigar_reads.sh
	bash tests/shell/test_step_06_split_bam_by_read_orientation.sh
	bash tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
	bash tests/shell/test_step_08_vcf_preprocessing.sh
	bash tests/shell/test_step_09_cmh_editing_site_calling.sh
	bash tests/shell/test_step_09c_scientific_validation.sh
	bash tests/shell/test_local_r_environment.sh
	bash tests/shell/test_render_run_report.sh

shell-test: validation-shell-contracts
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_runtime_preflight.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_reference_provenance.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_storage_inventory.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_00c_reference_sidecars.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_02_canonical_bam.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_02b_bam_qc.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_03_rseqc_orientation.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_04_mark_duplicates.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_05_split_ncigar.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_06_orientation_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_07_mpileup_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_08_preprocessing_outputs.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_09_cmh_outputs.py

real-r-test:
	bash tests/r/run_step_08_vcf_preprocessing_tests.sh
	bash tests/r/run_step_09_cmh_tests.sh

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

quarto-restore:
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"

report-test:
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"
	NORAD_REQUIRE_QUARTO=1 QUARTO_BIN="$(QUARTO_BIN)" \
		"$(REPORT_PYTHON_BIN)" -m pytest \
		tests/test_quarto_restore.py \
		tests/test_artifact_run_summary.py \
		tests/test_report_html_v1.py \
		tests/test_report_exports_v1.py
	QUARTO_BIN="$(QUARTO_BIN)" REPORT_PYTHON_BIN="$(REPORT_PYTHON_BIN)" \
		bash tests/shell/test_render_run_report.sh

validation-report-runtime:
	test -n "$(REPORT_TEST_RESULT)" || { \
		printf 'ERROR: REPORT_TEST_RESULT is required\n' >&2; \
		exit 1; \
	}
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	"$(PYTHON_BIN)" scripts/restore_quarto.py \
		--install-root "$(QUARTO_TOOLS_ROOT)"
	NORAD_REQUIRE_QUARTO=1 QUARTO_BIN="$(QUARTO_BIN)" \
		"$(REPORT_PYTHON_BIN)" -m pytest -q --tb=short \
		-m report_runtime --junitxml="$(REPORT_TEST_RESULT)" \
		tests/test_report_html_v1.py \
		tests/test_report_exports_v1.py

demo-report:
	test -x "$(QUARTO_BIN)" || { \
		printf 'ERROR: pinned Quarto is unavailable: %s\nRun make quarto-restore first.\n' \
			"$(QUARTO_BIN)" >&2; \
			exit 1; \
	}
	command -v "$(REPORT_PYTHON_BIN)" >/dev/null 2>&1 || { \
		printf 'ERROR: report Python is unavailable: %s\n' \
			"$(REPORT_PYTHON_BIN)" >&2; \
		exit 1; \
	}
	"$(REPORT_PYTHON_BIN)" -c \
		'import jsonschema, pypdf, yaml' || { \
			printf 'ERROR: report Python dependencies are unavailable: %s\n' \
				"$(REPORT_PYTHON_BIN)" >&2; \
			exit 1; \
		}
	case "$(DEMO_REPORT_FORMATS)" in \
		html|pdf|all) ;; \
		*) \
			printf 'ERROR: DEMO_REPORT_FORMATS must be html, pdf, or all; observed: %s\n' \
				"$(DEMO_REPORT_FORMATS)" >&2; \
			exit 1; \
			;; \
	esac
	"$(REPORT_PYTHON_BIN)" \
		tests/fixtures/artifact_run_summary_v1/build_fixture.py \
		--root "$(DEMO_REPORT_FIXTURE_ROOT)" \
		--full-science-demo
	SOURCE_DATE_EPOCH=1700000000 \
		"$(REPORT_PYTHON_BIN)" scripts/build_run_summary.py \
		--run-id "$(DEMO_REPORT_RUN_ID)" \
		--artifact-receipt \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).artifact_receipt.tsv" \
		--output-root "$(DEMO_REPORT_ARTIFACT_ROOT)" \
		--science-review-summary "$(DEMO_REPORT_SCIENCE_SUMMARY)" \
		--report-table-approvals "$(DEMO_REPORT_TABLE_APPROVALS)" \
		--execute
	SOURCE_DATE_EPOCH=1700000000 \
		PYTHON_BIN_OVERRIDE="$(REPORT_PYTHON_BIN)" \
		scripts/render_run_report.sh \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)" \
		--quarto-bin "$(QUARTO_BIN)" \
		--formats "$(DEMO_REPORT_FORMATS)"
	SOURCE_DATE_EPOCH=1700000000 \
		PYTHON_BIN_OVERRIDE="$(REPORT_PYTHON_BIN)" \
		scripts/render_run_report.sh \
		--run-summary \
			"$(DEMO_REPORT_ARTIFACT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.json" \
		--output-root "$(DEMO_REPORT_OUTPUT_ROOT)" \
		--quarto-bin "$(QUARTO_BIN)" \
		--formats "$(DEMO_REPORT_FORMATS)" \
		--execute
	@printf 'Demo report bundle: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)"
	@case "$(DEMO_REPORT_FORMATS)" in \
		html|all) \
			printf '  HTML: %s\n' \
				"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_report.html" \
			;; \
	esac
	@case "$(DEMO_REPORT_FORMATS)" in \
		pdf|all) \
			printf '  PDF: %s\n' \
				"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_report.pdf" \
			;; \
	esac
	@printf '  Summary: %s\n  Receipt: %s\n' \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).run_summary.tsv" \
		"$(DEMO_REPORT_OUTPUT_ROOT)/$(DEMO_REPORT_RUN_ID)/$(DEMO_REPORT_RUN_ID).report_outputs.tsv"

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
		--new-shared-module src/norad/libraries/validation_report.py

python-coverage-baseline-update: python-coverage-measure
	cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"

validation-python-coverage: python-coverage-check

validation-guarded-r:
	$(MAKE) -s r-check
	$(MAKE) -s local-real-r-test

validation-static:
	git diff --check
	bash -n scripts/*.sh src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh
	bash -n scripts/git_orchestration/*.sh
	bash -n jobs/*.slurm src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm
	PYTHONDONTWRITEBYTECODE=1 \
		"$(REPORT_PYTHON_BIN)" -m compileall -q scripts src/norad tests
	"$(REPORT_PYTHON_BIN)" scripts/validate_manifest.py \
		--manifest samples.example.tsv

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh
	bash -n scripts/git_orchestration/*.sh
	bash -n jobs/*.slurm src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm

lint:
	python -m compileall scripts src/norad tests

all-checks:
	"$(REPORT_PYTHON_BIN)" tests/tools/run_validation.py \
		--repo-root "$(CURDIR)" \
		--python-bin "$(REPORT_PYTHON_BIN)" \
		--rscript-bin "$(RSCRIPT_BIN)" \
		--jobs "$(VALIDATION_JOBS)" \
		--python-workers "$(VALIDATION_PYTHON_WORKERS)" $(VALIDATION_ARGS)

demo-step03-dry-run:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm

demo-step03:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm
