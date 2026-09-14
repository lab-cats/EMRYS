# Ingestion tests

[Sample-manifest tests](sample_manifest_admission/README.md) check declared
inputs and the paired-FASTQ diagnostic. The
[ingestion owner](../../src/emrys/ingestion/README.md) defines their scope;
these checks do not acquire inputs, freeze a Run, or execute a workflow.
