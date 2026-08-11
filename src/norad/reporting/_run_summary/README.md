# Run-summary implementation owners

This private package supports the public
[`build_run_summary.py`](../build_run_summary.py) entry point. The facade owns
CLI compatibility, checkout admission, and context preparation; these modules
own bounded deterministic helpers and publication beneath it. There is no
grouped run-summary route or public `--source-checkout` option yet.

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
| [`science_projection.py`](science_projection.py) | Final scientific-review projection, schema and semantic validation, and one normalization error boundary. |

The package is not an additional supported command surface. The public facade
and publication recheck share the one canonical `science_projection.py`
module identity. Artifact-index parsing, validation, serialization, and shared
transaction primitives enter through the narrow private
[`_artifact_index/api.py`](../_artifact_index/api.py) boundary rather than the
private artifact-index command builder. That API also supplies the shared
`SourceCheckout` token, admission error, and admission function. After the
existing direct parser succeeds, the facade self-admits the checkout that owns
the executing package before it reads run inputs; a programmatic
`prepare_context` caller may instead supply an already admitted token. Package
identity is checked during admission, and both admission and later Git `HEAD`
resolution ignore ambient `GIT_*` routing while preserving unrelated
environment state.

The admitted token remains on `BuildContext`. Its root governs
contract-relative artifact intake, science-package and evidence intake,
approval-table paths, and document-semantic and predecessor validation.
Publication retains the same authority for input rechecks, science
renormalization, locked predecessor checks, post-publication validation, and
validation of a restored predecessor during rollback; it does not re-admit or
infer a root. Receipt-last publication, observation order, diagnostics,
serialized bytes, rollback, and recovery remain unchanged.

Both reporting owners still reuse the same artifact contract and error
identities. Science projection consumes the neutral review-package contract,
the committed public thirteen-file package, explicitly referenced evidence,
and validated index records. It does not load private Step `09c` inputs, own
review policy, promote computational or scientific state, or change an
evidence claim.
