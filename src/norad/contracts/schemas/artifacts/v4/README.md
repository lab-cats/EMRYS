# Artifact schemas v4

This directory contains the active version 4
[`report_receipt`](report_receipt.schema.json) schema. One receipt binds exactly
three outputs in a common run directory: separate self-contained scientific and
evidence HTML reports, plus the run-summary TSV.

The schema resolves shared path, hash, issue, and provenance definitions from
the packaged [`common` v1 resource](../v1/common.schema.json). The
[`artifact-contract owner`](../../../artifacts/README.md) defines the exact
output identity, kind, basename, and cross-output directory semantics.

Version 3 remains frozen under [`v3/`](../v3/) as historical contract evidence.
Do not alias or migrate a v3 receipt into this contract implicitly.
