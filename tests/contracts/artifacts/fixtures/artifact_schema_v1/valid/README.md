# Valid artifact schema v1 examples

This directory owns one accepted JSON example for each v1 record schema: an
artifact record, scientific-review record, and run summary. The active
[report-receipt fixture](../../report_receipt_v2.json) is version 2. The direct
[artifact-contract test](../../../test_artifact_schema_contracts.py) validates
their schema and semantic behavior.

These files are synthetic immutable test inputs. Do not regenerate them from
production serializers or treat schema validity as runtime, review, or
biological evidence.
