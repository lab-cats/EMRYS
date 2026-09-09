# Artifact schemas v1

`common.schema.json` supplies shared definitions used by active artifact
schemas. Its bytes and references remain a public contract; record schemas
moved to later major versions when scientific-review state was retired.

The [artifact contract](../../../artifacts/README.md) defines validation.
[Schema tests](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py)
and [independent goldens](../../../../../../tests/contract_integration/independent_contract_goldens/README.md)
check compatibility. The shared [version rules](../../README.md#version-and-identity-rules)
apply to changes.
