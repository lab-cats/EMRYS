# `construct_FASTA_sidecars` owner

Stage `00c` builds a FASTA index (`.fai`) and GATK sequence dictionary (`.dict`)
beside an existing reference FASTA. These support
[SplitNCigarReads](../split_n_cigar/README.md); they are not needed for STAR
alignment or BED12 conversion.

It uses samtools `faidx`, GATK `CreateSequenceDictionary`, and Java 17+.
Existing valid sidecars are reused; missing ones are generated and checked
against the FASTA. The reference itself is not modified or selected here.

Normal execution uses the [Project Run](../README.md#running-a-stage). For
standalone help from the checkout root:

```bash
bash src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh --help
emrys validate fasta-sidecars --help
```

The producer previews by default. Treat the FASTA and sidecars as one set when
investigating failure. The [contract](CONTRACT.md) defines contig checks,
existing-file handling, publication ownership, and retained recovery state.
