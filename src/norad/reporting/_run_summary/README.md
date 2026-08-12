# Run-summary implementation owners

This private package implements the grouped
`python -I -m norad build run-summary` route through [`builder.py`](builder.py).
The former direct script is retired without a compatibility shim. The grouped
dispatcher owns lightweight parsing and imports the builder only after this
route is selected; these modules own bounded deterministic context,
projection, and publication responsibilities beneath it.

| Module | Owned responsibility |
| --- | --- |
| [`builder.py`](builder.py) | Checkout admission, context coordination, diagnostics, and optional publication for the grouped route. |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and build context. |
| [`inputs.py`](inputs.py) | Explicit path guards and immutable file snapshots. |
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

The package is not an additional supported command surface. The private
builder and publication recheck share the one canonical
`science_projection.py` module identity. Artifact-index parsing, validation,
serialization, and shared transaction primitives enter through the narrow
private [`_artifact_index/api.py`](../_artifact_index/api.py) boundary rather
than the private artifact-index command builder. That API also supplies the
shared `SourceCheckout` token, admission error, and admission function. After
grouped argument parsing succeeds, the builder admits the required explicit checkout
before it reads run inputs and passes the token to context preparation. Package
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

The frozen `RunSummaryBuildDeps` record names only the preparation seams for
input loading, science and approval normalization, document construction, and
the final input recheck. The frozen `RunSummaryPublicationOps` record names
only publication replace, durability, locking, cleanup, signal, and validation
operations. Production uses immutable defaults; fault tests pass explicit
modified values. The builder exposes no model, projection, adapter, or
publication globals for compatibility patching.

All three reporting build owners still reuse the same artifact contract and error
identities. Science projection consumes the neutral review-package contract,
the committed public thirteen-file package, explicitly referenced evidence,
and validated index records. It does not load private Step `09c` inputs, own
review policy, promote computational or scientific state, or change an
evidence claim.
