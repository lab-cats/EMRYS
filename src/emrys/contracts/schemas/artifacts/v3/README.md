# Artifact schemas v3

These resources have independent version histories:

- Active [`run_summary`](run_summary.schema.json) v3 supports explicit Analysis
  modules. It binds analysis policy by path, SHA-256, and size rather than
  paired-CMH candidate fields.
- Frozen [`report_receipt`](report_receipt.schema.json) v3 describes the former
  single self-contained Jinja HTML transaction. It contains no scientific-review
  or approval state and is not an alias or migration route to v4/v5.

Both use shared definitions from [`common` v1](../v1/common.schema.json).
The [artifact contract](../../../artifacts/README.md) defines validation;
the shared [version rules](../../README.md#version-and-identity-rules) apply.
