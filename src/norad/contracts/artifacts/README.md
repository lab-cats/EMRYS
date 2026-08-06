# Artifact-contract owner

[`validate_artifact_contracts.py`](validate_artifact_contracts.py) validates
the closed artifact, scientific-review, run-summary, and report-receipt schemas.
It does not discover artifacts, build indexes, render reports, repair inputs,
or promote evidence. Private implementation is under
[`_artifact_contracts/`](_artifact_contracts/README.md).

Validate the schemas and starter inventory:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

Validate one explicit document:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --schema artifact-record \
  --document /explicit/path/to/artifact_record.json \
  --inventory /explicit/path/to/artifact_inventory.tsv
```

Supported selectors are `artifact-record`, `scientific-review-record`,
`run-summary`, and `report-receipt`. Direct protection is:

```bash
.venv/bin/python -m pytest -q \
  tests/contracts/artifacts/test_artifact_schema_contracts.py
```
