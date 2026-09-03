# `construct_STAR_index` owner

Stage `00a` builds the declared 15-member STAR index from an admitted FASTA,
GTF, STAR executable, and indexing policy. The repository producer is
[`step_00a_build_star_index.sh`](step_00a_build_star_index.sh); structural
validation is exposed as `emrys validate star-index` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, outputs, no-clobber publication,
recovery, validation, and evidence limits. Normal execution belongs to the
immutable `emrys run`/`resume` journey. This owner neither selects a reference
nor treats fixture validation as real STAR, scheduler, or production evidence.
