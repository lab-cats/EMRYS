# Artifact schemas v1

This directory contains the shared `common` resource referenced by the active
artifact schemas. It remains a public byte and reference-resolution contract;
the active record schemas moved to later major-version directories after the
scientific-review state was retired.

The [`artifact-contract owner`](../../../artifacts/README.md) defines supported
selectors and validation behavior. Direct schema/fixture protection lives in
[`test_artifact_schema_contracts.py`](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
with independent selected-path expectations under
[`independent_contract_goldens/`](../../../../../../tests/contract_integration/independent_contract_goldens/README.md).

Do not regenerate, split, or rebase this schema merely to satisfy tests; any
accepted change requires explicit version and consumer review.
