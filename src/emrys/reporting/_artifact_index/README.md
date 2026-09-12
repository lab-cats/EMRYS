# Artifact-index implementation

This private package prepares and publishes the Run result manifest and TSV views
as one operation for the Run reporting coordinator and developer fixtures.
[`context.py`](context.py) inspects native artifacts and derives the manifest and its projections;
[`publication.py`](publication.py) owns their combined publication.
Neither interface is a public command or operator recovery route. Filesystem
identity helpers remain in [`source_authority.py`](../../libraries/source_authority.py)
and are not re-exported here.

## Inputs and responsibilities

The coordinator admits the installed package and an independent artifact root
before Run inputs. Both stay on `BuildContext` under the common
[root rules](../README.md#code-and-artifact-roots). Full installed-package identity
is reobserved before attribution and publication; build-origin Git metadata is
recorded for the manifest publisher when available, without running Git.
The manifest separately binds the original scientific Run and Attempt by path
and hash. Those records retain the scientific package, commands, and reused
Attempt origins; reporting does not reconstruct producer attribution from
today's installed files. Both original records join the input rechecks. The manifest also binds the two
existing summary tables by path, hash, and size, so their original bytes remain
verifiable after the reporting code changes.

The canonical processing profile and task definitions supply artifact ownership
through the orchestration contract owner. Reporting adds each
native reader's file, header, and row-count rules; the selected Analysis descriptor
supplies its own typed declarations. The immutable Run profile controls its artifact locations and transaction roster. Current processing ownership comes
from the admitted installed package, so a Run profile cannot authorize an artifact
under another owner. These inputs drive `registry.py`, `records.py`, and context
preparation without scanning installed modules or discovering files.

Modules separate contracts and models, adapters, text/binary readers, inspection,
native-file reconciliation, artifact-entry assembly, context preparation,
and publication. Text readers are
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
Both reconcilers retain their canonical results on the inspected artifacts for
report rendering in the same operation. Reuse requires unchanged source identities
and an exact match to the published Run manifest; it does not trust a receipt alone.

## Validation-report limit

Inspection checks report structure, exact row count, safe unique check IDs,
step, scope, and status. Missing or extra rows and duplicate IDs fail validation.
It does not check each producer's exact ordered check list: reordered rows or
a substituted unique ID can still be marked complete. Existing adapter-mutation
tests demonstrate that distinction. Keep those tests and independent roster
expectations until this separately reviewed defect is fixed.

## Publication

[`publication.py`](publication.py) uses the shared
[`_files.py`](../_files.py) byte writes, durability syncing, locks, and owned-stage
removal, with [`_signals.py`](../_signals.py) interruption handling under the common
[recovery contract](../README.md#publication-and-recovery). One
`.artifact-index.<token>.tmp.records` directory holds the two TSV projections
and the canonical Run result manifest, retaining inode anchors while linking
finals exclusively. The manifest is installed last. Source, input and directory
rechecks cover the full operation; rollback removes only proven owned outputs.
Reuse revalidates native scientific sources and checks the original manifest
against its verified ledger. The manifest binds both existing TSV table hashes,
so reporting-only projection changes do not require rebuilding those tables.
Fresh publication still compares its exact prepared manifest and table bytes.
