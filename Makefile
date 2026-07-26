DEMO_SAMPLE ?= ABE_EV_2
RSCRIPT_BIN ?= Rscript

.PHONY: test shell-test real-r-test r-restore r-check local-real-r-test validate smoke lint all-checks demo-step03-dry-run demo-step03

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
	bash tests/shell/test_local_r_environment.sh

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

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh
	bash -n jobs/*.slurm

lint:
	python -m compileall scripts tests

all-checks: test shell-test real-r-test validate smoke lint

demo-step03-dry-run:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm

demo-step03:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm
