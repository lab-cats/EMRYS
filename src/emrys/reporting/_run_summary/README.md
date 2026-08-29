# Run-summary implementation owners

This private package implements the run-summary transaction used by the
Run-level reporting coordinator and developer fixtures through
[`builder.prepare_context`](builder.py) and
[`publication.py`](publication.py). It has no installed public command or
operator recovery route; these modules own bounded deterministic context,
projection, and publication responsibilities beneath the coordinator.

| Module | Owned responsibility |
| --- | --- |
| [`builder.py`](builder.py) | `prepare_context`: source-checkout and artifact-root admission plus context preparation. |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and build context. |
| [`inputs.py`](inputs.py) | Explicit path guards and immutable file snapshots. |
| [`transaction.py`](transaction.py) | Input transaction loading, history parsing, and stable value utilities. |
| [`projection.py`](projection.py) | Computational status, summary-row, and QC-row projections. |
| [`validation.py`](validation.py) | Canonical document, predecessor, and receipt validation. |
| [`document.py`](document.py) | Canonical deterministic run-summary document assembly. |
| [`publication.py`](publication.py) | Receipt-last publication, rollback, recovery, and published-output validation. |

The package is not an additional supported command surface. Context preparation
and publication recheck share the same validated artifact transaction.
Artifact-index parsing, validation, serialization, and shared transaction primitives enter through the narrow
private [`_artifact_index/api.py`](../_artifact_index/api.py) boundary rather
than artifact-index context preparation. `builder.prepare_context` imports the
neutral checkout and artifact-root authorities directly from
[`libraries/source_authority.py`](../../libraries/source_authority.py). It
admits both explicit roots before reading run inputs.
Package identity is checked during checkout admission; Git observations ignore
ambient `GIT_*` routing while preserving unrelated environment state.

Both admitted values remain on `BuildContext`. The artifact root governs
contract-relative artifact intake and document-semantic and predecessor validation; the
checkout governs producer Git identity. Publication retains both for input
rechecks, locked predecessor checks, post-publication
validation, and validation of a restored predecessor during rollback; it does
not re-admit or infer a root. Receipt-last publication, observation order,
diagnostics, serialized bytes, rollback, and recovery remain unchanged.

The frozen `RunSummaryBuildDeps` record names only the preparation seams for
input loading, document construction, and
the final input recheck. The frozen `RunSummaryPublicationOps` record names
only publication replace, durability, locking, cleanup, signal, and validation
operations. Production uses immutable defaults; fault tests pass explicit
modified values. The preparation owner exposes no model, projection, adapter,
or publication globals for compatibility patching.

The public read-only
[`reporting.transaction_validation`](../transaction_validation.py) owner owns
the semantic input recheck used by preparation, publication, lifecycle, and
inspection. The private publication module exposes no parallel recheck facade.

All three private reporting transactions reuse the same artifact contract and error
identities. The summary consumes validated computational artifact records. It
does not encode candidate review, adjudication, biological interpretation, an
approver gate, or a scientific-completion state.
