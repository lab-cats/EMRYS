# Data workspace

`data/` is the repository-local landing area for inputs that have already been
obtained and approved for use. It is storage, not an ingestion queue: no
implemented NORAD owner downloads, normalizes, or advances inputs through a
data lifecycle.

## Contents

- `raw/` and `full/` are ignored operator-managed locations for large inputs.
- `test/` is the retained local fixture path used by
  [`samples.example.tsv`](../samples.example.tsv),
  [`configs/local_test.yaml`](../configs/local_test.yaml), and Step `01` dry-run
  defaults. Directory or placeholder-file presence alone does not establish a
  runnable fixture or production evidence.

Exact cluster storage conventions belong in the
[runbook](../docs/operations/RUNBOOK.md#project-locations). Manifests declare
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
