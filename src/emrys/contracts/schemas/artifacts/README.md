# Current artifact schemas

The closed [artifact contract registry](../../artifacts/README.md) admits only current documents:

- [Artifact entries](v2/artifact_record.schema.json) contain independent artifact state.
- [Run result manifest v5](v3/run_summary.schema.json) owns shared Run identity, input bindings and publication provenance.
- [Report receipt v6](v5/report_receipt.schema.json) binds both HTML projections, their data inputs and their original renderer identities.
- [Common definitions](v1/common.schema.json) supply shared paths, hashes, status and evidence vocabulary.

Older document versions are unsupported. Stored Run data and retained evidence are not migrated or deleted.
