# Artifact schemas v5

This directory owns the explicit-module
[`report_receipt`](report_receipt.schema.json) v5. It retains the fixed two-HTML
plus summary-TSV transaction while binding three implementation identities
separately: the computation provider already admitted for the Run, the
module-specific scientific reporter, and the fixed EMRYS core renderer.

Reporter identity is derived-output provenance and never Analysis or Run
identity. The receipt resolves shared path/hash/output definitions from the
packaged [`common` v1 resource](../v1/common.schema.json) and pairs with
module-neutral run-summary v3. Flat paired-CMH compatibility continues to use
report-receipt v4; v5 is not an in-place rewrite or alias.
