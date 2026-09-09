# Artifact contracts

`emrys validate artifact-contracts` checks registered artifact records, run
summaries, report receipts, and explicit inventories through private
[`validator.py`](validator.py). Reporting uses [`api.py`](api.py). These
interfaces validate supplied data; they do not discover artifacts, build
indexes, render reports, repair inputs, or promote evidence.

The [schema version index](../schemas/artifacts/README.md) defines each record
family and its historical versions. Historical records keep their exact schema
meaning; versioned files are not aliases or automatic migration routes.

## Known CLI version limit

The CLI currently selects the default run-summary v2 or report-receipt v4
schema before checking a document's version. Module run-summary v3 and report-receipt v5 can pass their explicit
schemas yet fail the unversioned CLI. In [`schema.py`](_artifact_contracts/schema.py),
`schema_validator` supports their registered versions, but `schema_errors` does
not select them from the document. Earlier
local production-path reproduction documented this defect; no fix is implied
by schema support or this documentation. The
[compression backlog](../../../../docs/tasks/compression_backlog_matrix.md#artifact-cli-document-version-admission)
owns the proposed correction and its acceptance checks.
