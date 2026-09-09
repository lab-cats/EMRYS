# Run-summary implementation

This private package derives deterministic Run summaries from admitted artifact
records. The [artifact-index owner](../_artifact_index/README.md) prepares and
publishes the index and summary together. Summary generation has no separate
publisher, lock, command, or recovery interface.

| Module | Responsibility |
| --- | --- |
| [`document.py`](document.py) | Admit the Analysis policy and assemble canonical JSON and TSV projections from the same artifact records. |
| [`projection.py`](projection.py) | Derive computational status, summary rows, and QC rows. |
| [`validation.py`](validation.py) | Validate existing summaries and receipts; assemble the new receipt. |
| [`models.py`](models.py) | Constants, headers, errors, and output paths. |
| [`inputs.py`](inputs.py) | Admit existing summary files. |
| [`transaction.py`](transaction.py) | Stable value and historical-attempt helpers. |

Flat paired-CMH summaries retain v2; explicit modules retain v3 and their
Analysis-policy path, hash, and size. Artifact and summary files keep their
formats. The summary receipt is published last and completes the combined
operation; the artifact receipt remains bound provenance data.

[`transaction_validation.py`](../transaction_validation.py) reads current and
historical summaries without preparing a new publication. It reuses admitted
artifact records, reconstructs the expected projections, and checks their
bytes, source identities, receipts, and bound inputs. Historical reads retain
recorded producer identities and never authorize replacement or regeneration.

The summary records computational state. Candidate review, adjudication,
biological interpretation, and scientific completion remain external processes.
