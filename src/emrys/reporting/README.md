# Reporting

Reporting reads a successfully completed immutable Run and validated artifacts.
`emrys run` and `emrys resume` report automatically unless `--no-report` is set.
`emrys report [RUN]` plans or revalidates a bundle; `--execute` publishes it only
from empty owned state. Reporting failure does not change successful scientific
Attempts or Results. Reports are computational evidence, not scientific
adjudication or biological validation.

One operation publishes the Run result manifest and its TSV views under
`products/artifact-summary/RUN_ID`; a second builds HTML reports under
`results/reports/RUN_ID`. The first operation inspects artifacts once and derives
the manifest from those admitted entries. `RUN_ID.run_summary.json` contains the
shared Run identity, input hashes, publication provenance, and ordered artifact
entries once. `RUN_ID.run_summary.tsv` and `RUN_ID.qc_summary.tsv` are human
projections; no per-artifact JSON, artifact index, or summary receipt is persisted.
A selected `emrys.analysis_reporters` provider supplies the scientific view;
EMRYS supplies the evidence-and-operations view, safe rendering, portable links,
and publication. Both views use the same validated input bytes. There is no
generic scientific-report schema or section language.

## Report outputs

The report receipt defines this exact ordered roster. Filenames begin with `RUN_ID.`.

| Output ID | Kind | Filename suffix |
| --- | --- | --- |
| `scientific-report-html` | `scientific_html` | `scientific_report.html` |
| `evidence-report-html` | `evidence_html` | `evidence_report.html` |
| `run-summary-tsv` | `run_summary_tsv` | `run_summary.tsv` |

`RUN_ID.report_outputs.tsv` is the receipt, outside that roster. Only the first
two outputs are HTML Results. The frozen `ReportContext.stable_paths` stores
scientific HTML, evidence HTML, summary TSV, then receipt; receipt output rows
use its first three `Path` objects.

Current Runs use artifact entries v2, Run summaries v5 and report receipts v6.
The manifest binds the original scientific Run and Attempt by path and hash;
those records preserve the actual scientific packages, commands and reused task
origins. The manifest and HTML receipt separately identify their own publishers.
Reporting source changes and package release numbers do not change scientific
Run identity. Scientific code, validation, backend and locked-runtime changes
remain compatibility checks. Old-format inspection, resume and regeneration
are unsupported; existing data and evidence remain untouched.

## Code and artifact roots

Production callers observe the installed EMRYS package through
[`source_authority.py`](../libraries/source_authority.py). Its exact code hash,
version, and build provenance enter the manifest and report receipt. Original scientific code remains attributed by the Run and Attempt records.
Admission repeats at the existing
input and publication boundaries to detect changes during the operation; it
does not require Git or a matching checkout.

An independent canonical artifact root resolves contract-relative inventory and
native data paths. Both roots remain explicit in prepared contexts through
publication and rechecks; neither is inferred from the working directory or
from the summary's location. This keeps the generating code distinct from the
scientific data it reads.

## Publication and recovery

Each publisher creates only absent transaction-owned finals. Preparation never
authorizes replacing existing outputs. Manifest and TSV views share one lock,
staging operation, and rollback scope. Installing the manifest last completes
that operation; its file hash is the lifecycle's single evidence identity.

Publishers stage bytes, retain file anchors, install finals exclusively, and
install the manifest or HTML projection receipt last. They recheck inputs, source, outputs, and directories
at the relevant publication boundaries. Rollback removes only outputs with
proven ownership. Uncertain ownership or failed rollback preserves remaining
state and locks. Cleanup failure preserves committed outputs and remaining
recovery state; recovery markers are best effort inside a verified directory.
Directories or files replaced by another process are not cleanup targets.

Run-level generation refuses any existing output state, including incomplete
or ambiguous state. Preserve locks, partials, `.previous` files, staging
directories, and recovery evidence. Reporting provides no repair or evidence-deletion authority.

## Implementation

The private [_artifact_index](_artifact_index/README.md),
[_run_summary](_run_summary/README.md), and [_run_report](_run_report/README.md)
packages implement the sequence. Indexing derives expected artifacts from the
validated Analysis descriptor; it scans neither providers nor filesystem outputs
and creates no separate artifact registry or store. Its
[known validation-roster limit](_artifact_index/README.md#validation-report-limit)
requires independent roster and adapter-mutation tests.

The built-in [paired-CMH reporter](paired_cmh_candidate_ranking_report/README.md)
presents tested candidates, selected records, admitted context/motifs, methods,
and limitations. The evidence view presents provenance, artifacts, QC, tools,
issues, and Attempt history. Scientific-context admission reopens bound reference
files when required to validate the transaction. View rendering does not reopen
references, rerun analysis, discover motifs, infer missing data, or hide required
scientific caveats.
[`transaction_validation.py`](transaction_validation.py) validates the current
manifest, immutable inputs, native sources and report projections. Within one
operation, it carries checked contexts forward instead of rebuilding them:
indexing supplies canonical Step 09/10 projections, and publication supplies
the prepared HTML and TSV bytes. Source identities, complete file rosters and
exact published bytes are still checked before reuse and publication.
A fresh inspection validates native scientific sources and the original
manifest, retaining its publisher provenance and the hashes of both TSV tables. Completed HTML reports are checked
against their ledger-bound receipt and its complete data-input and output
rosters. Reuse does not invoke the current renderer. New publication still checks
exact prepared output bytes, HTML safety and accessibility, and package stability.

## Implementation and fault tests

Publication and source-identity checks call their real owners directly. See
[reporting tests](../../../tests/reporting/README.md#fault-injection) for injection
points and retired test-only interfaces. Artifact contexts retain source observers
for later checks; validated transactions retain real input-recheck callbacks.
