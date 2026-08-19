# Run-report implementation owners

This private package supports the direct public
[`norad build report`](../report.py) owner. It adds no command surface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable v4 contract constants, figure values, and two-view context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary admission with stable snapshots. |
| [`computational.py`](computational.py) | Exact primary-analysis Step 09 trio, mutation spectrum, all-pass owner validation, and summary-bound sample-manifest admission; source identity/snapshots; canonical admission; and bounded table-display rows. |
| [`scientific_context.py`](scientific_context.py) | Exact primary-analysis Step 10 selection, canonical receipt-transaction admission, record reconciliation, and stable snapshots of all outputs and receipt-bound inputs. |
| [`figures.py`](figures.py) | Shared controlled Matplotlib/Logomaker SVG boundary plus the five deterministic Step 09 figures. |
| [`scientific_context_figures.py`](scientific_context_figures.py) | Presentation-only observed/registered logos, motif-position/enrichment, and selected context-track figures from admitted Step 10 values. |
| [`context.py`](context.py) | Resource, output, and predecessor preparation without durable output state; cleaned temporary renderer initialization is explicit. |
| [`view.py`](view.py) | Separate structured scientific and operational-evidence projections without HTML construction. |
| [`validation.py`](validation.py) | Autoescaped strict Jinja environment plus CSS, security, per-view semantic HTML, and accessibility validation. |
| [`receipt.py`](receipt.py) | Deterministic summary TSV and v4 two-view receipt projection/validation. |
| [`publication.py`](publication.py) | One receipt-last two-HTML transaction using injected immutable fault operations. |
| [`transaction.py`](transaction.py) | Lock, snapshot, durability, staging, and recovery primitives. |

The public owner admits the required absolute canonical source checkout and
independent artifact source root before reading report inputs and passes both
into this package explicitly. The artifact root governs contract-relative
paths recorded in the run summary; the
checkout governs renderer Git identity. Private owners infer neither root from
the working directory or run-summary location and do not re-admit during
publication.

When the canonical run summary declares a complete primary Step 09 trio
(`cmh_all_sites`, `cmh_significant_sites`, and `cmh_summary`) and its exact
mutation-spectrum TSV and all-pass owner-validation report, reporting opens
only those artifact-record paths. It retains primary-analysis/adapter
selection; artifact-root, media type, expected path, SHA-256, size, and
row-count checks; roster admission; stable snapshots; unavailable handling;
and display limits. It delegates intrinsic trio and mutation-spectrum admission
to `step09.validate_step09_projection` and never searches for native outputs.
It separately admits the exact sample manifest recorded by the Step 09 summary,
requires its hash to match both that summary and the immutable run contract,
reuses canonical manifest and pairing validation, and requires exact result-
column sample order. The manifest snapshot participates in every input recheck
and report-receipt attempt identity.

The all-pass owner-validation artifact, not rendering, carries upstream Step
08, paired-sample CMH, global BH, PDF, and publication checks. Reporting
reimplements neither mutation-spectrum reconciliation, shell/R producer, nor
independent oracle; it discloses an incomplete source bundle without opening or
inferring candidate rows.

When all six primary-analysis Step 10 artifact records are complete, reporting
requires its one-check owner validation to pass and reuses
`validate_scientific_context_transaction(...)` as the sole semantic admission.
It reconciles every output artifact record with that receipt-last transaction,
snapshots the receipt plus all four outputs and six bound inputs, and requires
the receipt-bound Step 09 trio to be the same trio admitted for the report. A
run with no Step 10 records is treated as historical: only figures 6–8 are
unavailable. A partial or incomplete declared transaction is disclosed without
opening it; a present hash, path, row, schema, validation, or semantic mismatch
fails the report closed.

The scientific view labels these rows **computational results — not
scientifically adjudicated**. It presents Step 09 design, contrast, counts,
thresholds and method; displays the significant subset before the all-sites
table; includes raw per-sample DP/AD/AF; and caps each candidate table at 250
rows. Its current-data figures render a candidate landscape and condition-mean
concordance from every successfully tested all-sites row, a mutation spectrum
from the admitted canonical 12-row TSV, up to eight significant-candidate
paired-sample profiles under the fixed FDR/effect/ID display rule, and
independent Step 08 location-membership bars from the complete significant
subset. The remaining figures consume Step 10's observed ±10 frequency matrix,
registered PUM catalog, fixed 10-nt nearest-hit bins and Fisher result, and its
upstream-ranked candidate contexts. The selected-context view displays only a
±25-nt slice, admitted motif spans, and manifest-paired Step 09 AF values. It
does not reopen the FASTA, scan motifs, count bases or hits, reconstruct
populations, run enrichment, smooth position profiles, or select/rerank
candidates. Figures do not inherit the table-display cap. Selected
sample QC is copied only from exact complete metrics already in the run summary.
Paths, hashes, attempts, artifacts, tools, renderer provenance, and the
artifact-availability figure are excluded from this view.

The operational-evidence view contains no candidate rows. It retains run and
execution status, limitations, expected scopes, artifact QC, attempt lineage,
the artifact appendix, tools and issues, renderer provenance, and the accessible
artifact-availability figure. Its compact six-record Step 09 source table
preserves exact path, hash, size, and row-count orientation for the validation,
all-sites, significant-sites, summary, mutation-spectrum, and summary-bound
sample-manifest inputs. A separate Step 10 table records its validation,
receipt, four outputs, and every receipt-bound input; the adjacent policy table
keeps the orientation, windows, motif, populations, minima, Fisher policy, and
owner software in the evidence view. The existing provenance section records the fixed
figure roster, status, mappings, populations, SVG hashes/sizes, Matplotlib
and Logomaker versions, and figure-policy version without duplicating the images. Any
scientific-table truncation uses the v4 receipt contract to bind the displayed
prefix to its full source. Candidate review, adjudication, and biological
interpretation remain external research activities.

The transaction retains input rechecks, lock ownership, predecessor identity,
backup/rollback, recovery markers, foreign-state preservation, staged
validation, receipt-last publication, and characterized interruption behavior.
Tests inject a frozen `ReportPublicationOps` value rather than patching module
globals. The renderer producer is `4.3.0`; run-summary `2.0.0` and
report-receipt `4.0.0` are clean breaking contracts with no compatibility shim.
