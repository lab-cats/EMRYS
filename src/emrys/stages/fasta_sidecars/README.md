# `construct_FASTA_sidecars` owner

Stage `00c` constructs the FAI and sequence-dictionary sidecars for one
admitted FASTA. The repository producer is
[`step_00c_prepare_gatk_reference.sh`](step_00c_prepare_gatk_reference.sh);
structural validation is `emrys validate fasta-sidecars` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact tools, inputs, two-output transaction,
no-clobber and recovery behavior, validation, and evidence limits. Normal
execution belongs to the immutable `emrys run`/`resume` journey; this owner
does not choose or silently repair a reference bundle.
