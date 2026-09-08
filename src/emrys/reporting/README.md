# Reporting projection owner

Reporting consumes one successfully completed immutable Run and validated
artifacts. `emrys run`/`resume` invokes it automatically unless `--no-report`
is selected; `emrys report [RUN]` independently plans or revalidates a bundle,
and `--execute` publishes only from empty owned state. Reporting failure never
changes the successful scientific Attempt or Results.

The fixed sequence publishes an artifact index and run summary under
`products/artifact-summary/RUN_ID`, then a two-HTML report bundle under
`results/reports/RUN_ID`, ending with `RUN_ID.report_outputs.tsv`.
Flat paired-CMH Runs use run-summary v2/report-receipt v4; explicit modules use
v3/v5 so computation provider, bespoke scientific reporter, and fixed core
renderer remain separately attributable. Complete bundles are reused only
after full semantic revalidation, including supported historical bundles under
their recorded producer identities. Incomplete or ambiguous generation state
is preserved and rejected.

Artifact indexing derives a closed expected roster from the admitted Analysis
module descriptor. It discovers neither providers nor filesystem outputs and
is not an Artifact Store, service, database, or public registry. A selected
`emrys.analysis_reporters` provider owns bespoke scientific HTML; EMRYS owns
the evidence-and-operations view, safe Jinja/CSS rendering, portable links,
input rechecks, locking, rollback, and receipt-last publication. There is no
generic scientific report schema or section DSL.

Current artifact inspection validates report structure but not every
producer's exact ordered check roster. The independent roster and adapter
mutation tests remain required until that defect is resolved.

The built-in paired-CMH view presents its tested candidate population, bounded
selected-candidate records, context/motif projections when admitted, methods,
and limitations. It does not recompute analysis, reopen references, discover
motifs, hide required scientific caveats, or infer missing data. The evidence
view carries provenance, artifacts, QC, tools, issues, and Attempt lineage.
Both views are projections of the same admitted bytes.

The `_artifact_index`, `_run_summary`, and `_run_report` packages are private
implementation. Public read-only
[`transaction_validation.py`](transaction_validation.py) re-admits current and
historical receipts without treating the current checkout as their producer.
A rendered report is computational evidence, not scientific adjudication or
biological validation.

## Publication and recovery

Each private publisher creates only absent transaction-owned final paths.
Publication cannot replace a complete transaction, create predecessor backups,
or restore a predecessor. The run summary shares the artifact-index directory
but requires its own outputs to be absent. Preparation and read-only validation
still admit existing transactions and their recorded history; preparing a new
projection does not authorize replacing its predecessor.

Publishers stage bytes, retain file anchors, install final files exclusively,
and publish the receipt last. Input, source, output, and directory checks remain
at their publication boundaries. Rollback removes only provably owned outputs;
unproved ownership preserves remaining state. Failed rollback retains remaining
locks and staging evidence. Cleanup failure preserves committed outputs and
remaining recovery state; recovery markers are best effort within a verified
output directory. Foreign or replaced namespaces are not cleanup targets.

Run-level generation refuses existing output state. Existing locks, partials,
`.previous` files, staging directories, and recovery evidence must be preserved;
this publication contract provides no repair or evidence-deletion authority.

## Implementation and fault tests

Publication and source-identity observation call their existing owners directly.
`ArtifactPublicationOps`, `RunSummaryPublicationOps`, `ReportPublicationOps`,
`ArtifactIdentityOps`, `ReportIdentityOps`, and `ReceiptValidationOps`, including
the public validators' `receipt_ops` testing parameter, are retired. Fault tests
use scoped pytest monkeypatches at real filesystem and validation functions,
targeting the relevant path or receipt while delegating normal operations.
The artifact context still captures its source observer for later rechecks;
validated transactions retain their real input-recheck callbacks.
