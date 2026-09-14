# `mark_BAM_duplicates_with_Picard` owner

Stage `04` marks PCR/optical duplicates in a canonical BAM without removing
reads. Picard produces a marked BAM and metrics; samtools creates its index.
The marked pair feeds [SplitNCigarReads](../split_n_cigar/README.md).

Supply the BAM and exact adjacent `<bam>.bai`, sample ID, output/metrics
locations, Picard jar, Java, samtools, and writable temporary space.

Execution uses the [Project Run](../README.md#running-a-stage). The shell
script is an internal worker; its help describes the runner interface. The
validator remains directly available:

```bash
bash src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh --help
emrys validate duplicate-marking --help
```

The [contract](CONTRACT.md) describes native checks and retained limits. Validation
checks structure and metrics, not duplicate-marking accuracy or biological validity.
