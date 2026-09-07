# Reporting projection owner

Reporting consumes one successfully completed immutable Run and validated
artifacts. `emrys run`/`resume` invokes it automatically unless `--no-report`
is selected; `emrys report [RUN]` independently plans or revalidates a bundle,
and `--execute` publishes only from empty owned state. Reporting failure never
changes the successful scientific Attempt or Results.

The fixed sequence publishes an artifact index, run summary, and two-HTML report
bundle under `results/reports/RUN_ID`, ending with `RUN_ID.report_outputs.tsv`.
Flat paired-CMH Runs use run-summary v2/report-receipt v4; explicit modules use
v3/v5 so computation provider, bespoke scientific reporter, and fixed core
renderer remain separately attributable. Complete bundles are reused only
after full semantic revalidation; partial, legacy, or ambiguous state is
preserved and rejected.

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

[`report.py`](report.py) and the `_artifact_index`, `_run_summary`, and
`_run_report` packages are private implementation. Public read-only
[`transaction_validation.py`](transaction_validation.py) re-admits current and
historical receipts without treating the current checkout as their producer.
A rendered report is computational evidence, not scientific adjudication or
biological validation.
