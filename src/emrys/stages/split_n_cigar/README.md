# `split_N_cigar_reads_with_GATK` owner

Stage `05` runs GATK `SplitNCigarReads` on a duplicate-marked RNA-seq BAM and
publishes a checked, indexed BAM. The split pair feeds
[mechanical orientation partitioning](../mechanical_orientation/README.md).

It needs the marked BAM and exact adjacent BAI, an existing FASTA/FAI/dictionary
set, GATK, samtools, Java 17+, and project-storage temporary space. It does not
create or repair missing reference sidecars.

Execution uses the [Project Run](../README.md#running-a-stage). The shell
script is an internal worker; its help describes the runner interface. The
validator remains directly available:

```bash
bash src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh --help
emrys validate split-n-cigar --help
```

The [contract](CONTRACT.md) retains the historical restoration defect and
current native checks. Structural validation does not
prove the GATK transformation, sample identity, or biological validity.
