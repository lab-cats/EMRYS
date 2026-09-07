# `mark_BAM_duplicates_with_Picard` owner

Stage `04` marks duplicates in the admitted canonical BAM and publishes the
marked BAM/BAI pair plus Picard metrics.
[`step_04_mark_duplicates.sh`](step_04_mark_duplicates.sh) is the producer;
validation is `emrys validate duplicate-marking` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact tools, inputs, outputs, transaction,
recovery, validation, and evidence limits. Normal execution belongs to the
immutable `emrys run`/`resume` journey; metrics and structural checks do not
establish scientific or biological validity.
