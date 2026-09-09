# `mark_BAM_duplicates_with_Picard` owner

Stage `04` marks PCR/optical duplicates in a canonical BAM without removing
reads. Picard produces a marked BAM and metrics; samtools creates its index.
The marked pair feeds [SplitNCigarReads](../split_n_cigar/README.md).

Supply the BAM and exact adjacent `<bam>.bai`, sample ID, output/metrics
locations, Picard jar, Java, samtools, and writable temporary space.

Normal execution uses the [Project Run](../README.md#running-a-stage). For
standalone help from the checkout root:

```bash
bash src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh --help
emrys validate duplicate-marking --help
```

The Run uses `--no-clobber` to protect existing outputs. Standalone execute
without it retains a direct-write route that can leave partial results; review
the [contract](CONTRACT.md) before using it or handling failed output. Validation
checks structure and metrics, not duplicate-marking accuracy or biological validity.
