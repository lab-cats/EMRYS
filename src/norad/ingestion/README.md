# Ingestion owners

This directory contains implemented owners that admit declared external inputs
before computational stages consume them. It does not own operational inboxes,
acquired data, run or attempt state, or neutral cross-orchestration contracts.

| Owner | Role |
| --- | --- |
| [`sample_manifest_admission`](sample_manifest_admission/README.md) | Owns the `python -I -m norad validate manifest` route, validates optional FASTQ-path existence, provides an operator-run paired-FASTQ check, and exposes the lightweight sample-manifest scheduler smoke check. |

The current owner is a bounded admission surface, not an ingestion subsystem or
runner. Nothing here discovers inputs, chooses acquisition policy, copies or
normalizes data, hashes or freezes an admitted request, manages a lifecycle,
executes a pipeline stage, or creates or promotes evidence.

Public starter configuration remains under repository-root
[`configs/`](../../../configs/README.md). Use the
[`RUNBOOK`](../../../docs/operations/RUNBOOK.md) for supported commands and the
[`sample-manifest admission owner`](sample_manifest_admission/README.md) for its
exact interfaces and limits. System placement and dependency boundaries remain
owned by [`SOURCE_TOPOLOGY.md`](../contracts/SOURCE_TOPOLOGY.md)
and [`ARCHITECTURE.md`](../../../docs/architecture/ARCHITECTURE.md).
