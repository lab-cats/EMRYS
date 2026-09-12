# Artifact contracts

`emrys validate artifact-contracts` checks current artifact entries, Run result
manifests, report receipts and explicit inventories through private
[`validator.py`](validator.py). Reporting uses [`api.py`](api.py). These interfaces
validate supplied data; they do not discover artifacts, repair inputs, or promote
evidence.

The [schema index](../schemas/artifacts/README.md) defines the current formats.
A Run result manifest stores shared Run identity and publication provenance once,
plus the exact original scientific Run and Attempt references. Artifact entries
retain independent source, computation, validation and Attempt evidence. Schema and semantic admission reject old document versions.
The CLI and reporting readers use the same current schema registry.
