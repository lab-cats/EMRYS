# Artifact schemas v2

[`artifact_record`](artifact_record.schema.json) and
[`run_summary`](run_summary.schema.json) are the registered v2 records. Both
reference shared path, hash, issue, and provenance definitions from
[`common` v1](../v1/common.schema.json). They replace incompatible v1 records
that carried the retired scientific-review state.

The [artifact contract](../../../artifacts/README.md) defines validation.
[Schema tests](../../../../../../tests/contracts/artifacts/test_artifact_schema_contracts.py)
and [independent goldens](../../../../../../tests/contract_integration/independent_contract_goldens/README.md)
check compatibility. The shared [version rules](../../README.md#version-and-identity-rules)
apply to changes.
