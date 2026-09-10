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

Current Runs use run-summary v4/report-receipt v5, attributing the computation
provider, scientific reporter, and core renderer separately. Reporter identity
never changes Analysis or Run identity. Complete bundles are reused only after
current-source semantic revalidation. Old-version Run inspection, resume, and
report regeneration are unsupported; their data and evidence remain untouched.

## Source and artifact roots

Before reading inputs, production callers validate two explicit roots through
[`libraries/source_authority.py`](../libraries/source_authority.py). The source
checkout must be a canonical EMRYS Git top level without symlinks and match the
executing package's bytes. It supplies producer paths, hashes, and Git identity.
The independent artifact root resolves contract-relative inventory and native
paths, including post-publication validation. Neither comes from
the working directory or a run-summary location.

Both roots remain in prepared contexts through publication and input rechecks;
publishers neither infer nor re-admit them. Git observations ignore ambient
`GIT_*` routing but preserve unrelated environment settings. Source authority
caches neither the Git commit nor producer state; each transaction keeps its
own established observation points and real input-recheck callbacks.

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
Public [`transaction_validation.py`](transaction_validation.py) re-admits the
current manifest, immutable inputs, native sources, and deterministic TSV and
HTML projections. Revalidation binds source identities and complete file rosters;
cached predecessors retain recheck callbacks. Reporting has two stages: the Run
manifest followed by the HTML projections.

## Implementation and fault tests

Publication and source-identity checks call their real owners directly. See
[reporting tests](../../../tests/reporting/README.md#fault-injection) for injection
points and retired test-only interfaces. Artifact contexts retain source observers
for later checks; validated transactions retain real input-recheck callbacks.
