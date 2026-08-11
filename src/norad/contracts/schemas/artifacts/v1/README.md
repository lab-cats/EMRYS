# Artifact schemas v1

This directory contains the shared `common` resource and four registered JSON
Schema documents for artifact records, scientific-review records, run
summaries, and report receipts. These files are public byte and
reference-resolution contracts.

The [`artifact-contract owner`](../../../artifacts/README.md) defines supported
selectors and validation behavior. Direct schema/fixture protection lives in
[`test_artifact_schema_contracts.py`](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
with independent selected-path expectations under
[`independent_contract_goldens/`](../../../../../../tests/contract_integration/independent_contract_goldens/README.md).

Do not regenerate, split, or rebase these schemas merely to satisfy tests; any
accepted change requires explicit version and consumer review.
