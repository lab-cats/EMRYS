.PHONY: test validate lint

test:
	python -m pytest

shell-test:
	bash tests/shell/test_step_01_star_align.sh

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

smoke:
	bash -n scripts/*.sh
	bash -n jobs/*.slurm

lint:
	python -m compileall scripts tests

all-checks: test shell-test validate smoke