# Run result manifest

This private package derives the canonical Run result manifest and its human
TSV views from admitted artifact entries. The [artifact-index owner](../_artifact_index/README.md)
prepares and publishes that output set under one lock. No separate summary
receipt, publisher, or recovery interface remains.

| Module | Responsibility |
| --- | --- |
| [`document.py`](document.py) | Admit the current module policy and assemble the manifest and TSV projections. |
| [`projection.py`](projection.py) | Derive computational status, artifact summary rows, and QC rows. |
| [`validation.py`](validation.py) | Validate the manifest schema, semantics and inventory. |
| [`models.py`](models.py) | Constants, table headers, errors and output paths. |
| [`transaction.py`](transaction.py) | Stable value projections. |

`RUN_ID.run_summary.json` v4 contains the shared Run contract, immutable input
bindings, publication identity, provenance, and ordered artifact entries.
Installing it last commits the two TSV projections. The reader reconstructs
these values from current sources and checks canonical bytes and bound file
identities. Old-version Runs are unsupported and never migrated or deleted.

The manifest records computational state. Candidate review, adjudication,
biological interpretation, and scientific completion remain external processes.
