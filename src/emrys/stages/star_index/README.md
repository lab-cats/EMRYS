# `construct_STAR_index` owner

Stage `00a` builds a STAR genome index from an existing FASTA and matching GTF.
It does not choose or download the reference. The completed index lets each
sample proceed to [STAR alignment](../star_alignment/README.md).

Inputs include the STAR executable, threads, splice-junction overhang, and
suffix-array index length. The output is one index directory containing at
least the [15 required files](CONTRACT.md#outputs); extra STAR files are allowed.

Execution uses the [Project Run](../README.md#running-a-stage). The shell
script is an internal worker; its help describes the runner interface. The
validator remains directly available:

```bash
bash src/emrys/stages/star_index/step_00a_build_star_index.sh --help
emrys validate star-index --help
```

The validator checks structure and reference/settings agreement without
rerunning STAR. See the [contract](CONTRACT.md) for publication, recovery, and
validation limits; fixture checks are not evidence of real STAR or cluster use.
