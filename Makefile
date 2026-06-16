DEMO_SAMPLE ?= ABE_EV_2

.PHONY: test validate lint demo-step03

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

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh
	bash -n jobs/*.slurm

lint:
	python -m compileall scripts tests

all-checks: test shell-test validate smoke

demo-step03-dry-run:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm

demo-step03:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,SAMPLE_ID=$(DEMO_SAMPLE) \
		jobs/step_03_infer_strandedness_and_orientation.slurm