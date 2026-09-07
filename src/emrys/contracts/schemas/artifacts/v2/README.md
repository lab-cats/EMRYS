# Artifact schemas v2

This directory contains the registered version 2
[`artifact_record`](artifact_record.schema.json) and
[`run_summary`](run_summary.schema.json) schemas. They intentionally resolve
shared path, hash, issue, and provenance definitions from the packaged
[`common` v1 resource](../v1/common.schema.json); both version directories are
part of the closed schema registry and distribution boundary.

These schemas replace the incompatible v1 artifact and run-summary contracts
that carried the retired scientific-review state. The
[`artifact-contract owner`](../../../artifacts/README.md) defines supported
selectors and validation behavior. Direct schema/fixture protection lives in
[`test_artifact_schema_contracts.py`](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
with independent selected-path expectations under
[`independent_contract_goldens/`](../../../../../../tests/contract_integration/independent_contract_goldens/README.md).

Do not rewrite these schemas in place merely to satisfy tests; any accepted
change requires explicit version and consumer review.
