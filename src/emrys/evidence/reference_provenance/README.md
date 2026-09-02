# Reference-provenance evidence owner

The private [`reconciler.py`](reconciler.py) inventories and reconciles one
explicitly declared reference bundle through
`emrys reconcile reference-provenance`. It checks declared
artifacts and contig agreement; it never repairs, regenerates, discovers, or
selects a reference.

The public interface accepts an inventory, base directory, and output root; it
derives the inventory's single reference ID rather than accepting a separate
ID argument. Its dry run is the default and writes nothing. The reconciler owns
argument definition, reconciliation orchestration, output validation, and
fault-injectable publication. Private modules separately own the
data/error/output contracts, strict inventory admission, artifact observation
and contig reconciliation, and deterministic TSV rendering; none adds a
command or evidence state.

Supported artifact roles cover FASTA, FAI, dictionary, GTF, BED12, STAR
chromosome-name and chromosome-length files, and STAR index members. The
implementation reuses the neutral
[`references/contigs.py`](../../libraries/references/contigs.py) parser without
creating a package API.

Execute mode publishes under `<output-root>/<reference-id>/`:

- `<reference-id>.reference_artifacts.tsv`
- `<reference-id>.reference_contigs.tsv`
- `<reference-id>.reference_summary.tsv`, published last

Exit zero means reconciliation and any requested publication completed; it
does not mean the summary passed. The committed
[`reference_provenance.example.tsv`](../../../../configs/reference_provenance.example.tsv)
is a structural starter that requires real paths, identities, and provenance.
It is not production evidence. Direct protection lives in
[`test_reference_provenance.py`](../../../../tests/evidence/reference_provenance/test_reference_provenance.py).

An ordinary replacement failure restores a complete predecessor. If
restoration itself fails, predecessor `.previous` files remain while the owned
lock is removed and no recovery marker is written. Stop all readers and
writers and preserve every final, staged, backup, and lock path; an absent lock
does not prove a committed publication.

Dry-run, execute, and focused test are:

```bash
emrys reconcile reference-provenance \
  --inventory configs/reference_provenance.example.tsv \
  --base-dir . \
  --output-root results/qc/reference_provenance

mkdir -p results/qc/reference_provenance
emrys reconcile reference-provenance \
  --inventory /explicit/path/to/reference_provenance.tsv \
  --base-dir /explicit/reference/root \
  --output-root results/qc/reference_provenance \
  --execute

.venv/bin/python -m pytest -q \
  tests/evidence/reference_provenance/test_reference_provenance.py
```

Use [`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for
missing, malformed, hash, contig, or publication failures. Current evidence is
local fixture evidence only, not a production reference report or cluster proof.
