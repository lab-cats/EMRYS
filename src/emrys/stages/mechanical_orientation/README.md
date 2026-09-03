# `partition_BAM_by_mechanical_read_orientation` owner

Stage `06` partitions the admitted split-N-cigar BAM into `FWD_like` and
`REV_like` BAM/BAI pairs and publishes mechanical count evidence. Private
[`producer.py`](producer.py) performs the workflow transaction; validation is
`emrys validate mechanical-orientation` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, five outputs, transaction,
recovery, validation, and evidence meaning. The labels are flag groups—not
transcript strand, sense, antisense, or a biological interpretation.
