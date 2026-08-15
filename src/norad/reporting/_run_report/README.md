# Run-report implementation owners

This private package supports the direct public
[`norad build report`](../report.py) owner. It adds no command surface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable contract constants and context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary admission with stable snapshots. |
| [`computational.py`](computational.py) | Exact primary-analysis Step 09 result-trio plus all-pass owner-validation admission, semantic reconciliation, bounded display rows, and stable snapshots. |
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

When the canonical run summary declares a complete primary-analysis Step 09
`cmh_all_sites`, `cmh_significant_sites`, and `cmh_summary` trio plus its exact
all-pass owner-validation report, the report opens only those exact
artifact-record paths. Admission rechecks SHA-256, byte
size, row count, exact headers, ordered DP/AD/AF sample blocks, sample counts,
candidate uniqueness, statuses, summary counts and thresholds, and the exact
ordered significant subset. It never searches for native outputs. An
incomplete trio is reported as unavailable and no candidate row is opened or
inferred.

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
