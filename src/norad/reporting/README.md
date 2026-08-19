# Reporting projection owner

Reporting consumes explicit validated inputs. It does not discover or rerun
analysis, decide scientific validity, or promote evidence.

## Supported command boundaries

| Interface | Supported role | Responsibility |
| --- | --- | --- |
| `python -X pycache_prefix=/dev/null -I -m norad build report` | Operator-facing standalone rebuild | Render one canonical run summary under distinct code and artifact authorities into separate self-contained scientific and evidence HTML views, summary TSV, and a v4 receipt published last. |
| `python -X pycache_prefix=/dev/null -I -m norad build artifact-index` | Workflow-owned transaction; advanced diagnosis/recovery | Reconcile one declared artifact root and inventory under an independent producer-checkout authority into a receipt-last artifact index. |
| `python -X pycache_prefix=/dev/null -I -m norad build run-summary` | Workflow-owned transaction; advanced diagnosis/recovery | Project one admitted artifact-index receipt into the canonical run summary. |

The normal researcher path is `norad run`, which invokes all three transactions
in order. `build report` is also a supported direct operator route for an
existing canonical summary. The two intermediate commands remain stable and
documented for workflow execution and bounded diagnosis or recovery; they are
not a general invitation to assemble or adopt reporting state manually.

All three build routes require both `--source-checkout
ABSOLUTE_CANONICAL_CHECKOUT` and `--artifact-source-root
ABSOLUTE_CANONICAL_ARTIFACT_ROOT`. The report command is dry-run by default
and accepts only explicit inputs:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad build report \
  --source-checkout /absolute/path/to/norad \
  --artifact-source-root /absolute/path/to/run-root \
  --run-summary /absolute/path/to/run-root/products/artifact-summary/RUN_ID/RUN_ID.run_summary.json \
  --output-root /absolute/path/to/run-root/products/report
```

`--source-checkout` names the absolute canonical NORAD Git top level whose
Python and packaged-resource bytes match the executing package; it owns
producer and renderer Git identity. `--artifact-source-root` independently
resolves contract-relative inventory and native artifact paths. Reporting
infers neither root from the working directory
or the run-summary location.

Repeat with `--execute` to publish exactly:

- `RUN_ID.scientific_report.html`
- `RUN_ID.evidence_report.html`
- `RUN_ID.run_summary.tsv`
- `RUN_ID.report_outputs.tsv`

The last file is the `norad.report_receipt` v4 receipt. Existing older output
directories, bare HTML predecessors, and incomplete sets are rejected; use a
fresh output root unless an explicit migration is separately approved.

The scientific HTML is the reader-facing interpretation view. For the primary
analysis, it shows the Step `09` design and contrast, counts, declared
thresholds and method, the significant subset before all CMH-ranked candidates,
raw per-sample DP/AD/AF, and selected exact sample QC already recorded by STAR,
flagstat, RSeQC, and Picard artifacts. It also embeds deterministic candidate-
landscape, mutation-spectrum, condition-mean-concordance, manifest-paired
sample-profile, and nonexclusive annotation-membership SVG figures rendered
from the admitted Step `09` records. When a complete Step `10` scientific-
context transaction is present, it adds edit-centered observed and registered
PUM logos, a fixed-bin motif-position/Fisher-enrichment view, and upstream-
selected ±25-nt candidate context tracks with admitted motif spans and paired
sample AF values. It intentionally omits source paths,
hashes, attempts, the artifact appendix, tool records, renderer provenance, and
the artifact-availability figure.

The evidence HTML is the operational and provenance view. It retains run
identity and status, limitations, expected scopes, artifact-level QC, attempt
lineage, artifact appendix, tools and issues, renderer provenance, and the
accessible artifact-availability figure. A compact six-record table binds the
admitted Step `09` all-sites, significant-sites, summary, mutation-spectrum,
all-pass owner-validation, and its summary-bound sample manifest. A separate
table binds the Step `10` validation, receipt, four outputs, and all six receipt-
bound inputs; its context, motif, population, enrichment, and software policies
remain in the evidence view. Figure status,
input roles, mappings, population, SVG identity, renderer version, and policy
version remain in the existing report-provenance section. It does not display
candidate rows or scientific figure images.

Both views are projections of the same admitted inputs. Every Step `09` source
is checked by path, SHA-256, byte size, row count, header, sample blocks,
candidate identity, significant-subset identity, and summary reconciliation
under the canonical scientific-evidence owner. The renderer never discovers
native output by filename. The sample manifest is snapshot- and hash-checked
against both the Step `09` summary and immutable run contract, canonically
validated, required to match result-column order, and paired only by the
canonical Step `09` pairing owner.

Complete Step `10` records are re-admitted only through the canonical
scientific-context transaction validator. Reporting reconciles the run-summary
records with that receipt, retains stable snapshots of every file the owner
validated, and requires the receipt-bound Step `09` trio to match the report's
admitted trio. It consumes the owner's sequence frequencies, display ranks,
exact motif hits, fixed position bins, availability states, odds ratio,
confidence interval, and Fisher p-value. It does not reopen the FASTA, scan or
discover motifs, count bases or hits, rebuild populations, rerun a statistical
test, smooth profiles, or select candidates. Logomaker `0.8.7` renders the
admitted logo matrices inside the same cleaned temporary Matplotlib cache.

Scientific candidate tables display at most 250 rows each and disclose any
truncation without mixing paths or hashes into the scientific view. The evidence
view records the exact full sources, while receipt `truncations` bind truncated
scientific table displays to those sources. The candidate landscape consumes
all successfully tested rows rather than the 250-row table prefix; the mutation
spectrum consumes the canonical 12-row TSV and is not recomputed from candidate
rows. The location bars preserve independent Step `08` overlaps, so their
percentages need not sum to 100%. The paired profile is a display-only top-eight
selection by FDR ascending, absolute effect descending, then candidate ID; it
does not define a new scientific ranking. If the exact result trio, mutation
spectrum, or all-pass owner validation is incomplete, both views say so and no
candidate rows or scientific figures are opened.

Runs that predate Step `10` retain the five Step `09` figures and mark only the
three context figures unavailable. Partial or incomplete Step `10` declarations
are disclosed without inference; any complete present transaction with a path,
hash, size, row-count, schema, validation, or semantic mismatch fails closed.

These are explicitly **computational results — not scientifically
adjudicated**. Candidate review, adjudication, and biological interpretation
are external research activities and are not inferred from threshold-passing
rows.

[`report.py`](report.py) is the one public report owner. The private
[`_run_report/`](_run_report/README.md) package owns explicit input admission,
checkout-rooted semantic and table validation, structured view data, Jinja
rendering, centralized deterministic figure rendering, per-view static HTML
validation, receipt projection, and the lock/staging/rollback transaction. The
single shared packaged
[`run_report.html.j2`](templates/run_report.html.j2) template owns markup and
embeds the validated packaged [`run_report.css`](styles/run_report.css). Jinja
uses HTML autoescaping and `StrictUndefined`; only the tracked CSS crosses a
trusted raw boundary. Validated SVG bytes are base64 data URIs in ordinary
autoescaped image attributes. There are no scripts, remote assets, sidecars,
network access, format selection, or report PDF.

Focused protection is `make report-test`; `make demo-report` creates an ignored
synthetic two-view HTML demonstration beneath `results/demo-report-jinja/`.
Recovery routes are in
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md).

[`transaction_validation.py`](transaction_validation.py) is the public
read-only completion owner used by local lifecycle and inspection. Its three
specific validators and fixed-profile `validate_receipt(...)` dispatcher pin
receipt identity by no-follow descriptor before and after semantic validation,
then revalidate bound native sources, records, indexes, summaries, both HTML
views, TSV,
and receipts. A receipt path or hash alone is never completion evidence.

This completion boundary assumes the same single-user, cooperative workspace
as the local pilot. Pre-existing symlink components, leaf substitution,
unstable bytes, and roster drift fail closed; hostile concurrent replacement
of ancestor directories or mount namespaces requires external isolation and
lies outside this local evidence claim.

A rendered document or receipt reflects only its validated inputs and declared
computational evidence. It does not establish production execution, validated
editing sites, or biological readiness.
