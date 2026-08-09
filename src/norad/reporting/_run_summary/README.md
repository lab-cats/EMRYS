# Run-summary implementation owners

This private package supports the public
[`build_run_summary.py`](../build_run_summary.py) entry point. The facade owns
CLI compatibility and context preparation; these modules own bounded
deterministic helpers and publication beneath it.

| Module | Owned responsibility |
| --- | --- |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and build context. |
| [`inputs.py`](inputs.py) | CLI parsing, explicit path guards, and immutable file snapshots. |
| [`approvals.py`](approvals.py) | Run-bound report-table approval normalization. |
| [`transaction.py`](transaction.py) | Input transaction loading, history parsing, and stable value utilities. |
| [`projection.py`](projection.py) | Status, science, summary-row, and QC-row projections. |
| [`validation.py`](validation.py) | Canonical document, predecessor, and receipt validation. |
| [`document.py`](document.py) | Canonical deterministic run-summary document assembly. |
| [`publication.py`](publication.py) | Receipt-last publication, rollback, recovery, and published-output validation. |
| [`science_models.py`](science_models.py) | Scientific-review value objects, vocabulary aliases, and normalization error identity. |
| [`science_io.py`](science_io.py) | Guarded scientific-review file intake and mutation checks. |
| [`science_package.py`](science_package.py) | Committed public Step 09c package reconstruction and artifact binding. |
| [`science_evidence.py`](science_evidence.py) | Indexed input-artifact and scientific-evidence normalization. |

The package is not an additional supported command surface. Compatibility
bindings remain available from the public facade and
[`_run_summary_science.py`](../_run_summary_science.py), and all modules reuse
the same artifact adapter and contract owner.
