# Run-summary implementation owners

This private package implements the run-summary transaction used by the
Run-level reporting coordinator and developer fixtures through
[`builder.prepare_context`](builder.py) and
[`publication.py`](publication.py). It has no installed public command or
operator recovery route; these modules own bounded deterministic context,
projection, and publication responsibilities beneath the coordinator.

| Module | Owned responsibility |
| --- | --- |
| [`builder.py`](builder.py) | `prepare_context`: retain admitted source/artifact roots and prepare the context. |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and build context. |
| [`inputs.py`](inputs.py) | Explicit path guards and immutable file snapshots. |
| [`transaction.py`](transaction.py) | Input transaction loading, history parsing, and stable value utilities. |
| [`projection.py`](projection.py) | Computational status, summary-row, and QC-row projections. |
| [`validation.py`](validation.py) | Canonical document, predecessor, and receipt validation. |
| [`document.py`](document.py) | Canonical deterministic run-summary document assembly. |
| [`publication.py`](publication.py) | Receipt-last publication, rollback, recovery, and published-output validation. |

The package is not an additional supported command surface. Context preparation
and publication recheck share the same validated artifact transaction.
Document assembly selects the schema from the admitted Analysis form: existing
flat paired-CMH Runs retain run-summary v2, while explicit modules use
module-neutral run-summary v3. V3 carries the analysis-policy path, SHA-256,
and size without paired-CMH candidate terminology; it does not weaken the
artifact predecessor or transaction checks.
Artifact-index parsing, validation, serialization, and shared transaction primitives enter through the narrow
private [`_artifact_index/api.py`](../_artifact_index/api.py) boundary rather
than artifact-index context preparation. `builder.prepare_context` receives
the neutral checkout and artifact-root values defined by
[`libraries/source_authority.py`](../../libraries/source_authority.py).
Production callers admit both explicit roots before preparation reads inputs.
Package identity is checked during checkout admission; Git observations ignore
ambient `GIT_*` routing while preserving unrelated environment state.

Both admitted values remain on `BuildContext`. The artifact root governs
contract-relative artifact intake and document-semantic and predecessor validation; the
checkout governs producer Git identity. Publication retains both for input
rechecks and post-publication validation; it does not re-admit or infer a root.
Preparation and read-only validation retain predecessor and historical receipt
admission. Publication follows the shared
[publication and recovery contract](../README.md#publication-and-recovery).

The frozen `RunSummaryBuildDeps` record remains the preparation seam for
input loading, producer identity, document construction, and the final input
recheck. Production uses immutable defaults; preparation tests pass explicit
modified values. Publication fault tests patch the real called functions as
described in the shared [test boundary](../README.md#implementation-and-fault-tests).

The public read-only
[`reporting.transaction_validation`](../transaction_validation.py) owner owns
the semantic input recheck used by preparation, publication, lifecycle, and
inspection. The private publication module exposes no parallel recheck facade.

All three private reporting transactions reuse the same artifact contract and error
identities. The summary consumes validated computational artifact records. It
does not encode candidate review, adjudication, biological interpretation, an
approver gate, or a scientific-completion state.
