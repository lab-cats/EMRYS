# Reference-provenance evidence owner

This command checks one explicitly listed FASTA/FAI/dictionary/GTF/BED12/STAR
bundle for file and contig agreement. It never discovers, selects, repairs,
or regenerates a reference.

## Use and outputs

Start with the [inventory format](../../../../configs/reference_provenance.example.tsv),
replacing its structural example with your declared files. Relative inventory
paths use the explicit `--base-dir`. Preview without writing:

```bash
emrys reconcile reference-provenance \
  --inventory /absolute/path/to/reference_inventory.tsv \
  --base-dir /absolute/reference/base \
  --output-root /absolute/existing/output-directory
```

Add `--execute` to publish artifact, contig, and summary TSVs under
`<output-root>/<reference-id>/`, with the summary last. Exit zero means the
requested reconciliation/publication completed, not that every row passed.
[`reconciler.py`](reconciler.py) owns the command and publication behavior.

## Known publication limits

Replacement moves all predecessors to `.previous` paths before entering the
handler that rolls back final publication. Failure during those backup moves
can therefore leave an incomplete final set without restoring earlier moves.
If publication fails and restoring a predecessor also fails, cleanup can release
the lock while backups remain, without a recovery marker. A restoration error
can become the reported exception instead of the original publication error;
later cleanup failures may interrupt the remaining cleanup steps.

These are retained implementation defects, not an approved recovery procedure.
The [owner tests](../../../../tests/evidence/reference_provenance/test_reference_provenance.py)
characterize failed restoration. Preserve finals, staging, backups, and locks
together. Their presence or absence alone proves neither completed publication
nor a production-ready reference.
