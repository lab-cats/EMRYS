# Run-summary implementation owners

This private package supports the public
[`build_run_summary.py`](../build_run_summary.py) entry point. The facade owns
context preparation and the complete publication, rollback, and fault-handling
transaction; these modules own bounded deterministic helpers beneath it.

| Module | Owned responsibility |
| --- | --- |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and build context. |
| [`inputs.py`](inputs.py) | CLI parsing, explicit path guards, and immutable file snapshots. |
| [`approvals.py`](approvals.py) | Run-bound report-table approval normalization. |
| [`transaction.py`](transaction.py) | Input transaction loading, history parsing, and stable value utilities. |
| [`projection.py`](projection.py) | Status, science, summary-row, and QC-row projections. |
| [`validation.py`](validation.py) | Canonical document, predecessor, and receipt validation. |

The package is not an additional supported command surface. Compatibility
bindings remain available from the public facade, and all modules reuse the
same artifact adapter and contract owner.
