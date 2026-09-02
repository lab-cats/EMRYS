# Artifact-contract owner

The installed `emrys validate artifact-contracts` route validates
the closed artifact, run-summary, and report-receipt schemas.
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
emrys validate artifact-contracts \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

Validate one explicit document:

```sh
emrys validate artifact-contracts \
  --schema artifact-record \
  --document /explicit/path/to/artifact_record.json \
  --inventory /explicit/path/to/artifact_inventory.tsv
```

Supported selectors are `artifact-record`, `run-summary`, and
`report-receipt`. Direct protection is:

```sh
.venv/bin/python -m pytest -q \
  tests/contracts/artifacts/test_artifact_schema_contracts.py
```

## Schema packaging boundary

Packaged resources span [version `1`](../schemas/artifacts/v1/),
[version `2`](../schemas/artifacts/v2/),
[version `3`](../schemas/artifacts/v3/), and
[version `4`](../schemas/artifacts/v4/), and
[version `5`](../schemas/artifacts/v5/). Version `1` owns shared definitions.
Artifact-record v2 remains active and permits null `git_commit` only when exact
external-provider bytes are the recorded implementation authority. Flat
paired-CMH reporting uses run-summary v2 and report-receipt v4. Version `3`
contains both the frozen historical single-HTML receipt and the active
module-neutral run-summary v3; explicit modules pair that summary with
report-receipt v5. The closed registry does not alias or migrate historical
receipts.
Each registered public `$id` remains one packaged file. Large record schemas
use local `$defs` to organize one document identity. Those definitions are not
split into extra files merely to reduce line count: doing so would add registry
resources and change schema distribution and reference-resolution contracts. A
split requires a versioned schema-design change with explicit consumers, not a
source-layout refactor.
