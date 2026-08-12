# Run-report implementation owners

This private package supports the direct public
[`norad build report`](../report.py) owner. It adds no command surface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable contract constants and context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary and approved-table admission with stable snapshots. |
| [`context.py`](context.py) | Side-effect-free resource, output, and predecessor preparation. |
| [`view.py`](view.py) | Structured report view data without HTML construction. |
| [`validation.py`](validation.py) | Autoescaped strict Jinja environment plus CSS, security, semantic HTML, and accessibility validation. |
| [`receipt.py`](receipt.py) | Deterministic summary TSV and v2 receipt projection/validation. |
| [`publication.py`](publication.py) | One receipt-last HTML transaction using injected immutable fault operations. |
| [`transaction.py`](transaction.py) | Lock, snapshot, durability, staging, and recovery primitives. |

The public owner admits the required absolute canonical source checkout before
reading report inputs and passes that authority into this package explicitly.
Its root governs repository-relative contract paths recorded in the run
summary, including approved-table paths, plus renderer Git identity. Private
owners neither infer a root from the working directory or run-summary location
nor re-admit the checkout during publication.

The transaction retains input rechecks, lock ownership, predecessor identity,
backup/rollback, recovery markers, foreign-state preservation, staged
validation, receipt-last publication, and characterized interruption behavior.
Tests inject a frozen `ReportPublicationOps` value rather than patching module
globals.
