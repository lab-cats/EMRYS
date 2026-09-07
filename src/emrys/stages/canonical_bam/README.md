# `construct_canonical_BAM` owner

Stage `02` converts the admitted STAR BAM into the canonical coordinate-sorted
BAM/BAI pair. [`step_02_sort_index_bam.sh`](step_02_sort_index_bam.sh) is the
producer; validation is `emrys validate canonical-bam` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, outputs, transaction, recovery,
validation, and evidence meaning. Normal execution belongs to the immutable
`emrys run`/`resume` journey. Container and header checks do not prove sample
identity, alignment correctness, or biological validity.
