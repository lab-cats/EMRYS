# Reference-provenance evidence owner

[`reference_provenance.py`](reference_provenance.py) inventories and reconciles
one explicitly declared reference bundle. It checks declared artifacts and
contig agreement; it never repairs, regenerates, discovers, or selects a
reference.

The public interface accepts an inventory, base directory, and output root; it
derives the inventory's single reference ID rather than accepting a separate
ID argument. Its dry run is the default and writes nothing. Supported artifact
roles cover FASTA, FAI, dictionary, GTF, BED12, STAR chromosome-name and
chromosome-length files, and STAR index members. The implementation reuses the
neutral [`references/contigs.py`](../../libraries/references/contigs.py) parser
without creating a package API.

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

Dry-run, execute, and focused test are:

```bash
.venv/bin/python src/norad/evidence/reference_provenance/reference_provenance.py \
  --inventory configs/reference_provenance.example.tsv \
  --base-dir . \
  --output-root results/qc/reference_provenance

mkdir -p results/qc/reference_provenance
.venv/bin/python src/norad/evidence/reference_provenance/reference_provenance.py \
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
