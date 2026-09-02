# `align_RNA_reads_with_STAR` owner

Stage `01` aligns admitted paired FASTQs against an admitted STAR index and
publishes the coordinate BAM plus the four declared STAR log/junction files.
[`step_01_star_align.sh`](step_01_star_align.sh) is the producer; validation is
`emrys validate star-alignment` through private [`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, outputs, tools, transaction,
recovery, validation, and evidence meaning. Normal execution belongs to the
immutable `emrys run`/`resume` journey. Structural checks do not establish
alignment correctness or real-runtime, scheduler, or production evidence.
