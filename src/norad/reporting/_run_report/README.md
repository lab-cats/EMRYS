# Run-report implementation owners

This private package supports the direct public
[`norad build report`](../report.py) owner. It adds no command surface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable contract constants and context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary admission with stable snapshots. |
| [`computational.py`](computational.py) | Exact primary-analysis Step 09 trio and all-pass owner-validation selection, source identity/snapshots, canonical trio admission, and bounded display rows. |
| [`context.py`](context.py) | Side-effect-free resource, output, and predecessor preparation. |
| [`view.py`](view.py) | Structured report view data without HTML construction. |
| [`validation.py`](validation.py) | Autoescaped strict Jinja environment plus CSS, security, semantic HTML, and accessibility validation. |
| [`receipt.py`](receipt.py) | Deterministic summary TSV and v3 receipt projection/validation. |
| [`publication.py`](publication.py) | One receipt-last HTML transaction using injected immutable fault operations. |
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

The first open report category labels these rows **computational results — not
scientifically adjudicated**. It displays the significant subset before the
all-sites table, includes raw per-sample DP/AD/AF, and caps each candidate table
at 250 rows. Exact source identity and full row count remain visible; any
truncation uses the v3 receipt truncation contract. Candidate review,
adjudication, and biological interpretation remain external research
activities. Selected sample QC is copied only from exact complete metrics
already present in the run summary.

The transaction retains input rechecks, lock ownership, predecessor identity,
backup/rollback, recovery markers, foreign-state preservation, staged
validation, receipt-last publication, and characterized interruption behavior.
Tests inject a frozen `ReportPublicationOps` value rather than patching module
globals. The renderer producer is `3.0.0`; run-summary `2.0.0` and
report-receipt `3.0.0` are clean breaking contracts with no compatibility shim.
