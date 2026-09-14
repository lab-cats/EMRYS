# `align_RNA_reads_with_STAR` owner

Stage `01` aligns one declared FASTQ pair to an existing STAR index. Samples
can run independently once their inputs are ready. It produces a
coordinate-sorted BAM, three STAR logs, and a splice-junction table; the BAM
feeds [canonical BAM preparation](../canonical_bam/README.md).

Both mates must use the same plain or gzip format. Supply the sample ID,
index, output directory, threads, STAR executable, and a decompressor for gzip
reads. The Run checks input stability; this does not prove biological pairing.

Execution uses the [Project Run](../README.md#running-a-stage). The shell
script is an internal worker; its help describes the runner interface. The
validator remains directly available:

```bash
bash src/emrys/stages/star_alignment/step_01_star_align.sh --help
emrys validate star-alignment --help
```

The validator reads the five declared outputs without rerunning STAR. The
[contract](CONTRACT.md) defines exact arguments, output checks, and recovery;
structural checks do not establish alignment correctness or biological validity.
