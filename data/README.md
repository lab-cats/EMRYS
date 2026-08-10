# Data workspace

`data/` is the repository-local landing area for inputs that have already been
obtained and approved for use. It is storage, not an ingestion queue: no
implemented NORAD owner downloads, normalizes, or advances inputs through a
data lifecycle.

## Contents

- `raw/` and `full/` are ignored operator-managed locations for large inputs.
- [`test/`](test/) is the retained local fixture workspace named by the structural
  [`sample-manifest starter`](../configs/samples.example.tsv); no orchestrator
  wires that starter into a run. Independently, the
  [Step `01` scheduler owner](../src/norad/stages/align_RNA_reads_with_STAR/README.md)
  uses only the `sample_001` mate paths as current default dry-run placeholders.
  Directory or placeholder-file presence alone does not establish a runnable
  fixture or production evidence.

Verify site and checkout context through the cross-cutting
[runbook](../docs/operations/RUNBOOK.md#checkout-and-site-orientation). Manifests declare
sample paths and metadata, while reference-provenance records characterize
registered references. Directory placement alone is not provenance, and no
implemented ingestion owner currently creates an immutable raw-input run
contract.

## Retention and cleanup

FASTQs and other large or sensitive inputs stay out of Git; only tiny safe
fixtures may be tracked. Do not move or delete nonempty operator data without
checking its identity, persistence, active consumers, and approved retention
policy. Before removing local test material, distinguish reproducible dry-run
placeholders from real inputs.
