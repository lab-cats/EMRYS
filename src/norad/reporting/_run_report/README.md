# Run-report implementation owners

This private package supports the direct public
[`norad build report`](../report.py) owner. It adds no command surface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable v4 contract constants and two-view context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary admission with stable snapshots. |
| [`computational.py`](computational.py) | Exact primary-analysis Step 09 trio and all-pass owner-validation selection, source identity/snapshots, canonical trio admission, and bounded display rows. |
| [`context.py`](context.py) | Side-effect-free resource, output, and predecessor preparation. |
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
all-pass owner-validation report, reporting opens only those artifact-record
paths. It retains primary-analysis/adapter selection; artifact-root, media type,
expected path, SHA-256, size, and row-count checks; roster admission; stable
snapshots; unavailable handling; and display limits. It delegates intrinsic
trio admission to `step09.validate_step09_projection` and never searches for
native outputs.

The all-pass owner-validation artifact, not rendering, carries upstream Step
08, paired-sample CMH, global BH, mutation-spectrum, PDF, and publication
checks. Reporting reimplements neither shell/R producer nor independent oracle;
it discloses an incomplete trio without opening or inferring candidate rows.

The scientific view labels these rows **computational results — not
scientifically adjudicated**. It presents Step 09 design, contrast, counts,
thresholds and method; displays the significant subset before the all-sites
table; includes raw per-sample DP/AD/AF; and caps each candidate table at 250
rows. Selected sample QC is copied only from exact complete metrics already in
the run summary. Paths, hashes, attempts, artifacts, tools, renderer provenance,
and the artifact-availability figure are excluded from this view.

The operational-evidence view contains no candidate rows. It retains run and
execution status, limitations, expected scopes, artifact QC, attempt lineage,
the artifact appendix, tools and issues, renderer provenance, and the accessible
artifact-availability figure. Its compact four-record Step 09 source table
preserves exact path, hash, size, and row-count orientation for the validation,
all-sites, significant-sites, and summary inputs. Any scientific-table
truncation uses the v4 receipt contract to bind the displayed prefix to its full
source. Candidate review, adjudication, and biological interpretation remain
external research activities.

The transaction retains input rechecks, lock ownership, predecessor identity,
backup/rollback, recovery markers, foreign-state preservation, staged
validation, receipt-last publication, and characterized interruption behavior.
Tests inject a frozen `ReportPublicationOps` value rather than patching module
globals. The renderer producer is `4.0.0`; run-summary `2.0.0` and
report-receipt `4.0.0` are clean breaking contracts with no compatibility shim.
