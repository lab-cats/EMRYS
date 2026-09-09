# Artifact schemas v5

[`report_receipt`](report_receipt.schema.json) v5 describes the same two-HTML
plus summary-TSV transaction for explicit Analysis modules. It binds the Run's
computation provider, module-specific scientific reporter, and fixed EMRYS core
renderer separately. Reporter provenance belongs to derived outputs, never
Analysis or Run identity.

This receipt uses [`common` v1](../v1/common.schema.json) path/hash/output
definitions and pairs with run-summary v3. Flat paired-CMH keeps receipt v4;
v5 is not its alias or an in-place rewrite.
