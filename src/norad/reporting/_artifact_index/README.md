# Artifact-index internals

This private package decomposes the artifact-index implementation behind
[`build_artifact_index.py`](../build_artifact_index.py). The public script path
remains the CLI and compatibility facade protected by the artifact contract
tests. [`api.py`](api.py) is the narrow private import boundary used by
run-summary reporting; it is not another command or public application API.

After argument parsing, the public facade uses the root-only
[`source_checkout.py`](source_checkout.py) authority to admit the source
checkout that owns the artifact-index implementation before it validates run
inputs or builds a context. Admission requires one canonical, nonsymlink NORAD
Git top level and exact bytes between the executing package and that checkout.
Help and parser failures therefore remain available without checkout admission;
after parsing succeeds, a checkout or package mismatch fails closed before an
input diagnostic. The admitted `SourceCheckout` remains on `BuildContext`
through publication. Its root governs relative inventory and native-contract
paths, Git `HEAD` resolution and producer existence and hashing, and
predecessor, post-publish, and rollback record validation. The authority caches
neither Git commit nor producer state: those observations stay at their
established points in context construction, preserving their timing,
diagnostics, and serialized evidence.

The modules keep observed responsibilities separate: the curated run-summary
API, exact contract loading, models and rosters, explicit adapter registration,
text and binary readers, inspection, named native/scientific reconciliation,
record and receipt assembly, context construction, receipt-last publication,
and published-transaction validation.
Stage-specific rules remain in their named reconciliation modules; this
package is not a generic stage framework.

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
coordinator, rollback, recovery, and cleanup order. The public facade re-exports
the same primitives and remains the live artifact-index fault-injection surface;
run-summary reporting reaches them through the private `api.py` boundary. These
internals do not change artifact schemas, serialized bytes, source discovery
policy, evidence states, diagnostics, or publication order.
