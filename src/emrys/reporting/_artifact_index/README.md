# Artifact-index internals

This private package implements the artifact-index transaction used by the
Run-level reporting coordinator and developer fixtures through
[`context.py`](context.py) and [`publication.py`](publication.py). It has no
installed public command or operator recovery route. [`api.py`](api.py) is the narrow private import boundary used
by sibling reporting owners for deliberate artifact parsing, validation,
serialization, and transaction primitives. It is not a command or public
application API. Neutral filesystem authorities live directly in
[`libraries/source_authority.py`](../../libraries/source_authority.py); this
private package does not forward them.

The coordinator supplies the source checkout and independent artifact source
root before `context.py` validates Run inputs and prepares the transaction. Checkout
admission requires one canonical, nonsymlink EMRYS Git top level and exact
bytes between the executing package and that checkout. Both admitted values
remain on `BuildContext` through publication. The artifact root governs
relative inventory and native-contract
paths plus predecessor, post-publish, and rollback record validation. The
checkout governs Git `HEAD` resolution and producer existence and hashing. The
authority caches neither Git commit nor producer state; the later `HEAD` probe
ignores ambient `GIT_*` routing while preserving unrelated environment state. Those
observations stay at their established points in context construction,
preserving their timing, diagnostics, and serialized evidence.

The private run-summary preparation imports both neutral authorities directly,
not through this package or the artifact-index context. Its checkout governs
producer identity; its artifact root governs contract-relative artifact paths
plus semantic, predecessor, post-publication, and rollback validation.

The modules keep observed responsibilities separate: the curated run-summary
API, exact contract loading, models and rosters, explicit adapter registration,
text and binary readers, inspection, named native reconciliation, record and
receipt assembly, context construction, receipt-last publication, and
published-transaction validation.
Stage-specific rules remain in their named reconciliation modules; this
package is not a generic stage framework.

[`reconcile_step09.py`](reconcile_step09.py) delegates intrinsic admission of
the exact result trio and mutation-spectrum reconciliation to
`step09.validate_step09_projection`. Artifact indexing retains
adapter/inventory selection, native source identity, the referenced Step 08
path/hash/adapter/sample-order graph, and artifact-state failure propagation;
it does not replay upstream, paired-sample CMH, global BH, PDF, R-producer, or
independent-oracle work.

[`reconcile_step10.py`](reconcile_step10.py) delegates the complete receipt-
last scientific-context transaction to
`scientific_context.validate_scientific_context_transaction`. Artifact
indexing retains exact adapter/inventory selection and binds the receipt's
Step `09` trio, FASTA/FAI, and four output paths, hashes, and row counts to the
declared graph. Reference extraction, motif matching, logo/statistic
reconciliation, and display selection remain canonical contract or producer
work rather than a second artifact-index implementation.

Artifact inspection enforces common validation-report structure, safe unique
check IDs, step, scope, and status, but does not yet enforce each producer's
exact ordered check roster. A structurally plausible report with a missing,
extra, substituted, duplicate, or reordered check can therefore enter the
artifact graph; retain the independent roster expectations and
artifact-adapter mutation tests until that separately reviewed defect is
corrected.

Text inspection imports three private owners directly: `_text_common.py` owns
UTF-8 line admission, `_text_tabular.py` owns TSV, sample-block, and native
anchor parsing, and `_text_genomic.py` owns VCF, reference, BED12, STAR, and
Picard inspection. The split adds no adapter kind, registry entry, schema,
artifact state, or discovery behavior.

[`publication.py`](publication.py) owns the shared byte-write, durability-sync,
lock, removal, and signal transaction primitives as well as the artifact-index
coordinator, rollback, recovery, and cleanup order. Its frozen
`ArtifactPublicationOps` record names only the transaction fault seams and is
passed explicitly by tests; production uses the immutable default. Context
preparation exposes no publication or contract modules for patching. Run-summary assembly reaches deliberately shared
transaction primitives through `api.py`; static reporting imports neutral
checkout admission and Git identity directly. These internals do not change artifact schemas, serialized bytes,
source discovery policy, evidence states, diagnostics, or publication order.
