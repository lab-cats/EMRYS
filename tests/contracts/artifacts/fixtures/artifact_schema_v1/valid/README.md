# Valid artifact schema v1 examples

This directory owns one accepted JSON example for each public artifact schema:
an artifact record, scientific-review record, run summary, and report receipt.
The direct
[artifact-contract test](../../../test_artifact_schema_contracts.py) validates
their schema and semantic behavior.

These files are synthetic immutable test inputs. Do not regenerate them from
production serializers or treat schema validity as runtime, review, or
biological evidence.
