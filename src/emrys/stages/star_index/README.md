# `construct_STAR_index` owner

Stage `00a` builds a STAR genome index from an existing FASTA and matching GTF.
It does not choose or download the reference. The completed index lets each
sample proceed to [STAR alignment](../star_alignment/README.md).

Inputs include the STAR executable, threads, splice-junction overhang, and
suffix-array index length. The output is one index directory containing at
least the [15 required files](CONTRACT.md#outputs); extra STAR files are allowed.

Normal execution uses the [Project Run](../README.md#running-a-stage). For a
standalone invocation from the checkout root, start with:

```bash
bash src/emrys/stages/star_index/step_00a_build_star_index.sh --help
emrys validate star-index --help
```

The producer previews by default and refuses an existing output directory.
The validator checks structure and reference/settings agreement without
rerunning STAR. See the [contract](CONTRACT.md) for publication, recovery, and
validation limits; fixture checks are not evidence of real STAR or cluster use.
