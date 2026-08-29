# Reporting projection owner

Reporting consumes explicit validated inputs. It does not discover or rerun
analysis, decide scientific validity, or promote evidence.

## Supported command boundaries

| Interface | Supported role | Responsibility |
| --- | --- | --- |
| `emrys run` / `emrys resume` | Normal operator path | Close the scientific Attempt at `cohort_slice`, release its Run lock, then invoke reporting automatically unless `--no-report` was selected. |
| `emrys report --run-root ABSOLUTE_RUN_ROOT` | Independent reporting path | Re-admit one successful scientific Run and either validate reusable reports or print a no-write generation plan; add `--execute` to generate an absent bundle. |

Reporting is downstream of, and not part of, the scientific Attempt. A
reporting failure returns nonzero but leaves the successful Attempt receipt and
scientific Results unchanged. `--no-report` disables only this downstream
operation; it does not change the scientific graph, receipt, or Results.

The independent command is dry-run/read-only by default:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys report \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST
```

Repeat with `--execute` to publish the ordered artifact-index, run-summary, and
HTML transactions. The final report transaction publishes exactly:

- `RUN_ID.scientific_report.html`
- `RUN_ID.evidence_report.html`
- `RUN_ID.run_summary.tsv`
- `RUN_ID.report_outputs.tsv`

The last file is the `emrys.report_receipt` v4 receipt. Existing older output
directories, bare HTML predecessors, partial ledgers, and incomplete sets are
rejected and preserved. A complete existing bundle is reused only after every
transaction and output is revalidated. New publication begins only when all
three reporting ledgers and both Run-specific output locations are exactly
empty; the public command does not overwrite, adopt, delete, or repair state.

The artifact-index, run-summary, and HTML builder modules remain private
implementation used by the Run-level coordinator and developer fixtures. They
are not installed public commands or operator recovery routes.

For current fixed-profile Runs, orchestration publishes this bundle only at
`results/reports/RUN_ID`. An exact historical profile and verified reporting
ledger may still bind `products/report/RUN_ID` for read-only inspection; current
publication cannot select or adopt that legacy location. The fixed-profile
content change creates new Run identities, so historical Runs remain readable
but are not thereby made resumable under the current profile.

The scientific HTML is the print-oriented reader-facing interpretation view.
It opens with a concise analysis summary, then presents four primary figures,
four supporting figures, a visible figure-reading guide, and a visible methods
and data note. It uses static sections only: no scientific explanation or
limitation is hidden in a collapsible control. Every figure carries a plain-
language takeaway, question, reading guide, population statement, and explicit
limitations. Primary figures use reader-facing labels `Figure 1` through
`Figure 4`; supporting appendix figures use `Figure S1` through `Figure S4`,
while stable internal figure IDs continue to own validation and provenance.

The primary set contains the complete candidate effect-versus-depth landscape,
the selected candidate-centered context panels, the nonexclusive annotation-
membership summary, and the registered-motif position/enrichment view. The
supporting set preserves the mutation spectrum, condition-mean concordance,
manifest-paired sample profiles, and sequence-context logos. The ranked-card
selected-candidate index and vertical evidence records state editing rate,
exact location and orientation facts, paired AF/AD/DP support, and nearby
registered motif evidence from the same immutable display projection used by
the paired-profile and selected-context figures. The selected-context figure
is explicitly candidate-centered mechanically oriented genomic context; it
does not claim a continuous transcript locus, choose an isoform, or infer
biological strand. The scientific view
intentionally omits source paths, hashes, attempts, the artifact appendix, tool
records, renderer provenance, and the artifact-availability figure.

Both HTML files carry relative navigation to the scientific report, evidence
and provenance, and operations. The evidence HTML is titled **Evidence and
operations** and separates those two audiences without introducing another
artifact. Evidence and provenance owns admitted scientific sources, artifact-
level QC, the artifact appendix, tools/issues, and renderer provenance. The
retained Run overview owns run identity, status,
limitations, expected scopes, and the accessible artifact-availability figure;
Operations owns Attempt lineage and the existing Run-inspection command. Both
views also link, using portable relative paths, to every admitted Step `09`
all-sites and threshold-passing table and Step `10` candidate-context table;
unavailable inputs produce no dead link. A compact six-record table binds the
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

The scientific HTML does not reproduce either native candidate TSV as a wide
table. The complete all-sites and threshold-passing TSVs remain admitted,
evidence-bound data artifacts; the evidence view records their exact paths and
hashes. The scientific view instead uses the complete tested population for the
candidate landscape plus one bounded, vertically structured selected-candidate
projection. When Step `10` is present, its upstream display ranks are preserved;
historical runs use the fixed FDR/effect/candidate-ID fallback rule. The mutation
spectrum consumes the canonical 12-row TSV and is not recomputed from candidate
rows. Location memberships remain independent and nonexclusive, so percentages
need not sum to 100%; an all-false record is labeled as no recorded overlap, not
inferred to be intergenic. If the exact result trio, mutation spectrum, or all-
pass owner validation is incomplete, both views disclose that state and do not
infer candidate evidence or figures.

Runs that predate Step `10` retain the five Step `09` figures and the selected-
candidate panels, with motif context explicitly marked unavailable; the two
population-level Step `10` figures remain unavailable. Partial or incomplete
Step `10` declarations are disclosed without inference; any complete present
transaction with a path, hash, size, row-count, schema, validation, or semantic
mismatch fails closed.

These are explicitly **computational results — not scientifically
adjudicated**. Candidate review, adjudication, and biological interpretation
are external research activities and are not inferred from threshold-passing
rows.

[`report.py`](report.py) is the private HTML builder used by the Run-level
reporting coordinator and developer fixtures. The private
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
Current reports are reconstructed byte-for-byte. Read-only inspection of an
exact verified legacy profile instead re-admits the artifact-index, run-summary,
and report ledgers against each transaction's recorded producer identity and
full bound inputs and outputs. Historical artifact records are admitted from
their receipt-bound roster rather than reconstructed from today's producer
registry. The current checkout is admitted as the reader, not misrepresented as
any historical producer. The report read validates
receipt v4, its bound run summary, and every declared output path/hash/size; it
does not misclassify preserved 5.1.0 HTML as a failed 5.2.0 reconstruction or
permit that legacy location for current publication.

This completion boundary assumes the same single-user, cooperative workspace
as the local pilot. Pre-existing symlink components, leaf substitution,
unstable bytes, and roster drift fail closed; hostile concurrent replacement
of ancestor directories or mount namespaces requires external isolation and
lies outside this local evidence claim.

A rendered document or receipt reflects only its validated inputs and declared
computational evidence. It does not establish production execution, validated
editing sites, or biological readiness.
