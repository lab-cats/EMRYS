# Sample-manifest tests

These tests check malformed manifests and values, optional file-existence
checks, execution from other working directories, and paired-FASTQ counts and
leading read IDs. The [input owner](../../../src/emrys/ingestion/sample_manifest_admission/README.md)
defines accepted inputs and commands.

Tiny generated FASTQs do not prove complete pairing, sample identity, or
provenance. The [shared evidence limits](../../README.md#evidence-limits) also apply.
