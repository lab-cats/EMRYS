# `partition_BAM_by_mechanical_read_orientation` owner

Stage `06` divides one split-N-cigar BAM into the legacy `FWD_like` and
`REV_like` flag groups, indexes both outputs, and records their counts. These
labels describe SAM flags, not transcript strand, sense, or antisense.

The inputs are the BAM and exact adjacent BAI, sample ID, output/QC locations,
threads, owner token, and selected samtools. The five outputs are two BAM/BAI
pairs and `<sample>.orientation_counts.tsv`. Unassigned reads are allowed;
the operation does not claim to partition every read.

The private [producer](producer.py) runs through the
[Project Run](../README.md#running-a-stage), publishing only to absent paths.
For the standalone structural validator's arguments:

```bash
emrys validate mechanical-orientation --help
```

The [contract](CONTRACT.md) defines exact flag groups, count arithmetic,
publication, and recovery. Validation neither runs samtools nor recounts BAMs;
count evidence and producer checks therefore answer different questions.
