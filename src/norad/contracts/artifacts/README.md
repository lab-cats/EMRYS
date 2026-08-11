# Artifact-contract owner

The installed `python -I -m norad validate artifact-contracts` route validates
the closed artifact, scientific-review, run-summary, and report-receipt schemas.
It does not discover artifacts, build indexes, render reports, repair inputs,
or promote evidence. The route is coordinated by private
[`validator.py`](validator.py), with responsibility modules under
[`_artifact_contracts/`](_artifact_contracts/README.md).

Reporting code separately imports the curated [`api.py`](api.py) library
surface: one shared module identity exposes only the contract definitions and
operations used by artifact indexing, run-summary assembly, and report
rendering. The private implementation owners remain responsible for schema
I/O, identity, evidence, record semantics, inventory reconciliation, and status
reduction; the former `core.py` compatibility layer is retired.

Validate the schemas and starter inventory:

```sh
python -I -m norad validate artifact-contracts \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

Validate one explicit document:

```sh
python -I -m norad validate artifact-contracts \
  --schema artifact-record \
  --document /explicit/path/to/artifact_record.json \
  --inventory /explicit/path/to/artifact_inventory.tsv
```

Supported selectors are `artifact-record`, `scientific-review-record`,
`run-summary`, and `report-receipt`. Direct protection is:

```sh
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
