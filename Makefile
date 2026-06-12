.PHONY: test validate lint

test:
	python -m pytest

shell-test:
	bash tests/shell/test_step_01_star_align.sh
	bash tests/shell/test_step_02_sort_index_bam.sh
	bash tests/shell/test_step_02b_bam_qc.sh
	bash tests/shell/test_step_03_infer_strandedness_and_orientation.sh

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh
	bash -n jobs/*.slurm

lint:
	python -m compileall scripts tests

all-checks: test shell-test validate smoke
