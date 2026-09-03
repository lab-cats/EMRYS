# Reference-provenance evidence owner

`emrys reconcile reference-provenance` inventories one explicitly declared
FASTA/FAI/dictionary/GTF/BED12/STAR bundle and reconciles artifact and contig
identity. Private [`reconciler.py`](reconciler.py) owns the dry-run-first
command. It never discovers, selects, repairs, or regenerates a reference.

Execute mode publishes deterministic artifact, contig, and summary TSVs under
`<output-root>/<reference-id>/`, with the summary last. Exit zero means the
requested reconciliation/publication completed, not that every row passed.
The committed inventory is only a structural starter.

A failed restoration can leave predecessor `.previous` files without a lock or
recovery marker. Preserve finals, staging, backups, and locks together; their
absence or presence alone is not committed-publication or production-reference
evidence.
