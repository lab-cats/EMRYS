# `convert_GTF_to_BED12` owner

Stage `00b` converts transcript exon models from a GTF into deterministic
BED12 records for RSeQC orientation evidence. The validator compares the BED12
with its source GTF without modifying either file.

The input is a GTF with `exon` rows, `transcript_id` attributes, and optional
`gene_id` attributes. The output has one sorted BED12 row per valid transcript.
Malformed rows are warned about and skipped; the [contract](CONTRACT.md)
defines transcript rejection, coordinates, and ordering.

Conversion runs through the [Project Run](../README.md#running-a-stage).
The runner owns working paths, publication, logs, and recovery. To check an
existing BED12 against its source GTF, inspect the validator's arguments:

```bash
emrys validate bed12 --help
```

GTF agreement reuses the converter's normalization, so it is not an independent
scientific oracle. This stage does not select, repair, or biologically validate
a reference.
