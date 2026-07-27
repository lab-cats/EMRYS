DEMO_SAMPLE ?= ABE_EV_2
RSCRIPT_BIN ?= Rscript
PYTHON_BIN ?= python3
REPORT_PYTHON_BIN ?= $(CURDIR)/.venv/bin/python
QUARTO_VERSION := 1.9.38
QUARTO_SHA256 := 47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a
QUARTO_TOOLS_ROOT ?= $(CURDIR)/.tools/quarto
QUARTO_BIN ?= $(QUARTO_TOOLS_ROOT)/$(QUARTO_VERSION)/bin/quarto

.PHONY: test shell-test real-r-test r-restore r-check local-real-r-test quarto-restore report-test validate smoke lint all-checks demo-step03-dry-run demo-step03

test:
	python -m pytest

shell-test:
	bash tests/shell/test_step_00c_prepare_gatk_reference.sh
	bash tests/shell/test_step_01_star_align.sh
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
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_runtime_preflight.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_reference_provenance.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_storage_inventory.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_00a_star_index.py
	"$(REPORT_PYTHON_BIN)" -m pytest tests/test_validate_step_00b_bed12.py

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

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh
	bash -n jobs/*.slurm

lint:
	python -m compileall scripts tests

all-checks: test shell-test real-r-test validate smoke lint report-test

demo-step03-dry-run:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm

demo-step03:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm
