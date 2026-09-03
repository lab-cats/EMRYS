# `split_N_cigar_reads_with_GATK` owner

Stage `05` applies GATK SplitNCigarReads to the admitted marked BAM using the
admitted FASTA sidecars and publishes one BAM/BAI pair.
[`step_05_split_n_cigar_reads.sh`](step_05_split_n_cigar_reads.sh) is the
producer; validation is `emrys validate split-n-cigar` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact tools, inputs, outputs, transaction,
recovery, validation, and retained defects. Normal execution belongs to the
immutable `emrys run`/`resume` journey; structural checks do not prove the GATK
transform, sample identity, or biological validity.
