# Reporting tests

These tests check artifact indexing, run summaries, report models and exports,
Jinja safety, publication, and rendered HTML. They pin candidate selection,
primary/supporting figures, visible figure guidance, ranked candidate cards,
and print behavior, including the absence of scientific disclosure controls
and wide-table wrappers. [Fixtures](fixtures/README.md) supply shared builders
and literal inputs; the [reporting owner](../../src/emrys/reporting/README.md)
defines the production contract and recovery rules.

## Fault injection

Publication and source-identity tests patch real filesystem or validation
functions with scoped pytest monkeypatches. Each patch targets the relevant
path or receipt and delegates other calls. The retired interfaces were
`ArtifactPublicationOps`, `RunSummaryPublicationOps`, `ReportPublicationOps`,
`ArtifactIdentityOps`, `ReportIdentityOps`, `ReceiptValidationOps`, and the public
validators' `receipt_ops` parameter; they are not current test entry points.
The artifact context still captures its real source observer for later rechecks,
and validated transactions retain real input-recheck callbacks.

Combined publication tests cover the index and summary output set, including
terminal-receipt failure and owned rollback. Summary tests retain independent
schema, deterministic projection, QC, provenance, and current-source checks.
Faults target the actual publisher and read validator, without test-only
production behavior or a second suite for the retired summary publisher.
