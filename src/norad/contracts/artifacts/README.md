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

## Schema packaging boundary

The [version `1` schema directory](../schemas/artifacts/v1/) keeps one file per
registered public `$id`, plus the shared `common` resource. Large record
schemas use local `$defs` to organize one document identity. Those definitions
are not split into extra files merely to reduce line count: doing so would add
registry resources and change schema distribution and reference-resolution
contracts. A split requires a versioned schema-design change with explicit
consumers, not a source-layout refactor.
