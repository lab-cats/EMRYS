# Artifact schemas v4

[`report_receipt`](report_receipt.schema.json) v4 binds three outputs in one Run
directory: self-contained scientific HTML, evidence HTML, and run-summary TSV.
Shared path, hash, issue, and provenance definitions come from
[`common` v1](../v1/common.schema.json). The
[artifact contract](../../../artifacts/README.md) validates exact output IDs,
kinds, basenames, and their common directory.

The frozen [v3 receipt](../v3/README.md) remains historical input; never silently
alias or migrate it into v4. The shared [version rules](../../README.md#version-and-identity-rules)
apply to changes.
