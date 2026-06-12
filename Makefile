.PHONY: test validate lint

test:
	python -m pytest

validate:
	python scripts/validate_manifest.py --manifest samples.example.tsv

lint:
	python -m compileall scripts tests
