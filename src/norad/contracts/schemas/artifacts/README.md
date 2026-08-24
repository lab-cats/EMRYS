# Artifact schema versions

This directory groups public artifact-contract schemas by resource version.
Each version is a distribution and reference-resolution boundary, not a
documentation-only folder split. Active resources can span more than one
version directory:

- [`v1/`](v1/) — shared definitions used by the active schemas.
- [`v2/`](v2/) — active artifact-record and run-summary schemas.
- [`v3/`](v3/) — the frozen historical single-HTML report-receipt schema.
- [`v4/`](v4/) — the active receipt for separate scientific and evidence HTML
  reports plus the run-summary TSV.

Schema registration and validation remain owned by the
[`artifacts` contract](../../artifacts/README.md). A new resource version
requires an explicit contract and consumer change rather than an in-place
rewrite.
