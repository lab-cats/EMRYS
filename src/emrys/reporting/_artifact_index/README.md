# Artifact-index implementation

This private package builds the artifact index for the Run reporting coordinator
and developer fixtures through [`context.py`](context.py) and
[`publication.py`](publication.py). Sibling reporting packages use private
[`api.py`](api.py) for parsing, validation, serialization, and transaction helpers.
Neither interface is a public command or operator recovery route. Filesystem
identity helpers remain in [`source_authority.py`](../../libraries/source_authority.py)
and are not re-exported here.

## Inputs and responsibilities

The coordinator validates explicit source and artifact roots before Run inputs.
Both stay on `BuildContext` under the common
[root rules](../README.md#source-and-artifact-roots). Git `HEAD` and producer
observations remain at their existing points during context construction,
retaining their timing, diagnostics, and recorded evidence.

The immutable Analysis descriptor and composed Run profile supply typed artifact
declarations. `registry.py`, `records.py`, and context preparation derive the
complete adapter set, producer evidence, and expected paths from them. They do
not scan installed modules or discover files. There is no separate database,
service, authored manifest, or public mutable registry.

Modules separate contracts and models, adapters, text/binary readers, inspection,
native-file reconciliation, record/receipt assembly, context preparation,
publication, and published-transaction validation. Text readers are
`_text_common.py` (UTF-8 lines), `_text_tabular.py` (TSV, sample blocks, native
anchors), and `_text_genomic.py` (VCF, references, BED12, STAR, Picard).
Stage-specific reconciliation stays with its named module.

[`reconcile_step09.py`](reconcile_step09.py) uses
`step09.validate_step09_projection` for the result trio and mutation spectrum.
Indexing still selects adapters/inventory, verifies native producer identity,
binds Step 08 paths/hashes/adapters/sample order, and propagates artifact failure.
It does not repeat upstream computation, paired CMH, global BH, PDF/R production,
or the independent oracle.

[`reconcile_step10.py`](reconcile_step10.py) uses
`scientific_context.validate_scientific_context_transaction` for the complete
receipt-last transaction. Indexing binds the declared Step 09 trio, FASTA/FAI,
and four output paths, hashes, and row counts to the artifact graph. Reference
extraction, motif matching, logo/statistic checks, and display selection remain
with their contract or producer, without a second implementation here.

## Validation-report limit

Inspection checks report structure, exact row count, safe unique check IDs,
step, scope, and status. Missing or extra rows and duplicate IDs fail validation.
It does not check each producer's exact ordered check list: reordered rows or
a substituted unique ID can still be marked complete. Existing adapter-mutation
tests demonstrate that distinction. Keep those tests and independent roster
expectations until this separately reviewed defect is fixed.

## Publication

[`publication.py`](publication.py) provides byte writes, durability syncing,
locks, removal, signals, and artifact-index publication order under the common
[recovery contract](../README.md#publication-and-recovery). One
`.artifact-index.<token>.tmp.records` directory holds staged records, index,
and receipt, retaining their file anchors while publishing. Exclusive `mkdir`
reserves the final records directory before linking files. Run-summary
publication uses the shared helpers through `api.py`.
