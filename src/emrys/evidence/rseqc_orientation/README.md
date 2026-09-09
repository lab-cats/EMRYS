# `collect_RSeQC_paired_orientation_evidence` owner

Operation `03` runs RSeQC `infer_experiment.py` on one BAM and BED12 annotation.
It records fractions assigned to two paired-read orientation groups or left
undetermined. These are mechanical observations, not transcript-strand or
sense/antisense conclusions; they never update manifest `strandedness`.

Inputs are the sample ID, BAM with adjacent BAI, BED12, output directory, and
RSeQC executable. The output is `<sample>.infer_experiment.txt`.

The normal Run includes this operation. For standalone help from the checkout
root, invoke the script through Bash:

```bash
bash src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh --help
emrys validate rseqc-orientation --help
```

The producer previews by default and refuses an existing report. The
[contract](CONTRACT.md) owns exact labels, fraction tolerance, publication,
recovery, and historical behavior. Passing validation does not select a
biological interpretation or make this evidence a computational gate.
