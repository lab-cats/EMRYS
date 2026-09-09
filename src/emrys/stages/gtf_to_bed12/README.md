# `convert_GTF_to_BED12` owner

Stage `00b` converts transcript exon models from a GTF into deterministic
BED12 records for RSeQC orientation evidence. The validator compares the BED12
with its source GTF without modifying either file.

Inputs are the GTF and optional feature/transcript/gene selectors. The output
has one sorted BED12 row per valid transcript. Malformed rows are warned about
and skipped; the [contract](CONTRACT.md) defines transcript-level rejection,
coordinates, ordering, and publication/recovery rules.

Use the [Project Run](../README.md#running-a-stage) for normal processing.
The Run uses the shared normalization code through its internal worker. The
independently useful conversion and validation commands expose their arguments
through:

```bash
emrys convert gtf-to-bed12 --help
emrys validate bed12 --help
```

Conversion previews by default and refuses an existing destination. GTF
agreement reuses the converter's normalization, so it is not an independent
scientific oracle. This stage does not select, repair, or biologically validate
a reference.
