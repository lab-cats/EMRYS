# Ingestion tests

This directory owns local protection for declared-input admission. Its current
child is
[`sample_manifest_admission/`](sample_manifest_admission/README.md), which
protects the bounded sample-manifest and paired-FASTQ interfaces.

The [ingestion owner](../../src/norad/ingestion/README.md) defines placement and
scope. These tests do not discover or acquire inputs, freeze a run request,
execute a pipeline stage, or establish production or scientific evidence.
