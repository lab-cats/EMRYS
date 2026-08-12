# Artifact schemas v2

This directory contains the registered version 2
[`report_receipt`](report_receipt.schema.json) schema for one self-contained
Jinja HTML report transaction. It intentionally resolves shared path, hash,
issue, and provenance definitions from the packaged
[`common` v1 resource](../v1/common.schema.json); both version directories are
part of the closed schema registry and distribution boundary.

The v2 report receipt does not replace the active v1 artifact-record,
scientific-review-record, or run-summary schemas. The
[`artifact-contract owner`](../../../artifacts/README.md) defines supported
selectors and validation behavior. Direct schema/fixture protection lives in
[`test_artifact_schema_contracts.py`](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
with independent selected-path expectations under
[`independent_contract_goldens/`](../../../../../../tests/contract_integration/independent_contract_goldens/README.md).

Do not rewrite this schema in place merely to satisfy tests; any accepted
change requires explicit version and consumer review.
