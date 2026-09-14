# `construct_canonical_BAM` owner

Stage `02` prepares a coordinate-sorted, read-group-tagged BAM and adjacent BAI
from one SAM or BAM. STAR is the usual input source, but STAR-specific names
and logs are not required. An already canonical alignment can be reused without
sorting or retagging it.

Supply a sample ID, alignment, output directory, threads, and samtools.
The outputs are `<sample>.sorted.bam` and `<sample>.sorted.bam.bai`, used by
BAM QC, RSeQC orientation evidence, and duplicate marking.

Execution uses the [Project Run](../README.md#running-a-stage). The shell
script is an internal worker; its help describes the runner interface. The
validator remains directly available:

```bash
bash src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh --help
emrys validate canonical-bam --help
```

The independent validator checks containers, sorting, read groups, and alignment tags without
changing the pair. Read the [contract](CONTRACT.md) before handling residue:
it preserves important producer/validator differences and the historical
replacement defect. Neither surface proves sample identity or biological validity.
