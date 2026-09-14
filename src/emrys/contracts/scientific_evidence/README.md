# Scientific-evidence contracts

These shared APIs validate supplied table bytes and agreement between files:

- [`step08.py`](step08.py): candidate-preprocessing inputs and outputs.
- [`step09.py`](step09.py): the three paired-CMH result tables, mutation spectrum,
  and related validation helpers.
- [`scientific_context.py`](scientific_context.py): candidate context, motifs,
  logos, enrichment, and transactions whose receipt is published last.

Their callers still choose paths, run algorithms, publish artifacts, build
provenance graphs, select candidates, and render figures. Shared validation
replaces neither those responsibilities nor independent test oracles.
