# Artifact-index internals

This private package implements the grouped
`python -I -m norad build artifact-index` route through
[`builder.py`](builder.py). The former direct script is retired without a
compatibility shim. [`api.py`](api.py) is the narrow private import boundary
used by run-summary reporting. In addition to artifact parsing, validation,
serialization, and publication primitives, it exposes the shared
`SourceCheckout` token, admission error, and admission function without
importing the command builder. It is not another command or public application
API.

The grouped dispatcher owns the lightweight public parser and imports the
private builder only after selecting this command. Help, parser failures, and
unrelated installed commands therefore do not load artifact-index runtime
dependencies. After argument parsing, the builder uses the required
`--source-checkout` with the root-only
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
neither Git commit nor producer state; the later `HEAD` probe ignores ambient
`GIT_*` routing while preserving unrelated environment state. Those
observations stay at their established points in context construction,
preserving their timing, diagnostics, and serialized evidence.

The grouped `python -I -m norad build run-summary` route uses the same checkout
authority through `api.py`, not through the artifact-index command builder.
After lightweight parsing selects the route, the private run-summary builder
admits its required `--source-checkout` before reading run inputs. That token
remains on the run-summary build context; its root governs contract-relative
artifact, science, and approval paths and semantic, predecessor,
post-publication, and rollback validation. Run-summary Git admission and later
`HEAD` resolution also ignore ambient `GIT_*` routing while preserving
unrelated environment state.

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
coordinator, rollback, recovery, and cleanup order. Its frozen
`ArtifactPublicationOps` record names only the transaction fault seams and is
passed explicitly by tests; production uses the immutable default. The private
builder owns only command coordination and exposes no publication or contract
modules for patching. Run-summary reporting reaches deliberately shared
primitives through the explicit private `api.py` boundary, together with the
shared checkout authority, without importing the builder. These internals do
not change artifact schemas, serialized bytes, source discovery policy,
evidence states, diagnostics, or publication order.
