Begin designing manifest-driven execution, but don’t build the whole thing yet

The next architectural piece is: how does a SLURM array pick sample N from samples.tsv?

You’ll eventually want a tiny helper like:

scripts/get_manifest_row.py \
  --manifest samples.tsv \
  --row "$SLURM_ARRAY_TASK_ID"

or:

scripts/get_sample_from_manifest.py \
  --manifest samples.tsv \
  --sample-id sample_001

But don’t build this until Step 02 is done. Otherwise you’ll start weaving layers too early.

Still ask for the real data/reference paths

Even if you can keep building, this remains the external blocker:

input data location
STAR index path
genome build
annotation version
strandedness confirmation
project/scratch output path
SLURM partition/account/memory rules
Stop when Step 02 is green

Tomorrow’s “excellent” outcome is:

Step 01 STAR wrapper tested + SLURM dry-run works
Step 02 samtools sort/index wrapper tested + SLURM dry-run works
Makefile runs all checks
docs updated
everything committed/pushed